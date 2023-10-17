import pulumi
from pulumi import export, ResourceOptions
import pulumi_aws as aws
import yaml

"""
Grab Config
"""
config = pulumi.Config()
region = aws.config.region

class FlowLogs():
    def __init__(self, environment, vpc):
        self.environment = str(environment)
        self.vpc = vpc
    
    def create(self):
        environment = self.environment
        vpc = self.vpc

        """
        Create Cloudwatch Group
        """
        flow_logs_log_group_name = f"{environment}-vpc-flow-logs-lg"
        flow_logs_log_group = aws.cloudwatch.LogGroup(
            flow_logs_log_group_name,
            name = flow_logs_log_group_name,
            retention_in_days = config.require_object("vpc").get("flow_logs").get("retention_in_days"),
        )

        """
        Create Flow Logs Role
        """
        flow_logs_role = aws.iam.Role(
            f"{environment}-vpc-flow-logs-role",
            assume_role_policy="""{
            "Version": "2012-10-17",
            "Statement": [
                {
                "Sid": "",
                "Effect": "Allow",
                "Principal": {
                    "Service": "vpc-flow-logs.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
                }
            ]
            }
            """
        )

        """
        Create Flow Logs Role Policy
        """
        flow_logs_role_policy = aws.iam.RolePolicy(
            f"{environment}-vpc-flow-logs-role-policy",
            role = flow_logs_role.id,
            policy="""{
            "Version": "2012-10-17",
            "Statement": [
                {
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                    "logs:DescribeLogGroups",
                    "logs:DescribeLogStreams"
                ],
                "Effect": "Allow",
                "Resource": "*"
                }
            ]
            }
            """
        )
        
        """
        Create Flow Logs
        """
        flow_log = aws.ec2.FlowLog(
            f"{environment}-vpc-flow-log",
            iam_role_arn = flow_logs_role.arn,
            log_destination = flow_logs_log_group.arn,
            traffic_type = config.require_object("vpc").get("flow_logs").get("traffic_type"),
            max_aggregation_interval = 60,
            vpc_id = vpc.id
        )