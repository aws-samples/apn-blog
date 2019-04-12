"""CloudEndure.py by Carmen A. Puccio"""
from __future__ import print_function  # Python 2/3 compatibility
import datetime
import json
import os
import re
import sys
import requests
import time
import yaml
import boto3
from botocore.exceptions import ClientError

vpc_stack_name = ""
session_cookie = ""
cookies = ""


def launch_stack(ami):
    """Launch highly available Gogs CloudFormation Stack"""
    try:
        cfclient = boto3.client('cloudformation', region_name=CFG['region'])
        cfstacks = cfclient.describe_stacks()

        for stack in cfstacks['Stacks']:
            if CFG['stackname'] in stack['StackName']:
                if CFG['stackname'] + "-VPCStack" in stack['StackName']:
                    vpc_stack_name = stack['StackName']

        cfresponse = cfclient.create_stack(
            StackName=CFG['stackname'] + '-gogs-autoscale-'
            + datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S"),
            TemplateURL=CFG['gogstemplate'],
            Parameters=[
                {
                    'ParameterKey': 'VPCStackName',
                    'ParameterValue': vpc_stack_name,
                },
                {
                    'ParameterKey': 'KeyPairName',
                    'ParameterValue': CFG['keypairname'],
                },
                {
                    'ParameterKey': 'AMIID',
                    'ParameterValue': ami,
                },
                {
                    'ParameterKey': 'GogsDNSName',
                    'ParameterValue': CFG['gogsdns'],
                }
            ],
            OnFailure='DO_NOTHING',
        )
        print(cfresponse)

    except ClientError as err:
        print(err.response)


def poll_for_ami(image_id):
    """Poll for AMI to see if it's ready"""
    try:
        ami_ready = False
        ec2client = boto3.client('ec2', region_name=CFG['region'])
        amiresponse = ec2client.describe_images(
            ImageIds=[image_id],
            Owners=['self']
        )

        for image in amiresponse['Images']:
            if image['State'] == "available":
                ami_ready = True
                print("AMI is available. Launching Stack")
                launch_stack(image_id)
                return ami_ready
            else:
                print("AMI is not available")
                time.sleep(5)
                return ami_ready

    except ClientError as err:
        print(err.response)


def receive_messages():
    """Poll SQS Queue for Lambda Message about the new AMI"""
    try:
        foundamimessage = False

        sqs = boto3.client('sqs', region_name=CFG['region'])
        resp_queue_url = sqs.get_queue_url(
            QueueName=CFG['sqsqueue']
        )
        print("SQS For AMI information is QueueUrl is: %s" % resp_queue_url['QueueUrl'])

        while not foundamimessage:
            messages = sqs.receive_message(
                QueueUrl=resp_queue_url['QueueUrl'],
                AttributeNames=['All'],
                MaxNumberOfMessages=10,
                VisibilityTimeout=10
                )

            if messages.get('Messages'):
                for message in messages.get('Messages'):
                    print(message['MessageId'])
                    print(message['Body'])
                    print(message['ReceiptHandle'])

                    parsed_json = json.loads(message['Body'])
                    print(parsed_json)
                    print(parsed_json['ImageId'])

                    print("Searching for AMI for " + parsed_json['ImageId'] +
                          " and see if it's available")
                    ami_ready = poll_for_ami(parsed_json['ImageId'])
                    while not ami_ready:
                        ami_ready = poll_for_ami(parsed_json['ImageId'])

                    sqs.delete_message(
                        QueueUrl=resp_queue_url['QueueUrl'],
                        ReceiptHandle=message['ReceiptHandle'],
                        )

                    print("Deleted: %s" % message['MessageId'])
                    foundamimessage = True

            else:
                print("NO MESSAGES IN QUEUE")
                time.sleep(5)

    except ClientError as err:
        print(err.response)


def describe_stack():
    """This function is gets the ClouFormation output values
    and writes them to a json doc
    """
    try:
        global vpc_stack_name
        cfclient = boto3.client('cloudformation', region_name=CFG['region'])
        cfstacks = cfclient.describe_stacks()

        print("Describing CloudFormation Stacks for %s" % CFG['stackname'])
        for stack in cfstacks['Stacks']:
            if CFG['stackname'] in stack['StackName']:
                print("CloudFormation Stack: %s" % stack['StackName'])
                if CFG['stackname'] + "-VPCStack" in stack['StackName']:
                    vpc_stack_name = stack['StackName']
                if 'Outputs' in stack:
                    data = {}
                    for output in stack['Outputs']:
                        data.update(
                            {output['OutputKey']: output['OutputValue']})
                    with open(
                        os.path.join(sys.path[0], stack['StackName'] + '.json'), 'w') as json_file:
                        print("Writing CloudFormation Output Data to %s.json" % stack['StackName'])
                        json_file.write(json.dumps(data))

    except ClientError as err:
        print(err.response)


def invoke_cloudendure(method, operation, params, headers, version):
    """Function to invoke the CloudEndure API"""

    try:
        headers.update({'Content-Type': 'application/json'})
        url = 'https://console.cloudendure.com/api' + version + operation
        print(url)
        data = json.dumps(params).encode('utf8')
        session = {'session': session_cookie}
        if method == "GET":
            response = requests.get(url, headers=headers, cookies=session)
        else:
            response = requests.post(url, data, headers=headers)

        print(response.content)
        print("CloudEndure Response Status Code: %s" % response)
        return response

    except ClientError as err:
        print(err.response)

def check_machine_ready(ce_machine_id, project_id):
    """Check to see if machine is ready to migrate in CloudEndure"""
    try:
        machine_ready = False
        # Need the lastConsistencyDateTime before
        # launching a test machine.
        print("Checking To See If %s Is Ready To Migrate" % CFG['hosttomigrate'])
        get_machines_response = invoke_cloudendure(
            'GET', 'projects/' + project_id + '/machines/' + ce_machine_id, {},
            {'session': session_cookie,'X-XSRF-TOKEN':cookies}, CFG['version'])
        print(get_machines_response.content)
        parsed_json = json.loads(get_machines_response.content)
        if 'lastConsistencyDateTime' in parsed_json['replicationInfo']:
            print("%s Is Ready To Migrate" % CFG['hosttomigrate'])
            print(parsed_json['replicationInfo']['lastConsistencyDateTime'])
            machine_ready = True
            return machine_ready

        else:
            print("%s Is Not Ready To Migrate In CloudEndure." % CFG['hosttomigrate'])
            print("Sleeping For 30 Seconds")
            time.sleep(30)
            return machine_ready

    except ClientError as err:
        print(err.response)

def start_conversion():
    """This function does all of the heavy lifting
    in CloudEndure. It makes sure that the machine
    is ready before trying to launch a test instance
    for the migration.
    """
    # Returns all projects the current user can use.
    print("Get CloudEndure Projects")
    get_projects_response = invoke_cloudendure(
        'GET', 'projects', {}, {'X-XSRF-TOKEN':cookies}, CFG['version'])
    parsed_json = json.loads(get_projects_response.content)
    projects = [project['id'] for project in parsed_json['items']]
    print("projectId: %s" % projects)

    # Get a list of all machines in a specific project
    # Find the matching InstanceID/machineCloudId for a
    # passed test and perform a cutover
    print("Listing All Machines Registered in CloudEndure")
    for project_id in projects:
        get_all_machines_response = invoke_cloudendure(
            'GET', 'projects/' + project_id + '/machines', {},
            {'session': session_cookie,'X-XSRF-TOKEN': cookies}, CFG['version'])
        parsed_json = json.loads(get_all_machines_response.content)
        for i in parsed_json['items']:
            if i['sourceProperties']['name'] == CFG['hosttomigrate']:
                print("We Hava A Match In CloudEndure for %s" % CFG['hosttomigrate'])
                print("MachineID For %s: %s" % (CFG['hosttomigrate'], i['id']))
                machine_id = i['id']

                number_of_tries = 0
                machine_ready = False
                while not machine_ready:
                    number_of_tries = number_of_tries + 1
                    # CloudEndure cookies expire after 60 min
                    # The check_machine_ready function sleeps
                    # every 30 seconds so re-logging in
                    # every 45 min or so should work...
                    if number_of_tries < 25:
                        machine_ready = check_machine_ready(machine_id, project_id)
                    else:
                        number_of_tries = 0
                        login()

                # Create a replica ininstance
                print("Creating A Replica For %s: %s" % (CFG['hosttomigrate'], i['id']))
                invoke_cloudendure(
                    'PUT', 'projects/' + project_id + '/performTest',
                    {'items': [{'machineId': machine_id}]},
                    {'session': session_cookie,'X-XSRF-TOKEN':cookies}, CFG['version'])

                # Start polling the queue for the passed AMI message
                receive_messages()


def login():
    """Log into CloudEndure"""
    global session_cookie
    global cookies
    print("Logging into CloudEndure")
    login_response = invoke_cloudendure(
        'POST', 'login',
        {'username': CFG['username'], 'password': CFG['password']}, {}, CFG['version'])

    # Extract the session cookie and token from the response
    session_cookie = login_response.cookies['session']
    cookies = login_response.cookies['XSRF-TOKEN']
    cookies = cookies.replace('"', '')

# Starting the script
print("*********** ENT312 Powered by " +
      "CloudEndure and AWS Database Migration Service ***********")

with open(os.path.join(sys.path[0], "config.yml"), 'r') as ymlfile:
    CFG = yaml.load(ymlfile)

time.sleep(5)
login()

# Describing CloudFormation Stacks
describe_stack()

# Start Conversion
start_conversion()