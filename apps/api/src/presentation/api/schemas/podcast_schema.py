from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreatePodcastRequest(BaseModel):
    """Request schema for creating a podcast"""

    book_id: str = Field(..., description="ID of the book to create podcast for")
    title: str | None = Field(None, description="Custom title for the podcast")


class PodcastScriptTurn(BaseModel):
    """Schema for a single script turn"""

    speaker: str = Field(..., description="Speaker identifier (HOST or GUEST)")
    text: str = Field(..., description="What the speaker says")


class PodcastResponse(BaseModel):
    """Response schema for podcast details"""

    id: str = Field(..., description="Podcast ID")
    book_id: str = Field(..., description="Book ID")
    user_id: str = Field(..., description="User ID")
    title: str = Field(..., description="Podcast title")
    status: str = Field(..., description="Generation status")
    audio_url: str | None = Field(None, description="URL to the generated audio")
    error_message: str | None = Field(None, description="Error message if generation failed")
    script: list[PodcastScriptTurn] | None = Field(None, description="Podcast script")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class PodcastStatusResponse(BaseModel):
    """Response schema for podcast status"""

    id: str = Field(..., description="Podcast ID")
    status: str = Field(..., description="Generation status")
    title: str = Field(..., description="Podcast title")
    audio_url: str | None = Field(None, description="URL to the generated audio if completed")
    error_message: str | None = Field(None, description="Error message if failed")
    has_script: bool = Field(..., description="Whether script has been generated")
    script_turn_count: int | None = Field(None, description="Number of script turns")
    script_character_count: int | None = Field(None, description="Total character count in script")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class CreatePodcastResponse(BaseModel):
    """Response schema for podcast creation"""

    id: str = Field(..., description="Created podcast ID")
    status: str = Field(..., description="Initial status")
    message: str = Field(..., description="Success message")


class PodcastListResponse(BaseModel):
    """Response schema for podcast list"""

    podcasts: list[PodcastResponse] = Field(..., description="List of podcasts")
    total: int = Field(..., description="Total number of podcasts")
