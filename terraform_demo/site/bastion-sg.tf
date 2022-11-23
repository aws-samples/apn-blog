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
resource "aws_security_group" "bastion_ssh_sg" {
  name = "bastion_ssh"
  description = "Allow SSH to Bastion host from approved ranges"
  ingress {
    from_port = 22
    to_port = 22
    protocol = "tcp"
    cidr_blocks = ["${var.ip_range}"]
  }
  egress {
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  vpc_id = "${aws_vpc.default.id}"
  tags = {
      Name = "terraform_bastion_ssh"
  }
}
output "bastion_ssh_sg_id" {
  value = "${aws_security_group.bastion_ssh_sg.id}"
}

resource "aws_security_group" "ssh_from_bastion_sg" {
  name = "ssh_from_bastion"
  description = "Allow SSH from Bastion host(s)"
  ingress {
    from_port = 22
    to_port = 22
    protocol = "tcp"
    security_groups = [
      "${aws_security_group.bastion_ssh_sg.id}",
      "${aws_security_group.nat.id}"
    ]
  }
  vpc_id = "${aws_vpc.default.id}"
  tags = {
      Name = "terraform_ssh_from_bastion"
  }
}
output "ssh_from_bastion_sg_id" {
  value = "${aws_security_group.ssh_from_bastion_sg.id}"
}
