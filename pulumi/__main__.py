import pulumi
from pulumi import StackReference, export, ResourceOptions, Output
from datetime import datetime
import pytz
import json
import os
import platform
import pulumi_aws as aws
from common.autotag import register_auto_tags

"""
Grab Config
"""
config = pulumi.Config()

"""
Create Variables from pulumi config
"""
environment = pulumi.get_stack()

"""
Deployment Timestamp
"""
UTC = pytz.utc
datetime_utc = datetime.now(UTC)
deployment_timestamp = f"{datetime_utc.strftime('%Y-%m-%d %H:%M:%S %Z %z')}"

"""
Auto Tagging
"""
# Automagically applies the following tags to any resource created and managed by pulumi.
register_auto_tags({
    'managed_by_pulumi': 'true',
    'pulumi_project': pulumi.get_project(),
    'pulumi_stack': pulumi.get_stack(),
    'environment': environment,
    'deployment_timestamp_utc': deployment_timestamp,
    'deployed_by': os.getlogin(),
    'deployed_from': f"{platform.node()} - {platform.system()} {platform.release()}",
    'caller_identity_user_id': aws.get_caller_identity().user_id,
    'caller_identity_account_id': aws.get_caller_identity().account_id
})

"""
Create VPC
"""
vpc_name = f"{environment}VPC"
vpc = aws.ec2.Vpc(
        vpc_name,
        cidr_block = config.require_object("vpc.cidr_block"),
        enable_dns_hostnames=config.require_object("vpc.enable_dns_hostnames"),
        tags = {"Name": vpc_name}
    )

"""
Create Internet Gateway
"""
igw_name = f"{environment}-igw"
igw = aws.ec2.InternetGateway(
    igw_name,
    vpc_id = vpc.id,
    tags = {"Name": igw_name}
)

"""
Create Subnets
"""

"""
Create NAT Gateways
"""

"""
Create Route Tables
"""

"""
Create Security Groups
"""

"""
Create Export for README.md
"""
#- Allows the readme to be visible in the pulumi web console for added visibility.
with open('../README.md') as f:
    pulumi.export('readme', f.read())