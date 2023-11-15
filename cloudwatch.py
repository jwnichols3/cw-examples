import argparse
from cloudwatch.cloudwatch_utilities import (
    list_cloudwatch_dashboards,
    list_cloudwatch_alarms,
    get_dashboard_details,
)


def list_dashboards_cli(detailed=False):
    dashboards = list_cloudwatch_dashboards()
    for dashboard in dashboards:
        print(dashboard)
        if detailed:
            details = get_dashboard_details(dashboard)
            print("Details:", details)


def list_alarms_cli():
    alarms = list_cloudwatch_alarms()
    for alarm in alarms:
        print(alarm)


def main():
    parser = argparse.ArgumentParser(description="AWS CloudWatch Management Tool")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Command to list CloudWatch dashboards
    list_dashboards_parser = subparsers.add_parser(
        "list-dashboards", help="List CloudWatch dashboards"
    )
    list_dashboards_parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed information for each dashboard",
    )

    # Command to list CloudWatch alarms
    list_alarms_parser = subparsers.add_parser(
        "list-alarms", help="List CloudWatch alarms"
    )

    args = parser.parse_args()

    if args.command == "list-dashboards":
        list_dashboards_cli(args.detailed)
    elif args.command == "list-alarms":
        list_alarms_cli()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
