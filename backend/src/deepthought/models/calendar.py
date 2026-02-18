"""Pydantic models for calendar events."""

from datetime import datetime

from pydantic import BaseModel, Field


class CalendarEvent(BaseModel):
    """Full calendar event as stored in DynamoDB.

    In DynamoDB, pk is the user's email and sk is {start_time}#{event_id}.
    """

    event_id: str = Field(..., description="Unique event identifier")
    title: str = Field(..., description="Event title")
    description: str | None = Field(None, description="Event description")
    start_time: datetime = Field(..., description="Event start time (ISO 8601 with offset)")
    end_time: datetime = Field(..., description="Event end time (ISO 8601 with offset)")
    rrule: str | None = Field(None, description="RFC 5545 recurrence rule or null for one-off events")
    created_at: datetime = Field(..., description="Event creation timestamp")
    updated_at: datetime = Field(..., description="Event last updated timestamp")


class CalendarEventCreate(BaseModel):
    """Request model for creating a calendar event."""

    title: str = Field(..., description="Event title")
    description: str | None = Field(None, description="Event description")
    start_time: datetime = Field(..., description="Event start time (ISO 8601 with offset)")
    end_time: datetime = Field(..., description="Event end time (ISO 8601 with offset)")
    rrule: str | None = Field(None, description="RFC 5545 recurrence rule or null for one-off events")


class CalendarEventUpdate(BaseModel):
    """Request model for updating a calendar event. All fields optional."""

    title: str | None = Field(None, description="Event title")
    description: str | None = Field(None, description="Event description")
    start_time: datetime | None = Field(None, description="Event start time (ISO 8601 with offset)")
    end_time: datetime | None = Field(None, description="Event end time (ISO 8601 with offset)")
    rrule: str | None = Field(None, description="RFC 5545 recurrence rule or null for one-off events")


class CalendarEventResponse(BaseModel):
    """Response model for calendar event data."""

    event_id: str = Field(..., description="Unique event identifier")
    title: str = Field(..., description="Event title")
    description: str | None = Field(None, description="Event description")
    start_time: datetime = Field(..., description="Event start time (ISO 8601 with offset)")
    end_time: datetime = Field(..., description="Event end time (ISO 8601 with offset)")
    rrule: str | None = Field(None, description="RFC 5545 recurrence rule or null for one-off events")
    created_at: datetime = Field(..., description="Event creation timestamp")
    updated_at: datetime = Field(..., description="Event last updated timestamp")
