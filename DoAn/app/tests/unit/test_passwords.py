import pytest

from domain.passwords import SEED_SHA256_123456, hash_password, verify_password

pytestmark = pytest.mark.auth


def test_seed_sha256():
    assert SEED_SHA256_123456 == '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92'
    assert verify_password('123456', SEED_SHA256_123456)
    assert not verify_password('1234567', SEED_SHA256_123456)
    assert not verify_password('x', None)


def test_pbkdf2_hash():
    h = hash_password('matkhau1')
    assert h.startswith('pbkdf2_sha256$100000$')
    assert verify_password('matkhau1', h)
    assert not verify_password('matkhau2', h)
    assert hash_password('matkhau1') != h


def test_malformed_stored_is_false():
    assert not verify_password('a', '')
    assert not verify_password('a', 'pbkdf2_sha256$abc')
