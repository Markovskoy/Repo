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
    with open(filepath, encoding="uf-8") as f:
        data = yaml.safe_load(f)
    if "servers" not in data:
        print("В файле нет ключа 'servers'")
        sys.exit(1)
    return data['servers']

servers = load_servers('./servers/servers.yaml')
print(servers)