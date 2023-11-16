import sys
import argparse
from tabulate import tabulate
from common.logging_utilities import setup_logging
from common.aws_client import initialize_aws_client
from rds.rds_utilities import (
    list_rds_instances,
    get_rds_allocated_storage,
    get_rds_free_storage,
    get_rds_instance_details,
)


def list_rds_instances_cli(region_name=None):
    print("Listing RDS Instances:")
    try:
        instances = list_rds_instances(region_name=region_name)
        for instance in instances:
            print(f"Instance Identifier: {instance['DBInstanceIdentifier']}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def display_cloudwatch_data(region_name=None):
    print("Fetching RDS CloudWatch Data:")
    try:
        instances = list_rds_instances(region_name=region_name)
        data = []
        for instance in instances:
            instance_id = instance["DBInstanceIdentifier"]
            allocated_storage_gb = get_rds_allocated_storage(
                instance_id, region_name=region_name
            )
            free_storage_bytes = get_rds_free_storage(
                instance_id, region_name=region_name
            )  # Now in bytes

            # Convert bytes to GB and format numbers
            allocated_storage_str = f"{allocated_storage_gb:,.2f} GB"
            free_storage_gb = free_storage_bytes / (1024**3)
            free_storage_str = f"{free_storage_gb:,.2f} GB"

            data.append([instance_id, allocated_storage_str, free_storage_str])

        print(
            tabulate(
                data,
                headers=["RDS Instance", "Allocated Storage (GB)", "Free Storage (GB)"],
            )
        )
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def display_detailed_rds_data(region_name=None):
    print("Fetching Detailed RDS Data:")
    try:
        instances = list_rds_instances(region_name=region_name)
        data = []
        for instance in instances:
            details = get_rds_instance_details(instance["DBInstanceIdentifier"])
            allocated_storage_gb = details["allocated_storage"]  # Already in GiB
            free_storage_bytes = get_rds_free_storage(
                details["instance_id"], region_name=region_name
            )  # In bytes
            free_storage_gb = free_storage_bytes / (1024**3)  # Convert to GB

            # Formatting tags as a comma-separated list
            tag_str = ", ".join([f"{k}: {v}" for k, v in details["tags"].items()])

            data.append(
                [
                    details["instance_id"],
                    f"{allocated_storage_gb:,.2f} GB",
                    f"{free_storage_gb:,.2f} GB",
                    details["engine"],
                    details["availability_zone"],
                    details["created_at"].strftime("%Y-%m-%d %H:%M:%S"),
                    tag_str,
                ]
            )

        print(
            tabulate(
                data,
                headers=[
                    "Instance",
                    "Allocated Storage",
                    "Free Storage",
                    "Engine",
                    "AZ",
                    "Created At",
                    "Tags",
                ],
            )
        )
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def parse_global_args(argv):
    global_parser = argparse.ArgumentParser(add_help=False)
    global_parser.add_argument("--region", help="Specify AWS region", default=None)

    # Parse only the global args
    global_args, remaining_argv = global_parser.parse_known_args(argv)

    return global_args, remaining_argv


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    global_args, remaining_argv = parse_global_args(argv)

    parser = argparse.ArgumentParser(description="AWS RDS Management Tool")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Command to list RDS instances
    list_parser = subparsers.add_parser("list", help="List RDS instances")

    # Command to display CloudWatch data
    cw_parser = subparsers.add_parser(
        "cw", help="Display CloudWatch data for RDS instances"
    )
    detail_parser = subparsers.add_parser(
        "detail", help="Display detailed information for RDS instances"
    )

    args = parser.parse_args(remaining_argv)

    if args.command == "list":
        list_rds_instances_cli(global_args.region)
    elif args.command == "cw":
        display_cloudwatch_data(global_args.region)
    elif args.command == "detail":
        display_detailed_rds_data(global_args.region)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
