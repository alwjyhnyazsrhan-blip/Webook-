"""
Request Shape Snapshots & Drift Detection
==========================================

Captures structural request/response fingerprints without logging secrets.
Used for detecting backend/API drift over time.
"""

from __future__ import annotations

import hashlib
import re
import time

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional
from urllib.parse import urlparse, urlunparse

from core.logging.logger import logger


_TOKEN_PARAMS = re.compile(
    r"(token|access_token|bearer|auth|otp|code|key|secret|session|sid)=[^&]+",
    re.IGNORECASE,
)


def _strip_url(url: str) -> str:
    parsed = urlparse(url)
    clean_query = _TOKEN_PARAMS.sub(r"\1=REDACTED", parsed.query)

    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            "",
            clean_query,
            "",
        )
    )


def _hash_header_keys(headers: dict) -> str:
    keys = sorted(k.lower() for k in headers.keys())
    return hashlib.sha256("|".join(keys).encode()).hexdigest()[:16]


def _hash_body_keys(body) -> str:
    if isinstance(body, dict):
        keys = sorted(str(k) for k in body.keys())
    elif isinstance(body, (list, tuple)):
        keys = [f"[{i}]" for i in range(len(body))]
    elif body is None:
        return "empty"
    else:
        return "scalar"

    return hashlib.sha256("|".join(keys).encode()).hexdigest()[:16]


@dataclass
class RequestSnapshot:
    stage: str
    method: str
    url_stripped: str

    header_keys: List[str]
    header_hash: str

    body_keys: List[str]
    body_hash: str

    response_code: int

    response_header_keys: List[str]
    response_header_hash: str

    captured_at: str
    mono_time: float

    @classmethod
    def capture(
        cls,
        stage: str,
        method: str,
        url: str,
        headers: dict,
        response_code: int,
        body=None,
        response_headers: Optional[dict] = None,
    ) -> "RequestSnapshot":

        url_s = _strip_url(url)

        h_keys = sorted(k.lower() for k in headers.keys())
        h_hash = _hash_header_keys(headers)

        b_keys = (
            sorted(str(k) for k in body.keys())
            if isinstance(body, dict)
            else []
        )

        b_hash = _hash_body_keys(body)

        rh_keys = sorted(
            k.lower() for k in (response_headers or {}).keys()
        )

        rh_hash = _hash_header_keys(response_headers or {})

        return cls(
            stage=stage,
            method=method.upper(),
            url_stripped=url_s,
            header_keys=h_keys,
            header_hash=h_hash,
            body_keys=b_keys,
            body_hash=b_hash,
            response_code=response_code,
            response_header_keys=rh_keys,
            response_header_hash=rh_hash,
            captured_at=datetime.now(timezone.utc).isoformat(),
            mono_time=time.monotonic(),
        )

    def shape_fingerprint(self) -> str:
        return hashlib.sha256(
            (
                f"{self.method}|"
                f"{self.url_stripped}|"
                f"{self.header_hash}|"
                f"{self.body_hash}|"
                f"{self.response_code}|"
                f"{self.response_header_hash}"
            ).encode()
        ).hexdigest()[:24]

    def to_dict(self) -> dict:
        return {
            "stage": self.stage,
            "method": self.method,
            "url": self.url_stripped,
            "header_keys": self.header_keys,
            "header_hash": self.header_hash,
            "body_keys": self.body_keys,
            "body_hash": self.body_hash,
            "response_code": self.response_code,
            "response_header_hash": self.response_header_hash,
            "shape_fingerprint": self.shape_fingerprint(),
            "captured_at": self.captured_at,
        }


@dataclass
class ShapeDrift:
    stage: str

    baseline_at: str
    detected_at: str

    baseline_fp: str
    current_fp: str

    added_headers: List[str]
    removed_headers: List[str]

    added_body_keys: List[str]
    removed_body_keys: List[str]

    response_code_changed: bool

    baseline_code: int
    current_code: int

    severity: str

    def to_dict(self) -> dict:
        return self.__dict__

    def assess(self) -> str:

        if self.response_code_changed and self.current_code in (
            403,
            429,
            503,
        ):
            return "CRITICAL"

        if self.removed_headers or self.removed_body_keys:
            return "HIGH"

        if self.added_headers or self.added_body_keys:
            return "MEDIUM"

        return "LOW"


class SnapshotStore:

    def __init__(self):
        self._baselines: Dict[str, RequestSnapshot] = {}
        self._history: List[RequestSnapshot] = []

    def record_and_detect(
        self,
        snap: RequestSnapshot,
        correlation_id: str,
    ) -> Optional[ShapeDrift]:

        self._history.append(snap)

        if snap.stage not in self._baselines:
            self._baselines[snap.stage] = snap

            logger.debug(
                f"[SNAPSHOT_BASELINE] "
                f"stage={snap.stage} "
                f"fp={snap.shape_fingerprint()} "
                f"correlation_id={correlation_id}"
            )

            return None

        baseline = self._baselines[snap.stage]

        if baseline.shape_fingerprint() == snap.shape_fingerprint():

            logger.debug(
                f"[SNAPSHOT_STABLE] "
                f"stage={snap.stage} "
                f"fp={snap.shape_fingerprint()} "
                f"correlation_id={correlation_id}"
            )

            return None

        added_h = [
            h for h in snap.header_keys
            if h not in baseline.header_keys
        ]

        removed_h = [
            h for h in baseline.header_keys
            if h not in snap.header_keys
        ]

        added_b = [
            k for k in snap.body_keys
            if k not in baseline.body_keys
        ]

        removed_b = [
            k for k in baseline.body_keys
            if k not in snap.body_keys
        ]

        code_changed = (
            baseline.response_code != snap.response_code
        )

        drift = ShapeDrift(
            stage=snap.stage,
            baseline_at=baseline.captured_at,
            detected_at=snap.captured_at,
            baseline_fp=baseline.shape_fingerprint(),
            current_fp=snap.shape_fingerprint(),
            added_headers=added_h,
            removed_headers=removed_h,
            added_body_keys=added_b,
            removed_body_keys=removed_b,
            response_code_changed=code_changed,
            baseline_code=baseline.response_code,
            current_code=snap.response_code,
            severity="",
        )

        drift.severity = drift.assess()

        logger.warning(
            f"[SHAPE_DRIFT] "
            f"correlation_id={correlation_id} "
            f"stage={drift.stage} "
            f"severity={drift.severity}"
        )

        return drift

    def export_history(self) -> List[dict]:
        return [s.to_dict() for s in self._history]


global_snapshot_store = SnapshotStore()
