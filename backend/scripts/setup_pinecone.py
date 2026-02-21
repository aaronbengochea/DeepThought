#!/usr/bin/env python3
"""Create the Pinecone index for hybrid RAG if it doesn't exist."""

import os

from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

load_dotenv()


def main() -> None:
    """Main entry point."""
    api_key = os.environ["PINECONE_API_KEY"]
    index_name = os.environ["PINECONE_INDEX_NAME"]
    cloud = os.environ["PINECONE_CLOUD"]
    region = os.environ["PINECONE_REGION"]
    dimensions = int(os.environ["PINECONE_DIMENSIONS"])
    metric = os.environ["PINECONE_METRIC"]

    pc = Pinecone(api_key=api_key)

    existing = [i.name for i in pc.list_indexes()]
    if index_name in existing:
        print(f"Index already exists: {index_name}")
        return

    pc.create_index(
        name=index_name,
        dimension=dimensions,
        metric=metric,
        spec=ServerlessSpec(cloud=cloud, region=region),
    )
    print(f"Created index: {index_name} ({dimensions}d, {metric}, {cloud}/{region})")


if __name__ == "__main__":
    main()
