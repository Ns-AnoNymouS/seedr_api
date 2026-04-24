"""Pydantic v2 models for Seedr API responses — user/account domain."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class UserInfo(BaseModel):
    """Seedr user profile information."""

    user_id: str | None = None
    email: str | None = None
    display_name: str | None = None
    created_at: str | None = None


class StorageQuota(BaseModel):
    """Storage quota breakdown."""

    total: int | None = None
    used: int | None = None


class BandwidthQuota(BaseModel):
    """Bandwidth quota breakdown."""

    limit: int | None = None
    used: int | None = None
    reset_date: str | None = None


class Quota(BaseModel):
    """Storage and bandwidth quota for the authenticated user."""

    storage: StorageQuota = Field(default_factory=StorageQuota)
    bandwidth: BandwidthQuota = Field(default_factory=BandwidthQuota)
    is_premium: bool | None = None


class UserSettings(BaseModel):
    """Application-specific settings for the authenticated user."""

    settings: dict[str, Any] = Field(default_factory=dict)
