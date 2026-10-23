
def is_content_stale(
    source_content_hash: str,
    current_content_hash: str | None,
) -> bool:
    """Return whether the source is missing or its content has changed."""
    if current_content_hash is None:
        return True

    return source_content_hash != current_content_hash
