import base64
import boto3
import json
import os
import urlparse


def slash_command(event, context):
    print(json.dumps(event))

    data = urlparse.parse_qs(event['body'])
    if data.get('text', [''])[0] == '':
        return {
            'statusCode': '200',
            'headers': {
                'Content-Type': 'application/json',
            },
            'body': json.dumps({
                'response_type': 'ephemeral',
                'text': 'Please provide a prompt.',
            }),
        }

    poll_id = base64.b64encode(os.urandom(32))
    prompt = data['text'][0]

    api_url = event['headers']['X-Forwarded-Proto'] + '://' + event['headers']['Host'] + '/' + event['requestContext']['stage']

    return {
        'statusCode': '200',
        'headers': {
            'Content-Type': 'application/json',
        },
        'body': json.dumps({
            'response_type': 'in_channel',
            'attachments': [{
                'text': prompt,
                'actions': [{
                    'name': 'Vote Yes',
                    'integration': {
                        'url': api_url + '/vote',
                        'context': {
                            'poll_id': poll_id,
                            'vote': 'Yes'
                        }
                    }
                }, {
                    'name': 'Vote No',
                    'integration': {
                        'url': api_url + '/vote',
                        'context': {
                            'poll_id': poll_id,
                            'vote': 'No'
                        }
                    }
                }, {
                    'name': 'End Poll',
                    'integration': {
                        'url': api_url + '/end-poll',
                        'context': {
                            'poll_id': poll_id,
                            'prompt': prompt,
                        }
                    }
                }]
            }]
        }),
    }


def vote_action(event, context):
    print(json.dumps(event))

    data = json.loads(event['body'])

    db = boto3.client('dynamodb')

    result = db.put_item(
        TableName=os.environ['VOTES_TABLE'],
        Item={
            'PollId': {
                'S': data['context']['poll_id'],
            },
            'UserId': {
                'S': data['user_id'],
            },
            'Vote': {
                'S': data['context']['vote'],
            },
        },
        ReturnValues='ALL_OLD',
    )

    return {
        'statusCode': '200',
        'headers': {
            'Content-Type': 'application/json',
        },
        'body': json.dumps({
            'ephemeral_text': 'Your vote has been updated.' if result.get('Attributes') else 'Thanks for your vote!',
        }),
    }


def end_poll_action(event, context):
    print(json.dumps(event))

    data = json.loads(event['body'])

    db = boto3.client('dynamodb')

    counts = {vote: db.query(
        TableName=os.environ['VOTES_TABLE'],
        KeyConditionExpression='PollId = :pid',
        FilterExpression='Vote = :vote',
        ExpressionAttributeValues={
            ':pid': {
                'S': data['context']['poll_id'],
            },
            ':vote': {
                'S': vote,
            },
        },
        Select='COUNT',
    )['Count'] for vote in ['Yes', 'No']}
    total = sum(counts.values())

    return {
        'statusCode': '200',
        'headers': {
            'Content-Type': 'application/json',
        },
        'body': json.dumps({
            'update': {
                'props': {
                    'attachments': [{
                        'text': data['context']['prompt'],
                        'fields': [{
                            'short': True,
                            'title': vote,
                            'value': '{} ({:.2f}%)'.format(count, count / total * 100),
                        } for vote, count in counts.items()],
                    }],
                },
            },
        }),
    }
