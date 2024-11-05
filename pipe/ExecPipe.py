import os
import json
from typing import Union, Tuple

from utils.ExecUtils import ExecUtils

CONFIG_FILE_PATH = os.path.join(os.getcwd(), 'config.json')
CONFIG = json.load(open(CONFIG_FILE_PATH, 'r'))
PROCESS = CONFIG['PROCESS']
class ExecPipe:
    @staticmethod
    def exec_pipe(content: str, time_limit: int, memory_limit: int, stdin: str, language: str, processes: int = PROCESS) -> Union[Tuple[str, int, int], str]:
        if language not in CONFIG['ALLOWED_LANGUAGES'].keys():
            return f"Language {language} not allowed"
        if language == "Python":
            output = ExecUtils.execute_python(content, stdin, time_limit, memory_limit, processes)
        else:
            output = ExecUtils.execute_cpp(content, stdin, time_limit, memory_limit, processes)
        return output
        