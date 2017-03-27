"""CloudEndure.py by Carmen A. Puccio"""
from __future__ import print_function  # Python 2/3 compatibility
import datetime
import json
import os
import re
import sys
import urllib2
import time
import yaml
import boto3
from botocore.exceptions import ClientError

vpc_stack_name = ""
session_cookie = ""


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
        url = 'https://console.cloudendure.com' + version + operation
        print(url)
        data = json.dumps(params).encode('utf8')
        print("Data:" + data)
        if method == "GET":
            req = urllib2.Request(url, headers=headers)
        else:
            req = urllib2.Request(url, data, headers=headers)

        response = urllib2.urlopen(req)
        print("CloudEndure Response Status Code: %s" % response.getcode())
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
            {'Cookie': session_cookie}, CFG['version'])
        parsed_json = json.loads(get_machines_response.read().decode('utf-8'))
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
        'GET', 'projects', {}, {'Cookie': session_cookie}, CFG['version'])
    parsed_json = json.loads(get_projects_response.read().decode('utf-8'))
    projects = [project['id'] for project in parsed_json['items']]
    print("projectId: %s" % projects)

    # Get a list of all machines in a specific project
    # Find the matching InstanceID/machineCloudId for a
    # passed test and perform a cutover
    print("Listing All Machines Registered in CloudEndure")
    for project_id in projects:
        get_all_machines_response = invoke_cloudendure(
            'GET', 'projects/' + project_id + '/machines', {},
            {'Cookie': session_cookie}, CFG['version'])
        parsed_json = json.loads(get_all_machines_response.read().decode('utf-8'))
        for i in parsed_json['items']:
            if i['sourceProperties']['name'] == CFG['hosttomigrate']:
                print("We Hava A Match In CloudEndure for %s" % CFG['hosttomigrate'])
                print("MachineID For %s: %s" % (CFG['hosttomigrate'], i['id']))
                machine_id = i['id']

                number_of_tries = 0
                machine_ready = False
                while not machine_ready:
                    number_of_tries = number_of_tries + 1
                    # Guessing here because I don't know
                    # when the cookies expire in CloudEndure.
                    # The check_machine_ready function sleeps
                    # every 30 seconds so re-logging in
                    # every 15 min or so should work...
                    if number_of_tries < 7:
                        machine_ready = check_machine_ready(machine_id, project_id)
                    else:
                        number_of_tries = 0
                        login()

                # Create a replica ininstance
                print("Creating A Replica For %s: %s" % (CFG['hosttomigrate'], i['id']))
                invoke_cloudendure(
                    'PUT', 'projects/' + project_id + '/performTest',
                    {'items': [{'machineId': machine_id}]},
                    {'Cookie': session_cookie}, CFG['version'])

                # Start polling the queue for the passed AMI message
                receive_messages()


def login():
    """Log into CloudEndure"""
    global session_cookie
    print("Logging into CloudEndure")
    login_response = invoke_cloudendure(
        'POST', 'celogin',
        {'username': CFG['username'], 'password': CFG['password']}, {}, CFG['version'])

    # Extract the session cookie from the response
    session_cookie = login_response.info().getheader('Set-Cookie')
    cookies = re.split('; |/ ', session_cookie)
    session_cookie = [cookie for cookie in cookies
                      if cookie.startswith('session')][0].strip()

# Starting the script
print("*********** ENT312 Powered by " +
      "CloudEndure and AWS Database Migration Service ***********")

with open(os.path.join(sys.path[0], "config.yml"), 'r') as ymlfile:
    CFG = yaml.load(ymlfile)

time.sleep(5)
login()

# Describing CloudFromation Stacks
describe_stack()

# Start Conversion
start_conversion()
