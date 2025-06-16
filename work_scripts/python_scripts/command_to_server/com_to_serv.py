import os
import sys
import subprocess
import logging
import getpass
import signal
import base64
from datetime import datetime
import yaml
import paramiko
import re
from cryptography.fernet import Fernet
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# === Проверка зависимостей ===
try:
    import paramiko
    import yaml
    from tqdm import tqdm
    from cryptography.fernet import Fernet
except ImportError as e:
    print(f"[ОШИБКА] Не найдена библиотека: {e.name}. Установите зависимости командой:\n\npip install -r requirements.txt")
    sys.exit(1)

# === Константы ===
CRED_DIR = os.path.expanduser("~/.com_to_serv")
CRED_FILE = os.path.join(CRED_DIR, "cred")
KEY_FILE = os.path.join(CRED_DIR, "key")

# === Шифрование пароля ===
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

def save_password_encrypted(password):
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

# === Логгирование ===
def setup_logging():
    logger = logging.getLogger("multi_ssh")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%H:%M:%S")
    today = datetime.now().strftime("%Y-%m-%d")
    log_filename = f"log({today}).log"
    file_handler = logging.FileHandler(log_filename, encoding="utf-8")
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

# === Проверка sudo ===
def check_sudo_access(password):
    print("\n[INFO] Проверка доступа sudo...")
    try:
        result = subprocess.run(["sudo", "-n", "true"], capture_output=True)
        if result.returncode == 0:
            print("[OK] Доступ к sudo есть.")
            return True
        else:
            check = subprocess.run(
                f"echo {password} | sudo -S true",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            if check.returncode == 0:
                print("[OK] Доступ к sudo подтверждён через пароль.")
                return True
            else:
                print("[ОШИБКА] Неверный пароль или нет доступа к sudo.")
                return False
    except Exception as e:
        print(f"[ОШИБКА] Не удалось проверить sudo: {e}")
        return False

# === Обработка сигналов ===
def graceful_exit(signum, frame):
    print("\nЗавершение работы, закрытие соединений...")
    logger.info("Скрипт завершён пользователем.")
    sys.exit(0)

signal.signal(signal.SIGINT, graceful_exit)

# === Загрузка серверов ===
def choose_file(folder):
    files = [f for f in os.listdir(folder) if f.endswith('.yaml')]
    if not files:
        print("Нет доступных файлов для выбора.")
        sys.exit(1)
    for i, f in enumerate(files):
        print(f"{i+1}: {f}\n")
    while True:
        try:
            idx = int(input("Выберите файл: ")) - 1
            if 0 <= idx < len(files):
                return os.path.join(folder, files[idx])
        except ValueError:
            pass
        print("Некорректный ввод. Попробуйте снова.")

def load_hosts_from_yaml(filepath):
    with open(filepath, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if "servers" not in data:
        print("В файле нет ключа 'servers'")
        sys.exit(1)
    hosts = []
    for entry in data["servers"]:
        parts = entry.strip().split()
        if len(parts) != 2 or not parts[1].isdigit():
            print(f"Неверный формат: {entry}")
            sys.exit(1)
        hosts.append({"host": parts[0], "port": int(parts[1])})
    return hosts

# === Выбор файла из папки ===
def choose_local_file():
    folder = os.path.join(".", "to_remote")
    if not os.path.isdir(folder):
        print("Папка 'to_remote' не найдена.")
        return None, None
    files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
    if not files:
        print("Нет файлов в папке 'to_remote'.")
        return None, None
    print("Доступные файлы:")
    for i, f in enumerate(files):
        print(f"{i+1}: {f}")
    while True:
        try:
            idx = int(input("Выберите файл по номеру: ")) - 1
            if 0 <= idx < len(files):
                file_path = os.path.join(folder, files[idx])
                remote_path = input("Куда отправить файл на сервере (например, /usr/local/bin): ").strip()
                return file_path, remote_path
        except ValueError:
            pass
        print("Некорректный ввод.")

# === Отправка файла по SCP ===
def send_file_scp(username, host, local_file, remote_path):
    scp_command = ["scp", local_file, f"{username}@{host}:{remote_path}"]
    try:
        print(f"\n[INFO] Отправка {local_file} на {host}:{remote_path} через SCP...")
        subprocess.run(scp_command, check=True)
        print(f"[OK] Файл отправлен на {host}")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Не удалось отправить файл на {host}: {e}")

# === Выполнение команд ===
connection_logged = {}
def execute_commands_on_server(host, port, username, password, command):
    try:
        with paramiko.SSHClient() as client:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(host, port, username=username, password=password, timeout=5)

            key = f"{host}:{port}"
            if not connection_logged.get(key):
                logger.info(f"Подключение к {host}... успешно.")
                connection_logged[key] = True

            for com in command:
                full_command = f"echo {password} | sudo -S -p '' {com}" if com.strip().startswith("sudo ") else com
                stdin, stdout, stderr = client.exec_command(full_command, get_pty=True)
                stdin.write(password + "\n")
                stdin.flush()
                output = stdout.read().decode()
                error = stderr.read().decode()
                if error and "password" not in error.lower():
                    logger.warning(f"[{host}] Ошибка: {error.strip()}")
                else:
                    logger.info(f"[{host}] Результат:\n{output}")
        return True
    except Exception as e:
        logger.error(f"[{host}] Ошибка подключения: {e}")
        return False

# === Главное меню ===
def main_menu(servers, username, password):
    while True:
        print("""
1. Отправить файл на сервера
2. Выполнить команду на серверах
0. Выход
        """)
        choice = input("Введите номер действия: ").strip()
        if choice == "1":
            file_path, remote_path = choose_local_file()
            if not file_path:
                continue
            for server in servers:
                send_file_scp(username, server['host'], file_path, remote_path)
        elif choice == "2":
            command = input("Введите команду: ").strip()
            if not command:
                continue
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = {
                    executor.submit(execute_commands_on_server, s['host'], s['port'], username, password, [command]): s
                    for s in servers
                }
                for future in tqdm(as_completed(futures), total=len(futures), desc="Выполнение"):
                    future.result()
        elif choice == "0":
            print("Выход из программы.")
            break
        else:
            print("Неверный ввод.")

# === Точка входа ===
def main():
    global logger
    logger = setup_logging()
    folder = os.path.join(".", "servers")
    if not os.path.isdir(folder):
        print("Папка 'servers' не найдена.")
        sys.exit(1)
    filepath = choose_file(folder)
    servers = load_hosts_from_yaml(filepath)
    username = input("Введите имя пользователя: ")
    password = get_or_prompt_password()
    if not check_sudo_access(password):
        logger.error("Нет доступа к sudo. Завершение.")
        sys.exit(1)
    main_menu(servers, username, password)

if __name__ == "__main__":
    main()
