#!/usr/bin/env python
from __future__ import print_function # Python 2/3 compatibility
import sys
import boto3
import urllib
import json
from botocore.exceptions import ClientError

try:
	instance_metadata = urllib.urlopen("http://169.254.169.254/latest/dynamic/instance-identity/document/imageId").read()
	json_instance_metadata = json.loads(instance_metadata)
	
	sns_topic = "arn:aws:sns:%s:%s:ENT312CloudEndureSNSTopic" % ((json_instance_metadata['region']),(json_instance_metadata['accountId']))
	
	message = {"Pass": "True", "instanceId": json_instance_metadata['instanceId']}
	sns_client = boto3.client('sns', region_name=json_instance_metadata['region'])
	
	sns_response = sns_client.publish(
        TopicArn = sns_topic,
        Message=json.dumps(message),
        Subject = 'ENT312Demo'
    )

except ClientError as e:
	print(e.response)
