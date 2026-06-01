FROM ubuntu:22.04

RUN apt-get update && \
    apt-get install -y --no-install-recommends socat && \
    rm -rf /var/lib/apt/lists/* && \
    useradd -m -s /bin/sh ctf

WORKDIR /chal
COPY one_more_pwn /chal/one_more_pwn
COPY flag.txt /flag.txt
RUN chmod 555 /chal/one_more_pwn && chmod 644 /flag.txt

EXPOSE 36769
CMD ["socat", "-T", "120", \
     "TCP-LISTEN:36769,reuseaddr,fork", \
     "EXEC:/chal/one_more_pwn,su=ctf,stderr"]
