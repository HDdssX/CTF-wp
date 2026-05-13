# Use a modern Ubuntu base image
FROM ubuntu:24.04

# Avoid prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies and tools for debugging
RUN apt-get update && apt-get install -y \
    libc6 \
    gdb \
    iproute2 \
    procps \
    git \
    python3-pip \
    python3-dev \
    libglib2.0-dev \
    wget \
    curl \
    vim \
    psmisc \
    && rm -rf /var/lib/apt/lists/*

# Install pwndbg
WORKDIR /opt
RUN git clone https://github.com/pwndbg/pwndbg && \
    cd pwndbg && \
    ./setup.sh

# Set working directory
WORKDIR /app

# Copy all firmware files into the container
COPY . /app

# Ensure binaries and scripts are executable, and move library to standard path
RUN chmod +x /app/http /app/mainproc /app/start.sh && \
    chmod +x /app/www/cgi-bin/*.cgi /app/www/cgi-bin/restart.sh && \
    cp /app/lib/libutils.so /usr/lib/libutils.so

# Expose the web server port
EXPOSE 80

# Start services via start.sh
CMD ["/app/start.sh"]
