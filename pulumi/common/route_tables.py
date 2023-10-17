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

class RouteTables():
    def __init__(self, environment, igw, nat_gateways, subnets, vpc):
        self.environment = str(environment)
        self.igw = igw
        self.nat_gateways = nat_gateways
        self.subnets = subnets
        self.vpc = vpc

    def  get_subnets(self):
        subnets = config.require_object("vpc").get("subnets")
        return subnets
    
    def get_subnet_abbreviation(self, subnet):
        abbreviation =  self.get_subnets().get(subnet).get("abbreviation")
        return abbreviation

    def get_nat_gateway_id(self, availability_zone):
        nat_gateways = self.nat_gateways
        ngw = list(filter(lambda ngw: ngw["availability_zone"] == availability_zone, nat_gateways))[0]
        nat_gateway_id = ngw["ngw_id"]
        pulumi.log.info(f"{Helpers.get_current_timestamp()} | INFO | NAT Gateway: {ngw['name']} will be set for default route destination.")
        return nat_gateway_id

    def get_route_args(self, subnet_group, availability_zone=None):
        routes = config.require_object("vpc").get("subnets").get(subnet_group).get("routes")
        route_args = []
        for route in routes:
            
            #- NAT Gateway
            if routes[route]['target'] == 'ngw':
                
                route_args.append(
                    aws.ec2.RouteTableRouteArgs(
                        cidr_block = route,
                        nat_gateway_id = self.get_nat_gateway_id(availability_zone)
                    )
                )
            
            #- Internet Gateway    
            elif routes[route]['target']== 'igw':
                route_args.append(
                    aws.ec2.RouteTableRouteArgs(
                        cidr_block = route,
                        gateway_id = self.igw.id
                    )
                )
                
        return route_args

    def create(self):
        environment = self.environment
        subnets = self.subnets
        vpc = self.vpc
        
        for subnet_group in subnets:
            if subnet_group == "public":
                
                """
                Generate public route table name
                """
                subnet_group_abbreviation = Subnets(environment, vpc).get_subnet_abbreviation(subnet_group)
                route_table_name = f"{environment}-{subnet_group_abbreviation}-rtb"
                
                """
                Create public route table
                """
                route_table = aws.ec2.RouteTable(
                    route_table_name,
                    vpc_id = vpc.id,
                    routes = self.get_route_args(subnet_group),
                    tags = {'Name': route_table_name}
                )
                
                """
                Associate each of the public subnets with the public route table.
                """
                # The public route table is shared across all public subnets in the VPC. So iterate over the public subnets
                # and create the route table association.
                for subnet in subnets[subnet_group]:
                    aws.ec2.RouteTableAssociation(
                        f"{subnet['name']}-rtb-assoc",
                        route_table_id = route_table.id,
                        subnet_id = subnet["subnet_id"]
                    )
            
            else:
                # The non "public" subnets will each have their own route table. Iterate over the remaining subnets within each subnet_group
                # creating a route table and associating it with the subnet.
                for subnet in subnets[subnet_group]:
                    pulumi.log.info(f"{Helpers.get_current_timestamp()} | INFO | Creating a route table for {subnet_group} subnet: {subnet['name']}")
                    
                    """
                    Generate route table name
                    """
                    subnet_group_abbreviation = Subnets(environment, vpc).get_subnet_abbreviation(subnet_group)
                    az_alias = Helpers.get_az_alias(subnet["availability_zone"])
                    route_table_name = f"{environment}-{subnet_group_abbreviation}-{az_alias}-rtb"

                    """
                    Create Route Table
                    """
                    route_table = aws.ec2.RouteTable(
                        route_table_name,
                        vpc_id = vpc.id,
                        routes = self.get_route_args(subnet_group, subnet["availability_zone"]),
                        tags = {'Name': route_table_name}
                    )
                    
                    """
                    Assocaite subnet with route table
                    """
                    pulumi.log.info(f"{Helpers.get_current_timestamp()} | INFO | Associating route table: {route_table_name} with subnet: {subnet['name']}")
                    aws.ec2.RouteTableAssociation(
                        f"{subnet['name']}-rtb-assoc",
                        route_table_id = route_table.id,
                        subnet_id = subnet["subnet_id"]
                    )

        #return route_table