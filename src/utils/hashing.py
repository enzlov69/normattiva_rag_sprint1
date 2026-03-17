import hashlib


def sha256_text(value: str) -> str:
    digest = hashlib.sha256(value.encode('utf-8')).hexdigest()
    return f'sha256:{digest}'
