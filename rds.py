import sys
import argparse
from rds.rds_utilities import list_rds_instances


def list_rds_instances_cli():
    print("Listing RDS Instances:")
    try:
        instances = list_rds_instances()
        for instance in instances:
            print(f"Instance Identifier: {instance['DBInstanceIdentifier']}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="AWS RDS Management Tool")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Command to list RDS instances
    list_parser = subparsers.add_parser("list", help="List RDS instances")

    args = parser.parse_args()

    if args.command == "list":
        list_rds_instances_cli()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
