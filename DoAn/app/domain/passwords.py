"""Băm mật khẩu: pbkdf2_sha256 (stdlib) cho mật khẩu mới; vẫn chấp nhận SHA-256 hex của seed."""
from __future__ import annotations

import hashlib
import hmac
import re
import secrets

SEED_SHA256_123456 = '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92'
_ITERATIONS = 100000
_SHA256_HEX = re.compile(r'^[0-9a-fA-F]{64}$')


def _pbkdf2(plain: str, salt: str, iterations: int) -> str:
    return hashlib.pbkdf2_hmac('sha256', plain.encode('utf-8'), salt.encode('utf-8'), iterations).hex()


def hash_password(plain: str) -> str:
    salt = secrets.token_hex(8)
    return f'pbkdf2_sha256${_ITERATIONS}${salt}${_pbkdf2(plain, salt, _ITERATIONS)}'


def verify_password(plain: str, stored: str | None) -> bool:
    if not stored:
        return False
    if stored.startswith('pbkdf2_sha256$'):
        parts = stored.split('$')
        if len(parts) != 4:
            return False
        try:
            iterations = int(parts[1])
        except ValueError:
            return False
        return hmac.compare_digest(_pbkdf2(plain, parts[2], iterations), parts[3])
    if _SHA256_HEX.match(stored):
        digest = hashlib.sha256(plain.encode('utf-8')).hexdigest()
        return hmac.compare_digest(digest, stored.lower())
    return False
