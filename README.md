🔐 Secure Password Manager
A local, encrypted password manager with AES‑256‑GCM and a master password that is never stored.

✨ Features
One master password unlocks everything.

Strong encryption: AES‑256‑GCM + PBKDF2 (200k iterations).

Passwords stored as encrypted blobs (nonce + tag + ciphertext).

Built‑in password generator (custom length).

Search, add, update, delete, and copy to clipboard.

Clean dark‑themed GUI (Tkinter).

🧠 Security Design
What	How
Master password	Never stored – used only to derive the key.
Salt + Key derivation	Random 16‑byte salt + PBKDF2‑HMAC‑SHA256 (200k iterations).
Encryption	AES‑256‑GCM (confidentiality + integrity).
Verification	Encrypted known string – successful decryption proves correct password.
Database	SQLite – stores only nonce + tag + ciphertext.
⚠️ No password reset – if you forget the master password, your vault is unrecoverable.

🖥️ Usage
First run: Create a master password (min. 6 characters).

Login: Enter your master password to unlock.

Manage: View, add, edit, delete, search, and copy passwords.

Generate: Click Generate to create a secure password.

📁 File Structure
text
.
├── crypto_utils.py       # encryption/decryption
├── db.py                 # SQLite operations
├── gui.py                # Tkinter interface
├── main.py               # entry point
├── password_generator.py # random password generator
├── requirements.txt
└── vault.db              # database (auto‑created)
🛠️ Technologies
Python 3.8+, Tkinter, SQLite, pycryptodome, pyperclip.

🔧 Customisation
Edit crypto_utils.py to change:

python
PBKDF2_ITERATIONS = 200_000   # increase for more security
KEY_LENGTH_BYTES = 32         # AES‑256
SALT_LENGTH_BYTES = 16
Changing these after first run will break decryption.

📄 License
MIT – see LICENSE.

## Author 
Diya Pahooja
