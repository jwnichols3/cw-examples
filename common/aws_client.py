import boto3
from botocore.exceptions import NoCredentialsError
from common.logging_utilities import setup_logging

# Initialize the logger
logger = setup_logging()


def initialize_aws_client(service_name, region_name=None):
    """
    Initializes and returns an AWS service client.

    Parameters:
    service_name (str): The name of the AWS service for which to create the client.
    region_name (str, optional): The AWS region to use. Defaults to None, which will use the default configured region.

    Returns:
    boto3.client: An initialized AWS service client, or None if an error occurs.
    """
    try:
        if region_name:
            client = boto3.client(service_name, region_name=region_name)
        else:
            client = boto3.client(service_name)
        return client
    except NoCredentialsError:
        logger.error("Credentials not available")
        return None
