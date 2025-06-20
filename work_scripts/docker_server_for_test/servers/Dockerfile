FROM ubuntu:20.04

# Аргументы сборки
ARG USERNAME=victor
ARG PASSWORD=123321
ARG CREATE_USER=true

ENV DEBIAN_FRONTEND=noninteractive

# Обновление и установка SSH
RUN apt-get update && apt-get install -y \
    openssh-server \
    sudo \
    net-tools \
    iputils-ping \
    vim \
    less \
    zip \
    python3 \
    python3-pip \
    mc \
    && rm -rf /var/lib/apt/lists/*

# Создание пользователя (если CREATE_USER=true)
RUN if [ "$CREATE_USER" = "true" ]; then \
      useradd -ms /bin/bash $USERNAME && \
      echo "$USERNAME:$PASSWORD" | chpasswd && \
      usermod -aG sudo $USERNAME && \
      mkdir -p /home/$USERNAME/.ssh && \
      chown -R $USERNAME:$USERNAME /home/$USERNAME/.ssh; \
    fi

# Подготовка SSH
RUN mkdir /var/run/sshd

# Разрешение root входа и входа по паролю
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Установка hostname через переменную окружения (при запуске)
ENV HOSTNAME=default-host
RUN echo "$HOSTNAME" > /etc/hostname

# Старт SSH
EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
