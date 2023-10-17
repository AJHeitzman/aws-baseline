import pulumi
from pulumi import StackReference, export, ResourceOptions, Output
from datetime import datetime
import pytz
import json
import os
import platform
import pulumi_aws as aws
from ipaddress import IPv4Network
from common.autotag import register_auto_tags
from common.vpc import VPC
from common.subnets import Subnets
from common.nat_gateways import NATGateways
from common.route_tables import RouteTables
from common.security_groups import SecurityGroups

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
# Creates the VPC and Flow Log resources if enabled.
vpc = VPC(environment).create()

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
#- Create subnets. Will return a dictionary of subnet_groups the subnets created for each. 
# It will also return a list of availability zones that require a NAT Gateway.
subnets, availability_zones_that_need_nat_gateways = Subnets(environment, vpc).create()

"""
Create NAT Gateways
"""
#- Create a NAT Gateway for each AZ that contains private (The private and database subnets in the config) 
# subnets that require access to the internet. Return a dictionary containing the ngw name and id.
nat_gateways = NATGateways(availability_zones_that_need_nat_gateways, environment, subnets).create()

"""
Create Route Tables
"""
#- Create the route tables adding routes to the appropriate NGW or IGW and then associate with the appropriate subnet(s).
route_tables = RouteTables(environment, igw, nat_gateways, subnets, vpc).create()

"""
Create Security Groups
"""
# Creates the baseline security groups for each subnet group. These security groups would be the first to get applied
# to any resources created in the respective subnet.
security_groups = SecurityGroups(environment, subnets, vpc).create()

"""
Create Export for README.md
"""
#- Allows the readme to be visible in the pulumi web console for added visibility.
with open('../README.md') as f:
    pulumi.export('readme', f.read())