
![Language](https://img.shields.io/badge/language-Bash%2C%20Python%2C%20SQL-blue)
![Purpose](https://img.shields.io/badge/type-Portfolio-important)
![Status](https://img.shields.io/badge/status-Demo-lightgrey)
![Updated](https://img.shields.io/github/last-commit/Markovskoy/Repo)
![Size](https://img.shields.io/github/repo-size/Markovskoy/Repo)



## Описание

Этот репозиторий содержит рабочие скрипты (`work_scripts`), которые я использую на работе (или писал для работы), а также пет-проекты (будущие) (`pet_project`). 
Ниже подробно описана структура и назначение основных папок.

---

## Структура репозитория

```
pet_project/
    Main_pet_project/
    mini_pet_project/
work_scripts/
    bash_scripts/
    powershell_scripts/
    python_scripts/
        command_to_server/
        docker_server_for_test/
    sql_scripts/
```

---

## Описание папок

### `work_scripts/`

#### **bash_scripts/**
Скрипты для мониторинга и автоматизации, часто с использованием SQL-запросов и интеграцией с Zabbix.

**Примеры:**
- `CLI.sh` — мониторинг состояния задач через SQL и отправка результатов в Zabbix.
- `khd.sh` — мониторинг отчетов и ETL-процессов с отправкой статусов в Zabbix.

#### **python_scripts/**

- **command_to_server/**  
  Скрипт для параллельного выполнения команд на нескольких Linux-серверах по SSH.  
  Серверы задаются в YAML-файле с IP и портами.

  **Пример:**
  ```python
  # com_to_serv.py — выполнение команд на нескольких серверах
  import paramiko
  from concurrent.futures import ThreadPoolExecutor
  # ... (см. полный код в [com_to_serv.py](work_scripts/python_scripts/command_to_server/com_to_serv.py))
  ```

- **docker_server_for_test/**  
  Docker Compose-файлы и Dockerfile для развёртывания тестовых SSH-серверов с фиксированными IP-адресами в одной сети (network).  
  Каждый контейнер получает свой IP в сети `172.30.0.0/16` и пробрасывает порт наружу.

  **Пример:**
  ```yaml
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
  ```

#### **sql_scripts/**
Папка для SQL-скриптов (пока пуста, но планируется наполнение).

#### **powershell_scripts/**
Папка для PowerShell-скриптов (пока пуста, но планируется наполнение).

---

### `pet_project/`

Папка для пет-проектов (пока только структура, проекты будут добавляться в будущем).

---

## Примеры

### Bash-скрипт мониторинга с SQL-запросом

```bash
# work_scripts/bash_scripts/khd.sh
$ORACLE_HOME/sqlplus -silent "$bduser/$bdauth@$DBSID" <<EOF
select ... from ...;
EOF
# Отправка результата в Zabbix
```

### Скрипт для выполнения команд на нескольких Linux-серверах

```python
# work_scripts/python_scripts/command_to_server/com_to_serv.py
from concurrent.futures import ThreadPoolExecutor
import paramiko
# ... (см. полный код в файле)
```

### Docker Compose для тестовых SSH-серверов с фиксированными IP

```yaml
# work_scripts/python_scripts/docker_server_for_test/docker-compose.yml
services:
  ssh1:
    networks:
      net:
        ipv4_address: 172.30.0.10
  ssh2:
    networks:
      net:
        ipv4_address: 172.30.0.11
  # ...
networks:
  net:
    ipam:
      config:
        - subnet: 172.30.0.0/16
```

---

## TODO

- Добавить новые пет-проекты в `pet_project/`
- Расширить коллекцию SQL- и PowerShell-скриптов

---

> Для подробностей см. соответствующие файлы в папках.
