from pydantic import BaseModel, Field
from typing import List, Literal

PATTERN: Literal[None] = r"^(Python|C\+\+)$"
DESCRIPTION: str = "File extension for code: Python or C++"

class Config:
    ALLOWED_ORIGINS = ["*"]
    TEMP_FOLDER_TO_READ = "read_temp"
    TEMP_FOLDER_TO_WRITE = "write_temp"
    DOCKER_FOLDER_TO_READ = "app_read"
    DOCKER_FOLDER_TO_WRITE = "app_write"
    CPP_VERSIONS = {"c++17", "c++14", "c++11", "c++98", "c++03", "c++20"}
    DEFAULT_CPP_VERSION = "c++17"
    DOCKER_IMAGE_NAME = "code-sandbox"
    CPUS = 2
    PROCESSES = 250
    
    class ExecuteRequest(BaseModel):
        code: str
        extension: str = Field(..., pattern=PATTERN, description=DESCRIPTION)
        time: int = 1
        memory: int = 256
        input: str = ""

    class HackRequest(BaseModel):
        class Mode(BaseModel):
            how: str
            tc: List[str]
        
        class TimeAndMemory(BaseModel):
            time: int = 1
            memory: int = 256

        mode: Mode
        correctCode: str
        correctExtension: str = Field(..., pattern=PATTERN, description=DESCRIPTION)
        correctCodeTimeAndMemory: TimeAndMemory
        newCode: str
        newExtension: str = Field(..., pattern=PATTERN, description=DESCRIPTION)
        newCodeTimeAndMemory: TimeAndMemory