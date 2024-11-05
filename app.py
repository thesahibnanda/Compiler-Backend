import psutil
import platform
from fastapi import FastAPI
from typing import List, Literal
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware


PATTERN: Literal[None] = r"^(Python|C\+\+)$"
DESCRIPTION: str = "File extension for code: Python or C++"

from pipe.ExecPipe import ExecPipe

app = FastAPI()

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/execute")
async def execute(request: ExecuteRequest):
    try:
        output = ExecPipe.exec_pipe(request.code, request.time, request.memory, request.input, request.extension)
        if isinstance(output, str):
            return JSONResponse(status_code=400, content={"error": True, "message": output})
        output_code, exec_time, memory_used = output
        return JSONResponse(status_code=200, content={"error": False, "output": output_code, "time": exec_time, "memory": memory_used})
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": True, "message": str(e)})

@app.post("/hack")
async def hack(request: HackRequest):
    try:
        if request.mode.how not in {"manual", "generated"}:
                return JSONResponse(status_code=400, content={"error": True, "message": "Invalid mode 'how'"})
        if request.mode.how == "manual":
            if len(request.mode.tc) != 1:
                return JSONResponse(status_code=400, content={"error": True, "message": "Manual mode requires a single test case"})
            test_case = request.mode.tc[0]
        elif request.mode.how == "generated":
            if len(request.mode.tc) < 2:
                return JSONResponse(status_code=400, content={"error": True, "message": "Generated mode requires generator code and extension"})
            generator_code, generator_extension = request.mode.tc[0], request.mode.tc[1]
            
            generator_output = ExecPipe.exec_pipe(generator_code, 60, 1024, "", generator_extension)
            if isinstance(generator_output, str):
                return JSONResponse(status_code=400, content={"error": True, "message": "Error at Generator's Code\n" + generator_output})
            test_case, _, _ = generator_output
        
        correct_output = ExecPipe.exec_pipe(request.correctCode, request.correctCodeTimeAndMemory.time, request.correctCodeTimeAndMemory.memory, test_case, request.correctExtension)
        if isinstance(correct_output, str):
            return JSONResponse(status_code=400, content={"error": True, "message": "Error at Correct Code\n" + correct_output})
        
        new_output = ExecPipe.exec_pipe(request.newCode, request.newCodeTimeAndMemory.time, request.newCodeTimeAndMemory.memory, test_case, request.newExtension)
        if isinstance(new_output, str):
            return JSONResponse(status_code=400, content={"error": True, "message": "Error at New Code\n" + new_output})
        
        correct_output_code, correct_time, correct_memory = correct_output
        new_output_code, new_time, new_memory = new_output
        
        if correct_output_code == new_output_code:
            return JSONResponse(status_code=200, content={
                        "error": False,
                        "hackSuccessful": False,
                        "message": "Hack unsuccessful🥺 Outputs match.",
                        "correctCodeTime": correct_time,
                        "correctCodeMemory": correct_memory,
                        "newCodeTime": new_time,
                        "newCodeMemory": new_memory
                    })
        return JSONResponse(status_code=200, content={
                        "error": False,
                        "hackSuccessful": True,
                        "message": "Hack successful😎 Outputs don't match.",
                        "correctCodeTime": correct_time,
                        "correctCodeMemory": correct_memory,
                        "newCodeTime": new_time,
                        "newCodeMemory": new_memory
                    })
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": True, "message": str(e)})
    
@app.get("/healthz")
async def healthz():
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "running": True,
            "details": "Service is operational"
        }
    )

@app.get("/metrics")
async def metrics():
    try:
        memory = psutil.virtual_memory()
        available_memory_mb = memory.available / (1024 * 1024)  
        os_type = platform.system()
        is_linux = os_type == "Linux"
        if not is_linux:
            return JSONResponse(
                status_code=503,
                content={
                    "error": True,
                    "message": "System health check failed. OS is not Linux.",
                    "available_memory_mb": available_memory_mb,
                    "os_type": os_type
                }
            )
            
        if available_memory_mb < 100:
            return JSONResponse(
                status_code=503,
                content={
                    "error": True,
                    "message": "Memory critically low.",
                    "available_memory_mb": available_memory_mb,
                    "os_type": os_type
                }
            )

        return JSONResponse(
            status_code=200,
            content={
                "error": False,
                "message": "System health is good.",
                "available_memory_mb": available_memory_mb,
                "os_type": os_type
            }
        )
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": True, "message": f"An error occurred: {str(e)}"}
        )