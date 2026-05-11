import hashlib
import os


def hash_student_id(raw_id: str) -> str:
    """
    Return a keyed BLAKE2b hex digest of the raw student identifier.

    The key is read from STUDENT_HASH_SECRET (no fallback). Using a secret key
    means the hash is not reproducible without the server secret, preventing
    offline rainbow-table attacks against known student ID formats.

    Key rotation warning: if STUDENT_HASH_SECRET ever changes, all existing
    student_id_hash values in the database become unlinkable. Treat this secret
    like the LUKS master key — back it up and never rotate without a migration.
    """
    key_hex = os.environ.get("STUDENT_HASH_SECRET")
    if not key_hex:
        raise RuntimeError(
            "STUDENT_HASH_SECRET must be set in environment — no fallback permitted."
        )
    key = bytes.fromhex(key_hex)
    return hashlib.blake2b(raw_id.encode(), key=key, digest_size=32).hexdigest()
