# modules/auth.py

import os
import getpass
from cryptography.fernet import Fernet

CRED_DIR = os.path.expanduser("~/.com_to_serv")
CRED_FILE = os.path.join(CRED_DIR, "cred")
KEY_FILE = os.path.join(CRED_DIR, "key")

def generate_key():
    key = Fernet.generate_key()
    os.makedirs(CRED_DIR, exist_ok=True)
    with open(KEY_FILE, 'wb') as f:
        f.write(key)
    return key

def load_key():
    if not os.path.exists(KEY_FILE):
        return generate_key()
    with open(KEY_FILE, 'rb') as f:
        return f.read()

def save_password_encrypted(password: str):
    key = load_key()
    fernet = Fernet(key)
    encrypted = fernet.encrypt(password.encode())
    with open(CRED_FILE, 'wb') as f:
        f.write(encrypted)

def load_password_encrypted():
    if not os.path.exists(CRED_FILE):
        return None
    key = load_key()
    fernet = Fernet(key)
    with open(CRED_FILE, 'rb') as f:
        encrypted = f.read()
    return fernet.decrypt(encrypted).decode()

def get_or_prompt_password():
    saved = load_password_encrypted()
    if saved:
        return saved
    password = getpass.getpass("Введите пароль: ")
    save_password_encrypted(password)
    return password

def get_username_and_password():
    current_user = os.getenv("USER") or os.getenv("USERNAME")
    username = input("Введите имя пользователя: ").strip()
    saved_password = load_password_encrypted()
    if username == current_user and saved_password:
        print("[INFO] Пароль не требуется: пользователь совпадает и пароль уже сохранён.")
        return username, saved_password
    password = get_or_prompt_password()
    return username, password