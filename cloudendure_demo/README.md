# Facilitating a Migration to AWS with CloudEndure by Leveraging Automation
===========

## Demo from re:Invent ENT312 Presentation that uses CloudEndure, Ansible and DMS to migrate a Gogs Environment to AWS.

## Files you need to edit and familiarize yourself with:

Note: This toolkit end to end only works in us-west-2 until the Application Discovery Service is available in other regions. 
If you try and run this in another region, you will get an error in Ansible when trying to provision aws_cli_ads_agent_install.yml. 
The rest of the demo should work. You can check availability of ADS by going to this link:
https://aws.amazon.com/about-aws/global-infrastructure/regional-product-services/

Ansible Playbooks, Variables and Files:
* playbooks/files/CloudEndure.sh – This file will be deployed to /boot/ce_conversion which is where CloudEndure executes post-migration scripts. It is used to reconfigure Gogs to point to RDS and test the service.
	- The reinvent-ent312-source-instances.yml CloudFormation template replaces all occurrences of ent312.five0.ninja in this file with your Amazon Route 53 domain alias that you want to point to your ELB load balancer for to the highly available Gogs environment with Auto Scaling. This value is passed into the template via the GogsDNS parameter in the CloudFormation Template.
* playbooks/cloudendure_agent_install.yml
	- The reinvent-ent312-source-instances.yml CloudFormation template sets your CloudEndure UserName and Password in this Ansible Playbook in the section called “Install CloudEndure” based off the CloudEndureUser and CloudEndurePassword parameters in the CloudFormation Template.

Migration Script:
* scripts/config.yml
	- username - Username for CloudEndure
	- password - Password for CloudEndure
	- hosttomigrate - Name of host to migrate in the CloudEndure dashboard. This value won’t be available in the dashboard until after CloudEndure starts the initial replication process.
	- keypairname - KeyPair for Launching Gogs AutoScale Stack
	- gogsdns - Route53 Domain Alias that you want to point your ELB for Gogs AutoScaling

CloudFormation:
* reinvent-ent312-migrated-gogs.template
	- This value is your Route 53 domain alias that you want to map to your ELB load balancer for Gogs automatic scaling. The parameter GogsDNSName is passed in based off the gogsdns value in the config.yml when the CloudEndure.py script is run.


Example CloudEndure.py Output:
Logging into CloudEndure
https://console.cloudendure.com/latest/celogin
Data:{"username": "CloudEndureUser", "password": "CloudEndurePassword"}
CloudEndure Response Status Code: 200
Describing CloudFormation Stacks for CloudEndureBlogDemo
CloudFormation Stack: CloudEndureBlogDemo-DMSStacks-JJ406HHWD4R4-YFunctionStack-11KQQXHSUC7O2
Writing CloudFormation Output Data to CloudEndureBlogDemo-DMSStacks-JJ406HHWD4R4-YFunctionStack-11KQQXHSUC7O2.json
CloudFormation Stack: CloudEndureBlogDemo-DMSStacks-JJ406HHWD4R4
Writing CloudFormation Output Data to CloudEndureBlogDemo-DMSStacks-JJ406HHWD4R4.json
CloudFormation Stack: CloudEndureBlogDemo-SourceInstanceResources-GCGLT302JCLW
Writing CloudFormation Output Data to CloudEndureBlogDemo-SourceInstanceResources-GCGLT302JCLW.json
CloudFormation Stack: CloudEndureBlogDemo-RDSStack-IYRQR4VLDATO
Writing CloudFormation Output Data to CloudEndureBlogDemo-RDSStack-IYRQR4VLDATO.json
CloudFormation Stack: CloudEndureBlogDemo-CloudEndureLambdaStack-Z8GGHLM6TE7B
Writing CloudFormation Output Data to CloudEndureBlogDemo-CloudEndureLambdaStack-Z8GGHLM6TE7B.json
CloudFormation Stack: CloudEndureBlogDemo-VPCStack-1VCMY09N8WJF6
Writing CloudFormation Output Data to CloudEndureBlogDemo-VPCStack-1VCMY09N8WJF6.json
CloudFormation Stack: CloudEndureBlogDemo
Get CloudEndure Projects
https://console.cloudendure.com/latest/projects
Data:{}
CloudEndure Response Status Code: 200
projectId: [u'683fefc8-4dc9-4792-966a-780567b49548']
Listing All Machines Registered in CloudEndure
https://console.cloudendure.com/latest/projects/683fefc8-4dc9-4792-966a-780567b49548/machines
Data:{}
CloudEndure Response Status Code: 200
We Hava A Match In CloudEndure for ip-10-10-143-236
MachineID For ip-10-10-143-236: b865bed6-e850-4926-9b76-a6a28f2df588
Checking To See If ip-10-10-143-236 Is Ready To Migrate
https://console.cloudendure.com/latest/projects/683fefc8-4dc9-4792-966a-780567b49548/machines/b865bed6-e850-4926-9b76-a6a28f2df588
Data:{}
CloudEndure Response Status Code: 200
ip-10-10-143-236 Is Ready To Migrate
2017-03-07T20:07:47.070420+00:00
Creating A Replica For ip-10-10-143-236: b865bed6-e850-4926-9b76-a6a28f2df588
https://console.cloudendure.com/latest/projects/683fefc8-4dc9-4792-966a-780567b49548/performTest
Data:{"items": [{"machineId": "b865bed6-e850-4926-9b76-a6a28f2df588"}]}
CloudEndure Response Status Code: 202
SQS For AMI information is QueueUrl is: https://us-west-2.queue.amazonaws.com/{YourAWSAccountID}/ENT312CloudEndureSQSQueue
NO MESSAGES IN QUEUE
…
NO MESSAGES IN QUEUE
7772cfaf-c4a8-404e-b787-3b5b8573c905
{"ResponseMetadata": {"RetryAttempts": 0, "HTTPStatusCode": 200, "RequestId": "8eba46c8-d69e-4056-af60-9b47aa71421d", "HTTPHeaders": {"transfer-encoding": "chunked", "vary": "Accept-Encoding", "server": "AmazonEC2", "content-type": "text/xml;charset=UTF-8", "date": "Tue, 07 Mar 2017 20:13:14 GMT"}}, "ImageId": "ami-1f63ef7f"}
AQEBg6aN1UKHrp77Ur7fzWaB2QVRcoUCuYjrcxpWsh3y12umZLCfNVLqej48LUA5a4Z3Qlw6c8k8IBxIB/sMLZTYzPnlRguud/zx2TGX2yvKuiISRx8hNgyjit7gMS1sU7a5fNsBPl22ROm5AgUxc4hS1C31C6dNndIAtjVc/4lqON1T6lRMkGcNOnIEAoGaxE39HmXyQ5mNte4uv0veFAzY19ruSVAT4DsVNd3FdefEqJd/e+608uVIsUJuy5KGiAw0CjKGW6ayCuRmTPUxVTdaRv0R32eKRxcnxIp/97nS4qUN1Pklq152DccpvsJojnuBU0+mmJRscdLyuJeM6ZgA8tT3SfmKiSnbIbD3ffFOl8UxPftWyFB7wzGljYIoq4hSmPBJx/3oi0BOmPJc0f6avvLFWm3EBi5fP1DQS9kLSzM=
{u'ResponseMetadata': {u'RetryAttempts': 0, u'HTTPStatusCode': 200, u'RequestId': u'8eba46c8-d69e-4056-af60-9b47aa71421d', u'HTTPHeaders': {u'transfer-encoding': u'chunked', u'content-type': u'text/xml;charset=UTF-8', u'vary': u'Accept-Encoding', u'date': u'Tue, 07 Mar 2017 20:13:14 GMT', u'server': u'AmazonEC2'}}, u'ImageId': u'ami-1f63ef7f'}
ami-1f63ef7f
Searching for AMI for ami-1f63ef7f and see if it's available
AMI is not available
…
AMI is not available
AMI is available. Launching Stack
{u'StackId': 'arn:aws:cloudformation:us-west-2:{YourAWSAccountID}:stack/CloudEndureBlogDemo-gogs-autoscale-20170307201555/dee2cc90-0372-11e7-8632-50a686be7356', 'ResponseMetadata': {'RetryAttempts': 0, 'HTTPStatusCode': 200, 'RequestId': 'dedd9ce7-0372-11e7-b781-99bae1e35c17', 'HTTPHeaders': {'x-amzn-requestid': 'dedd9ce7-0372-11e7-b781-99bae1e35c17', 'date': 'Tue, 07 Mar 2017 20:15:56 GMT', 'content-length': '419', 'content-type': 'text/xml'}}}
Deleted: 7772cfaf-c4a8-404e-b787-3b5b8573c905



