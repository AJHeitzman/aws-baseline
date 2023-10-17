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

class Subnets():
    def __init__(self, environment, vpc):
        self.environment = str(environment)
        self.vpc = vpc
        
    def  get_subnets(self):
        subnets = config.require_object("vpc").get("subnets")
        return subnets
    
    def get_subnet_abbreviation(self, subnet):
        abbreviation =  self.get_subnets().get(subnet).get("abbreviation")
        return abbreviation
    
    def get_subnet_cidr_blocks(self, subnet):
        cidr_blocks = self.get_subnets().get(subnet).get("cidr_blocks")
        return cidr_blocks
    
    def requires_ngw(self, subnet):
        routes = self.get_subnets().get(subnet).get("routes")
        
        if "0.0.0.0/0" in routes:
            if routes.get("0.0.0.0/0").get("target") == "ngw":
                return True
            else:
                return False
        else:
            return False
    
    def create(self):
        environment = self.environment
        vpc = self.vpc
        subnets = self.get_subnets()
        
        #- An empty dictionary that will be used to hold the created subnets so they can be returned and used outside.
        all_created_subnets = {}
        
        #- An empty array to hold the AZ's that will need NAT Gateways created.
        availability_zones_that_need_nat_gateways = []        
        
        for subnet in subnets:
            
            #- An empty array that will be used to store the created subnets for the current subnet type.
            created_subnets = []
            
            #- Check if subnet will require
            subnet_requires_ngw = self.requires_ngw(subnet)
            
            #- Get the list of cidr blocks for the subnet
            cidr_blocks = self.get_subnet_cidr_blocks(subnet)
            
            for cidr_block in cidr_blocks:
                #- Retrieve the index of the current cidr_block
                index = cidr_blocks.index(cidr_block)
                
                #- Use the index + 1 to get the corresponding letter in the alphabet
                letter = chr(ord('`')+(index+1))
                
                #- Use the letter and region to create the string that will be used for the Availablilty Zone when creating the subnet below.
                az = f"{region}{letter}"
                
                #- Generate a shortend name for the AZ, which gets used in the subnet name below.
                az_abbr = Helpers.get_az_alias(az)
                
                #- Uncomment for troubleshooting
                #print(f"The current index of {cidr_block} is: {index}")
                #print(f"The corresponding letter for {cidr_block} is: {letter}")
                #print(f"The corresponding az for the {cidr_block} is: {az}")
                #print(az_abbr)
                #print("----------------------------------")
                
                #- Check if we need to append the Availability Zone to the availability_zones_that_need_nat_gateway arrays
                if subnet_requires_ngw and az not in availability_zones_that_need_nat_gateways:
                    availability_zones_that_need_nat_gateways.append(az)
                
                subnet_name = f"{environment}-{self.get_subnet_abbreviation(subnet)}-subnet-{az_abbr}"
                created_subnet = aws.ec2.Subnet(
                                subnet_name,
                                vpc_id = vpc.id,
                                cidr_block = cidr_block,
                                availability_zone = az,
                                tags = {'Name': subnet_name}
                )
                
                created_subnets.append({"name": subnet_name, "availability_zone": az, "subnet_id": created_subnet.id})
            
            """
            Structure of returned subnets to main. Keep for reference.
            
            {'database': [{'name': 'prod-db-subnet-use1a', 'availability_zone': 'us-east-1a', 'subnet_id': <pulumi.output.Output object at 0x000001994F2AB850>}, {'name': 'prod-db-subnet-use1b', 'availability_zone': 'us-east-1b', 'subnet_id': <pulumi.output.Output object at 0x000001994F2D9990>}, {'name': 'prod-db-subnet-use1c', 'availability_zone': 'us-east-1c', 'subnet_id': <pulumi.output.Output object at 0x000001994F2DBB50>}], 'private': [{'name': 'prod-pri-subnet-use1a', 'availability_zone': 'us-east-1a', 'subnet_id': <pulumi.output.Output object at 0x000001994F2F1C50>}, {'name': 'prod-pri-subnet-use1b', 'availability_zone': 'us-east-1b', 'subnet_id': <pulumi.output.Output object at 0x000001994F304DD0>}, {'name': 'prod-pri-subnet-use1c', 'availability_zone': 'us-east-1c', 'subnet_id': <pulumi.output.Output object at 0x000001994F3079D0>}], 'public': [{'name': 'prod-pub-subnet-use1a', 'availability_zone': 'us-east-1a', 'subnet_id': <pulumi.output.Output object at 0x000001994F325D90>}, {'name': 'prod-pub-subnet-use1b', 'availability_zone': 'us-east-1b', 'subnet_id': <pulumi.output.Output object at 0x000001994F334450>}, {'name': 'prod-pub-subnet-use1c', 'availability_zone': 'us-east-1c', 'subnet_id': <pulumi.output.Output object at 0x000001994F336810>}]}
            """
            
            all_created_subnets.update({subnet: created_subnets })
                
        return all_created_subnets, availability_zones_that_need_nat_gateways