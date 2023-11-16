import boto3
from botocore.exceptions import NoCredentialsError


def initialize_aws_client(service_name, region_name=None):
    try:
        if region_name:
            client = boto3.client(service_name, region_name=region_name)
        else:
            client = boto3.client(service_name)
        return client
    except NoCredentialsError:
        print("Credentials not available")
        return None
