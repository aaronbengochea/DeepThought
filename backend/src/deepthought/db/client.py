"""Async DynamoDB client wrapper."""

from typing import Any

import aioboto3
from botocore.exceptions import ClientError

from deepthought.core.exceptions import DatabaseError


class DynamoDBClient:
    """Async wrapper for DynamoDB operations."""

    def __init__(
        self,
        table_name: str,
        region: str = "us-east-1",
        endpoint_url: str | None = None,
    ) -> None:
        self.table_name = table_name
        self.region = region
        self.endpoint_url = endpoint_url
        self._session = aioboto3.Session()

    async def get_item(self, pk: str, sk: str | None = None) -> dict[str, Any] | None:
        """
        Get an item from DynamoDB by primary key.

        Args:
            pk: Partition key value
            sk: Sort key value (optional for pk-only tables)

        Returns:
            The item if found, None otherwise.

        Raises:
            DatabaseError: If the operation fails.
        """
        try:
            async with self._session.resource(
                "dynamodb",
                region_name=self.region,
                endpoint_url=self.endpoint_url,
            ) as dynamodb:
                table = await dynamodb.Table(self.table_name)
                key: dict[str, str] = {"pk": pk}
                if sk is not None:
                    key["sk"] = sk
                response = await table.get_item(Key=key)
                return response.get("Item")
        except ClientError as e:
            raise DatabaseError(f"Failed to get item: {e}") from e

    async def put_item(self, item: dict[str, Any]) -> None:
        """
        Put an item into DynamoDB.

        Args:
            item: The item to put (must include pk, and sk if the table uses a composite key).

        Raises:
            DatabaseError: If the operation fails.
        """
        try:
            async with self._session.resource(
                "dynamodb",
                region_name=self.region,
                endpoint_url=self.endpoint_url,
            ) as dynamodb:
                table = await dynamodb.Table(self.table_name)
                await table.put_item(Item=item)
        except ClientError as e:
            raise DatabaseError(f"Failed to put item: {e}") from e

    async def query(
        self,
        pk: str,
        sk_prefix: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Query items by partition key with optional sort key prefix.

        Args:
            pk: Partition key value
            sk_prefix: Optional sort key prefix for begins_with condition
            limit: Maximum number of items to return

        Returns:
            List of matching items.

        Raises:
            DatabaseError: If the operation fails.
        """
        try:
            async with self._session.resource(
                "dynamodb",
                region_name=self.region,
                endpoint_url=self.endpoint_url,
            ) as dynamodb:
                table = await dynamodb.Table(self.table_name)

                key_condition = "pk = :pk"
                expression_values: dict[str, Any] = {":pk": pk}

                if sk_prefix:
                    key_condition += " AND begins_with(sk, :sk_prefix)"
                    expression_values[":sk_prefix"] = sk_prefix

                kwargs: dict[str, Any] = {
                    "KeyConditionExpression": key_condition,
                    "ExpressionAttributeValues": expression_values,
                }
                if limit:
                    kwargs["Limit"] = limit

                response = await table.query(**kwargs)
                return response.get("Items", [])
        except ClientError as e:
            raise DatabaseError(f"Failed to query items: {e}") from e
