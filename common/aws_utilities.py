from common.aws_client import initialize_aws_client
from common.logging_utilities import setup_logging

logger = setup_logging()


def get_latest_amazon_linux_ami(region_name=None):
    """
    Retrieves the latest Amazon Linux AMI ID for a given region.

    :param region_name: AWS region name. If None, will use the default configured region.
    :return: The latest Amazon Linux AMI ID or None if not found or an error occurs.
    """
    ec2_client = initialize_aws_client("ec2", region_name=region_name)

    if ec2_client is None:
        logger.error("Failed to initialize EC2 client.")
        return None

    try:
        response = ec2_client.describe_images(
            Filters=[
                {"Name": "name", "Values": ["amzn2-ami-hvm-*"]},
                {"Name": "architecture", "Values": ["x86_64"]},
                {"Name": "virtualization-type", "Values": ["hvm"]},
                {"Name": "owner-alias", "Values": ["amazon"]},
                {"Name": "state", "Values": ["available"]},
            ],
            Owners=["amazon"],
        )

        amis = sorted(response["Images"], key=lambda x: x["CreationDate"], reverse=True)
        return amis[0]["ImageId"] if amis else None
    except Exception as e:
        logger.error(f"Error retrieving the latest Amazon Linux AMI: {e}")
        return None


def get_subnet_id_for_az_and_vpc(az, vpc_id, ec2_client=None, region_name=None):
    """
    Retrieves the Subnet ID for a specified Availability Zone and VPC ID.

    :param az: The Availability Zone.
    :param vpc_id: The VPC ID.
    :param ec2_client: An optional boto3 EC2 client. If not provided, one will be initialized.
    :return: The Subnet ID or None if not found or an error occurs.
    """
    if ec2_client is None:
        ec2_client = initialize_aws_client("ec2", region_name=region_name)

    if ec2_client is None:
        logger.error("Failed to initialize EC2 client.")
        return None

    try:
        response = ec2_client.describe_subnets(
            Filters=[
                {"Name": "availability-zone", "Values": [az]},
                {"Name": "vpc-id", "Values": [vpc_id]},
            ]
        )
        subnets = response.get("Subnets", [])
        return subnets[0]["SubnetId"] if subnets else None
    except Exception as e:
        logger.error(f"Error retrieving subnet ID for AZ {az} and VPC {vpc_id}: {e}")
        return None


def get_key_pairs(ec2_client=None, region_name=None):
    """
    Retrieves a list of EC2 key pairs available in a specified AWS region.

    This function queries the AWS EC2 service to get a list of key pair names. It can use an existing EC2 client
    or create a new one. If the region is not specified, the default region configured in the environment is used.

    Parameters:
    ec2_client (boto3.client, optional): An initialized boto3 EC2 client. If None, a new client is created.
    region_name (str, optional): The AWS region where the key pairs are located. If None, the default region is used.

    Returns:
    list: A list of key pair names (strings). If an error occurs or no key pairs are found, returns None.

    Raises:
    Exception: Propagates any exceptions encountered during the EC2 client operation.

    Example:
    >>> get_key_pairs(region_name="us-west-2")
    ['keypair1', 'keypair2', ...]

    Note:
    The function prints an error message to the console if an exception occurs during the retrieval process.
    """

    if ec2_client is None:
        ec2_client = initialize_aws_client("ec2", region_name=region_name)
    try:
        response = ec2_client.describe_key_pairs()
        return [key_pair["KeyName"] for key_pair in response["KeyPairs"]]
    except Exception as e:
        logger.error(f"Error retrieving key pairs: {e}")
        return None


def get_security_groups(ec2_client=None, region_name=None):
    """
    Retrieves a list of security group IDs from AWS EC2.

    This function queries the AWS EC2 service to get a list of all security groups in the specified region.
    It can use an existing EC2 client or create a new one. If the region is not specified, the default region
    configured in the environment is used.

    Parameters:
    ec2_client (boto3.client, optional): An initialized boto3 EC2 client. If None, a new client is created.
    region_name (str, optional): The AWS region where the security groups are located. If None, the default region is used.

    Returns:
    list: A list of security group IDs (strings). Returns None if an error occurs.

    Raises:
    Exception: Propagates any exceptions encountered during the EC2 client operation.
    """
    if ec2_client is None:
        ec2_client = initialize_aws_client("ec2", region_name=region_name)
    try:
        response = ec2_client.describe_security_groups()
        return [sg["GroupId"] for sg in response["SecurityGroups"]]
    except Exception as e:
        logger.error(f"Error retrieving security groups: {e}")
        return None


def get_security_groups_with_names(ec2_client=None, region_name=None):
    """
    Retrieves a list of security group IDs from AWS EC2.

    This function queries the AWS EC2 service to get a list of all security groups in the specified region.
    It can use an existing EC2 client or create a new one. If the region is not specified, the default region
    configured in the environment is used.

    Parameters:
    ec2_client (boto3.client, optional): An initialized boto3 EC2 client. If None, a new client is created.
    region_name (str, optional): The AWS region where the security groups are located. If None, the default region is used.

    Returns:
    list: A list of security group IDs (strings). Returns None if an error occurs.

    Raises:
    Exception: Propagates any exceptions encountered during the EC2 client operation.
    """
    if ec2_client is None:
        ec2_client = initialize_aws_client("ec2", region_name=region_name)
    try:
        response = ec2_client.describe_security_groups()
        return [
            {"GroupId": sg["GroupId"], "GroupName": sg["GroupName"]}
            for sg in response["SecurityGroups"]
        ]
    except Exception as e:
        logger.error(f"Error retrieving security groups: {e}")
        return None


def get_vpcs(ec2_client=None, region_name=None):
    """
    Retrieves a list of VPC IDs from AWS EC2.

    This function queries the AWS EC2 service to get a list of all Virtual Private Clouds (VPCs) in the specified region.
    It can use an existing EC2 client or create a new one. If the region is not specified, the default region
    configured in the environment is used.

    Parameters:
    ec2_client (boto3.client, optional): An initialized boto3 EC2 client. If None, a new client is created.
    region_name (str, optional): The AWS region where the VPCs are located. If None, the default region is used.

    Returns:
    list: A list of VPC IDs (strings). Returns None if an error occurs.

    Raises:
    Exception: Propagates any exceptions encountered during the EC2 client operation.
    """
    if ec2_client is None:
        ec2_client = initialize_aws_client("ec2", region_name=region_name)
    try:
        response = ec2_client.describe_vpcs()
        return [vpc["VpcId"] for vpc in response["Vpcs"]]
    except Exception as e:
        logger.error(f"Error retrieving VPCs: {e}")
        return None


def get_vpcs_with_names(ec2_client=None, region_name=None):
    """
    Retrieves a list of VPCs along with their names from AWS EC2.

    This function queries the AWS EC2 service to get a list of all VPCs and their associated names in the specified region.
    The names are extracted from the VPC tags. It can use an existing EC2 client or create a new one. If the region is not
    specified, the default region configured in the environment is used.

    Parameters:
    ec2_client (boto3.client, optional): An initialized boto3 EC2 client. If None, a new client is created.
    region_name (str, optional): The AWS region where the VPCs are located. If None, the default region is used.

    Returns:
    list of dict: Each dictionary contains 'VpcId' and 'Name' for a VPC. Returns None if an error occurs.

    Raises:
    Exception: Propagates any exceptions encountered during the EC2 client operation.
    """
    if ec2_client is None:
        ec2_client = initialize_aws_client("ec2", region_name=region_name)
    try:
        response = ec2_client.describe_vpcs()
        vpcs = []
        for vpc in response["Vpcs"]:
            name = ""
            for tag in vpc.get("Tags", []):
                if tag["Key"] == "Name":
                    name = tag["Value"]
                    break
            vpcs.append({"VpcId": vpc["VpcId"], "Name": name})
        return vpcs
    except Exception as e:
        logger.error(f"Error retrieving VPCs with names: {e}")
        return None


def get_security_groups_for_vpc(vpc_id, ec2_client=None, region_name=None):
    """
    Retrieves a list of security group IDs associated with a specific VPC.

    This function queries the AWS EC2 service to get a list of all security groups that are associated with the specified VPC.
    It can use an existing EC2 client or create a new one. If the region is not specified, the default region configured
    in the environment is used.

    Parameters:
    vpc_id (str): The ID of the VPC.
    ec2_client (boto3.client, optional): An initialized boto3 EC2 client. If None, a new client is created.
    region_name (str, optional): The AWS region where the VPC is located. If None, the default region is used.

    Returns:
    list: A list of security group IDs (strings) for the specified VPC. Returns None if an error occurs.

    Raises:
    Exception: Propagates any exceptions encountered during the EC2 client operation.
    """
    if ec2_client is None:
        ec2_client = initialize_aws_client("ec2", region_name=region_name)
    try:
        response = ec2_client.describe_security_groups(
            Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
        )
        return [sg["GroupId"] for sg in response["SecurityGroups"]]
    except Exception as e:
        logger.error(f"Error retrieving security groups for VPC {vpc_id}: {e}")
        return None


def get_availability_zones_for_vpc(vpc_id, ec2_client=None, region_name=None):
    """
    Retrieves a list of availability zones for the subnets associated with a specific VPC.

    This function queries the AWS EC2 service to get a list of all availability zones that the subnets of the specified VPC
    are located in. It can use an existing EC2 client or create a new one. If the region is not specified, the default region
    configured in the environment is used.

    Parameters:
    vpc_id (str): The ID of the VPC.
    ec2_client (boto3.client, optional): An initialized boto3 EC2 client. If None, a new client is created.
    region_name (str, optional): The AWS region where the VPC is located. If None, the default region is used.

    Returns:
    list: A list of availability zones (strings) for the specified VPC. Returns None if an error occurs.

    Raises:
    Exception: Propagates any exceptions encountered during the EC2 client operation.
    """
    if ec2_client is None:
        ec2_client = initialize_aws_client("ec2", region_name=region_name)
    try:
        response = ec2_client.describe_subnets(
            Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
        )
        return list(set([subnet["AvailabilityZone"] for subnet in response["Subnets"]]))
    except Exception as e:
        logger.error(f"Error retrieving availability zones for VPC {vpc_id}: {e}")
        return None


def get_subnets_for_vpc(vpc_id, ec2_client=None, region_name=None):
    """
    Retrieves a list of subnet IDs associated with a specific VPC.

    This function queries the AWS EC2 service to get a list of all subnets that are associated with the specified VPC.
    It can use an existing EC2 client or create a new one. If the region is not specified, the default region
    configured in the environment is used.

    Parameters:
    vpc_id (str): The ID of the VPC.
    ec2_client (boto3.client, optional): An initialized boto3 EC2 client. If None, a new client is created.
    region_name (str, optional): The AWS region where the VPC is located. If None, the default region is used.

    Returns:
    list: A list of subnet IDs (strings) for the specified VPC. Returns None if an error occurs.

    Raises:
    Exception: Propagates any exceptions encountered during the EC2 client operation.
    """
    if ec2_client is None:
        ec2_client = initialize_aws_client("ec2", region_name=region_name)
    try:
        response = ec2_client.describe_subnets(
            Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
        )
        return [subnet["SubnetId"] for subnet in response["Subnets"]]
    except Exception as e:
        logger.error(f"Error retrieving subnets for VPC {vpc_id}: {e}")
        return None
