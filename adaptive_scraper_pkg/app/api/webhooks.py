# app/api/webhooks.py

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request, status
from pydantic import BaseModel, Field, HttpUrl

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "change-me")
MAX_BODY_BYTES = int(os.getenv("WEBHOOK_MAX_BODY_BYTES", "1048576"))  # 1 MB


# -------------------------------------------------------------------
# Request / Response Schemas
# -------------------------------------------------------------------

class AnalyzeWebhookPayload(BaseModel):
    source_url: HttpUrl
    trigger: Literal["manual", "scheduled", "watchlist", "change_detected"] = "manual"
    priority: Literal["low", "normal", "high"] = "normal"
    source_type: Literal["web_page", "pricing_page", "blog", "news", "investor_page", "custom"] = "web_page"
    tenant_id: str | None = None
    watchlist_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReportWebhookPayload(BaseModel):
    job_id: str
    destination: Literal["slack", "email", "crm", "notion", "custom"]
    target: str
    format: Literal["json", "markdown", "summary"] = "json"
    metadata: dict[str, Any] = Field(default_factory=dict)


class AlertWebhookPayload(BaseModel):
    event_type: Literal[
        "pricing_changed",
        "product_changed",
        "funding_detected",
        "competitor_signal",
        "risk_detected",
        "analysis_failed",
    ]
    source_url: HttpUrl
    severity: Literal["info", 
                      "warning", 
                      "critical"] = "info"
    title: str
    summary: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class WebhookAcceptedResponse(BaseModel):
    status: Literal["accepted"]
    job_id: str
    received_at: datetime
    route: str


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    time_utc: datetime


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def generate_job_id() -> str:
    return str(uuid.uuid4())

def constant_time_compare(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))

def compute_hmac_signature(secret: str, body: bytes) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"

async def read_raw_body_safely(request: Request) -> bytes:
    body = await request.body()
    if len(body) > MAX_BODY_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"Request body too large. Limit is {MAX_BODY_BYTES} bytes.",
        )
    return body

# def verify_signature_or_raise(sign)
