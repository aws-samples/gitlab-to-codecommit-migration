import json
import os
import logging
import re
import boto3
import requests

logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    print(json.dumps(event))
    log_level = os.environ.get('LOG_LEVEL')
    if log_level:
        logger.setLevel(log_level)

    p = "arn:aws:codecommit:.*:\\d{12}:(.*)"

    # Records in events, when CloudWatch Events to SNS to Lambda
    if 'Records' in event:
        for record in event['Records']:
            event_source = record["EventSource"]
            if event_source == "aws:sns":
                j = json.loads(record['Sns']['Message'])
                logger.debug(j)
                # if Records, then commit related message assumed
                if 'Records' in j:
                    code_commit_client = boto3.client('codecommit')
                    for commit_record in j['Records']:
                        repository_name = re.match(p, commit_record['eventSourceARN'])[1]
                        code_commit_info = commit_record['codecommit']
                        for reference in code_commit_info['references']:
                            commit_id = reference.get('commit')
                            get_commit_response = code_commit_client.get_commit(
                                repositoryName=repository_name,
                                commitId=commit_id)
                            post_to_chime(get_commit_response.get('commit').get('message'))
                # if detail, then pull request related message assumed
                elif 'detail' in j:
                    post_to_chime(j['detail']['notificationBody'])
                # Assume plain message
                else:
                    post_to_chime(record['Sns']['Message'])
            else:
                logger.error(f"unsupported event source: {event_source}")
                raise Exception(f"unsupported event source: {event_source}")
    # detail-type when source is CloudWatch Events direct to Lambda
    elif 'detail-type' in event:
        source = event.get('source')
        if source == 'aws.codecommit':
            # commit
            if event['detail-type'] == "CodeCommit Repository State Change":
                detail = event.get('detail')
                repository_name = detail.get('repositoryName')
                commit_id = detail.get('commitId')
                code_commit_client = boto3.client('codecommit')
                get_commit_response = code_commit_client.get_commit(
                    repositoryName=repository_name,
                    commitId=commit_id)
                message = get_commit_response.get('commit').get('message')
                author = get_commit_response.get('commit').get('author').get('name')
                committer = get_commit_response.get('commit').get('committer').get('name')
                post_to_chime(f'{author}/{committer}: {message}')
            # Pull Request
            elif event['detail-type'] in ['CodeCommit Comment on Commit', 'CodeCommit Comment on Pull Request', 'CodeCommit Pull Request State Change']:
                detail = event.get('detail')
                message = detail['notificationBody']
                post_to_chime(message)
        elif source == 'aws.codebuild':
            if event['detail-type'] == "CodeBuild Build State Change":
                detail = event.get('detail')
                message = f"{detail['project-name']} CodeBuild: {detail['build-status']}, logs: {detail['additional-information']['logs']['deep-link']}"
                post_to_chime(message)
        else:
            logger.error(f"unsupported event source: {event.get('source')}")
            raise Exception(f"unsupported event source: {event.get('source')}")


def post_to_chime(message):
    http_endpoint = os.environ.get('HTTP_ENDPOINT')
    logger.debug(http_endpoint)
    logger.debug(f'message: {message}')
    data = {'Content': f'@All : {message}'}
    encoded_data = json.dumps(data).encode('utf-8')
    headers = {'Content-Type': 'application/json'}
    http_response = requests.post(http_endpoint, body=encoded_data, headers=headers)
    logger.debug(http_response)
