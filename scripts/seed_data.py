#!/usr/bin/env python3
"""Seed test data into local DynamoDB."""

import asyncio
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError


def create_table(dynamodb_resource: boto3.resource) -> None:
    """Create the DynamoDB table if it doesn't exist."""
    try:
        table = dynamodb_resource.create_table(
            TableName="deepthought-calculations",
            KeySchema=[
                {"AttributeName": "pk", "KeyType": "HASH"},
                {"AttributeName": "sk", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "pk", "AttributeType": "S"},
                {"AttributeName": "sk", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()
        print("Created table: deepthought-calculations")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print("Table already exists: deepthought-calculations")
        else:
            raise


def seed_data(dynamodb_resource: boto3.resource) -> None:
    """Seed test calculation items."""
    table = dynamodb_resource.Table("deepthought-calculations")

    items = [
        {
            "pk": "CALC#test",
            "sk": "ITEM#001",
            "val1": 42,
            "val2": 58,
            "description": "Test calculation 1",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "pk": "CALC#test",
            "sk": "ITEM#002",
            "val1": 100,
            "val2": 200,
            "description": "Test calculation 2",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "pk": "CALC#user123",
            "sk": "ITEM#calc001",
            "val1": 15,
            "val2": 25,
            "description": "User calculation",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    ]

    for item in items:
        table.put_item(Item=item)
        print(f"Seeded: {item['pk']}/{item['sk']}")


def main() -> None:
    """Main entry point."""
    # Connect to local DynamoDB
    dynamodb = boto3.resource(
        "dynamodb",
        endpoint_url="http://localhost:8000",
        region_name="us-east-1",
        aws_access_key_id="dummy",
        aws_secret_access_key="dummy",
    )

    print("Connecting to local DynamoDB at http://localhost:8000")
    create_table(dynamodb)
    seed_data(dynamodb)
    print("Done!")


if __name__ == "__main__":
    main()
