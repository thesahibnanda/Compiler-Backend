import os
import time
import subprocess
import resource
from config import Config

class DockerUtils:

    @staticmethod
    def execute_python3(image: str, memory: int, time_limit: int, file_path: str, cpus: int, processes: int, stdin: str):
        command = [
            "docker",
            "run",
            "--rm",
            "--memory", f"{memory}m",
            "--cpus", str(cpus),
            "--pids-limit", str(processes),
            "-v", f"{os.path.join(os.getcwd(), Config.TEMP_FOLDER_TO_READ)}:/{Config.DOCKER_FOLDER_TO_READ}:ro",
            "--network", "none",
            "--user", "nobody",
            image,
            "bash", "-c",
            f"echo \"{stdin}\" | timeout {time_limit}s python3 /{Config.DOCKER_FOLDER_TO_READ}/{file_path.split('/')[-2]}/{file_path.split('/')[-1]}"
        ]

        try:
            start_time = time.time()
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=time_limit
            )
            elapsed_time = time.time() - start_time
            peak_memory_usage_mb = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024

            if result.returncode == 0:
                return result.stdout.strip(), elapsed_time, peak_memory_usage_mb
            elif result.returncode == 124:
                return "Time Limit Exceeded"
            elif peak_memory_usage_mb > memory or result.returncode == 137:
                return "Memory Limit Exceeded"
            else:
                return f"Error Code: {result.returncode}\n{result.stderr.strip() if result.stderr else 'Unknown error'}"
        
        except subprocess.TimeoutExpired:
            return "Time Limit Exceeded"
        except subprocess.CalledProcessError as e:
            return f"Error Code: {e.returncode}\n{e.stderr.strip() if e.stderr else 'Unknown error'}"
        except Exception as e:
            return f"Unexpected Error: {str(e)}"

    @staticmethod
    def compile_cpp(image: str, memory: int, time_limit: int, file_path: str, cpus: int, processes: int, version: str = Config.DEFAULT_CPP_VERSION):
        if version not in Config.CPP_VERSIONS:
            return f"Invalid C++ Version. Allowed Versions Are: {', '.join(Config.CPP_VERSIONS)}"

        try:
            base_dir = os.path.basename(os.path.dirname(file_path))
            file_name = os.path.basename(file_path).split(".")[0] + ".out"
            output_dir = f"/{Config.DOCKER_FOLDER_TO_WRITE}/{base_dir}"
            output_path = f"{output_dir}/{file_name}"
        except Exception:
            return "Error in constructing paths for compilation."

        command = (
            f"mkdir -p {output_dir} && "
            f"timeout {time_limit}s g++ --std={version} "
            f"/{Config.DOCKER_FOLDER_TO_READ}/{file_path.split('/')[-2]}/{file_path.split('/')[-1]} -o {output_path}"
        )

        docker_command = [
            "docker",
            "run",
            "--rm",
            "--memory", f"{memory}m",
            "--cpus", str(cpus),
            "--pids-limit", str(processes),
            "-v", f"{os.path.join(os.getcwd(), Config.TEMP_FOLDER_TO_READ)}:/{Config.DOCKER_FOLDER_TO_READ}:ro",
            "-v", f"{os.path.join(os.getcwd(), Config.TEMP_FOLDER_TO_WRITE)}:/{Config.DOCKER_FOLDER_TO_WRITE}",
            "--network", "none",
            "--user", "nobody",
            image,
            "bash", "-c",
            command
        ]

        try:
            result = subprocess.run(
                docker_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=time_limit
            )
            peak_memory_usage_mb = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024

            if result.returncode == 0:
                return output_path
            elif result.returncode == 124:
                return "Time Limit Exceeded During Compilation"
            elif peak_memory_usage_mb > memory or result.returncode == 137:
                return "Memory Limit Exceeded During Compilation"
            else:
                return f"Compilation Error: {result.stderr if result.stderr else ''}"
        
        except subprocess.TimeoutExpired:
            return "Time Limit Exceeded During Compilation"
        except subprocess.CalledProcessError as e:
            return f"Compilation Error: {e.returncode}\n{e.stderr if e.stderr else ''}"
        except Exception as e:
            return str(e)

    @staticmethod
    def execute_cpp(image: str, memory: int, time_limit: int, cpus: int, processes: int, path: str, stdin: str):
        if not (os.path.isabs(path) and path.endswith(".out")):
            return f"Invalid executable path: {path}"
        command = [
            "docker",
            "run",
            "--rm",
            "--memory", f"{memory}m",
            "--cpus", str(cpus),
            "--pids-limit", str(processes),
            "-v", f"{os.path.join(os.getcwd(), Config.TEMP_FOLDER_TO_WRITE)}:/{Config.DOCKER_FOLDER_TO_WRITE}:ro",
            "--network", "none",
            "--user", "nobody",
            image,
            "bash", "-c",
            f"echo \"{stdin}\" | timeout {time_limit}s /{Config.DOCKER_FOLDER_TO_WRITE}/{path.split('/')[-2]}/{path.split('/')[-1]}"
        ]

        try:
            start_time = time.time()

            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=time_limit
            )
            elapsed_time = time.time() - start_time
            peak_memory_usage_mb = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024

            if result.returncode == 0:
                return result.stdout.strip(), elapsed_time, peak_memory_usage_mb
            elif result.returncode == 124:
                return "Time Limit Exceeded During Execution"
            elif peak_memory_usage_mb > memory or result.returncode == 137:
                return "Memory Limit Exceeded During Execution"
            else:
                return f"Runtime Error: {result.stderr.strip() if result.stderr else 'Unknown error'}"
        
        except subprocess.TimeoutExpired:
            return "Time Limit Exceeded During Execution"
        except subprocess.CalledProcessError as e:
            return f"Runtime Error: {e.returncode}\n{e.stderr.strip() if e.stderr else 'Unknown error'}"
        except Exception as e:
            return f"Unexpected Error: {str(e)}"