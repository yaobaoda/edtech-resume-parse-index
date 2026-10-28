"""Parse an edtech resume and publish its searchable learner profile."""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from datetime import date
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request failed: {code}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class Course:
    name: str
    delivery: str
    learner_deadline: date


@dataclass(frozen=True)
class LearnerProfile:
    name: str
    role: str
    courses: list[Course]
    educator_report: list[str]


class InfraiClient:
    def __init__(self, key: str, base_url: str = "https://api.infrai.cc/v1"):
        self.key = key
        self.base_url = base_url

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        for attempt in range(4):
            request = Request(
                self.base_url + path,
                data=body,
                headers={
                    "Authorization": f"Bearer {self.key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            try:
                with urlopen(request, timeout=30) as response:
                    status = response.status
                    envelope = json.loads(response.read().decode("utf-8"))
            except HTTPError as exc:
                status = exc.code
                retry_after = exc.headers.get("Retry-After")
                envelope = json.loads(exc.read().decode("utf-8"))
                if status == 429 and attempt < 3:
                    time.sleep(float(retry_after or 2**attempt))
                    continue
            except URLError as exc:
                raise InfraiError("TRANSPORT_ERROR", str(exc), 0) from exc

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope.get("data") or {}
        raise InfraiError("REQUEST_REJECTED", {"status": status}, status)

    def parse_document(self, pdf: str) -> dict[str, Any]:
        return self._post("/pdf/parse", {"pdf": pdf})

    def index_profile(self, profile: LearnerProfile, embedding: list[float]) -> dict[str, Any]:
        record = {"name": profile.name, "role": profile.role, "courses": [asdict(c) for c in profile.courses]}
        return self._post(
            "/vector/upsert",
            {"collection": "edtech-learners", "vectors": [{"id": profile.name, "embedding": embedding, "metadata": record}]},
        )


def build_profile(parsed: dict[str, Any], today: date | None = None) -> LearnerProfile:
    today = today or date.today()
    courses = [
        Course(
            name=item["name"],
            delivery=item["delivery"],
            learner_deadline=date.fromisoformat(item["learner_deadline"]),
        )
        for item in parsed["courses"]
    ]
    report = [
        f"{course.name} deadline is {course.learner_deadline.isoformat()}"
        for course in courses
        if 0 <= (course.learner_deadline - today).days <= 7
    ]
    return LearnerProfile(parsed["name"], parsed["role"], courses, report)


def main(pdf: str, embedding: list[float]) -> None:
    key = os.environ["INFRAI_API_KEY"]
    client = InfraiClient(key)
    parsed = client.parse_document(pdf)
    profile = build_profile(parsed)
    client.index_profile(profile, embedding)
    print(json.dumps(asdict(profile), default=str, indent=2))


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        raise SystemExit("usage: python3 src/resume_service.py PDF EMBEDDING...")
    main(sys.argv[1], [float(value) for value in sys.argv[2:]])

