## GitLab to CodeCommit Migration

Script to migrate from GitLab to Amazon CodeCommit easily and setup your AWS environment with CodeCommit, CodePipeline and CodeDeploy as well.

## License Summary

This sample code is made available under the MIT-0 license. See the LICENSE file.

## Setup

* Run a pip install on a command line: ```pip install gitlab-to-codecommit-migration```
* Create a personal access token in GitLab href="https://docs.gitlab.com/ce/user/profile/personal_access_tokens.html">instructions
* Configure ssh-key based access for your user in GitLab https://docs.gitlab.com/ce/gitlab-basics/create-your-ssh-keys.html 
* Setup your AWS account for CodeCommit following https://docs.aws.amazon.com/codecommit/latest/userguide/setting-up-ssh-unixes.html. You can use the same SSH key for both, GitLab and AWS.
* Setup your <code class="lang-bash">~/.ssh/config</code> to have one entry for the GitLab server and one for the CodeCommit environment. Example:
```
  IdentityFile ~/.ssh/<your-private-key-name>

Host git-codecommit.*.amazonaws.com
  User APKEXAMPLEEXAMPLE-replace-with-your-user
  IdentityFile ~/.ssh/<your-private-key-name>
```
This way the git client uses the key for both domains and the correct user. Make sure to use the **SSH key ID** and not the **AWS Access key ID**

## Migrate
After you have set up the environment, I recommend to test the migration with one sample project. On a command line, type
```
gitlab-to-codecommit --gitlab-access-token youraccesstokenhere --gitlab-url https://yourgitlab.yourdomain.com --repository-names namespace/sample-project
```

It will take around 30 seconds for the CloudFormation template to create the AWS CodeCommit repository and the AWS CodePipeline and deploy the Lambda function. While deploying or when you are interested in the setup you can check the state in the AWS Management Console in the CloudFormation service section and look at the template.

