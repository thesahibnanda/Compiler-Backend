import os
import uuid
from fastapi.responses import JSONResponse

from config import Config
from utils.FileUtils import FileUtils
from utils.DockerUtils import DockerUtils


class ExecutePipelines:
    
    @staticmethod
    def execute(code: str, extension: str, memory: int, time: int, stdin: str, prior_message: str):
        try:
            if extension not in {"Python", "C++"}:
                return JSONResponse(status_code=400, content={"error": True, "message": f"{prior_message}\nInvalid extension"})

            file_path = FileUtils.make_file(code, str(uuid.uuid4()), extension)
            if file_path is None:
                return JSONResponse(status_code=500, content={"error": True, "message": f"{prior_message}\nInternal Server Error, A Big Fuck Up Happened"})
            
            if extension == "Python":
                output = DockerUtils.execute_python3(Config.DOCKER_IMAGE_NAME, memory, time, file_path, Config.CPUS, Config.PROCESSES, stdin)
            else:
                compiled_path = DockerUtils.compile_cpp(Config.DOCKER_IMAGE_NAME, memory, time, file_path, Config.CPUS, Config.PROCESSES, Config.DEFAULT_CPP_VERSION)
                output = DockerUtils.execute_cpp(Config.DOCKER_IMAGE_NAME, memory, time, Config.CPUS, Config.PROCESSES, compiled_path, stdin)
                compiled_path_here = os.getcwd() + compiled_path.replace(Config.DOCKER_FOLDER_TO_WRITE, Config.TEMP_FOLDER_TO_WRITE, 1)
                if not FileUtils.delete_file(compiled_path_here):
                    return JSONResponse(status_code=500, content={"error": True, "message": f"{prior_message}\nInternal Server Error, A Small Itsy-Bitsy Fuck Up Happened\nMaybe Reload And Try Again\nDev's Code: X123IS"})
            
            if not FileUtils.delete_file(file_path):
                return JSONResponse(status_code=500, content={"error": True, "message": f"{prior_message}\nInternal Server Error, A Small Itsy-Bitsy Fuck Up Happened\nMaybe Reload And Try Again"})
            
            if isinstance(output, str):
                return JSONResponse(status_code=500, content={"error": True, "message": f"{prior_message}\n{output}"})    
            
            output_code, exec_time, memory_used = output
            return JSONResponse(status_code=200, content={"error": False, "output": output_code, "time": exec_time, "memory": memory_used})
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": True, "message": f"{prior_message}\n{str(e)}"}) 