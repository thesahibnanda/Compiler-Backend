import subprocess
import sys
import os
import platform
from config import Config

def step0():
    try:
        print("Checking if Docker is installed...")
        subprocess.run(["docker", "--version"], stdout=sys.stdout, stderr=sys.stderr, check=True)
        print("Docker is already installed.")
    except subprocess.CalledProcessError:
        print("Docker is not installed. Attempting to install Docker...")
        try:
            system_platform = platform.system()

            if system_platform == "Linux":
                subprocess.run(
                    [
                        "sudo", "apt-get", "update"
                    ], stdout=sys.stdout, stderr=sys.stderr, check=True
                )
                subprocess.run(
                    [
                        "sudo", "apt-get", "install", "-y", "docker.io"
                    ], stdout=sys.stdout, stderr=sys.stderr, check=True
                )
                print("Docker installed successfully on Linux.")
            elif system_platform == "Darwin":
                # Instructions for macOS (Darwin)
                print("Please install Docker manually on macOS from https://docs.docker.com/docker-for-mac/")
                sys.exit(1)
            elif system_platform == "Windows":
                print("Please install Docker manually on Windows from https://docs.docker.com/docker-for-windows/")
                sys.exit(1)
            else:
                print(f"Unsupported platform: {system_platform}. Please install Docker manually.")
                sys.exit(1)
        except Exception as e:
            print(f"Failed to install Docker: {e}")
            sys.exit(1)
            
def step1():
    try:
        print("Making Temp Folders")
        os.makedirs(Config.TEMP_FOLDER_TO_READ, exist_ok=True)
        os.makedirs(Config.TEMP_FOLDER_TO_WRITE, exist_ok=True)
        print("Temp folders created successfully.")
    except Exception as e:
        print(f"Making Of Temp Folders Failed: {e}")
        sys.exit(1)

    
def step2():
    try:
        print("Building Docker image...")
        result = subprocess.run(
            ["docker", "build", "-t", Config.DOCKER_IMAGE_NAME, "-f", "Dockerfile.sandbox", "."],
            stdout=sys.stdout,
            stderr=sys.stderr,
            check=True
        )
        if result.returncode == 0:
            print("Docker image built successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred during Docker build: {e}")
        sys.exit(1)

def step3():

    try:
        print("Starting Gunicorn server...")
        subprocess.run(
            [
                "gunicorn", 
                "-w", "4", 
                "-k", "uvicorn.workers.UvicornWorker", 
                "-b", "0.0.0.0:8000", 
                "--threads", "4", 
                "--worker-connections", "1000", 
                "--max-requests", "1000", 
                "--timeout", "60", 
                "--keep-alive", "10", 
                "app:app"
            ],
            stdout=sys.stdout,
            stderr=sys.stderr,
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while starting Gunicorn: {e}")
        sys.exit(1)

if __name__ == "__main__":
    step0()
    step1()
    step2()
    step3()