#!/usr/bin/env python3
"""Seed test data into local DynamoDB."""

import os
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()


def get_table_names() -> list[str]:
    """Get table names from environment variables."""
    return [
        os.environ["DYNAMODB_TABLE_NAME"],
        os.environ["DYNAMODB_USERS_TABLE"],
        os.environ["DYNAMODB_PAIRS_TABLE"],
        os.environ["DYNAMODB_LOGS_TABLE"],
    ]


def create_table(dynamodb_resource: boto3.resource, table_name: str) -> None:
    """Create a DynamoDB table if it doesn't exist."""
    try:
        table = dynamodb_resource.create_table(
            TableName=table_name,
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
        print(f"Created table: {table_name}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"Table already exists: {table_name}")
        else:
            raise


def seed_calculations(dynamodb_resource: boto3.resource) -> None:
    """Seed test calculation items."""
    table = dynamodb_resource.Table(os.environ["DYNAMODB_TABLE_NAME"])

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
        print(f"Seeded calculation: {item['pk']}/{item['sk']}")


def seed_users(dynamodb_resource: boto3.resource) -> None:
    """Seed a test user."""
    table = dynamodb_resource.Table(os.environ["DYNAMODB_USERS_TABLE"])

    user = {
        "pk": "test@example.com",
        "sk": "PROFILE",
        "email": "test@example.com",
        "name": "Test User",
        "password_hash": os.environ["TEST_USER_PASSWORD_HASH"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    table.put_item(Item=user)
    print(f"Seeded user: {user['email']}")


def seed_pairs(dynamodb_resource: boto3.resource) -> None:
    """Seed two test pairs for the test user."""
    table = dynamodb_resource.Table(os.environ["DYNAMODB_PAIRS_TABLE"])

    pairs = [
        {
            "pk": "test@example.com",
            "sk": f"PAIR#{uuid.uuid4()}",
            "pair_id": str(uuid.uuid4()),
            "user_email": "test@example.com",
            "val1": 42,
            "val2": 58,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "pk": "test@example.com",
            "sk": f"PAIR#{uuid.uuid4()}",
            "pair_id": str(uuid.uuid4()),
            "user_email": "test@example.com",
            "val1": 100,
            "val2": 200,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    ]

    for pair in pairs:
        table.put_item(Item=pair)
        print(f"Seeded pair: {pair['pair_id']} (val1={pair['val1']}, val2={pair['val2']})")


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

    # Create all tables
    for table_name in get_table_names():
        create_table(dynamodb, table_name)

    # Seed data
    seed_calculations(dynamodb)
    seed_users(dynamodb)
    seed_pairs(dynamodb)

    print("Done!")


if __name__ == "__main__":
    main()
