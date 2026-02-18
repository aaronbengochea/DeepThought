"""Pydantic models for chat conversations and messages."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class Conversation(BaseModel):
    """Full conversation as stored in DynamoDB.

    In DynamoDB, pk is the user's email and sk is {created_at}#{conversation_id}.
    """

    conversation_id: str = Field(..., description="Unique conversation identifier")
    context_type: Literal["pairs", "calendar", "todos", "general"] = Field(
        ..., description="Domain context for this conversation"
    )
    title: str = Field(..., description="Conversation title")
    created_at: datetime = Field(..., description="Conversation creation timestamp")
    updated_at: datetime = Field(..., description="Conversation last updated timestamp")


class ConversationCreate(BaseModel):
    """Request model for creating a conversation."""

    context_type: Literal["pairs", "calendar", "todos", "general"] = Field(
        "general", description="Domain context for this conversation"
    )
    title: str | None = Field(None, description="Conversation title")


class ConversationResponse(BaseModel):
    """Response model for conversation data."""

    conversation_id: str = Field(..., description="Unique conversation identifier")
    context_type: Literal["pairs", "calendar", "todos", "general"] = Field(
        ..., description="Domain context for this conversation"
    )
    title: str = Field(..., description="Conversation title")
    created_at: datetime = Field(..., description="Conversation creation timestamp")
    updated_at: datetime = Field(..., description="Conversation last updated timestamp")


class ChatMessage(BaseModel):
    """Full chat message as stored in DynamoDB.

    In DynamoDB, pk is the conversation_id and sk is {created_at}#{message_id}.
    """

    message_id: str = Field(..., description="Unique message identifier")
    conversation_id: str = Field(..., description="Parent conversation identifier")
    role: Literal["user", "assistant"] = Field(..., description="Message sender role")
    content: str = Field(..., description="Message text content")
    tool_calls: list[dict[str, Any]] | None = Field(
        None, description="Tool calls made by the assistant or null"
    )
    created_at: datetime = Field(..., description="Message creation timestamp")


class ChatMessageCreate(BaseModel):
    """Request model for creating a chat message."""

    content: str = Field(..., description="Message text content")


class ChatMessageResponse(BaseModel):
    """Response model for chat message data."""

    message_id: str = Field(..., description="Unique message identifier")
    conversation_id: str = Field(..., description="Parent conversation identifier")
    role: Literal["user", "assistant"] = Field(..., description="Message sender role")
    content: str = Field(..., description="Message text content")
    tool_calls: list[dict[str, Any]] | None = Field(
        None, description="Tool calls made by the assistant or null"
    )
    created_at: datetime = Field(..., description="Message creation timestamp")


class ChatRequest(BaseModel):
    """Request model for sending a chat message to the agent."""

    message: str = Field(..., description="User message to send")
    conversation_id: str | None = Field(
        None, description="Existing conversation ID or null to create a new one"
    )
    context_type: Literal["pairs", "calendar", "todos", "general"] = Field(
        "general", description="Domain context for this conversation"
    )


class ChatResponse(BaseModel):
    """Response model for a chat agent reply."""

    conversation_id: str = Field(..., description="Conversation identifier")
    message: str = Field(..., description="Assistant response text")
    tool_calls: list[dict[str, Any]] | None = Field(
        None, description="Tool calls made during response generation"
    )
