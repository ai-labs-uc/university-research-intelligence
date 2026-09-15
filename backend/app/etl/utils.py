import hashlib
import re
from urllib.parse import urlsplit, urlunsplit

def clean_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()

def canonicalize_url(url: str) -> str:
    p = urlsplit(url)
    return urlunsplit(
        (
            p.scheme.lower(),
            p.netloc.lower(),
            p.path.rstrip("/"),
            "",
            "",
        )
    )

def make_hash(url: str, title: str) -> str:
    raw = f"{canonicalize_url(url)}|{clean_text(title).lower()}"
    return hashlib.sha256(raw.encode()).hexdigest()
