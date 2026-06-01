FROM ubuntu:24.04

RUN apt-get update && apt-get install -y socat build-essential

RUN useradd -d /home/ctf/ -m -p ctf -s /bin/bash ctf
RUN echo "ctf:ctf" | chpasswd

WORKDIR /home/ctf

COPY neural_link.c .
COPY Makefile .
COPY flag.txt .

RUN make
RUN chown -R root:ctf /home/ctf && chmod -R 750 /home/ctf && chmod 440 flag.txt

EXPOSE 5000

CMD ["socat", "TCP-LISTEN:5000,reuseaddr,fork,su=ctf", "EXEC:./neural_link,stderr"]
