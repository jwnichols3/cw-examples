import boto3
import json
from common.aws_client import initialize_aws_client


def list_cloudwatch_alarms(region_name=None):
    client = initialize_aws_client("cloudwatch", region_name=region_name)
    if client is None:
        return []

    try:
        response = client.describe_alarms()
        return [alarm["AlarmName"] for alarm in response["MetricAlarms"]]
    except Exception as e:
        print(f"Error listing CloudWatch alarms: {e}")
        return []


def list_cloudwatch_dashboards(region_name=None):
    client = initialize_aws_client("cloudwatch", region_name=region_name)
    if client is None:
        return []

    try:
        response = client.list_dashboards()
        return [
            dashboard["DashboardName"] for dashboard in response["DashboardEntries"]
        ]
    except Exception as e:
        print(f"Error listing CloudWatch dashboards: {e}")
        return []


def get_dashboard_details(dashboard_name, region_name=None):
    client = initialize_aws_client("cloudwatch", region_name=region_name)
    if client is None:
        return "AWS client initialization failed"

    try:
        response = client.get_dashboard(DashboardName=dashboard_name)
        dashboard_body = response["DashboardBody"]
        return json.loads(dashboard_body)
    except Exception as e:
        return f"Error getting dashboard details: {e}"


def create_or_update_rds_dashboard(dashboard_name, rds_instance_ids, region_name=None):
    client = initialize_aws_client("cloudwatch", region_name=region_name)
    if client is None:
        return "AWS client initialization failed"

    widgets = []  # Initialize an empty list of widgets

    # Loop through RDS instance IDs and create widgets for each
    for instance_id in rds_instance_ids:
        # Example widget: CPUUtilization
        cpu_widget = {
            # Widget configuration goes here
        }
        # Add other widgets as needed
        widgets.append(cpu_widget)

    dashboard_body = {"widgets": widgets}

    try:
        client.put_dashboard(
            DashboardName=dashboard_name, DashboardBody=json.dumps(dashboard_body)
        )
        return "Dashboard created/updated successfully"
    except Exception as e:
        return f"Error creating/updating dashboard: {e}"
