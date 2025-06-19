FROM ubuntu:22.04

# Установка SSH-сервера, Python3 и pip
RUN apt-get update && apt-get install -y openssh-server python3 python3-pip mc && \
    mkdir /var/run/sshd && \
    # Установка пароля root: root
    echo 'root:root' | chpasswd && \
    # Разрешаем вход под root по паролю
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    # Отключаем pam_loginuid
    sed -i 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' /etc/pam.d/sshd && \
    useradd -m -s /bin/bash victor && \
    echo "victor:password" | chpasswd && \
    usermod -aG sudo victor

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]
