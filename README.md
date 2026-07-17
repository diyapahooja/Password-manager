# 🔐 Password Manager – AES-256 Local Vault

A desktop password manager using **AES-256-GCM** encryption to store credentials in a local SQLite database. The master password is **never stored**; only a derived key lives in RAM during the session.

---

## ✨ Features

- 🔑 **Master Password Login** – Set on first run; required every unlock.
- 🔒 **AES-256-GCM** – Per-password encryption with integrity checks (tamper-proof).
- 🎲 **Password Generator** – One-click strong passwords (8–32 chars).
- 🔍 **Instant Search** – Filter by website or username.
- ➕✏️🗑️ **Full CRUD** – Add, Edit, Delete saved logins.
- 📋 **Copy to Clipboard** – One-click copy (pyperclip / Tkinter fallback).
- 🎨 **Dark Modern UI** – Tkinter + ttk, eye-friendly dark theme.
- 🧠 **Zero-Knowledge** – Database theft reveals zero readable data.

---

## 🧠 Encryption Flow
Master Password → PBKDF2-HMAC-SHA256 (200k iters + Random Salt)
→ AES-256 Key (RAM only, never stored)
→ AES-256-GCM (Plaintext → nonce+tag+ciphertext)
→ SQLite BLOB

text

**Security Highlights:**
- **Salt** prevents rainbow-table attacks.
- **Verifier** (`"VERIFIED_OK"`) encrypted & decrypted to check login – no separate hash stored.
- **GCM Mode** provides both confidentiality and authentication (detects tampering).
- Master password is **never persisted** – not even hashed; only the derived key exists ephemerally.

---

## 🗂 Project Structure
password-manager/
├── main.py # Entry point
├── gui.py # Tkinter UI (Login + Vault screens)
├── db.py # SQLite CRUD + verification
├── crypto_utils.py # AES-GCM + PBKDF2 logic
├── password_generator.py # Random strong password generator
├── requirements.txt # Dependencies
├── .gitignore # Excludes vault.db
└── README.md

text

---

## 🗃 Database Schema

**config** (Singleton)
| Column     | Type | Description |
|------------|------|-------------|
| `id`       | INT  | Always 1 |
| `key_salt` | BLOB | PBKDF2 salt |
| `verifier` | BLOB | Encrypted known string for login verification |

**passwords**
| Column              | Type | Description |
|---------------------|------|-------------|
| `id`                | INT  | Primary key |
| `website`           | TEXT | Site name |
| `username`          | TEXT | Login ID |
| `encrypted_password`| BLOB | `nonce + tag + ciphertext` |

---

## ⚙️ Setup & Run

##```bash
git clone <repo-url>
cd password-manager
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py

## ⚠️ No password reset – forget the master password = vault unrecoverable by design.

🔐 Why This Is Secure (Zero-Knowledge)
PBKDF2 (200k iterations) makes brute-force impractical even if vault.db is stolen.

No plaintext – neither master password nor saved passwords ever touch the disk in readable form.

Ephemeral key – the AES key exists only in memory and is destroyed when the app closes.

GCM integrity – any modification to ciphertext causes decryption to fail, preventing data forgery.

## 👤 Author
Diya Pahooja
