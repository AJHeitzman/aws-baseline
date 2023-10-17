import pulumi
from pulumi import export, ResourceOptions
import pulumi_aws as aws
import yaml
from common.helpers import Helpers
from common.subnets import Subnets

"""
Grab Config
"""
config = pulumi.Config()

class SecurityGroups():
    def __init__(self, environment, subnets, vpc):
        self.environment = str(environment)
        self.subnets = subnets
        self.vpc = vpc
    
    def get_rules(self, subnet_group, direction):
        rules = config.get_object("vpc").get("subnets").get(subnet_group).get("baseline_security_group").get(direction)
        return rules

    def get_rule_property(self, subnet_group, direction, rule, key):
        rules = self.get_rules(subnet_group, direction)
        
        if rules != "None":
            rule_config = rules.get(rule)
            key_value = rule_config.get(key)
            #key_value = config.get_object("vpc").get("subnets").get(subnet_group).get("baseline_security_group").get(direction).get(rule).get(key)
            return key_value
    
    def get_directional_args(self, subnet_group, direction):
        directional_args = []
        rules = self.get_rules(subnet_group, direction)
        
        if rules != "None":
            for rule in rules:
                directional_args.append(
                    aws.ec2.SecurityGroupIngressArgs(
                        description = f"{rule}",
                        protocol = self.get_rule_property(subnet_group, direction, rule, "protocol"),
                        from_port = self.get_rule_property(subnet_group, direction, rule, "from_port"),
                        to_port = self.get_rule_property(subnet_group, direction, rule, "to_port"),
                        cidr_blocks = self.get_rule_property(subnet_group, direction, rule, "cidr_blocks"),
                    )
                )
                
        return directional_args
    
    def create(self):
        environment = self.environment
        subnets = self.subnets
        vpc = self.vpc
        
        security_groups = []
        
        for subnet_group in subnets:
            
            """
            Generate Baseline Security Group Name
            """
            baseline_security_group_name = f"{environment}-{subnet_group}-baseline-sg"
            
            """
            Create Security Group
            """
            baseline_security_group = aws.ec2.SecurityGroup(
                baseline_security_group_name,
                description = f"Baseline security group for the {subnet_group} subnets.",
                vpc_id = vpc.id,
                ingress = self.get_directional_args(subnet_group, "ingresses"),
                egress = self.get_directional_args(subnet_group, "egresses"),
                tags={
                    "Name": baseline_security_group_name,
                })
            
            security_groups.append(baseline_security_group)
            
        return security_groups