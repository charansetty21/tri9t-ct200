
from app.services.staleness import is_content_stale


def test_same_hash_is_not_stale():
    assert is_content_stale("hash-v1", "hash-v1") is False


def test_different_hash_is_stale():
    assert is_content_stale("hash-v1", "hash-v2") is True


def test_missing_current_hash_is_stale():
    assert is_content_stale("hash-v1", None) is True
