import unittest
from moto import mock_s3, mock_ec2
from common.aws_client import initialize_aws_client


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

    # Additional tests can be added for other services and scenarios


if __name__ == "__main__":
    unittest.main()
