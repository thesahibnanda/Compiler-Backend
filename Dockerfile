FROM ubuntu:22.04

# Install Docker, Python, and dependencies
RUN apt update && apt install -y \
    docker.io \
    python3 \
    python3-pip \
    python3-venv \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    && apt clean && rm -rf /var/lib/apt/lists/* \
    && python3 -m venv /venv

# Upgrade pip in the virtual environment
RUN /venv/bin/pip install --upgrade pip

# Install Docker Buildx
RUN mkdir -p ~/.docker/cli-plugins/ && \
    curl -L https://github.com/docker/buildx/releases/download/v0.10.5/buildx-v0.10.5.linux-amd64 > ~/.docker/cli-plugins/docker-buildx && \
    chmod +x ~/.docker/cli-plugins/docker-buildx

# Copy requirements to the container
COPY requirements.txt /requirements.txt

# Install Python dependencies
RUN /venv/bin/pip install -r /requirements.txt

# Copy the rest of the application files
COPY . .

# Expose the application port
EXPOSE 8000

# Start Docker daemon with `vfs` storage driver and run the setup script
CMD ["sh", "-c", "dockerd --storage-driver=vfs & sleep 5 && /venv/bin/python3 setup.py"]
