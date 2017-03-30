"""CloudEndure Lambda Function by Carmen A. Puccio"""
from __future__ import print_function # Python 2/3 compatibility
import datetime
import json
import logging
import os
import boto3
from botocore.exceptions import ClientError

DEBUG = False # Set verbose debugging information

logger = logging.getLogger()
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

def send_sqs_message(imageinfo):
    """Sends a SQS message with the AMI information
    that was created from the migrated instance
    that passed testing post migration in CloudEndure
    """
    try:
        message = json.dumps(imageinfo)
        sqsclient = boto3.client('sqs')
        sqsclient.send_message(
            QueueUrl=os.environ['QueueURL'],
            MessageBody=message
            )

    except ClientError as err:
        logger.error(err.response)

def create_ami(instance_id):
    """Creates an AMI based off the migrated instance
    that passed testing post migration in CloudEndure
    """
    try:
        ec2_client = boto3.client('ec2')

        # Create an AMI from the migrated instance
        image_creation_time = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
        ec2_image = ec2_client.create_image(
            InstanceId=instance_id,
            Name="ENT312Demo_%s" % (image_creation_time),
            Description="ENT312Demo_%s" % (image_creation_time),
            NoReboot=True
            )
        logger.info('AMI Id: %s', ec2_image)

        # Tag the newly created AMI by getting the tags of the migrated instance to copy to the AMI.
        ec2_tags = ec2_client.describe_tags(
            Filters=[
                {
                    'Name': 'resource-id',
                    'Values': [instance_id]
                }
            ]
        )

        logger.info(ec2_tags)
        for tag in ec2_tags['Tags']:
            ec2_client.create_tags(
                Resources=[ec2_image['ImageId']],
                Tags=[{'Key': tag['Key'], 'Value': tag['Value']}])

        send_sqs_message(ec2_image)

    except ClientError as err:
        logger.error(err.response)

def lambda_handler(event, context):
    """Lambda entry point"""
    try:
        logger.info(event)
        json_sns_message = json.loads(event['Records'][0]['Sns']['Message'])

        if json_sns_message['Pass'] != "True":
            logger.error("%s did not pass post migration testing! Not creating an AMI." % (json_sns_message['instanceId']))

        else:
            logger.info("%s passed post migration testing. Creating an AMI." % (json_sns_message['instanceId']))
            create_ami(json_sns_message['instanceId'])

    except ClientError as err:
        logger.error(err.response)
