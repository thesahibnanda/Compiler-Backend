import subprocess
import os
import time
import resource
from typing import Optional, Tuple
from config import Config

class ExecuteUtils:
    SUPPORTED_CPP_VERSIONS = {"c++98", "c++03", "c++11", "c++14", "c++17", "c++20", "c++23"}
    COMPILATION_ERROR = "Compilation Error"
    MEMORY_LIMIT_EXCEEDED = "Memory Limit Exceeded"
    TIME_LIMIT_EXCEEDED = "Time Limit Exceeded"
    EXECUTION_EXCEPTION = "Execution Exception"

    @staticmethod
    def execute_cpp(file_path: str, cpp_version: str = "c++17", time_limit: int = 10, memory_limit_mb: int = 256, stdin: Optional[str] = None):
        if cpp_version not in ExecuteUtils.SUPPORTED_CPP_VERSIONS:
            raise ValueError(f"Unsupported C++ version: {cpp_version}. Supported versions are: {', '.join(ExecuteUtils.SUPPORTED_CPP_VERSIONS)}.")
        
        output_file = os.path.join(Config.TEMP_FOLDER, f"output_executable_{os.path.basename(file_path).split('.')[0]}")
        compile_command = ["g++", f"-std={cpp_version}", file_path, "-o", output_file]
        
        try:
            compile_result = subprocess.run(compile_command, capture_output=True, text=True)
            if compile_result.returncode != 0:
                return f"{ExecuteUtils.COMPILATION_ERROR}:\n{compile_result.stderr}"
        except Exception as e:
            return f"{ExecuteUtils.COMPILATION_ERROR}: {str(e)}"
        
        memory_limit_bytes = memory_limit_mb * 1024 * 1024
        
        try:
            start_time = time.time()
            execute_result = subprocess.run(
                [output_file],
                input=stdin,
                capture_output=True,
                text=True,
                timeout=time_limit,
                preexec_fn=lambda: resource.setrlimit(resource.RLIMIT_AS, (memory_limit_bytes, memory_limit_bytes))
            )
            end_time = time.time()
            elapsed_time = end_time - start_time
            peak_memory_usage_mb = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024
            
            if peak_memory_usage_mb > memory_limit_mb:
                return ExecuteUtils.MEMORY_LIMIT_EXCEEDED
            
            output = execute_result.stdout if execute_result.returncode == 0 else f"Runtime Error:\n{execute_result.stderr}"
            return output, elapsed_time, peak_memory_usage_mb
        
        except subprocess.TimeoutExpired:
            return ExecuteUtils.TIME_LIMIT_EXCEEDED
        except Exception as e:
            return f"{ExecuteUtils.EXECUTION_EXCEPTION}: {str(e)}"
        
        finally:
            if os.path.exists(output_file):
                os.remove(output_file)

    @staticmethod
    def execute_py(file_path: str, time_limit: int = 10, memory_limit_mb: int = 256, stdin: Optional[str] = None):
        memory_limit_bytes = memory_limit_mb * 1024 * 1024

        try:
            start_time = time.time()
            execute_result = subprocess.run(
                ["python3", file_path],
                input=stdin,
                capture_output=True,
                text=True,
                timeout=time_limit,
                preexec_fn=lambda: resource.setrlimit(resource.RLIMIT_AS, (memory_limit_bytes, memory_limit_bytes))
            )
            end_time = time.time()
            elapsed_time = end_time - start_time
            peak_memory_usage_mb = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024  
            
            if peak_memory_usage_mb > memory_limit_mb:
                return ExecuteUtils.MEMORY_LIMIT_EXCEEDED
            
            output = execute_result.stdout if execute_result.returncode == 0 else f"Runtime Error:\n{execute_result.stderr}"
            return output, elapsed_time, peak_memory_usage_mb
        
        except subprocess.TimeoutExpired:
            return ExecuteUtils.TIME_LIMIT_EXCEEDED
        except Exception as e:
            return f"{ExecuteUtils.EXECUTION_EXCEPTION}: {str(e)}"