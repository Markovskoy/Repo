# Проверка наличия необходимых библиотек
import subprocess
import sys

REQUIRED_PACKAGES = {
    "pyyaml": "yaml",
    "paramiko": "paramiko",
    "tqdm": "tqdm"
}

def check_packages():
    import importlib
    missing = []
    for pip_name, import_name in REQUIRED_PACKAGES.items():
        try:
            importlib.import_module(import_name)
        except ImportError:
            missing.append(pip_name)
    if missing:
        print(f"Устанавливаю недостающие библиотеки: {', '.join(missing)}")
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
from datetime import datetime
import re
import signal


# Настройка логирования
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
        print(f"{i+1}: {f}\n")
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
        logger.error(f"В файле некорректный формат: нет ключа 'servers'")
        sys.exit(1)
    
    hosts = []
    for entry in data["servers"]:
        parts = entry.strip().split()
        if len(parts) != 2:
            logger.error(f"Неверный формат записи сервера: {entry}")
            print(f"Ошибка: неверный формат записи сервера: {entry}")
            sys.exit(1)
        host = parts[0]
        try:
            port = int(parts[1])
        except ValueError:
            logger.error(f"Порт должен быть числом: {parts[1]}")
            print(f"Ошибка: порт должен быть числом: {parts[1]}")
            sys.exit(1)
        hosts.append({"host": host, "port": port})
    return hosts

connection_logged = {}
# Функция для выполнения команд на сервере
def execute_commands_on_server(host, port, username, password, command):
    global connection_logged
    try:
        with paramiko.SSHClient() as client:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(host, port, username=username, password=password, timeout=5)
            
            key = f"{host}:{port}"
            if not connection_logged.get(key):
                logger.info(f"Подключение к серверу {host}...")
                logger.info(f"Подключение успешно {host}...")
                connection_logged[key] = True

            for com in command:
                match = re.match(r"^\s*sudo\s+(.*)", com)
                if match:
                    sudo_cmd = match.group(1)
                    full_command = f"echo {password} | sudo -S -p '' {sudo_cmd}"
                else:
                    full_command = com

                stdin, stdout, stderr = client.exec_command(full_command, get_pty=True)
                output = stdout.read().decode()
                error = stderr.read().decode()

                if error and "password" not in error.lower() and "пароль" not in error.lower():
                    logger.warning(f"[{host}] Не удалось выполнить команду: {com}\nОшибка: {error.strip()}")
                else:
                    logger.info(f"[{host}] Команда успешно выполнена: {com}")
                    logger.info(f"Результат от сервера {host}:\n{output}")
        return True
    except paramiko.AuthenticationException:
        logger.error(f"[{host}] Ошибка авторизации (неверный логин/пароль).")
        sys.exit(1)
        return False
    except paramiko.SSHException as e:
        logger.error(f"[{host}:{port}] SSH ошибка: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Ошибка на сервере {host}: {e}")
        sys.exit(1)
        return False

# Основная часть скрипта
def main():
    global logger
    logger = setup_logging()
    folder = os.path.join(".", "servers")
    if not os.path.isdir(folder):
        logger.error(f"Папка {folder} не найдена.")
        sys.exit(1)
    filepath = choose_file(folder)
    hosts = load_hosts_from_yaml(filepath)
    username = input("Введите имя пользователя: ")
    password = getpass.getpass("Введите пароль: ")
    print("Введите команду. Для выхода введите 'exit' или пустую строку.")

    while True:
        command = input("> ").strip()
        if command.lower() == "exit" or command == "":
            print("Завершение работы.")
            break

        success_count = 0
        fail_count = 0

        # Парарелельное выполнение команд
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_host = {
                executor.submit(execute_commands_on_server, host_info['host'], host_info['port'], username, password, [command]): host_info 
                for host_info in hosts
            }

            for future in tqdm(as_completed(future_to_host), total=len(hosts), desc=f"Команда: {command[:20]}..." if len(command) > 20 else f"Команда: {command}"):
                host = future_to_host[future]
                try:
                    result = future.result()
                    if result:
                        success_count += 1
                    else:
                        fail_count += 1
                except Exception as exc:
                    logger.error(f"[{host['host']}] Ошибка выполнения: {exc}")
                    fail_count += 1
        if fail_count > 0:
            logger.warning(f"Команда '{command}' выполнена на {success_count} серверах, не выполнена на {fail_count} серверах.")
        else:
            logger.info(f"Команда '{command}' выполнена на всех серверах.")

if __name__ == "__main__":
    main()