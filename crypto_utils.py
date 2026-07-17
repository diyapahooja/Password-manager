"""
crypto_utils.py
----------------
Handles all cryptography for the password manager.

Design:
- The master password is NEVER stored anywhere.
- A random 16-byte "key_salt" is stored in the DB (config table).
- Every time the app starts, the master password + key_salt are run
  through PBKDF2-HMAC-SHA256 (200,000 iterations) to derive a 256-bit
  AES key. This key only ever lives in memory (RAM), for the duration
  of the session.
- Each saved password is encrypted individually with AES-256 in GCM
  mode. GCM gives us confidentiality AND integrity (it detects if the
  ciphertext was tampered with) and needs no manual padding.
- What actually goes in the DB per row = nonce + tag + ciphertext,
  all concatenated and stored as a single BLOB.
"""

import os
import hashlib
from Crypto.Cipher import AES

# ---- Tunable constants -----------------------------------------------
PBKDF2_ITERATIONS = 200_000
KEY_LENGTH_BYTES = 32          # 32 bytes = 256 bits -> AES-256
SALT_LENGTH_BYTES = 16
NONCE_LENGTH_BYTES = 16        # AES-GCM nonce
TAG_LENGTH_BYTES = 16          # AES-GCM auth tag


def generate_salt() -> bytes:
    """Generate a fresh random salt (used once, at first-run setup)."""
    return os.urandom(SALT_LENGTH_BYTES)


def derive_key(master_password: str, salt: bytes) -> bytes:
    """
    Turn the human-typed master password into a strong 256-bit AES key.
    PBKDF2 with a high iteration count makes brute-forcing slow even if
    someone steals the database file.
    """
    return hashlib.pbkdf2_hmac(
        "sha256",
        master_password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
        dklen=KEY_LENGTH_BYTES,
    )


def encrypt(key: bytes, plaintext: str) -> bytes:
    """
    Encrypt a plaintext string with AES-256-GCM.
    Returns nonce + tag + ciphertext as one blob (ready to store in SQLite).
    """
    cipher = AES.new(key, AES.MODE_GCM, nonce=os.urandom(NONCE_LENGTH_BYTES))
    ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode("utf-8"))
    return cipher.nonce + tag + ciphertext


def decrypt(key: bytes, blob: bytes) -> str:
    """
    Reverse of encrypt(). Splits the stored blob back into
    nonce / tag / ciphertext, then decrypts and verifies integrity.
    Raises ValueError if the key is wrong or data was tampered with.
    """
    nonce = blob[:NONCE_LENGTH_BYTES]
    tag = blob[NONCE_LENGTH_BYTES:NONCE_LENGTH_BYTES + TAG_LENGTH_BYTES]
    ciphertext = blob[NONCE_LENGTH_BYTES + TAG_LENGTH_BYTES:]

    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    return plaintext.decode("utf-8")
