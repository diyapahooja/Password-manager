##🔐 Password Manager

A secure, offline desktop password manager built with Python and Tkinter, featuring AES-256 encryption, a local SQLite vault, and a clean, modern GUI.

Show Image
Show Image
Show Image


##Overview

This application allows users to securely store, retrieve, and manage website credentials on their local machine. All passwords are encrypted with AES-256 (GCM mode) before being written to the database, and the vault can only be unlocked with a master password that is never stored anywhere on disk.


##Features

FeatureDescription🔑 Master Password LoginA single master password protects the entire vault. The application cannot be opened without it.🔒 AES-256 EncryptionEvery stored password is individually encrypted using AES-256-GCM before being saved to the database.🎲 Password GeneratorInstantly generate strong random passwords with a configurable length.🔍 Live SearchFilter saved credentials in real time by website or username.➕ Add / ✏️ Edit / 🗑️ DeleteFull CRUD support for managing saved credentials.📋 Copy to ClipboardCopy any password to the clipboard with a single click.🎨 Modern GUIA polished, dark-themed interface built with Tkinter and ttk — no external UI framework required.


##How It Works

The application never stores the master password itself. Instead, it derives an encryption key from the password each time the app is unlocked:

Master Password
      │
      ▼  PBKDF2-HMAC-SHA256 (200,000 iterations + random salt)
AES-256 Key   (kept in memory only, never written to disk)
      │
      ▼  AES-256-GCM
Plaintext Password ──encrypt──▶ nonce + tag + ciphertext ──▶ SQLite BLOB

At login, the typed password is used to re-derive the key, which is then used to attempt decryption of a stored "verifier" value. If decryption fails, the password is rejected — meaning no password hash ever needs to be stored either.

As a result, if the database file were ever copied or stolen, it would contain nothing but encrypted, unreadable bytes.


##Project Structure

password-manager/
├── main.py               # Application entry point
├── gui.py                # Tkinter GUI (login screen + vault screen)
├── db.py                 # SQLite operations and master password verification
├── crypto_utils.py       # AES-256-GCM encryption/decryption and key derivation
├── password_generator.py # Random secure password generator
├── requirements.txt      # Python dependencies
├── .gitignore
└── README.md


##Database Schema

config — single-row table storing app-level security settings

ColumnTypeDescriptionidINTAlways 1key_saltBLOBSalt used for PBKDF2 key derivationverifierBLOBEncrypted known value used to validate login

passwords — stores all saved credentials

ColumnTypeDescriptionidINTPrimary key, auto-incrementwebsiteTEXTWebsite or service nameusernameTEXTAssociated username or emailencrypted_passwordBLOBAES-256-GCM encrypted password blob


##Installation

Prerequisites: Python 3.9 or higher

bash# 1. Clone the repository
git clone https://github.com/<your-username>/password-manager.git
cd password-manager

# 2. (Recommended) Create a virtual environment
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python main.py

On first launch, you will be prompted to create a master password. This password is required on every subsequent launch and cannot be recovered or reset — this is intentional, as the encryption key is derived directly from it.


##Tech Stack

LibraryPurposetkinterGraphical user interface (built into Python)sqlite3Local database storage (built into Python)pycryptodomeAES-256-GCM encryptionhashlibPBKDF2 key derivation from the master passwordos, random, stringSecure salts, nonces, and password generationpyperclip (optional)One-click clipboard copy; falls back to Tkinter's native clipboard if unavailable


##Security Notes


The master password is never written to disk in any form.
Encryption keys exist only in memory for the duration of a session.
Each password is encrypted individually with a unique nonce (AES-GCM), so identical passwords never produce identical ciphertext.
AES-GCM provides both confidentiality and integrity — any tampering with stored data is detected automatically during decryption.



##Roadmap


 Change master password (re-encrypt vault with a new key)
 Auto-lock after a period of inactivity
 Password strength indicator
 Encrypted vault export/import
 Light/dark theme toggle


##Author

Built by Diya Pahooja — BS Computer Science student.
