import argparse
import uuid
import boto3
import sys
import time
from tabulate import tabulate
from botocore.exceptions import ClientError
from common.general_utilities import prompt_for_choice, prompt_if_none
from common.logging_utilities import setup_logging
from common.aws_utilities import (
    get_vpcs,
    get_vpcs_with_names,
    get_subnets_for_vpc,
    get_security_groups_for_vpc,
)
from common.aws_client import initialize_aws_client

logger = setup_logging()


def create_rds_instances(args, rds_client):
    launch_run_id = str(uuid.uuid4())
    instance_ids = []

    for i in range(args.count):
        instance_name = f"{args.name}_{i}"
        print(
            f"Creating RDS instance {instance_name}\nargs.allocated_storage={args.allocated_storage}\nargs.instance_class={args.instance_class}\nargs.engine={args.engine}\nargs.security_group={args.security_group}\nargs.subnet={args.subnet}"
        )
        try:
            response = rds_client.create_db_instance(
                DBInstanceIdentifier=instance_name,
                AllocatedStorage=args.allocated_storage,
                DBInstanceClass=args.instance_class,
                Engine=args.engine,
                MasterUsername="rocket",
                MasterUserPassword=args.password,
                VpcSecurityGroupIds=[args.security_group],
                DBSubnetGroupName=args.subnet,
                Tags=[{"Key": "LaunchRun", "Value": launch_run_id}],
                PubliclyAccessible=args.public_access,
                MultiAZ=args.multi_az,
            )
            instance_ids.append(response["DBInstance"]["DBInstanceIdentifier"])
        except ClientError as e:
            print(f"Failed to create instance {instance_name}: {e}")

    print("Waiting for instances to launch. Press Ctrl-C to skip.")
    try:
        for instance_id in instance_ids:
            waiter = rds_client.get_waiter("db_instance_available")
            waiter.wait(DBInstanceIdentifier=instance_id)
            print(f"Instance {instance_id} is available.")
    except KeyboardInterrupt:
        print("Waiting skipped by user.")
    finally:
        return launch_run_id, instance_ids


def summarize_instances(rds_client, instance_ids):
    table_data = []
    for instance_id in instance_ids:
        instance = rds_client.describe_db_instances(DBInstanceIdentifier=instance_id)[
            "DBInstances"
        ][0]
        table_data.append(
            [
                instance["DBInstanceIdentifier"],
                instance["DBInstanceStatus"],
                instance["Engine"],
                instance["DBInstanceClass"],
                instance["AllocatedStorage"],
            ]
        )
    print(
        tabulate(
            table_data,
            headers=["Instance ID", "Status", "Engine", "Class", "Storage (GB)"],
            tablefmt="grid",
        )
    )


def delete_rds_batch(rds_client, launch_run_id):
    instances = rds_client.describe_db_instances()["DBInstances"]
    for instance in instances:
        tags = {tag["Key"]: tag["Value"] for tag in instance.get("TagList", [])}
        if tags.get("LaunchRun") == launch_run_id:
            instance_id = instance["DBInstanceIdentifier"]
            try:
                rds_client.delete_db_instance(
                    DBInstanceIdentifier=instance_id, SkipFinalSnapshot=True
                )
                print(f"Deleted instance {instance_id}")
            except ClientError as e:
                print(f"Failed to delete instance {instance_id}: {e}")


def main():
    region_list = ["us-east-1", "us-east-2", "us-west-2", "eu-west-1"]
    rds_engine_list = ["postgres", "mysql", "mariadb"]
    parser = argparse.ArgumentParser(description="RDS Instance Management Tool")
    subparsers = parser.add_subparsers(dest="command")

    # Create parser
    create_parser = subparsers.add_parser("create", help="Create RDS instances")
    create_parser.add_argument("--name", help="RDS instance name prefix")
    create_parser.add_argument(
        "--count", type=int, default=1, help="Number of RDS instances to launch"
    )
    create_parser.add_argument(
        "--region",
        choices=region_list,
        help="Database engine",
    )
    create_parser.add_argument(
        "--engine",
        choices=rds_engine_list,
        help="Database engine",
    )
    create_parser.add_argument(
        "--password", help="Master user password (auto-generated if not provided)"
    )
    create_parser.add_argument("--vpc", help="VPC ID")
    create_parser.add_argument("--subnet", help="Subnet ID")
    create_parser.add_argument("--security_group", help="Security Group ID")
    create_parser.add_argument(
        "--allocated_storage",
        type=int,
        default=200,
        choices=range(20, 4001),
        help="Allocated storage in GB",
    )
    create_parser.add_argument(
        "--public_access",
        action="store_true",
        help="Make the DB instance publicly accessible",
    )
    create_parser.add_argument(
        "--multi_az", action="store_true", help="Enable Multi-AZ deployment"
    )
    create_parser.add_argument(
        "--instance_class", default="db.m4.large", help="DB instance class"
    )

    # Delete parser
    delete_parser = subparsers.add_parser("delete", help="Delete RDS batch")
    delete_parser.add_argument(
        "--launch_run_id", required=True, help="Launch run ID for deletion"
    )

    args = parser.parse_args()

    # Check if a command is provided
    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Prompt for region with choices
    if args.region not in region_list:
        print("Available regions:")
        for i, region in enumerate(region_list, 1):
            print(f"{i}. {region}")
        region_choice = int(input("Choose a region (number): "))
        args.region = region_list[region_choice - 1]

    rds_client = initialize_aws_client("rds", region_name=args.region)
    if not rds_client:
        print("Failed to initialize RDS client.")
        sys.exit(1)

    rds_client = initialize_aws_client("rds", region_name=args.region)
    if not rds_client:
        print("Failed to initialize RDS client.")
        sys.exit(1)

    if args.command == "create":
        # Move these prompts inside the 'create' command section
        args.name = prompt_if_none(args.name, "Enter RDS instance name prefix: ")
        args.engine = prompt_if_none(
            args.engine, "Enter database engine (postgres, mysql, mariadb): "
        )
        args.password = args.password or str(
            uuid.uuid4()
        )  # Generate random password if not provided

        if not args.vpc:
            vpcs = get_vpcs(region_name=args.region)
            args.vpc = prompt_for_choice(vpcs, "Choose a VPC: ")
        if not args.subnet:
            subnets = get_subnets_for_vpc(args.vpc)
            args.subnet = prompt_for_choice(subnets, "Choose a Subnet: ")
        if not args.security_group:
            security_groups = get_security_groups_for_vpc(args.vpc)
            args.security_group = prompt_for_choice(
                security_groups, "Choose a Security Group: "
            )

        launch_run_id, instance_ids = create_rds_instances(args, rds_client)
        summarize_instances(rds_client, instance_ids)
        print(f"Launched instances with LaunchRun ID: {launch_run_id}")
        print(
            f"To replicate this operation: python rds_manager.py create --name {args.name} --count {args.count} --engine {args.engine} --password {args.password} --vpc {args.vpc} --subnet {args.subnet} --security_group {args.security_group} --allocated_storage {args.allocated_storage} {'--public_access' if args.public_access else ''} {'--multi_az' if args.multi_az else ''} --instance_class {args.instance_class}"
        )
        print(
            f"To delete these instances: python rds_manager.py delete --launch_run_id {launch_run_id}"
        )

    elif args.command == "delete":
        args.launch_run_id = prompt_if_none(
            args.launch_run_id, "Enter LaunchRun ID for deletion: "
        )
        delete_rds_batch(rds_client, args.launch_run_id)


if __name__ == "__main__":
    main()
