from modules.auth import get_username_and_password
from modules.log import setup_logger
from modules.ui import choose_yaml_file, select_files_from_folder
from modules.ssh_utils import check_ssh_and_sudo, execute_command
from modules.transfer import send_file

import yaml
import signal
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

logger = setup_logger()

# === Обработка сигналов ===
def graceful_exit(signum, frame):
    print("\nЗавершение работы, закрытие соединений...")
    logger.info("Скрипт завершён пользователем.")
    sys.exit(0)

signal.signal(signal.SIGINT, graceful_exit)

# === Загрузка серверов из YAML ===
def load_hosts_from_yaml(filepath):
    with open(filepath, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if "servers" not in data:
        logger.error("В файле нет ключа 'servers'")
        sys.exit(1)
    hosts = []
    for entry in data["servers"]:
        parts = entry.strip().split()
        if len(parts) != 2 or not parts[1].isdigit():
            logger.error(f"Неверный формат строки: {entry}")
            sys.exit(1)
        hosts.append({"host": parts[0], "port": int(parts[1])})
    return hosts

# === Главное меню ===
def main_menu(servers, username, password):
    while True:
        print("""
1. Отправить файлы на сервера
2. Выполнить команду на серверах
0. Выход
        """)
        choice = input("Введите номер действия: ").strip()
        if choice == "1":
            files = select_files_from_folder("to_remote")
            if not files:
                continue
            remote_path = input("Куда отправить файлы на сервере (например, /usr/local/bin): ").strip()
            for server in servers:
                for file_path in files:
                    send_file(username, server['host'], file_path, remote_path, password, logger)
        elif choice == "2":
            command = input("Введите команду: ").strip()
            if not command:
                continue
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = {
                    executor.submit(execute_command, s['host'], s['port'], username, password, command, logger): s
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
    filepath = choose_yaml_file("servers")
    servers = load_hosts_from_yaml(filepath)
    username, password = get_username_and_password()
    accessible = check_ssh_and_sudo(servers, username, password, logger)
    if not accessible:
        logger.warning("Нет доступных серверов для работы.")
        sys.exit(1)
    main_menu(accessible, username, password)

if __name__ == "__main__":
    main()