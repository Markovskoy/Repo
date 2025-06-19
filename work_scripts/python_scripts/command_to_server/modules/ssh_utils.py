# modules/ssh_utils.py

import paramiko
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict


def check_ssh_and_sudo(servers: List[Dict], username: str, password: str, logger) -> List[Dict]:
    accessible = []
    inaccessible = []
    no_sudo = []

    def check_one(server):
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(server['host'], port=server['port'], username=username, password=password, timeout=5)
            stdin, stdout, stderr = client.exec_command("sudo -n true")
            if stdout.channel.recv_exit_status() != 0:
                stdin, stdout, stderr = client.exec_command("sudo -S -v")
                stdin.write(password + '\n')
                stdin.flush()
                if stdout.channel.recv_exit_status() != 0:
                    no_sudo.append(server)
                    return
            accessible.append(server)
            client.close()
        except Exception:
            inaccessible.append(server)

    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(check_one, servers)

    logger.info(f"Доступно по SSH и sudo: {len(accessible)} серверов")
    if inaccessible:
        logger.warning(f"Недоступны по SSH: {len(inaccessible)}")
        for s in inaccessible:
            logger.warning(f" - {s['host']}:{s['port']}")
    if no_sudo:
        logger.warning(f"Нет доступа к sudo: {len(no_sudo)}")
        for s in no_sudo:
            logger.warning(f" - {s['host']}:{s['port']}")

    return accessible


def execute_command(host: str, port: int, username: str, password: str, command: str, logger) -> bool:
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, port, username=username, password=password, timeout=5)

        full_command = f"echo '{password}' | sudo -S -p '' {command[len('sudo'):].strip()}" if command.strip().startswith("sudo") else command
        stdin, stdout, stderr = client.exec_command(full_command, get_pty=True)

        if command.strip().startswith("sudo"):
            stdin.write(password + "\n")
            stdin.flush()

        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()

        if output:
            logger.info(f"[{host}] Результат:\n{output}")
        if error:
            logger.warning(f"[{host}] Ошибка:\n{error}")

        client.close()
        return True
    except Exception as e:
        logger.error(f"[{host}] Ошибка подключения: {e}")
        return False