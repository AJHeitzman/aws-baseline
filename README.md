![Pulumi](https://img.shields.io/badge/Pulumi-3.88.0-informational?logo=Pulumi&logoColor=purple)
![Python](https://img.shields.io/badge/Python-3.11.6-informational?logo=Python&logoColor=yellow)
![AWS-CLI](https://img.shields.io/badge/AWS_CLI-2.13.5-informational?logo=Amazon&logoColor=orange)
![Visual_Studio_Code](https://img.shields.io/badge/Visual_Studio_Code-1.83.0-informational?logo=VisualStudioCode)

# AWS Baseline
This is a [Pulumi](www.pulumi.com) Python project used to provisions a baseline VPC with a typical subnet setup.

The following resources get created:
* VPC
* Internet Gateway
* Subnets
* NAT Gateways
* Route Tables
* Security Groups

## IP Addressing Considerations and Requirements
I find it easiest to work my way backwards on this.
1. Determine how many ```Availability Zones``` you want to be spread across.
2. Determine the types of subnets. So for example lets say we know we want an subnet for ```databases``` which would be a private subnet. We also want an isolated ```private``` subnet for everything else that should not be publicly exposed and that isn't a database. Then finally the ```public``` subnet which will contain any public facing components.
3. Determine the size of the subnets for each type of subnet you want to deploy. So for example if we want to be in 3 ```Availability Zones``` across the 3 subnet types we determined above (```databse```, ```private```, and ```public```), we would need to carve out at least 9 ```cidr_blocks```. To do that we just need to decide how large the subnets will be, for the sake of simplicity lets just make them all a ```/23```, giving use a total of 510 usable ip addresses per subnet.
4. Determine the ```cidr_block``` for the ```VPC```. So in step 3 above, we determined **9** subnets with **512** ip addresses each (which is a /23 with 510 usable addresses), multiply that to get **4,608**, so we would at the very least need to go with a ```/19```.

Checkout [Visual Subnet Calculator](https://www.davidc.net/sites/default/subnets/subnets.html), its a handy online tool that makes subnetting easier.

> [!important]  
> You will need determine what ```CIDR``` block you want to use for the ```VPC```. Try to think ahead and leave a cushion for any potential future growth. Whatever you determine will need to be updated in the stacks config.

```yaml
config:
  AWS-Baseline:vpc:
    cidr_block: 10.0.0.0/19
```

| CIDR | Subnet Mask | IP Addresses |
|--|--|--|
| /20 | 255.255.240.0 | 4,096
| /19 | 255.255.224.0 | 8,192
| /18 | 255.255.192.0 | 16,384
| /17 | 255.255.128.0 | 32,768
| /16 | 255.255.0.0 | 65,536

Once you have figured out your ```cidr_block``` for the ```VPC``` you will need to determine how you want to carve out you subnets. So for example if deploying EKS nodes in the private subnets consider how many IP addresses each ```node``` will consume. 

> [!warning]  
> You **CANNOT** update the CIDR on the ```VPC``` or a ```Subnet``` once created! To modify an existing subnet you would have to detroy and recreate it, which means any resources built within that subnet would also need to be destroy and rebuilt.

## EIP (Elastic IP)
By default this project will provision 3 ```eip``` addresses, one for each of the ```nat gateways``` _(one nat gateway per az)_.
> [!important]  
By default your account is allowed to create 5 ```eip``` addresses. If you plan on using more than 5 ```availability zones``` and you also plan on deploying a ```nat gateway``` for resources in the private subnets to reach the internet, then you will need to request an increase in the number of ```eip``` addresses allowed. This increase can be requested in the web console and usually takes 15-30 minutes for it to get approved, large requests will take longer and require contacting someone at AWS.

## Understanding the Config
Some notes on the stacks config layout.....


