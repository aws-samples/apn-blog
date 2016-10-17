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
resource "aws_launch_configuration" "webapp_lc" {
  lifecycle { create_before_destroy = true }
  image_id = "${lookup(var.amis, var.region)}"
  instance_type = "${var.instance_type}"
  security_groups = [
    "${var.webapp_http_inbound_sg_id}",
    "${var.webapp_ssh_inbound_sg_id}",
    "${var.webapp_outbound_sg_id}"
  ]
  user_data = "${file("./launch_configurations/userdata.sh")}"
  key_name = "${var.key_name}"
  associate_public_ip_address = true
}
output "webapp_lc_id" {
  value = "${aws_launch_configuration.webapp_lc.id}"
}
output "webapp_lc_name" {
  value = "${aws_launch_configuration.webapp_lc.name}"
}
