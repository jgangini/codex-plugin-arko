import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .io import inside, read_json, write_json


def review_entry(baseline: bytes, reason: str) -> dict[str, str]:
    return {
        "at": datetime.now(timezone.utc).isoformat(),
        "reason": reason,
        "sha256": hashlib.sha256(baseline).hexdigest(),
    }


def _read_log(path: Path) -> dict:
    try:
        log = read_json(path)
    except FileNotFoundError:
        return {"reviews": []}
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError("Invalid contract approval log: contracts/acceptance.json") from error
    if not isinstance(log, dict) or not isinstance(log.get("reviews"), list):
        raise ValueError("Invalid contract approval log: contracts/acceptance.json")
    return log


def approved_baseline(root: Path) -> dict:
    reviews = _read_log(inside(root, "contracts/acceptance.json"))["reviews"]
    if not reviews:
        raise ValueError("Missing contract approval in contracts/acceptance.json; review before running accept-contract")
    latest = reviews[-1]
    expected = latest.get("sha256") if isinstance(latest, dict) else None
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected):
        raise ValueError("Invalid latest contract approval in contracts/acceptance.json")
    baseline = inside(root, "contracts/baseline.json").read_bytes()
    if hashlib.sha256(baseline).hexdigest() != expected.lower():
        raise ValueError("contracts/baseline.json does not match the latest approval in contracts/acceptance.json")
    return json.loads(baseline)


def record_approval(root: Path, schema: dict, reason: str) -> None:
    baseline = inside(root, "contracts/baseline.json")
    path = inside(root, "contracts/acceptance.json")
    log = _read_log(path)
    content = (json.dumps(schema, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    log["reviews"].append(review_entry(content, reason))
    baseline.write_bytes(content)
    write_json(path, log)
