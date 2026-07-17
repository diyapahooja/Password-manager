"""
db.py
-----
All SQLite access lives here. Two tables:

config (single row, id=1)
    key_salt   BLOB  -> salt used to derive the AES key from the master password
    verifier   BLOB  -> encrypted known string, used to check the master
                        password is correct at login (without ever storing
                        the master password itself)

passwords
    id                  INTEGER PRIMARY KEY AUTOINCREMENT
    website             TEXT
    username            TEXT
    encrypted_password  BLOB
"""

import sqlite3
import os

import crypto_utils

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vault.db")
VERIFIER_PLAINTEXT = "VERIFIED_OK"  # arbitrary known string


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create tables if they don't already exist. Safe to call every startup."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            key_salt BLOB NOT NULL,
            verifier BLOB NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS passwords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            website TEXT NOT NULL,
            username TEXT NOT NULL,
            encrypted_password BLOB NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def is_master_password_set() -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM config WHERE id = 1")
    row = cur.fetchone()
    conn.close()
    return row is not None


def setup_master_password(master_password: str) -> bytes:
    """
    First-run only. Derives a key from the chosen master password,
    stores the salt + an encrypted verifier string, and returns the key
    so the caller's session can start immediately.
    """
    key_salt = crypto_utils.generate_salt()
    key = crypto_utils.derive_key(master_password, key_salt)
    verifier_blob = crypto_utils.encrypt(key, VERIFIER_PLAINTEXT)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO config (id, key_salt, verifier) VALUES (1, ?, ?)",
        (key_salt, verifier_blob),
    )
    conn.commit()
    conn.close()
    return key


def verify_master_password(master_password: str):
    """
    Returns the derived AES key if the password is correct, else None.
    This is what actually 'logs the user in' -- there's no separate
    stored password hash to check against, we just try to decrypt the
    verifier and see if it succeeds.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT key_salt, verifier FROM config WHERE id = 1")
    row = cur.fetchone()
    conn.close()

    if row is None:
        return None

    key_salt, verifier_blob = row
    key = crypto_utils.derive_key(master_password, key_salt)
    try:
        decrypted = crypto_utils.decrypt(key, verifier_blob)
    except Exception:
        return None

    if decrypted == VERIFIER_PLAINTEXT:
        return key
    return None


# ---- Password entry CRUD ----------------------------------------------

def add_password(website: str, username: str, key: bytes, plaintext_password: str) -> int:
    encrypted = crypto_utils.encrypt(key, plaintext_password)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO passwords (website, username, encrypted_password) VALUES (?, ?, ?)",
        (website, username, encrypted),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def get_all_entries(key: bytes):
    """Returns list of dicts: id, website, username, password (decrypted)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, website, username, encrypted_password FROM passwords ORDER BY website COLLATE NOCASE")
    rows = cur.fetchall()
    conn.close()

    entries = []
    for row_id, website, username, enc in rows:
        try:
            plain = crypto_utils.decrypt(key, enc)
        except Exception:
            plain = "<decryption error>"
        entries.append({"id": row_id, "website": website, "username": username, "password": plain})
    return entries


def search_entries(key: bytes, term: str):
    all_entries = get_all_entries(key)
    term = term.lower().strip()
    if not term:
        return all_entries
    return [e for e in all_entries if term in e["website"].lower() or term in e["username"].lower()]


def update_entry(entry_id: int, key: bytes, website: str, username: str, plaintext_password: str):
    encrypted = crypto_utils.encrypt(key, plaintext_password)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE passwords SET website = ?, username = ?, encrypted_password = ? WHERE id = ?",
        (website, username, encrypted, entry_id),
    )
    conn.commit()
    conn.close()


def delete_entry(entry_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM passwords WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()
