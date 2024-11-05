# Start with an Ubuntu base image
FROM ubuntu:latest
# Update the package list and install system dependencies
RUN apt update && apt install -y \
    g++ \
    build-essential \
    python3 \
    python3-pip \
    python3-venv \
    && apt clean
# Get the GCC version and install the appropriate libstdc++-X-dev package
# For example, for GCC 10, install libstdc++-10-dev
RUN gcc_version=$(gcc -dumpversion | cut -f1 -d.) && \
    apt install -y libstdc++-${gcc_version}-dev
# Set the working directory inside the container
WORKDIR /app
# Copy the FastAPI app code and requirements file into the container
COPY . /app
# Create a virtual environment for Python and activate it
RUN python3 -m venv /app/venv
# Activate the virtual environment and install dependencies from requirements.txt
RUN /app/venv/bin/pip install --no-cache-dir -r requirements.txt
# Expose the port that Gunicorn will run on
EXPOSE 8000
# Run Gunicorn with Uvicorn worker for FastAPI using the virtual environment
CMD ["/app/venv/bin/gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "--threads", "4", "--worker-connections", "1000", "--max-requests", "1000", "--timeout", "60", "--keep-alive", "10", "app:app"]