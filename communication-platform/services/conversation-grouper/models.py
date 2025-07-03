from typing import List
from uuid import UUID
from pydantic import BaseModel, Field
from ...shared.models import Conversation, Message

class GroupingRequest(BaseModel):
    message_ids: List[UUID] = Field(..., description="List of message UUIDs to group.")
    force_group: bool = Field(default=False, description="Force grouping even if criteria are not met.")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "message_ids": [
                        "123e4567-e89b-12d3-a456-426614174000",
                        "123e4567-e89b-12d3-a456-426614174001"
                    ],
                    "force_group": False
                }
            ]
        }

class GroupingResponse(BaseModel):
    conversation_id: UUID = Field(..., description="ID of the grouped conversation.")
    action: str = Field(..., description="Action taken: created, updated, or merged.")
    message_count: int = Field(..., description="Number of messages in the conversation.")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "conversation_id": "123e4567-e89b-12d3-a456-426614174999",
                    "action": "created",
                    "message_count": 5
                }
            ]
        }

class ConversationSummary(BaseModel):
    conversation_id: UUID = Field(..., description="ID of the conversation.")
    summary: str = Field(..., description="Summary of the conversation.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for the summary.")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "conversation_id": "123e4567-e89b-12d3-a456-426614174999",
                    "summary": "Customer inquired about pricing and requested a quote.",
                    "confidence": 0.92
                }
            ]
        } 