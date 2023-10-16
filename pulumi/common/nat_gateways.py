import pulumi
from pulumi import StackReference, export, ResourceOptions, Output
from datetime import datetime
import pytz
import json
import os
import pulumi_aws as aws
from common.helpers import Helpers

config = pulumi.Config()
region = aws.config.region

class NATGateways():
    def __init__(self, availability_zones_that_need_nat_gateways, environment, subnets):
        self.availability_zones_that_need_nat_gateways = availability_zones_that_need_nat_gateways
        self.environment = str(environment)
        self.subnets = subnets
        
    def  get_subnets(self):
        subnets = config.require_object("vpc").get("subnets")
        return subnets
    
    def determine_subnets_for_ngws(self, subnets, availability_zones_that_need_nat_gateways):
        #- use the passed params to create a list of public subnets that can get returned.

        #- AN empty dictionary to hold keys pairs of az:subnet_id
        ngw_subnets = {}
        
        #- Grab the public subnets
        public_subnets = self.subnets["public"]
        
        #- Empty dictionary to hold subnet_id and az
        ngw_subnets = {}
        
        for subnet in public_subnets:
            if subnet["availability_zone"] in availability_zones_that_need_nat_gateways:
                #print(subnet["subnet_id"])
                ngw_subnets.update({subnet["availability_zone"]: subnet["subnet_id"]})
                print(ngw_subnets)
        return ngw_subnets
        
    def create(self):
        availability_zones_that_need_nat_gateways = self.availability_zones_that_need_nat_gateways
        environment = self.environment
        subnets = self.subnets
        
        #- An empty dictionary that will contain the created nat gateways. This gets returned to main and passed
        # to the RouteTables class to create the necessary route tables.
        ngws = {}
        
        ngw_subnets = self.determine_subnets_for_ngws(subnets, availability_zones_that_need_nat_gateways)
        
        for subnet in ngw_subnets:
            
            ngw_name = f"{environment}-{Helpers.get_az_alias(subnet)}-ngw"
            
            #- Create the NGW
            nat_gateway = aws.ec2.NatGateway(
                                    ngw_name,
                                    subnet_id = ngw_subnets[subnet],
                                    allocation_id = (aws.ec2.Eip(
                                        f"{ngw_name}-eip",
                                        tags = { "Name": f"{ngw_name}-eip"}
                                        ).id))
            
            #- Append the NGW to the ngws dictionary
            ngws.update({ngw_name: nat_gateway})
            
        return ngws