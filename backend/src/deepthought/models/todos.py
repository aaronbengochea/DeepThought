"""Pydantic models for todo lists and items."""

from datetime import datetime

from pydantic import BaseModel, Field


class TodoList(BaseModel):
    """Full todo list as stored in DynamoDB.

    In DynamoDB, pk is the user's email and sk is LIST#{list_id}.
    """

    list_id: str = Field(..., description="Unique list identifier")
    title: str = Field(..., description="List title")
    created_at: datetime = Field(..., description="List creation timestamp")
    updated_at: datetime = Field(..., description="List last updated timestamp")


class TodoListCreate(BaseModel):
    """Request model for creating a todo list."""

    title: str = Field(..., description="List title")


class TodoListResponse(BaseModel):
    """Response model for todo list data."""

    list_id: str = Field(..., description="Unique list identifier")
    title: str = Field(..., description="List title")
    item_count: int = Field(0, description="Total number of items in the list")
    completed_count: int = Field(0, description="Number of completed items in the list")
    created_at: datetime = Field(..., description="List creation timestamp")
    updated_at: datetime = Field(..., description="List last updated timestamp")


class TodoItem(BaseModel):
    """Full todo item as stored in DynamoDB.

    In DynamoDB, pk is the user's email and sk is ITEM#{list_id}#{item_id}.
    """

    item_id: str = Field(..., description="Unique item identifier")
    list_id: str = Field(..., description="Parent list identifier")
    text: str = Field(..., description="Item text")
    completed: bool = Field(False, description="Whether the item is completed")
    completed_at: datetime | None = Field(None, description="Completion timestamp or null")
    sort_order: int = Field(0, description="Sort position within the list")
    created_at: datetime = Field(..., description="Item creation timestamp")
    updated_at: datetime = Field(..., description="Item last updated timestamp")


class TodoItemCreate(BaseModel):
    """Request model for creating a todo item."""

    text: str = Field(..., description="Item text")


class TodoItemUpdate(BaseModel):
    """Request model for updating a todo item. All fields optional."""

    text: str | None = Field(None, description="Item text")
    completed: bool | None = Field(None, description="Whether the item is completed")


class TodoItemResponse(BaseModel):
    """Response model for todo item data."""

    item_id: str = Field(..., description="Unique item identifier")
    list_id: str = Field(..., description="Parent list identifier")
    text: str = Field(..., description="Item text")
    completed: bool = Field(False, description="Whether the item is completed")
    completed_at: datetime | None = Field(None, description="Completion timestamp or null")
    sort_order: int = Field(0, description="Sort position within the list")
    created_at: datetime = Field(..., description="Item creation timestamp")
    updated_at: datetime = Field(..., description="Item last updated timestamp")
