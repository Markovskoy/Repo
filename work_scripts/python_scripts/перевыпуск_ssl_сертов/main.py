import os
import sys
import zipfile
import getpass
import subprocess
import shutil
import textwrap
import pathlib
import socket
import re
import collections

# === Проверка зависимостей ===
missing = []
try:
    import yaml
except ImportError:
    missing.append("pyyaml")
try:
    import paramiko
except ImportError:
    missing.append("paramiko")
try:
    from tqdm import tqdm
except ImportError:
    missing.append("tqdm")

if missing:
    print("[ОШИБКА] Не найдены библиотеки: " + ", ".join(missing))
    print("Установите зависимости командой:\n\npip install -r requirements.txt\n")
    sys.exit(1)

def load_servers(filepath):
    with open(filepath, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if "servers" not in data:
        print("В файле нет ключа 'servers'")
        sys.exit(1)
    return data['servers']

def get_hostname(ip, port, username, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(hostname=ip, port=port, username=username, password=password, timeout=10)
        stdin, stdout, stderr = client.exec_command("hostname -f")
        output = stdout.read().decode().strip()
        client.close()
        return output
    except Exception as e:
        print(f"[Ошибка] не удалось подключиться к {ip}:{port} - {e}")
        return None


def menu():
    print("""
Выберите действие:
1. Сгенерировать файл запроса сертификата
2. Применить подписанный сертификат""")
    choise = input()
    return choise.strip()


def main():
    servers = load_servers("./servers/servers.yaml")
    print(f"Сервера загружены: {servers}")

    username = input("Введите логин для SSH:")
    password = getpass.getpass("Введите пароль для SSH:")
    
    for line in servers:
        ip, port = line.strip().split()
        hostname = get_hostname(ip, int(port), username, password)
        if hostname:
            print(f"{ip}:{port} -> DNS:{hostname}")
        else:
            print(f"DNS не получен с {ip}")

    choise = menu()
    if choise == "1":
        print("Генерация CA")
    elif choise == "2":
        print("Применение серта")
    else:
        print("Неверная цифра")

if __name__ == "__main__":
    main()