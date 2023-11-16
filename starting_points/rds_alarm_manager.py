import boto3
import argparse
import sys
import os
import json
import logging

## STATUS: Not Working


# Make changes to how you want the alarm parameters in this class. The use of a Config data class is for simplicity in the script. It is not the best Python practice.
class Config:
    PAGINATION_COUNT = 100  # EBS Get volume pagination count
    DEFAULT_REGION = "us-west-2"
    VPC_ENDPOINT_CW = f"https://monitoring.{DEFAULT_REGION}.amazonaws.com"
    VPC_ENDPOINT_RDS = (
        f"https://rds.{DEFAULT_REGION}.amazonaws.com"  # UNKNOWN IF THIS WORKS
    )

    VPC_ENDPOINT_SNS = f"https://sns.{DEFAULT_REGION}.amazonaws.com"
    INCLUDE_OK_ACTION = True  # If set to False, this will not send the "OK" state change of the alarm to SNS
    SNS_OK_ACTION_ARN = "arn:aws:sns:us-west-2:357044226454:ebs_alerts"  # Consider this the default if --sns-topic is not passed
    SNS_ALARM_ACTION_ARN = (
        SNS_OK_ACTION_ARN  # For simplicity, use same SNS topic for Alarm and OK actions
    )
    ## RDS Storage Space ##
    ALARM_RDS_STORAGE_NAME_PREFIX = "RDS_Storage_"
    ALARM_RDS_STORAGE_THRESHOLD_VALUE = 1024000  # Adjust this to meet your needs
    ALARM_RDS_STORAGE_DATAPOINTS_TO_ALARM = 1
    ALARM_RDS_STORAGE_EVALUATION_PERIODS = 1
    ALARM_RDS_STORAGE_METRIC_PERIOD = 300  # 5 minutes


def main():
    args = parse_args()

    # Initialize logging
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    elif args.verbose:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)

    if args.region:
        Config.DEFAULT_REGION = args.region
        Config.VPC_ENDPOINT_CW = f"https://monitoring.{args.region}.amazonaws.com"
        Config.VPC_ENDPOINT_RDS = (
            f"https://rds.{args.region}.amazonaws.com"  # NOT SURE THIS WORKS
        )
        Config.VPC_ENDPOINT_SNS = f"https://sns.{args.region}.amazonaws.com"

    rds, cloudwatch, sns = initialize_aws_clients(args.region)
    # if --tag is used, it requires two values passed (tag_name, tag_value)
    tag_name, tag_value = args.tag if args.tag else (None, None)
    targets = get_target_ids(client=rds, tag_name=tag_name, tag_value=tag_value)
    alarm_names = get_all_alarm_names(cloudwatch=cloudwatch)

    stats = {"created": 0, "deleted": 0, "volumes_processed": 0}
    without_alarm = []

    if args.sns_topic:
        Config.SNS_ALARM_ACTION_ARN = args.sns_topic
        Config.SNS_OK_ACTION_ARN = args.sns_topic

    if not args.alarm_type:
        alarm_type = "all"
    else:
        alarm_type = args.alarm_type

    # Check SNS existence here only for --all and --create
    if args.create:
        if not check_sns_exists(sns=sns, sns_topic_arn=Config.SNS_ALARM_ACTION_ARN):
            logging.error(
                f"Invalid SNS ARN provided: {Config.SNS_ALARM_ACTION_ARN}. Exiting."
            )
            sys.exit(1)  # Stop the script here

        if Config.INCLUDE_OK_ACTION and not check_sns_exists(
            sns=sns, sns_topic_arn=Config.SNS_OK_ACTION_ARN
        ):
            logging.error(
                f"Invalid SNS ARN provided: {Config.SNS_OK_ACTION_ARN}. Exiting."
            )
            sys.exit(1)  # Stop the script here

    if alarm_type == "all":
        alarm_types_list = ["freestoragespace"]  # add more here
    else:
        alarm_types_list = [alarm_type]

    if args.create:
        for alarm_type in alarm_types_list:
            logging.info(f"Creating {alarm_type} alarms...")
            print(f"Creating {alarm_type} alarms...")
            stats["created"] += create_alarms(
                targets=targets,
                alarm_names=alarm_names,
                cloudwatch=cloudwatch,
                client=rds,
                alarm_type=alarm_type,
            )

    if args.cleanup:
        for alarm_type in alarm_types_list:
            logging.info(f"Cleanup {alarm_type} alarms...")
            print(f"Cleaning up {alarm_type} alarms...")
            stats["deleted"] += cleanup_alarms(
                targets=targets,
                alarm_names=alarm_names,
                cloudwatch=cloudwatch,
                alarm_type=alarm_type,
            )

    print(
        f"RDS Processed: {len(targets)}, Alarms Created: {stats['created']}, Alarms Deleted: {stats['deleted']}"
    )
    if without_alarm:
        print(f"The following do not have an Alarm: {', '.join(without_alarm)}")


def generate_alarm_description(target, client):
    target_details = fetch_target_info(target=target, client=client, service="rds")

    if not target_details:
        return f"Alarm description not available for target: {target}"

    db_instance_identifier = target_details.get("db_instance_identifier", "N/A")
    availability_zone = target_details.get("availability_zone", "N/A")
    tags_dict = target_details.get("tags", {})
    db_instance_class = target_details.get("db_instance_class", "N/A")
    engine = target_details.get("engine", "N/A")

    alarm_description = f"Alarm for RDS instance {db_instance_identifier} ({db_instance_class}, {engine}) in {availability_zone}."

    tag_string = ", ".join([f"{k}: {v}" for k, v in tags_dict.items()])
    alarm_description += f"\nTags: {tag_string if tag_string else 'No Tags'}"

    return alarm_description


def get_target_ids(client, tag_name=None, tag_value=None):
    paginator = client.get_paginator("describe_db_instances")
    target_ids = []

    for page in paginator.paginate(MaxRecords=Config.PAGINATION_COUNT):
        for instance in page["DBInstances"]:
            if tag_name and tag_value:
                # Manually filter the instances based on tags
                # Tags are fetched separately for each instance
                response = client.list_tags_for_resource(
                    ResourceName=instance["DBInstanceArn"]
                )
                tags = {tag["Key"]: tag["Value"] for tag in response.get("TagList", [])}
                if tags.get(tag_name) == tag_value:
                    target_ids.append(instance["DBInstanceIdentifier"])
            else:
                target_ids.append(instance["DBInstanceIdentifier"])

    logging.debug(f"RDS Instance IDs:\n{target_ids}")
    return target_ids


def cleanup_alarms(targets, alarm_names, cloudwatch, alarm_type):
    deleted_count = 0

    if alarm_type == "impairedvol":
        search_prefix = Config.ALARM_IMPAIREDVOL_NAME_PREFIX
    if alarm_type == "readlatency":
        search_prefix = Config.ALARM_READLATENCY_NAME_PREFIX
    if alarm_type == "writelatency":
        search_prefix = Config.ALARM_WRITELATENCY_NAME_PREFIX
    if alarm_type == "freestoragespace":
        search_prefix = Config.ALARM_RDS_STORAGE_NAME_PREFIX

    for alarm_name in alarm_names:
        # Only consider alarms that start with the prefix defined in the Config class
        if alarm_name.startswith(search_prefix):
            # Extract target from the alarm name
            target_id = alarm_name[len(search_prefix) :]

            if target_id not in targets:
                logging.info(
                    f"Deleting {alarm_type} alarm {alarm_name} as volume {id} no longer exists"
                )
                try:
                    cloudwatch.delete_alarms(AlarmNames=[alarm_name])
                    deleted_count += 1
                except cloudwatch.exceptions.ClientError as e:
                    logging.error(
                        f"Failed to delete {alarm_type} alarm {alarm_name}: {e}"
                    )
                except Exception as e:
                    logging.error(f"Unknown error when deleting {alarm_name}: {e}")

            else:
                logging.info(
                    f"No change to {alarm_type} alarm {alarm_name} as {id} still exists"
                )

    return deleted_count


def generate_alarm_name(target, alarm_type):
    if alarm_type == "freestoragespace":
        return Config.ALARM_RDS_STORAGE_NAME_PREFIX + target


def create_alarms(targets, alarm_names, cloudwatch, client, alarm_type):
    created_count = 0
    for target in targets:
        alarm_name = generate_alarm_name(target=target, alarm_type=alarm_type)
        if alarm_name not in alarm_names:
            create_alarm(
                target=target,
                cloudwatch=cloudwatch,
                client=client,
                alarm_name=alarm_name,
                alarm_type=alarm_type,
            )
            created_count += 1
        else:
            logging.info(f"CW Alarm {alarm_name} already exists.")

    return created_count


def create_alarm(target, cloudwatch, client, alarm_name, alarm_type):
    alarm_description = generate_alarm_description(target=target, client=client)

    alarm_details = {
        "AlarmName": alarm_name,
        "AlarmActions": [Config.SNS_ALARM_ACTION_ARN],
        "ComparisonOperator": "GreaterThanOrEqualToThreshold",
        "TreatMissingData": "missing",
        "AlarmDescription": alarm_description,
    }

    if alarm_type == "freestoragespace":
        alarm_details.update(get_rds_freestoragespace_params(target))

    if Config.INCLUDE_OK_ACTION:
        alarm_details.update(
            {
                "OKActions": [Config.SNS_OK_ACTION_ARN],
            }
        )

    logging.debug(f"CloudWatch JSON:\n{alarm_details}\n")
    logging.info(f"Creating {alarm_type} alarm {alarm_name} for volume {target}.")

    # Create the new alarm
    try:
        if Config.INCLUDE_OK_ACTION:
            cloudwatch.put_metric_alarm(
                AlarmName=alarm_details["AlarmName"],
                OKActions=alarm_details["OKActions"],
                AlarmActions=alarm_details["AlarmActions"],
                AlarmDescription=alarm_details["AlarmDescription"],
                EvaluationPeriods=alarm_details["EvaluationPeriods"],
                DatapointsToAlarm=alarm_details["DatapointsToAlarm"],
                Threshold=alarm_details["Threshold"],
                ComparisonOperator=alarm_details["ComparisonOperator"],
                TreatMissingData=alarm_details["TreatMissingData"],
                Metrics=alarm_details["Metrics"],
            )
        else:
            cloudwatch.put_metric_alarm(
                AlarmName=alarm_details["AlarmName"],
                AlarmActions=alarm_details["AlarmActions"],
                AlarmDescription=alarm_details["AlarmDescription"],
                EvaluationPeriods=alarm_details["EvaluationPeriods"],
                DatapointsToAlarm=alarm_details["DatapointsToAlarm"],
                Threshold=alarm_details["Threshold"],
                ComparisonOperator=alarm_details["ComparisonOperator"],
                TreatMissingData=alarm_details["TreatMissingData"],
                Metrics=alarm_details["Metrics"],
            )

        logging.info(
            f"New {alarm_type} alarm '{alarm_details['AlarmName']}' created for volume {target}"
        )
    except cloudwatch.exceptions.ClientError as error:
        logging.error(f"Error creating alarm {alarm_name} for volume {target}: {error}")
    except Exception as e:
        logging.error(
            f"Unexpected error creating alarm {alarm_name} for volume {target}: {e}"
        )


def get_rds_freestoragespace_params(target):
    return {
        "EvaluationPeriods": Config.ALARM_RDS_STORAGE_EVALUATION_PERIODS,
        "DatapointsToAlarm": Config.ALARM_RDS_STORAGE_DATAPOINTS_TO_ALARM,
        "Threshold": Config.ALARM_RDS_STORAGE_THRESHOLD_VALUE,
        "Metrics": [
            {
                "Id": "m1",
                "MetricStat": {
                    "Metric": {
                        "Namespace": "AWS/RDS",
                        "MetricName": "FreeStorageSpace",
                        "Dimensions": [
                            {
                                "Name": "DBInstanceIdentifier",
                                "Value": target,
                            }
                        ],
                    },
                    "Period": Config.ALARM_RDS_STORAGE_METRIC_PERIOD,
                    "Stat": "Average",
                },
                "ReturnData": True,  # Set to True
            },
        ],
    }


def fetch_target_info(target, client, service="rds"):
    # TODO: logic around different services. For now, the default is rds
    if not service or service.lower() != "rds":
        return None
    try:
        # Fetch all RDS information about the target ID
        response = client.describe_db_instances(DBInstanceIdentifier=target)
        instance_info = response["DBInstances"][0]

        # Parse information into tags, availability zone(s), and other relevant information
        tags_response = client.list_tags_for_resource(
            ResourceName=instance_info["DBInstanceArn"]
        )
        tags = {tag["Key"]: tag["Value"] for tag in tags_response.get("TagList", [])}

        target_details = {
            "db_instance_identifier": instance_info["DBInstanceIdentifier"],
            "db_instance_class": instance_info["DBInstanceClass"],
            "engine": instance_info["Engine"],
            "availability_zone": instance_info["AvailabilityZone"],
            "tags": tags
            # Add other relevant details you need
        }

        return target_details

    except Exception as e:
        logging.error(
            f"An error occurred while fetching information for target {target}: {e}"
        )
        return None


def get_all_alarm_names(cloudwatch):
    paginator = cloudwatch.get_paginator("describe_alarms")
    alarm_names = []
    for page in paginator.paginate(MaxRecords=Config.PAGINATION_COUNT):
        for alarm in page["MetricAlarms"]:
            alarm_names.append(alarm["AlarmName"])
    logging.debug(f"Alarm Names:\n{alarm_names}")
    return alarm_names


def check_sns_exists(sns, sns_topic_arn):
    logging.info(f"Checking if SNS topic {sns_topic_arn} exists...")
    try:
        response = sns.get_topic_attributes(TopicArn=sns_topic_arn)
        return True
    except sns.exceptions.AuthorizationErrorException:
        logging.error(
            f"The script does not have the necessary permissions to check if the SNS topic at ARN {sns_topic_arn} exists."
        )
        sys.exit(1)  # Stop the script here
    except sns.exceptions.NotFoundException:
        try:
            response = sns.list_topics()
            logging.error(
                f"The provided SNS ARN {sns_topic_arn} does not exist. Here are the existing topics: "
            )
            for topic in response["Topics"]:
                logging.error(topic["TopicArn"])
            return False
        except sns.exceptions.AuthorizationErrorException:
            logging.error(
                "The script does not have the necessary permissions to list SNS topics."
            )
            sys.exit(1)  # Stop the script here
        except Exception as e:
            logging.error("Failed to list SNS topics: " + str(e))
            sys.exit(1)  # Stop the script here


def initialize_aws_clients(region):
    try:
        rds = boto3.client(
            "rds", region_name=region, endpoint_url=Config.VPC_ENDPOINT_RDS
        )
        cloudwatch = boto3.client(
            "cloudwatch", region_name=region, endpoint_url=Config.VPC_ENDPOINT_CW
        )
        sns = boto3.client(
            "sns", region_name=region, endpoint_url=Config.VPC_ENDPOINT_SNS
        )
        logging.info(f"Initilized AWS Client in region {region}")
    except Exception as e:
        logging.error(f"Failed to initialize AWS clients: {e}")
        sys.exit(1)  # Stop the script here

    return rds, cloudwatch, sns


def parse_args():
    parser = argparse.ArgumentParser(
        description="Manage CloudWatch Alarms for RDS Instances."
    )
    parser.add_argument("--rds-id", help="Specific volume id to operate on.")
    parser.add_argument(
        "--sns-topic",
        help=f"SNS Topic ARN to notify on alarm or ok. Default is {Config.SNS_ALARM_ACTION_ARN}",
    )
    parser.add_argument(
        "--alarm-type",
        type=lambda x: x.lower(),
        choices=["all", "freestoragespace"],
        help=f"Which alarm type to process. Options are All or freestoragespace. Default is All.",
    )
    parser.add_argument(
        "--create", action="store_true", help="Create CloudWatch Alarms."
    )
    parser.add_argument(
        "--tag",
        nargs=2,
        metavar=("TagName", "TagValue"),
        help="TagName and TagValue to filter RDS instances.",
    )
    parser.add_argument(
        "--cleanup", action="store_true", help="Cleanup CloudWatch Alarms."
    )
    parser.add_argument(
        "--region",
        default=Config.DEFAULT_REGION,
        help=f"AWS Region (defaults to {Config.DEFAULT_REGION}).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Perform cleanup, create, and update operations.",
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose logging.")
    parser.add_argument("--debug", action="store_true", help="Debug logging.")
    return parser.parse_args()


if __name__ == "__main__":
    main()
