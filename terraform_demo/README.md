# Overview
WARNING:  LAUNCHING THIS WILL COST YOU MONEY

This is a demo of using Terraform (https://terraform.io) to provision a sample AWS architecture.  Using this will cost you money.

WARNING:  LAUNCHING THIS WILL COST YOU MONEY

# Before You Begin
If you haven't already configured the AWS CLI, or another SDK, on the machine where you will be running Terraform you should follow these instructions to setup the AWS CLI and create a credential profile which Terraform will use for authentication:  
http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html

# Launching
1. terraform get
2. terraform plan
3. terraform apply

# Destroying
There's [currently an issue](https://github.com/hashicorp/terraform/issues/2493) with using the [create_before_destroy lifecycle policy](https://www.terraform.io/docs/configuration/resources.html#lifecycle) on resources that effects destroying them.  The easiest way to destroy the environment is to change the create_before_destroy to false.  This change will need to be made in the `autoscaling_groups/webapp-asg.tf` and `launch_configurations/webapp-lc.tf` files.

Once you set create_before_destroy to false you can run `terraform destroy successfully`.

# License
Copyright 2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance with the License. A copy of the License is located at

    http://aws.amazon.com/apache2.0/

or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
