# repo

## Описание

Этот репозиторий содержит рабочие скрипты (`work_scripts`), которые я использую на работе (делал на работе), а также пет-проекты (`pet_project`). 
Ниже приведено описание структуры и назначения основных папок.

---

## Структура репозитория

## Описание папок

### `work_scripts/`

#### **bash_scripts/**
Содержит bash-скрипты для мониторинга и автоматизации.  
Примеры:
- `CLI.sh` — мониторинг состояния задач через SQL и отправка результатов в Zabbix.
- `khd.sh` — мониторинг отчетов и ETL-процессов с отправкой статусов в Zabbix.

#### **python_scripts/**

- **command_to_server/**  
  Скрипт для параллельного выполнения команд на нескольких Linux-серверах по SSH.  
  Серверы задаются в YAML-файле с IP и портами.  
  Пример запускаемого скрипта:

  ```python
  # com_to_serv.py — выполнение команд на нескольких серверах
  import paramiko
  from concurrent.futures import ThreadPoolExecutor
  # ... (см. полный код в [com_to_serv.py](work_scripts/python_scripts/command_to_server/com_to_serv.py))

docker_server_for_test/
Docker Compose-файлы и Dockerfile для развёртывания тестовых SSH-серверов с фиксированными IP-адресами в одной сети.
Каждый контейнер получает свой IP в сети 172.30.0.0/16 и пробрасывает порт наружу.
# docker-compose.yml — пример описания сети и сервисов
version: "3.9"
services:
  ssh1:
    build: ./servers
    networks:
      net:
        ipv4_address: 172.30.0.10
    ports:
      - "2222:22"
  # ...
networks:
  net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.30.0.0/16

sql_scripts/
Папка для SQL-скриптов (пока пуста).

powershell_scripts/
Папка для PowerShell-скриптов (пока пуста).

pet_project/
Папка для пет-проектов (пока только структура, проекты будут добавляться в будущем).

Примеры
Bash-скрипт мониторинга с SQL-запросом
Скрипт для выполнения команд на нескольких Linux-серверах
Docker Compose для тестовых SSH-серверов с фиксированными IP
TODO
Добавить новые пет-проекты в pet_project/
Расширить коллекцию SQL- и PowerShell-скриптов