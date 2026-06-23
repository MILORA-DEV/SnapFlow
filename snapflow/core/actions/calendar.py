"""Save calendar events as .ics files."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from snapflow.core.actions.base import ActionError, BaseAction
from snapflow.core.config import OUTPUT_DIR


def _parse_event_data(data: str) -> dict:
    data = data.strip()
    try:
        parsed = json.loads(data)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    return {"title": "SnapFlow Event", "description": data}


def _to_ics_datetime(value: str) -> str:
    cleaned = value.strip()
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(cleaned)
    except ValueError as exc:
        raise ActionError(f"Invalid datetime '{value}': {exc}") from exc

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y%m%dT%H%M%SZ")


def _escape_ics(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def _build_ics(event: dict) -> str:
    title = event.get("title") or "SnapFlow Event"
    description = event.get("description") or ""
    location = event.get("location") or ""

    start_raw = event.get("start")
    if not start_raw:
        raise ActionError("Calendar event missing 'start' datetime.")

    start = _to_ics_datetime(str(start_raw))

    end_raw = event.get("end")
    if end_raw:
        end = _to_ics_datetime(str(end_raw))
    else:
        start_dt = datetime.fromisoformat(str(start_raw).replace("Z", "+00:00"))
        end_dt = start_dt + timedelta(hours=1)
        end = end_dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    uid = f"{uuid4()}@snapflow"
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//SnapFlow//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{now}",
        f"DTSTART:{start}",
        f"DTEND:{end}",
        f"SUMMARY:{_escape_ics(title)}",
    ]
    if description:
        lines.append(f"DESCRIPTION:{_escape_ics(description)}")
    if location:
        lines.append(f"LOCATION:{_escape_ics(location)}")
    lines.extend(["END:VEVENT", "END:VCALENDAR"])
    return "\r\n".join(lines) + "\r\n"


def _safe_filename(title: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", title).strip().lower()
    slug = re.sub(r"[\s_-]+", "-", slug) or "event"
    return f"{slug}.ics"


class CalendarAction(BaseAction):
    action_type = "calendar"

    def execute(self, data: str) -> str:
        event = _parse_event_data(data)
        ics_content = _build_ics(event)

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        path = OUTPUT_DIR / _safe_filename(str(event.get("title", "event")))
        path.write_text(ics_content, encoding="utf-8")

        self._open_file(path)
        return f"Calendar event saved to {path.name}"

    def _open_file(self, path: Path) -> None:
        try:
            if sys.platform == "win32":
                subprocess.run(["start", "", str(path)], shell=True, check=False)
            elif sys.platform == "darwin":
                subprocess.run(["open", str(path)], check=False)
            else:
                subprocess.run(["xdg-open", str(path)], check=False)
        except OSError:
            pass


class CalendarEventAction(CalendarAction):
    action_type = "calendar_event"
