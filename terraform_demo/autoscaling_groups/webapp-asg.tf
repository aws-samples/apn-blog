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
resource "aws_autoscaling_group" "webapp_asg" {
  lifecycle { create_before_destroy = true }
  vpc_zone_identifier = ["${var.public_subnet_id}"]
  name = "demo_webapp_asg-${var.webapp_lc_name}"
  max_size = "${var.asg_max}"
  min_size = "${var.asg_min}"
  wait_for_elb_capacity = false
  force_delete = true
  launch_configuration = "${var.webapp_lc_id}"
  load_balancers = ["${var.webapp_elb_name}"]
  tag {
    key = "Name"
    value = "terraform_asg"
    propagate_at_launch = "true"
  }
}

#
# Scale Up Policy and Alarm
#
resource "aws_autoscaling_policy" "scale_up" {
  name = "terraform_asg_scale_up"
  scaling_adjustment = 2
  adjustment_type = "ChangeInCapacity"
  cooldown = 300
  autoscaling_group_name = "${aws_autoscaling_group.webapp_asg.name}"
}
resource "aws_cloudwatch_metric_alarm" "scale_up_alarm" {
  alarm_name = "terraform-demo-high-asg-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods = "2"
  metric_name = "CPUUtilization"
  namespace = "AWS/EC2"
  period = "120"
  statistic = "Average"
  threshold = "80"
  insufficient_data_actions = []
  dimensions {
      AutoScalingGroupName = "${aws_autoscaling_group.webapp_asg.name}"
  }
  alarm_description = "EC2 CPU Utilization"
  alarm_actions = ["${aws_autoscaling_policy.scale_up.arn}"]
}

#
# Scale Down Policy and Alarm
#
resource "aws_autoscaling_policy" "scale_down" {
  name = "terraform_asg_scale_down"
  scaling_adjustment = -1
  adjustment_type = "ChangeInCapacity"
  cooldown = 600
  autoscaling_group_name = "${aws_autoscaling_group.webapp_asg.name}"
}

resource "aws_cloudwatch_metric_alarm" "scale_down_alarm" {
  alarm_name = "terraform-demo-low-asg-cpu"
  comparison_operator = "LessThanThreshold"
  evaluation_periods = "5"
  metric_name = "CPUUtilization"
  namespace = "AWS/EC2"
  period = "120"
  statistic = "Average"
  threshold = "30"
  insufficient_data_actions = []
  dimensions {
      AutoScalingGroupName = "${aws_autoscaling_group.webapp_asg.name}"
  }
  alarm_description = "EC2 CPU Utilization"
  alarm_actions = ["${aws_autoscaling_policy.scale_down.arn}"]
}
output "asg_id" {
  value = "${aws_autoscaling_group.webapp_asg.id}"
}
