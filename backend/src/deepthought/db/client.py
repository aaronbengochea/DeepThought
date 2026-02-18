"""Async DynamoDB client wrapper."""

from typing import Any

import aioboto3
from botocore.exceptions import ClientError

from deepthought.core.exceptions import DatabaseError
from deepthought.models.database import ReturnValues


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

    async def update_item(
        self,
        pk: str,
        sk: str,
        updates: dict[str, Any],
        return_values: ReturnValues = ReturnValues.ALL_NEW,
    ) -> dict[str, Any]:
        """
        Partial attribute update via UpdateExpression with SET clauses.

        Args:
            pk: Partition key value.
            sk: Sort key value.
            updates: Dictionary of attribute names to new values.
            return_values: What to return after the update (default ALL_NEW).

        Returns:
            The returned item attributes (depends on return_values).

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

                set_parts: list[str] = []
                expression_names: dict[str, str] = {}
                expression_values: dict[str, Any] = {}

                for i, (attr, value) in enumerate(updates.items()):
                    placeholder_name = f"#attr{i}"
                    placeholder_value = f":val{i}"
                    set_parts.append(f"{placeholder_name} = {placeholder_value}")
                    expression_names[placeholder_name] = attr
                    expression_values[placeholder_value] = value

                response = await table.update_item(
                    Key={"pk": pk, "sk": sk},
                    UpdateExpression="SET " + ", ".join(set_parts),
                    ExpressionAttributeNames=expression_names,
                    ExpressionAttributeValues=expression_values,
                    ReturnValues=return_values,
                )
                return response.get("Attributes", {})
        except ClientError as e:
            raise DatabaseError(f"Failed to update item: {e}") from e

    async def delete_item(self, pk: str, sk: str) -> None:
        """
        Delete an item by composite key.

        Args:
            pk: Partition key value.
            sk: Sort key value.

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
                await table.delete_item(Key={"pk": pk, "sk": sk})
        except ClientError as e:
            raise DatabaseError(f"Failed to delete item: {e}") from e

    async def batch_delete(self, items: list[tuple[str, str]]) -> None:
        """
        Batch delete items by primary key (pk + sk).

        Handles DynamoDB's 25-item batch limit internally by chunking.
        Useful for deleting a todo list and all its items in one call.

        Args:
            items: List of (pk, sk) tuples to delete.

        Raises:
            DatabaseError: If the operation fails.
        """
        if not items:
            return

        try:
            async with self._session.resource(
                "dynamodb",
                region_name=self.region,
                endpoint_url=self.endpoint_url,
            ) as dynamodb:
                table = await dynamodb.Table(self.table_name)

                # DynamoDB BatchWriteItem supports max 25 operations per call
                for i in range(0, len(items), 25):
                    chunk = items[i : i + 25]
                    async with table.batch_writer() as batch:
                        for pk, sk in chunk:
                            await batch.delete_item(Key={"pk": pk, "sk": sk})
        except ClientError as e:
            raise DatabaseError(f"Failed to batch delete items: {e}") from e
