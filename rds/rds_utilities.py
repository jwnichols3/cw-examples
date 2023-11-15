import boto3
import datetime
from common.aws_client import initialize_aws_client
from common.logging_utilities import setup_logging

logger = setup_logging()


def list_rds_instances():
    client = initialize_aws_client("rds")
    if client is None:
        return []

    try:
        response = client.describe_db_instances()
        return response["DBInstances"]
    except Exception as e:
        logger.error(f"Error in listing RDS instances: {e}")
        return []


def get_rds_allocated_storage(instance_id):
    client = initialize_aws_client("rds")
    if client is None:
        return "AWS client initialization failed"

    try:
        response = client.describe_db_instances(DBInstanceIdentifier=instance_id)
        db_instances = response["DBInstances"]
        if not db_instances:
            return "Instance not found"

        instance = db_instances[0]
        allocated_storage = instance["AllocatedStorage"]  # Storage in GiB
        return allocated_storage
    except Exception as e:
        return f"Error: {e}"


def get_rds_free_storage(instance_id):
    try:
        client = initialize_aws_client("cloudwatch")
        metrics = client.get_metric_statistics(
            Namespace="AWS/RDS",
            MetricName="FreeStorageSpace",
            Dimensions=[{"Name": "DBInstanceIdentifier", "Value": instance_id}],
            StartTime=datetime.datetime.utcnow() - datetime.timedelta(minutes=5),
            EndTime=datetime.datetime.utcnow(),
            Period=60,
            Statistics=["Average"],
        )
        if metrics["Datapoints"]:
            free_storage = sorted(
                metrics["Datapoints"], key=lambda x: x["Timestamp"], reverse=True
            )[0]["Average"]
            return free_storage
        else:
            return "No data points found for FreeStorageSpace"
    except Exception as e:
        return f"Error getting free storage: {e}"


def get_rds_free_storage_percentage(instance_id):
    client = boto3.client("rds")

    try:
        # Fetch details of the RDS instance
        response = client.describe_db_instances(DBInstanceIdentifier=instance_id)
        db_instances = response["DBInstances"]
        if not db_instances:
            return "Instance not found"

        instance = db_instances[0]
        total_storage = (
            instance["AllocatedStorage"] * 1024**3
        )  # Convert from GiB to bytes

        # Fetch CloudWatch metrics for FreeStorageSpace
        cloudwatch = boto3.client("cloudwatch")
        metrics = cloudwatch.get_metric_statistics(
            Namespace="AWS/RDS",
            MetricName="FreeStorageSpace",
            Dimensions=[{"Name": "DBInstanceIdentifier", "Value": instance_id}],
            Period=3600,
            StartTime=datetime.datetime.utcnow() - datetime.timedelta(hours=1),
            EndTime=datetime.datetime.utcnow(),
            Statistics=["Average"],
        )

        if metrics["Datapoints"]:
            free_storage = metrics["Datapoints"][-1][
                "Average"
            ]  # Get the latest data point
            free_storage_percentage = (free_storage / total_storage) * 100
            return free_storage_percentage
        else:
            return "No data points found for FreeStorageSpace"

    except Exception as e:
        return f"Error: {e}"
