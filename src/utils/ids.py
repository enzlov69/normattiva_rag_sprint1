from uuid import uuid4


def build_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"
