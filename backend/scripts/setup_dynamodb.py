#!/usr/bin/env python3
"""Create DynamoDB tables for local development."""

import os

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()



def create_table(
    dynamodb_resource: boto3.resource,
    table_name: str,
    has_sort_key: bool = True,
) -> None:
    """Create a DynamoDB table if it doesn't exist.

    Args:
        dynamodb_resource: The boto3 DynamoDB resource.
        table_name: The name of the table to create.
        has_sort_key: Whether the table uses a composite key (pk + sk).
            If False, the table uses pk only.
    """
    key_schema = [{"AttributeName": "pk", "KeyType": "HASH"}]
    attribute_definitions = [{"AttributeName": "pk", "AttributeType": "S"}]

    if has_sort_key:
        key_schema.append({"AttributeName": "sk", "KeyType": "RANGE"})
        attribute_definitions.append({"AttributeName": "sk", "AttributeType": "S"})

    try:
        table = dynamodb_resource.create_table(
            TableName=table_name,
            KeySchema=key_schema,
            AttributeDefinitions=attribute_definitions,
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()
        print(f"Created table: {table_name}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"Table already exists: {table_name}")
        else:
            raise


def create_table_with_gsi(
    dynamodb_resource: boto3.resource,
    table_name: str,
    gsi_name: str,
    gsi_pk_attr: str,
    gsi_sk_attr: str,
    gsi_sk_type: str = "S",
) -> None:
    """Create a DynamoDB table with a composite key (pk + sk) and a GSI.

    Args:
        dynamodb_resource: The boto3 DynamoDB resource.
        table_name: The name of the table to create.
        gsi_name: Name of the Global Secondary Index.
        gsi_pk_attr: Partition key attribute name for the GSI.
        gsi_sk_attr: Sort key attribute name for the GSI.
        gsi_sk_type: DynamoDB type for the GSI sort key ("S", "N", or "B").
    """
    attribute_definitions = [
        {"AttributeName": "pk", "AttributeType": "S"},
        {"AttributeName": "sk", "AttributeType": "S"},
        {"AttributeName": gsi_sk_attr, "AttributeType": gsi_sk_type},
    ]

    # Avoid duplicate attribute definitions if the GSI pk reuses an existing attr
    gsi_pk_names = {ad["AttributeName"] for ad in attribute_definitions}
    if gsi_pk_attr not in gsi_pk_names:
        attribute_definitions.append({"AttributeName": gsi_pk_attr, "AttributeType": "S"})

    try:
        table = dynamodb_resource.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "pk", "KeyType": "HASH"},
                {"AttributeName": "sk", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=attribute_definitions,
            GlobalSecondaryIndexes=[
                {
                    "IndexName": gsi_name,
                    "KeySchema": [
                        {"AttributeName": gsi_pk_attr, "KeyType": "HASH"},
                        {"AttributeName": gsi_sk_attr, "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()
        print(f"Created table: {table_name} (with GSI: {gsi_name})")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"Table already exists: {table_name}")
        else:
            raise


def main() -> None:
    """Main entry point."""
    endpoint_url = os.environ["DYNAMODB_ENDPOINT_URL"]
    region = os.environ["AWS_REGION"]
    access_key = os.environ["AWS_ACCESS_KEY_ID"]
    secret_key = os.environ["AWS_SECRET_ACCESS_KEY"]

    dynamodb = boto3.resource(
        "dynamodb",
        endpoint_url=endpoint_url,
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )

    print(f"Connecting to local DynamoDB at {endpoint_url}")

    # Create tables with composite keys (pk + sk)
    composite_key_tables = [
        os.environ["DYNAMODB_PAIRS_TABLE"],
        os.environ["DYNAMODB_LOGS_TABLE"],
        os.environ["DYNAMODB_CALENDAR_TABLE"],
        os.environ["DYNAMODB_CONVERSATIONS_TABLE"],
        os.environ["DYNAMODB_MESSAGES_TABLE"],
    ]
    for table_name in composite_key_tables:
        create_table(dynamodb, table_name, has_sort_key=True)

    # Create users table with pk only (email is the partition key)
    create_table(dynamodb, os.environ["DYNAMODB_USERS_TABLE"], has_sort_key=False)

    # Create todos table with GSI for completed_at stats queries
    create_table_with_gsi(
        dynamodb,
        os.environ["DYNAMODB_TODOS_TABLE"],
        gsi_name="pk_completed_at_index",
        gsi_pk_attr="pk",
        gsi_sk_attr="completed_at",
    )

    print("Done!")


if __name__ == "__main__":
    main()
