# Use an official Ubuntu base image
FROM ubuntu:22.04

# Set environment variables to ensure non-interactive installation
ENV DEBIAN_FRONTEND=noninteractive

# Update, install required packages, and clean up in one line
RUN apt-get update && \
	apt-get install -y docker.io python3 python3-pip python3-venv && \
	apt-get clean && \
	rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the entire project to the container
COPY . .

# Create a virtual environment and install dependencies
RUN python3 -m venv venv && ./venv/bin/pip install --no-cache-dir -r requirements.txt

# Run the setup script using Python from the virtual environment
CMD ["./venv/bin/python3", "setup.py"]
