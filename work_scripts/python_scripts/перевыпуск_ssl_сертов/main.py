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

def find_all_app(app1_name, username, password, port=22, max_apps=5):
    cluster = {}

    def connect_and_get_ip(hostname):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=hostname, port=port, username=username, password=password, timeout=5)
        stdin, stdout, stderr = client.exec_command("hostname -I")
        ip = stdout.read().decode().strip().split()[0]  # берём первый IP
        client.close()
        return ip

    try:
        # Добавляем app1
        ip1 = connect_and_get_ip(app1_name)
        cluster['app1'] = {'hostname': app1_name, 'ip': ip1}
        print(f"[+] Обнаружен: {app1_name} → {ip1}")
    except Exception as e:
        print(f"[-] Не удалось подключиться к {app1_name}: {e}")
        return cluster

    base = app1_name.replace('app1', 'app{}')

    for i in range(2, max_apps + 1):
        hostname_try = base.format(i)
        try:
            ip = connect_and_get_ip(hostname_try)
            cluster[f'app{i}'] = {'hostname': hostname_try, 'ip': ip}
            print(f"[+] Обнаружен: {hostname_try} → {ip}")
        except Exception as e:
            print(f"[-] Не удалось подключиться к {hostname_try}: {e}")
            break
    return cluster

def generate_csr_on_app1(cluster,username, password):
    app1 = cluster.get('app1')
    if not app1:
        print("[Ошибка] В кластере нет app1")
        return
    hostname = app1['hostname']
    ip = app1['ip']
    port = 22

    # подключаемся
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(hostname=ip, port=port, username=username, password=password, timeout=10)
    except Exception as e:
        print(f"[ОШИБКА] Не удалось подключиться к APP1 ({hostname}) → {e}")
        return
    
    def run_sudo_command(cmd):
        stdin, stdout, stderr = client.exec_command(f"sudo -S -p '' {cmd}", get_pty=True)
        stdin.write(password + '\n')
        stdin.flush()
        out = stdout.read().decode()
        err = stderr.read().decode()
        return out, err

    # === Получаем короткое имя ===
    stdin, stdout, stderr = client.exec_command("hostname")
    shortname = stdout.read().decode().strip()

    print(f"[i] Генерация CSR для: {shortname}")

     # === Шаги выполнения ===
    commands = [
        "mkdir -p /root/keys",
        f"cd /root/keys && sudo openssl req -new -config openssl_srv.cnf -key private.key -out s{shortname}.ru.csr",
        f"cd /root/keys && zip dns_{shortname}.zip s{shortname}.ru.csr openssl_srv.cnf"
        f"sudo cp /root/keys/dns_{shortname}.zip /tmp/dns_{shortname}.zip",
        f"sudo chmod 644 /tmp/dns_{shortname}.zip"
    ]

    for cmd in commands:
        out, err = run_sudo_command(cmd)
        if err:
            print(f"[!] Ошибка при выполнении: {cmd}\n{err}")
        else:
            print(f"[+] Выполнено: {cmd}")
    
    # === Качаем архив себе ===
    local_ca_dir = pathlib.Path("CA")
    local_ca_dir.mkdir(exist_ok=True)

    sftp = client.open_sftp()
    remote_path = f"/tmp/dns_{shortname}.zip"
    local_path = str(local_ca_dir / f"dns_{shortname}.zip")
    try:
        sftp.get(remote_path, local_path)
        print(f"[✓] Архив скачан в: {local_path}")
    except Exception as e:
        print(f"[ОШИБКА] Не удалось скачать архив: {e}")
    finally:
        sftp.close()
        client.close()


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
        if not hostname:
            continue

        app1_name = hostname.split('.')[0]  # app1
        print(f"[+] Получено имя: {app1_name} от {ip}")

        cluster = find_all_app(app1_name, username, password, int(port))
        print("=== Обнаруженный кластер ===")
        for role, info in cluster.items():
            print(f"{role}: {info['hostname']}")

    choise = menu()
    if choise == "1":
        print("Генерация CA")
        generate_csr_on_app1(cluster, username, password)
    elif choise == "2":
        print("Применение серта")
    else:
        print("Неверная цифра")

if __name__ == "__main__":
    main()