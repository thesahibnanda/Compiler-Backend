import os
import pwd
import uuid
import json
import time
import shutil
import subprocess
import resource
from typing import List, Union, Tuple
from utils.RetryUtils import RetryUtils

CONFIG_FILE_PATH = os.path.join(os.getcwd(), 'config.json')

TIME_LIMIT_EXCEEDED = "Time Limit Exceeded"
MEMORY_LIMIT_EXCEEDED = "Memory Limit Exceeded"
ERROR_WHILE_COMPILATION = "Error While Compilation\n"
RUNTIME_ERROR = "Runtime Error\n"

class FileCreationError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

class FileDeleteError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

class ExecUtils:
    CONFIG = json.load(open(CONFIG_FILE_PATH, 'r'))

    
    @staticmethod
    def make_file(content: str, language: str) -> List[str]:       
        if language not in ExecUtils.CONFIG['ALLOWED_LANGUAGES']:
            raise FileCreationError(f'Language {language} not allowed')

        try:
            folder_name = str(uuid.uuid4())
            file_name = f"{uuid.uuid4()}.{ExecUtils.CONFIG['ALLOWED_LANGUAGES'][language]}"
            temp_folder_path = os.path.join(ExecUtils.CONFIG['TEMP_FOLDER'], folder_name)
            os.makedirs(temp_folder_path, exist_ok=True)
            file_path = os.path.join(temp_folder_path, file_name)

            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)

            return [ExecUtils.CONFIG['TEMP_FOLDER'], folder_name, file_name]
        except OSError as e:
            raise FileCreationError(f"File system error: {str(e)}")
        except Exception as e:
            raise FileCreationError(f"Unexpected error: {str(e)}")

    @staticmethod
    def delete_file(path: List[str]):
        try:
            file_path = os.path.join(*path)
            os.remove(file_path)
            dir_path = os.path.join(*path[:-1])
            shutil.rmtree(dir_path)
        except FileNotFoundError as e:
            raise FileDeleteError(f"File or directory not found: {str(e)}")
        except PermissionError as e:
            raise FileDeleteError(f"Permission denied: {str(e)}")
        except Exception as e:
            raise FileDeleteError(f"Unexpected error: {str(e)}")

    @staticmethod
    def execute_python(content: str, input_str: str, timeout: int, memory_mb: int, processes: int) -> Union[Tuple[str, float, float], str]:       
        file_path = RetryUtils.run_with_retry(
            ExecUtils.make_file, content, 'Python', try_limit=ExecUtils.CONFIG["TRY_LIMIT"], delay=ExecUtils.CONFIG["DELAY"]
        )

        try:
            command = ["python3", os.path.join(*file_path)]
            start_time = time.time()

            def set_limits():
                nobody = pwd.getpwnam("nobody")
                os.setgid(nobody.pw_gid)  
                os.setuid(nobody.pw_uid)
                resource.setrlimit(resource.RLIMIT_AS, (memory_mb * 1024 * 1024, memory_mb * 1024 * 1024))
                resource.setrlimit(resource.RLIMIT_NPROC, (processes, processes))

            
            
            result = subprocess.run(
                command,
                input=input_str,
                capture_output=True,
                text=True,
                timeout=timeout,
                preexec_fn=set_limits
            )
        

            elapsed_time = time.time() - start_time
            peak_memory_mb = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024

            if memory_mb < peak_memory_mb:
                return MEMORY_LIMIT_EXCEEDED
            if elapsed_time > timeout:
                return TIME_LIMIT_EXCEEDED
            if result.returncode == -6:
                return MEMORY_LIMIT_EXCEEDED
            if result.returncode == -9:
                return TIME_LIMIT_EXCEEDED
            if result.returncode != 0:
                result_error_list = result.stderr.split("\n")
                if len(result_error_list) > 1 and result_error_list[-2].split(" ")[0] in ["MemoryError", "MemoryError:"]:
                    return MEMORY_LIMIT_EXCEEDED
                print(result.returncode)
                return result.stderr

            return result.stdout, elapsed_time, peak_memory_mb
        except subprocess.TimeoutExpired:
            return TIME_LIMIT_EXCEEDED
        except MemoryError:
            return MEMORY_LIMIT_EXCEEDED
        except subprocess.CalledProcessError as e:
            print(e.returncode)
            return e.stderr
        except Exception as e:
            return str(e)
        finally:
            RetryUtils.run_with_retry(
                ExecUtils.delete_file, file_path, try_limit=ExecUtils.CONFIG["TRY_LIMIT"], delay=ExecUtils.CONFIG["DELAY"]
            )

    @staticmethod
    def execute_cpp(content: str, input_str: str, timeout: int, memory_mb: int, processes: int) -> Union[Tuple[str, float, float], str]:
        timeout+=0.5
        file_path = RetryUtils.run_with_retry(
            ExecUtils.make_file, content, 'C++', try_limit=ExecUtils.CONFIG["TRY_LIMIT"], delay=ExecUtils.CONFIG["DELAY"]
        )
        output_file_path = os.path.join(*file_path[:-1], file_path[-1].split('.')[0]) + '.out'

        def set_limits_exec():
            nobody = pwd.getpwnam("nobody")
            os.setgid(nobody.pw_gid)
            os.setuid(nobody.pw_uid)
            resource.setrlimit(resource.RLIMIT_AS, (memory_mb * 1024 * 1024, memory_mb * 1024 * 1024))
            resource.setrlimit(resource.RLIMIT_NPROC, (processes, processes))

        try:
            compile_command = ['g++', '--std=c++17', os.path.join(*file_path), '-o', output_file_path]
            
            compile_result = subprocess.run(
                compile_command,
                capture_output=True,
                text=True,
            )
            if compile_result.returncode != 0:
                return ERROR_WHILE_COMPILATION + compile_result.stderr
        except subprocess.CalledProcessError as e:
            return ERROR_WHILE_COMPILATION + e.stderr
        except Exception as e:
            return ERROR_WHILE_COMPILATION + str(e)

        try:
            start_time = time.time()
            exec_command = [output_file_path]
            exec_result = subprocess.run(
                exec_command,
                input=input_str,
                capture_output=True,
                text=True,
                timeout=timeout,
                preexec_fn=set_limits_exec
            )

            elapsed_time = time.time() - start_time
            peak_memory_mb = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024

            if memory_mb < peak_memory_mb or elapsed_time > timeout:
                return RUNTIME_ERROR + (MEMORY_LIMIT_EXCEEDED if memory_mb < peak_memory_mb else TIME_LIMIT_EXCEEDED)
            if exec_result.returncode in [-6, -9] or exec_result.returncode != 0:
                return RUNTIME_ERROR + exec_result.stderr

            return exec_result.stdout, elapsed_time, peak_memory_mb
        except subprocess.TimeoutExpired:
            return RUNTIME_ERROR + TIME_LIMIT_EXCEEDED
        except MemoryError:
            return RUNTIME_ERROR + MEMORY_LIMIT_EXCEEDED
        except subprocess.CalledProcessError as e:
            return RUNTIME_ERROR + e.stderr
        except Exception as e:
            return str(e)
        finally:
            RetryUtils.run_with_retry(
                ExecUtils.delete_file, file_path, try_limit=ExecUtils.CONFIG["TRY_LIMIT"], delay=ExecUtils.CONFIG["DELAY"]
            )
            try:
                if os.path.exists(output_file_path):
                    os.remove(output_file_path)
            except Exception as e:
                pass