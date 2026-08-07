"""
Assignment 11 — Audit Log starter (TODO).

Records every interaction for forensics. Never blocks by itself —
other layers catch attacks; this layer makes them reviewable.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone


import uuid
import time
from pathlib import Path


class AuditLogPlugin:
    """Framework-agnostic audit logger (wire into ADK callbacks or your pipeline)."""

    def __init__(self):
        self.name = "audit_log"
        self.logs: list[dict] = []
        self._open: dict[str, dict] = {}

    def record_input(self, *, user_id: str, text: str, request_id: str | None = None) -> str:
        """Store input + start timestamp keyed by request_id/user_id."""
        req_id = request_id or f"req_{uuid.uuid4().hex[:8]}"
        self._open[req_id] = {
            "user_id": user_id,
            "text": text,
            "start_time": time.time(),
        }
        return req_id

    def record_output(
        self,
        *,
        user_id: str,
        text: str,
        blocked: bool = False,
        layer: str | None = None,
        request_id: str | None = None,
    ) -> dict:
        """Store output, layer decision, latency; append to self.logs."""
        req_id = request_id or f"req_{uuid.uuid4().hex[:8]}"
        open_data = self._open.pop(req_id, {})
        start_time = open_data.get("start_time", time.time())
        latency_ms = round((time.time() - start_time) * 1000, 2)
        
        entry = {
            "request_id": req_id,
            "user_id": user_id,
            "timestamp": utc_now_iso(),
            "input_text": open_data.get("text", ""),
            "output_text": text,
            "blocked": blocked,
            "layer": layer,
            "latency_ms": latency_ms,
        }
        self.logs.append(entry)
        return entry

    def export_json(self, filepath: str = "outputs/audit_log.json"):
        """Write logs to disk (JSON array)."""
        out_path = Path(filepath)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(self.logs, ensure_ascii=False, indent=2), encoding="utf-8")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
