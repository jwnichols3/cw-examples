import unittest
from moto import mock_s3, mock_ec2
from botocore.exceptions import ClientError
from common.aws_client import initialize_aws_client, initialize_aws_resource


class TestAWSClient(unittest.TestCase):
    @mock_s3
    def test_initialize_s3_client_default_region(self):
        # Test S3 client initialization without specifying a region
        client = initialize_aws_client("s3", region_name="us-east-1")
        self.assertIsNotNone(client)
        self.assertEqual(
            client.meta.region_name, "us-east-1"
        )  # Default region for moto

    @mock_ec2
    def test_initialize_ec2_client_with_region(self):
        # Test EC2 client initialization with a specific region
        test_region = "us-east-2"
        client = initialize_aws_client("ec2", region_name=test_region)
        self.assertIsNotNone(client)
        self.assertEqual(client.meta.region_name, test_region)

    @mock_ec2
    def test_initialize_ec2_resource_with_region(self):
        # Test EC2 resource initialization with a specific region
        test_region = "us-east-2"
        resource = initialize_aws_resource("ec2", region_name=test_region)
        self.assertIsNotNone(resource)
        # Additional checks can be added here if necessary


@mock_ec2
def test_initialize_with_invalid_region(self):
    with self.assertRaises(ClientError):
        initialize_aws_client("ec2", region_name="invalid-region")


def test_initialize_with_invalid_service(self):
    with self.assertRaises(
        ValueError
    ):  # Assuming ValueError is raised for invalid service
        initialize_aws_client("invalid-service")


if __name__ == "__main__":
    unittest.main()
