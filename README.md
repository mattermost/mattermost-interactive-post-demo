# interactive-post-demo

This is an interactive post demo for Mattermost. It adds a /poll command that allows you to create interactive "yes" or "no" polls:

[![Demo](https://thumbs.gfycat.com/UntimelyPoisedAnkole-size_restricted.gif)](https://gfycat.com/UntimelyPoisedAnkole)

## Deploying

The slash command is designed to be deployed to AWS using the [Serverless Framework](https://serverless.com/):

* Create an AWS account, install the AWS CLI, and configure your credentials via `aws configure`.
* Install the [Serverless Framework](https://serverless.com/): `npm install serverless -g`
* Install the [serverless-python-requirements](https://www.npmjs.com/package/serverless-python-requirements) plugin for Serverless: `npm install serverless-python-requirements`
* Deploy: `serverless deploy -v`

Once deployed, just use the slash-command URL in the output to create a custom command in Mattermost.

## How it Works

When the slash command is triggered, a unique id is generated for the poll. The slash command then places a post in the channel with actions that contain the poll id in their context.

When a vote action is triggered, an entry is made in the database for the corresponding user and poll id, and an ephemeral message is returned to the user.

When the poll is ended, it counts all of the votes and replaces the message attachment's action buttons with the results.
