# Проверка наличия необходимых библиотек
import subprocess
import sys

REQUIRED_PACKAGES = ["paramiko", "pyyaml", "tqdm"]

def check_packages():
    import importlib
    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            importlib.import_module(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"Не хватает библиотек: {', '.join(missing)}. Устанавливаю...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])

check_packages()

import paramiko
import logging
import getpass
import signal
import yaml
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import re

# Настройка логирования
logger = logging.getLogger("multi_ssh")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%H:%M:%S")

#Логирование в файл
file_handler = logging.FileHandler("log.log", encoding="utf-8")
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)

#Логирование в консоль
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Закрытие соединения
def graceful_exit(signum, frame):
    print("\nЗавершение работы, закрытие соединений...")
    logger.info("Скрипт завершён пользователем.")
    sys.exit(0)

signal.signal(signal.SIGINT, graceful_exit)

# Функция для выбора файла
def choose_file(folder):
    files = [f for f in os.listdir(folder) if f.endswith('.yaml')]
    if not files:
        logger.error("Нет доступных файлов для выбора.")
        print("Нет доступных файлов для выбора.")
        sys.exit(1)
    for i, f in enumerate(files):
        print(f"{i+1}: {f}")
    while True:
        try:
            idx = int(input("Выберите файл: ")) - 1
            if 0 <= idx < len(files):
                return os.path.join(folder, files[idx])
            else:
                print("Некорректный номер. Попробуйте снова.")
        except ValueError:
            print("Введите число.")

# Функция для загрузки хостов из YAML файла
def load_hosts_from_yaml(filepath):
    with open(filepath, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if "servers" not in data:
        logger.error(f"В файле {filepath} нет ключа 'servers'")
        print(f"Ошибка: в файле нет ключа 'servers'")
        sys.exit(1)
    return data["servers"]

# Функция для выполнения команд на сервере
def execute_commands_on_server(host, username, password, commands):
    try:
        with paramiko.SSHClient() as client:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(host, port=22, username=username, password=password, timeout=5)
            logger.info(f"Подключение к серверу {host}")

            for command in commands:
                match = re.match(r"^\s*sudo\s+(.*)", command)
                if match:
                    sudo_cmd = match.group(1)
                    full_command = f"echo {password} | sudo -S -p '' {sudo_cmd}"
                else:
                    full_command = command

                stdin, stdout, stderr = client.exec_command(full_command, get_pty=True)
                output = stdout.read().decode()
                error = stderr.read().decode()

                if error and "password" not in error.lower() and "пароль" not in error.lower():
                    logger.warning(f"[{host}] Не удалось выполнить команду: {command}\nОшибка: {error.strip()}")
                else:
                    logger.info(f"[{host}] Команда успешно выполнена: {command}")
                    logger.info(f"Результат от сервера {host}:\n{output}")
        return True
    
    except paramiko.AuthenticationException:
        logger.error(f"[{host}] Ошибка авторизации (неверный логин/пароль).")
        return False

    except Exception as e:
        logger.error(f"Ошибка на сервере {host}: {e}")
        return False

# Основная часть скрипта
if __name__ == "__main__":
    folder = os.path.join(".", "servers")
    if not os.path.isdir(folder):
        logger.error(f"Папка {folder} не найдена.")
        sys.exit(1)
    filepath = choose_file(folder)
    hosts = load_hosts_from_yaml(filepath)
    username = input("Введите имя пользователя: ")
    password = getpass.getpass("Введите пароль: ")
    commands = []
    print("Введите команды (пустая строка для завершения):")
    while True:
        cmd = input("> ")
        if not cmd:
            logger.warning("Не введено ни одной команды. Завершение работы.")
            break
        commands.append(cmd)
    if not commands:
        logger.warning("Не введено ни одной команды. Завершение работы.")
        sys.exit(1)
        
    # Параллельное выполнение
    results = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        future_to_host = {executor.submit(execute_commands_on_server, host, username, password, commands): host for host in hosts}
        for future in tqdm(as_completed(future_to_host), total=len(hosts), desc="Выполнение команд"):
            host = future_to_host[future]
            try:
                result = future.result()
                results.append((host, result))
            except Exception as exc:
                logger.error(f"[{host}] Ошибка выполнения: {exc}")
