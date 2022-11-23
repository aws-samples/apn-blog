# Copyright 2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file
# except in compliance with the License. A copy of the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS"
# BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under the License.
resource "aws_instance" "private_subnet_instance" {
  ami = "${lookup(var.amis, var.region)}"
  instance_type = "${var.instance_type}"
  tags = {
    Name = "terraform_demo_private_subnet"
  }
  subnet_id = "${var.private_subnet_id}"
  vpc_security_group_ids = [
    "${var.ssh_from_bastion_sg_id}",
    "${var.web_access_from_nat_sg_id}"
    ]
  key_name = "oregon"
}
