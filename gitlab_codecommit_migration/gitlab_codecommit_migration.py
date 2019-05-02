import os
import logging
import sys
import boto3
import pathlib
import re
import shutil
import subprocess

logger = logging.getLogger(__name__)

artifacts_stack_name = 'gitlab-migration-account-setup'
code_artifacts_bucket_export = 'CodeArtifactsBucket'

python_script_dir = os.path.dirname(os.path.realpath(__file__))
infrastructure_folder_path = os.path.join(python_script_dir, '..', 'cloudformation')


def migrate(projects, path_local_target_clone_repos='/tmp', chime_webhook_url=None, log_level=logging.INFO):

    cfn_client = boto3.client('cloudformation')
    boto_session = boto3.Session()
    logger.info(f'region_name: {boto_session.region_name}')

    logging.basicConfig(stream=sys.stdout, level=log_level)

    # create artifacts bucket for Lambda and CodePipeline

    artifacts_bucket = next((x['Value'] for x in cfn_client.list_exports().get('Exports')
                             if x['Name'] == code_artifacts_bucket_export), None)

    if not artifacts_bucket:
        with open(os.path.join(python_script_dir, infrastructure_folder_path, 'account-setup.yaml')) as account_setup_template_file:
            cfn_result = cfn_client.create_stack(
                StackName=artifacts_stack_name,
                TemplateBody=account_setup_template_file.read()
            )
            waiter = cfn_client.get_waiter('stack_create_complete')
            logger.info(f'Waiting for stack: {artifacts_stack_name} to complete')
            waiter.wait(StackName=artifacts_stack_name)
            stack_status = cfn_client.describe_stacks(StackName=artifacts_stack_name)['Stacks'][0]['StackStatus']
            if stack_status not in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
                logger.error(f'Stack creation for {artifacts_stack_name} failed., status is {stack_status}')
                sys.exit(1)

    artifacts_bucket = next((x['Value'] for x in cfn_client.list_exports().get('Exports')
                             if x['Name'] == code_artifacts_bucket_export), None)

    # still no artifacts bucket
    if not artifacts_bucket:
        logger.error(f"No CloudFormation export for '{code_artifacts_bucket_export}' found.")
        sys.exit(1)

    code_environment_template_name = 'code-environment-setup.yaml'
    packaged_template_file_name = f'{code_environment_template_name}-packaged.yaml'

    # clean tmp folder
    local_temp_dir = f'{path_local_target_clone_repos}/gitlab'
    if os.path.exists(local_temp_dir):
        shutil.rmtree(local_temp_dir, ignore_errors=True)

    # build the template
    build_command = ['sam', 'build', '--template', f'{infrastructure_folder_path}/{code_environment_template_name}']
    if chime_webhook_url:
        build_command.extend(['--parameter-overrides', f'ParameterKey=HTTPWebHookParam,ParameterValue={chime_webhook_url}'])

    try:
        with open(os.path.join(infrastructure_folder_path, code_environment_template_name)) as template_file:
            r = subprocess.run(build_command,
                               cwd=infrastructure_folder_path,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)

        for p in projects:
            logger.info(p['path_with_namespace'])
            path_with_namespace = p['path_with_namespace']
            namespace = ''
            project_name = path_with_namespace
            if '/' in path_with_namespace:
                namespace, project_name = path_with_namespace.split('/')
                print(f'{namespace} and {project_name}')

            local_clone_dir = f'{local_temp_dir}/{namespace}'
            # create subdir for namespace if not exists
            if not pathlib.Path(local_clone_dir).exists():
                pathlib.Path(local_clone_dir).mkdir(parents=True, exist_ok=True)

            # clone from GitLab
            r = subprocess.run(['git', 'clone', '--mirror', p['ssh_url_to_repo'], project_name],
                               cwd=local_clone_dir,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               check=True)
            logger.info(f'stdout: {r.stdout}\nstderr:{r.stderr}')

            # Create stack with Repo
            # sub chars that may conflict with stack-naming convention
            stack_name = re.sub(r'[^-a-zA-Z0-9]', "-", f'{namespace}-{project_name}')

            package_command = ['sam', 'package', '--s3-bucket', f'{artifacts_bucket}',
                               '--template-file', code_environment_template_name, '--s3-prefix', f'{stack_name}',
                               '--output-template-file', packaged_template_file_name]

            r = subprocess.run(package_command,
                               cwd=infrastructure_folder_path,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               check=True)
            logger.info(f'{r.stdout}\n{r.stderr}')

            deploy_command = ['sam', 'deploy', '--template-file', f'{packaged_template_file_name}',
                              '--stack-name', f'{stack_name}',
                              '--capabilities', 'CAPABILITY_IAM', '--no-fail-on-empty-changeset']

            if chime_webhook_url:
                deploy_command.extend(['--parameter-overrides', f'HTTPWebHookParam={chime_webhook_url}'])

            r = subprocess.run(deploy_command,
                               cwd=infrastructure_folder_path,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               check=True)

            logger.info(f'{r.stdout}\n{r.stderr}')

            response = cfn_client.describe_stacks(
                StackName=stack_name
            )

            ssh_url = ''
            for output in response['Stacks'][0]['Outputs']:
                if 'CodeRepoSSH' == output['OutputKey']:
                    ssh_url = output['OutputValue']
                    break

            if not ssh_url:
                logger.error(
                    f'no ssh_url for stack {stack_name} found. Can not recover from that and have to exit with failure.')
                sys.exit(1)

            logger.info(f'ssh_url: {ssh_url}')

            # add remote
            r = subprocess.run(['git', 'remote', 'add', 'codecommit', ssh_url],
                               cwd=f'{local_clone_dir}/{project_name}',
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               check=True)
            logger.info(f'stdout: {r.stdout}\nstderr:{r.stderr}')

            # push to remote
            r = subprocess.run(['git', 'push', '--mirror', 'codecommit'],
                               cwd=f'{local_clone_dir}/{project_name}',
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
            logger.info(f'stdout: {r.stdout}\nstderr:{r.stderr}')

            # clean up the local git mirror folder
            shutil.rmtree(local_clone_dir)
    except subprocess.CalledProcessError as cpe:
        logger.error(f'returncode: {cpe.returncode}\ncmd: {cpe.cmd}\noutput: {cpe.output}\nstdout: {cpe.stdout}\nstderr: {cpe.stderr}' )

