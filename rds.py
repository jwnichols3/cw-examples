import sys
import argparse
from tabulate import tabulate
from rds.rds_utilities import (
    list_rds_instances,
    get_rds_allocated_storage,
    get_rds_free_storage_percentage,
)


def list_rds_instances_cli():
    print("Listing RDS Instances:")
    try:
        instances = list_rds_instances()
        for instance in instances:
            print(f"Instance Identifier: {instance['DBInstanceIdentifier']}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def display_cloudwatch_data():
    print("Fetching RDS CloudWatch Data:")
    try:
        instances = list_rds_instances()
        data = []
        for instance in instances:
            instance_id = instance["DBInstanceIdentifier"]
            allocated_storage_gb = get_rds_allocated_storage(
                instance_id
            )  # Already in GiB
            free_storage_percentage = get_rds_free_storage_percentage(instance_id)
            free_storage_gb = allocated_storage_gb * (free_storage_percentage / 100)

            # Format numbers with commas and two decimal places
            allocated_storage_str = f"{allocated_storage_gb:,.2f} GB"
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


def main():
    parser = argparse.ArgumentParser(description="AWS RDS Management Tool")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Command to list RDS instances
    list_parser = subparsers.add_parser("list", help="List RDS instances")

    # Command to display CloudWatch data
    cw_parser = subparsers.add_parser(
        "cw", help="Display CloudWatch data for RDS instances"
    )

    args = parser.parse_args()

    if args.command == "list":
        list_rds_instances_cli()
    elif args.command == "cw":
        display_cloudwatch_data()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
