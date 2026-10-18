"""Appeal deadline logic. The deadline printed on the denial letter always wins;
these defaults are only a fallback and are always shown as 'verify with your plan'."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

# Typical filing windows for a first-level (internal) appeal, in days from the denial notice.
DEFAULT_WINDOWS = {
    "employer_or_aca": (180, "ACA rules give most non-grandfathered plans at least 180 days for an internal appeal."),
    "medicare_advantage": (65, "Medicare Advantage plans typically allow 65 days to request reconsideration."),
    "original_medicare": (120, "Original Medicare allows 120 days to request a redetermination."),
    "medicaid": (60, "Medicaid managed-care plans typically allow 60 days for a plan appeal."),
    "unknown": (60, "Plan type unclear - using a conservative 60-day window."),
}


def _parse(d: str | None) -> date | None:
    if not d:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%B %d, %Y", "%b %d, %Y", "%d %B %Y"):
        try:
            return datetime.strptime(d.strip(), fmt).date()
        except ValueError:
            continue
    return None


def compute(denial_date: str | None, stated_deadline: str | None, plan_type: str | None,
            today: date | None = None) -> dict:
    today = today or date.today()
    stated = _parse(stated_deadline)
    if stated:
        due, basis = stated, "Deadline stated in your denial letter."
    else:
        days, why = DEFAULT_WINDOWS.get(plan_type or "unknown", DEFAULT_WINDOWS["unknown"])
        start = _parse(denial_date) or today
        due, basis = start + timedelta(days=days), why + " Verify with your plan."
    # Recommend sending a week early to leave room for mail and faxes.
    target = due - timedelta(days=7)
    return {
        "due": due.isoformat(),
        "send_by": max(target, today).isoformat(),
        "days_left": (due - today).days,
        "basis": basis,
        "from_letter": bool(stated),
    }


def ics(summary: str, day: str, description: str) -> str:
    d = day.replace("-", "")
    return "\r\n".join([
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Appeal//EN", "BEGIN:VEVENT",
        f"UID:appeal-{d}@appeal.local", f"DTSTAMP:{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}",
        f"DTSTART;VALUE=DATE:{d}", f"SUMMARY:{summary}",
        "DESCRIPTION:" + description.replace("\n", "\\n").replace(",", "\\,"),
        "BEGIN:VALARM", "TRIGGER:-P3D", "ACTION:DISPLAY", f"DESCRIPTION:{summary}", "END:VALARM",
        "END:VEVENT", "END:VCALENDAR", ""])
