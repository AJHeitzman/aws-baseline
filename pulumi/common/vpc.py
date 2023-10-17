import pulumi
from pulumi import export, ResourceOptions
import pulumi_aws as aws
from common.helpers import Helpers
from common.flow_logs import FlowLogs

config = pulumi.Config()
region = aws.config.region

class VPC():
    def __init__(self, environment):
        self.environment = str(environment)
    
    def vpc_flow_logs_enabled(self):
        return config.require_object("vpc").get("flow_logs").get("enabled")

    def create(self):
        environment = self.environment

        """
        Generate VPC name
        """
        vpc_name = f"{environment}-vpc"
        
        """
        Create VPC
        """
        vpc = aws.ec2.Vpc(
                vpc_name,
                cidr_block = config.require_object("vpc").get("cidr_block"),
                enable_dns_hostnames = config.require_object("vpc").get("enable_dns_hostnames"),
                tags = {"Name": vpc_name}
            )
        
        """
        Create Cloudwatch Group and Flow Logs if enabled.
        """
        if self.vpc_flow_logs_enabled():
            
           pulumi.log.info(f"{Helpers.get_current_timestamp()} | INFO | Flow logs for the VPC are enabled.")
           FlowLogs(environment,vpc).create()
        
        return vpc