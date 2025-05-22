import paramiko
import logging

# Настройка логирования
logging.getLogger("paramiko").setLevel(logging.CRITICAL)

# Настройка логирования только для твоих сообщений
logging.basicConfig(filename="result.txt", level=logging.INFO, format="%(asctime)s - %(message)s", encoding="utf-8")

def execute_command_on_server(host, username, password, command):
    try:
        with paramiko.SSHClient() as client:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(host, port=22, username=username, password=password, timeout=5)

            logging.info(f"Подключение к серверу {host}")
            print(f"Подключение к серверу {host}")

            stdin, stdout, stderr = client.exec_command(f"echo {password} | sudo -S -p '' {command}", get_pty=True)
            
            output = stdout.read().decode()
            error = stderr.read().decode()

            if error and "пароль" not in error.lower():
                logging.error(f"Ошибка на сервере {host}: {error}")
                print(f"Ошибка на сервере {host}: {error}")
            else:
                logging.info(f"Результат от сервера {host}:\n{output}")
                print(f"Результат от сервера {host}:\n{output}")

    except paramiko.ssh_exception.NoValidConnectionsError as e:
        logging.error(f"Не удалось подключиться к {host}: {e}")
        print(f"Не удалось подключиться к {host}: {e}")
    except Exception as e:
        logging.error(f"Ошибка на сервере {host}: {e}")
        print(f"Ошибка на сервере {host}: {e}")

def run_ssh_commands(hosts, username, password, command):
    for host in hosts:
        execute_command_on_server(host, username, password, command)

# Входные данные
hosts = ["10.13.192.10"
]
     
username = "markovskoy_vv"
#password = getpass.getpass("Введите пароль: ")
password = "GGg123321gGG!!"
#command = "echo -e 'проверка добавления' | sudo tee -a /home/markovskoy_vv/test && cat /home/markovskoy_vv/test"
#command = input("Введите команду Linux: ")
command = "crontab -l | grep USE_OR"
# Запуск
run_ssh_commands(hosts, username, password, command)