FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN sed -i 's/archive.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list && \
    sed -i 's/security.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    libssl3 \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install flask

RUN useradd -r -s /usr/sbin/nologin neuralchat

RUN mkdir -p /opt/neuralchat/bin \
    /opt/neuralchat/run \
    /opt/neuralchat/logs \
    /opt/neuralchat/data/models \
    /opt/neuralchat/data/knowledge \
    /opt/neuralchat/downloads \
    /opt/neuralchat/plugins \
    /opt/neuralchat/frontend/templates \
    /opt/neuralchat/frontend/static

RUN chown -R root:neuralchat /opt/neuralchat && \
    chmod -R 750 /opt/neuralchat && \
    chmod 770 /opt/neuralchat/downloads && \
    chmod 770 /opt/neuralchat/data/knowledge && \
    chmod 770 /opt/neuralchat/run && \
    chmod 770 /opt/neuralchat/logs

COPY bin/engine /opt/neuralchat/bin/engine
RUN chmod +x /opt/neuralchat/bin/engine

COPY frontend/ /opt/neuralchat/frontend/

COPY init.sh /opt/neuralchat/init.sh
COPY plugins/ /opt/neuralchat/plugins/

RUN useradd -m ctf && \
    mkdir -p /home/ctf/dev && \
    mkdir -p /home/ctf/bin

RUN mknod /home/ctf/dev/null c 1 3 && \
    mknod /home/ctf/dev/zero c 1 5 && \
    mknod /home/ctf/dev/random c 1 8 && \
    mknod /home/ctf/dev/urandom c 1 9 && \
    chmod 666 /home/ctf/dev/*

COPY flag.txt /home/ctf/flag
RUN chmod 000 /home/ctf/flag && chown root:ctf /home/ctf/flag

RUN chmod -R 750 /home/ctf && \
    chown -R root:ctf /home/ctf

RUN chmod +x /opt/neuralchat/init.sh /opt/neuralchat/plugins/*.sh

RUN echo "#!/bin/bash\necho \"Running system diagnostics...\"\nls -l /opt/neuralchat/data/models" > /opt/neuralchat/plugins/diag.sh && \
    chmod +x /opt/neuralchat/plugins/diag.sh && \
    chown root:root /opt/neuralchat/plugins/diag.sh

COPY scripts/gen_model.py /tmp/gen_model.py
RUN python3 /tmp/gen_model.py && rm /tmp/gen_model.py

EXPOSE 5000

CMD ["/opt/neuralchat/init.sh"]
