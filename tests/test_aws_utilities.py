import unittest
import boto3
from moto import mock_ec2, mock_rds
from common.aws_utilities import (
    get_latest_amazon_linux_ami,
    get_vpcs,
    get_key_pairs,
    get_subnet_id_for_az_and_vpc,
    get_security_groups,
    get_security_groups_with_names,
    get_security_groups_for_vpc,
    get_vpcs,
    get_vpcs_with_names,
    get_availability_zones_for_vpc,
    get_subnets_for_vpc,
    create_db_subnet_group,
    get_db_subnet_groups,
)


class TestAWSUtilities(unittest.TestCase):
    @mock_ec2
    def test_get_latest_amazon_linux_ami(self):
        # Setup the mock environment
        ec2 = boto3.client("ec2", region_name="us-east-1")

        # Create a list to hold created AMIs
        created_amis = []

        # Create multiple dummy AMIs
        for i in range(3):
            image_id = ec2.register_image(
                Name=f"amzn2-ami-hvm-2.0.20200101.{i}-x86_64-gp2",
                Description="test-ami",
                Architecture="x86_64",
                RootDeviceName="/dev/sda1",
                VirtualizationType="hvm",
            )["ImageId"]
            created_amis.append(image_id)

        # Test the function
        latest_ami = get_latest_amazon_linux_ami(region_name="us-east-1")

        # Check if the function returns a non-None AMI ID
        self.assertIsNotNone(latest_ami)

    @mock_ec2
    def test_get_vpcs(self):
        ec2 = boto3.client("ec2", region_name="us-east-1")
        # Create a dummy VPC
        vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")
        vpc_id = vpc["Vpc"]["VpcId"]

        # Test the function
        vpcs = get_vpcs(region_name="us-east-1")

        # Check if the function returns the correct VPC ID
        self.assertIn(vpc_id, vpcs)

    @mock_ec2
    def test_get_vpcs_with_names(self):
        ec2 = boto3.client("ec2", region_name="us-east-1")
        # Create a dummy VPC and add a name tag
        vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")
        vpc_id = vpc["Vpc"]["VpcId"]
        vpc_name = "TestVPC"
        ec2.create_tags(Resources=[vpc_id], Tags=[{"Key": "Name", "Value": vpc_name}])

        # Test the function
        vpcs_with_names = get_vpcs_with_names(region_name="us-east-1")

        # Check if the function returns the correct VPC ID and name
        found_vpc = next(
            (vpc for vpc in vpcs_with_names if vpc["VpcId"] == vpc_id), None
        )
        self.assertIsNotNone(found_vpc)
        self.assertEqual(found_vpc.get("Name"), vpc_name)

    @mock_ec2
    def test_get_key_pairs(self):
        ec2 = boto3.client("ec2", region_name="us-east-1")
        # Create a dummy key pair
        key_pair = ec2.create_key_pair(KeyName="TestKeyPair")
        key_name = key_pair["KeyName"]

        # Test the function
        key_pairs = get_key_pairs(region_name="us-east-1")

        # Check if the function returns the correct key name
        self.assertIn(key_name, key_pairs)

    @mock_ec2
    def test_get_subnet_id_for_az_and_vpc(self):
        ec2 = boto3.client("ec2", region_name="us-east-1")

        # Create a dummy VPC
        vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")
        vpc_id = vpc["Vpc"]["VpcId"]

        # Create a subnet in the VPC
        az = "us-east-1a"  # Example AZ, adjust as needed
        subnet = ec2.create_subnet(
            VpcId=vpc_id, CidrBlock="10.0.1.0/24", AvailabilityZone=az
        )
        subnet_id = subnet["Subnet"]["SubnetId"]

        # Test the function
        retrieved_subnet_id = get_subnet_id_for_az_and_vpc(
            az, vpc_id, region_name="us-east-1"
        )

        # Check if the function returns the correct subnet ID
        self.assertEqual(retrieved_subnet_id, subnet_id)

    @mock_ec2
    def test_get_security_groups(self):
        ec2 = boto3.client("ec2", region_name="us-east-1")
        security_group = ec2.create_security_group(
            GroupName="test", Description="test security group"
        )
        security_groups = get_security_groups(region_name="us-east-1")
        self.assertIn(security_group["GroupId"], security_groups)

    @mock_ec2
    def test_get_security_groups_with_names(self):
        ec2 = boto3.client("ec2", region_name="us-east-1")

        security_group_name = "TestSG"

        security_group = ec2.create_security_group(
            GroupName=security_group_name, Description="test security group"
        )

        ec2.create_tags(
            Resources=[security_group["GroupId"]],
            Tags=[{"Key": "Name", "Value": security_group_name}],
        )

        security_groups_with_names = get_security_groups_with_names(
            region_name="us-east-1"
        )

        found_sg = next(
            (
                sg
                for sg in security_groups_with_names
                if sg["GroupId"] == security_group["GroupId"]
            ),
            None,
        )
        self.assertIsNotNone(found_sg)
        self.assertEqual(found_sg.get("GroupName"), security_group_name)

    @mock_ec2
    def test_get_security_groups_for_vpc(self):
        ec2 = boto3.client("ec2", region_name="us-east-1")

        # Create a dummy VPC
        vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")
        vpc_id = vpc["Vpc"]["VpcId"]

        # Create a security group in the VPC
        sg = ec2.create_security_group(
            GroupName="TestSG", Description="Test security group", VpcId=vpc_id
        )
        sg_id = sg["GroupId"]

        # Test the function
        sg_ids = get_security_groups_for_vpc(vpc_id, region_name="us-east-1")

        # Check if the function returns the correct security group ID
        self.assertIn(sg_id, sg_ids)

    @mock_ec2
    def test_get_availability_zones_for_vpc(self):
        ec2 = boto3.client("ec2", region_name="us-east-1")

        # Create a dummy VPC
        vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")
        vpc_id = vpc["Vpc"]["VpcId"]

        # Create a subnet in the VPC
        az = "us-east-1a"  # Example AZ, adjust as needed
        ec2.create_subnet(VpcId=vpc_id, CidrBlock="10.0.1.0/24", AvailabilityZone=az)

        # Test the function
        azs = get_availability_zones_for_vpc(vpc_id, region_name="us-east-1")

        # Check if the function returns the correct availability zone
        self.assertIn(az, azs)

    @mock_ec2
    def test_get_subnets_for_vpc(self):
        ec2 = boto3.client("ec2", region_name="us-east-1")

        # Create a dummy VPC
        vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")
        vpc_id = vpc["Vpc"]["VpcId"]

        # Get initial subnets (if any)
        initial_subnets = ec2.describe_subnets(
            Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
        )
        initial_subnet_ids = {
            subnet["SubnetId"] for subnet in initial_subnets["Subnets"]
        }

        # Create a subnet in the VPC
        az = "us-east-1a"  # Example AZ, adjust as needed
        subnet0 = ec2.create_subnet(
            VpcId=vpc_id, CidrBlock="10.0.1.0/24", AvailabilityZone=az
        )

        subnet1 = ec2.create_subnet(
            VpcId=vpc_id, CidrBlock="10.0.2.0/24", AvailabilityZone="us-east-1b"
        )
        subnet2 = ec2.create_subnet(
            VpcId=vpc_id, CidrBlock="10.0.3.0/24", AvailabilityZone="us-east-1c"
        )
        subnet3 = ec2.create_subnet(
            VpcId=vpc_id, CidrBlock="10.0.4.0/24", AvailabilityZone="us-east-1c"
        )

        subnet_ids = [
            subnet0["Subnet"]["SubnetId"],
            subnet1["Subnet"]["SubnetId"],
            subnet2["Subnet"]["SubnetId"],
            subnet3["Subnet"]["SubnetId"],
        ]

        # Test the function
        retrieved_subnet_ids = set(get_subnets_for_vpc(vpc_id, region_name="us-east-1"))

        # Check the counts after excluding initial subnets
        self.assertEqual(
            len(retrieved_subnet_ids - initial_subnet_ids), len(subnet_ids)
        )

    @mock_rds
    def test_create_db_subnet_group(self):
        rds_client = boto3.client("rds", region_name="us-east-1")
        subnet_group_name = create_db_subnet_group(
            "test_subnet_group", "Test Description", ["subnet-12345"], rds_client
        )

        self.assertEqual(subnet_group_name, "test_subnet_group")

        # Verify the subnet group was created
        response = rds_client.describe_db_subnet_groups(
            DBSubnetGroupName="test_subnet_group"
        )
        self.assertEqual(
            response["DBSubnetGroups"][0]["DBSubnetGroupName"], "test_subnet_group"
        )

    @mock_rds
    def test_get_db_subnet_groups(self):
        rds_client = boto3.client("rds", region_name="us-east-1")

        # Create a dummy DB subnet group
        rds_client.create_db_subnet_group(
            DBSubnetGroupName="test_subnet_group",
            DBSubnetGroupDescription="Test Description",
            SubnetIds=["subnet-12345"],
        )

        subnet_groups = get_db_subnet_groups(rds_client)
        self.assertIn("test_subnet_group", subnet_groups)


if __name__ == "__main__":
    unittest.main()
