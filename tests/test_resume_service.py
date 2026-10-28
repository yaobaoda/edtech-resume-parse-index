from datetime import date

from src.resume_service import build_profile


def test_deadline_inside_seven_days_is_reported():
    parsed = {
        "name": "Mina Chen",
        "role": "Curriculum designer",
        "courses": [
            {"name": "Checkout Analytics", "delivery": "live workshop", "learner_deadline": "2026-10-30"},
            {"name": "Python Basics", "delivery": "self-paced", "learner_deadline": "2026-11-20"},
        ],
    }

    profile = build_profile(parsed, today=date(2026, 10, 25))

    assert profile.educator_report == ["Checkout Analytics deadline is 2026-10-30"]

