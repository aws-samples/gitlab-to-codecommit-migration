## GitLab to CodeCommit Migration

Script to migrate from GitLab to Amazon CodeCommit easily and setup your AWS environment with CodeCommit, CodePipeline and CodeDeploy as well.

## License Summary

This sample code is made available under the MIT-0 license. See the LICENSE file.


## Requirements
I wrote and tested the solution in Python 3 and assume pip and git are installed.

## Setup
Just run a pip install on command line: pip install gitlab-to-codecommit-migration
Create a personal access token in GitLab (instructions)
If not already setup, configure ssh-key based access for your user in GitLab (instructions) and AWS (instructions). Using the same key is fine.
Setup your ```~/.ssh/config``` to have one entry for the GitLab server and one for the CodeCommit environment. Example:
```
Host my-gitlab-server-example.com
  IdentityFile ~/.ssh/<your-private-key-name>

Host git-codecommit.*.amazonaws.com
  User APKEXAMPLEEXAMPLE-replace-with-your-user
  IdentityFile ~/.ssh/<your-private-key-name>
```

This way the git client uses the key for both domains and the correct user. Make sure to use the "SSH key ID" and not the "Access key ID", a mistake I made at one point actually and was wondering for a couple of minutes why it failed.

Configure your AWS CLI environment (Configuring the AWS CLI - essentially run aws configure ) in order to execute the CloudFormation template creation part of the script successful. For larger migrations I recommend to run the script on a small EC2 instance and use a role attached to the instance with all relevant permissions. Or use a small instance in your DC with a terminal multiplexer like tmux. You can also run it locally on your laptop to test it out or do smaller migrations. The instance just needs HTTP/S and SSH port access to the GitLab server and the HTTPS access through the Internet to access AWS APIs for CloudFormation.

### Limits 
* If you migrate more than 33 repositories, you should check the CloudWatch Events limit, which has a default of 100 https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/cloudwatch_limits_cwe.html. The link to increase the limits is on the same page. The setup uses CloudWatch Events Rules to trigger the pipeline (1 rule) and notifications (2 rules) to Chime for a total of 3 CloudWatch Events Rule per pipeline.
* For even larger migrations of more than 200 repos you should check CloudFormation limits, which default to max 200  (aws cloudformation describe-account-limits), CodePipeline has a limit of 300 and CodeCommit has a default limit of 1000, same as the CodeBuild limit of 1000. All the limits can be increased through a ticket and the link is on the limits page in the documentation.

## Migration
After everything is setup you can test it with one project by calling on command line:

```
> gitlab-to-codecommit
INFO:botocore.credentials:Found credentials in shared credentials file: ~/.aws/credentials
INFO:gitlab_codecommit_migration.gitlab_codecommit_migration:region_name: us-east-1
usage: gitlab-to-codecommit [-h] --gitlab-access-token GITLAB_ACCESS_TOKEN
                            --gitlab-url GITLAB_URL
                            [--chime-webhook-url CHIME_WEBHOOK_URL]
                            [--path-local-target-clone-repos PATH_LOCAL_TARGET_CLONE_REPOS]
                            (--repository-names REPOSITORY_NAMES [REPOSITORY_NAMES ...] | --all | --users USERS [USERS ...] | --groups GROUPS [GROUPS ...])
gitlab-to-codecommit: error: the following arguments are required: --gitlab-access-token, --gitlab-url
```

As you see the command requires at least a gitlab-access-token and a gitlab-url and one of the options to define which projects you would like to migrate.
Let's go with just one sample project:

```
gitlab-to-codecommit --gitlab-access-token youraccesstokenhere --gitlab-url https://gitlab.yourdomain.com --repository-names namespace/sample-project
```

It will take around 30 seconds for the CloudFormation template to create the AWS CodeCommit repository and the AWS CodePipeline and deploy the Lambda function. While deploying or when you are interested in the setup you can check the state in the AWS Console in the CloudFormation service section and look at the template.

Pushing the code depends on the size of your repository. Once you see this running successful you can continue to push all or a subset of projects.

```
gitlab-to-codecommit --gitlab-access-token youraccesstokenhere --gitlab-url https://gitlab.yourdomain.com --all
```

I also included a script to set repositories to read-only in GitLab, because to be sure you catch all the updates and got migrated to CodeCommit it is good to have this option (```gitlab-set-read-only```).

## Remarks

The script does not migrate user accounts and does not setup those in AWS IAM. There is potential to automate that as well, but requirements may be different. Would be happy to hear from you if this is a feature you would like to see and what your requirements are (e. g. which access levels you have, if you use groups, if you have a federated access setup).

Currently only supports ssh-key based migration. If you require https based, because of firewall rules for example, please let us know.

The migration is sequentially and running a script. This was sufficient for me, but I could see use cases where a higher level of concurrency for even larger migrations than mine (more commits, more and larger source repos) could be useful.

I was thinking about making it Lambda/serverless, but ultimately opted for a script to avoid going through potential networking setup to give Lambda access to your GitLab environment if it is not publicly accessible. Lambda would solve the concurrency requirement by breaking up the individual project migrations and the limit would be the API throttle for GitLab. Let us know when you plan larger scale migrations or more frequent ones, then this becomes quite interesting.

Currently only Chime is supported out of the box for notifications, but it is easy write your own Lambda or use SNS to push to other endpoints. Let me know which one you would like to use (Slack, anyone?).

The CloudFormation template has a DeletionPolicy: Retain for the CodeCommit Repository to avoid accidentally deleting the code when deleting the CloudFormation template. If you want to remove the CodeCommit repository as well at one point, you can change the default behavior or delete the repository through API, CLI or Console. During testing I would sometimes fail the deployment of a template because I didn't delete the CodeCommit repository after deleting the CloudFormation template. For migration purposes you will not run into any issues and not delete a CodeCommit repository by mistake when deleting a CloudFormation template.
