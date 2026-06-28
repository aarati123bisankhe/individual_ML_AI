from __future__ import annotations

from typing import Dict, Tuple
from urllib.parse import parse_qs, urlparse


def parse_request_path(path: str) -> Tuple[str, Dict[str, str]]:
    parsed = urlparse(path)
    params = {key: values[0] for key, values in parse_qs(parsed.query).items()}
    return parsed.path, params
