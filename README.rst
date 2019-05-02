====================================
aws-codecommit-migration-from-gitlab
====================================


.. image:: https://img.shields.io/pypi/v/aws-codecommit-migration-from-gitlab
        :target: https://pypi.python.org/pypi/aws-codecommit-migration-from-gitlab

.. image:: https://readthedocs.org/projects/aws-codecommit-migration-from-gitlab/badge/?version=latest
        :target: https://aws-codecommit-migration-from-gitlab.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

====================================
AWS CodeCommit Migration From GitLab
====================================

Script to migrate from GitLab to Amazon CodeCommit easily and setup your AWS environment with CodeCommit, CodePipeline and CodeDeploy as well.

Installation through pip:::

    pip install aws-codecommit-migration-from-gitlab

Migrating one project:::

    aws-codecommit-migration-from-gitlab --gitlab-access-token <your-access-token> --gitlab-url https://gitlab.youdomain.com --projects namespace/project-name


Migrate all projects from a GitLab server that the secure access token gives you access to read::

    aws-codecommit-migration-from-gitlab --gitlab-access-token <your-access-token> --gitlab-url https://gitlab.youdomain.com --all


Or projects for a specific user or users::

    aws-codecommit-migration-from-gitlab --gitlab-access-token <your-access-token> --gitlab-url https://gitlab.youdomain.com --users user1 user2

Or some groups::

    aws-codecommit-migration-from-gitlab --gitlab-access-token <your-access-token> --gitlab-url https://gitlab.youdomain.com --groups group1 group2

And you can specify a Chime Webhook to receive notifications in a chat room as well::

    aws-codecommit-migration-from-gitlab --gitlab-access-token <your-access-token> --gitlab-url https://gitlab.youdomain.com --projects namespace/project-name --chime-webhook-url <chime-webhook-url>


* Free software: MIT-0 license (https://github.com/aws/mit-0)
* Documentation: https://gitlab-to-codecommit-migration.readthedocs.io.


Feature Requests
----------------

Let me know :-)

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
