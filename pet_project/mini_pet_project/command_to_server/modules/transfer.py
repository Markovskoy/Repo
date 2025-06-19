# modules/transfer.py

import os
import shutil
import subprocess
import paramiko

def send_file(username: str, host: str, local_path: str, remote_path: str, password: str, logger):
    to_send = local_path
    cleanup = False
    unpack_remote = False
    archive_name = ""

    if os.path.isdir(local_path):
        base_name = os.path.basename(local_path.rstrip('/'))
        archive_name = f"/tmp/{base_name}.tar.gz"
        shutil.make_archive(f"/tmp/{base_name}", 'gztar', root_dir=os.path.dirname(local_path), base_dir=base_name)
        to_send = archive_name
        cleanup = True
        unpack_remote = True

    if password and shutil.which("sshpass"):
        cmd = ["sshpass", "-p", password, "scp", "-o", "StrictHostKeyChecking=no", to_send, f"{username}@{host}:{remote_path}"]
    else:
        cmd = ["scp", "-o", "StrictHostKeyChecking=no", to_send, f"{username}@{host}:{remote_path}"]

    try:
        logger.info(f"Отправка {to_send} на {host}:{remote_path}...")
        subprocess.run(cmd, check=True)
        logger.info(f"[OK] Файл отправлен на {host}")

        if unpack_remote:
            archive_remote = os.path.join(remote_path, os.path.basename(to_send))
            unpack_cmds = [
                f"tar -xzf {archive_remote} -C {remote_path}",
                f"rm {archive_remote}"
            ]
            with paramiko.SSHClient() as ssh:
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(hostname=host, username=username, password=password, timeout=5)
                for cmd in unpack_cmds:
                    stdin, stdout, stderr = ssh.exec_command(cmd)
                    if err := stderr.read().decode().strip():
                        logger.warning(f"[{host}] Ошибка распаковки: {err}")
                ssh.close()
    except subprocess.CalledProcessError as e:
        logger.error(f"Не удалось отправить файл на {host}: {e}")
    except Exception as e:
        logger.error(f"Не удалось распаковать архив на {host}: {e}")
    finally:
        if cleanup and os.path.exists(to_send):
            os.remove(to_send)