from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uuid
from models.MakeFileUtils import MakeFileUtils
from models.ExecuteUtils import ExecuteUtils
from models.HackUtils import HackUtils
from typing import List
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ExecuteRequest(BaseModel):
    code: str
    extension: str = Field(..., pattern=r"^(Python|C\+\+)$", description="File extension for code: Python or C++")
    time: int = 1
    memory: int = 256
    input: str = ""

class HackRequest(BaseModel):
    class Mode(BaseModel):
        how: str
        tc: List[str]

    mode: Mode
    correctCode: str
    correctExtension: str = Field(..., pattern=r"^(Python|C\+\+)$", description="File extension for correct code: Python or C++")
    newCode: str
    newExtension: str = Field(..., pattern=r"^(Python|C\+\+)$", description="File extension for new code: Python or C++")


@app.post("/execute")
async def execute(request: ExecuteRequest):
    try:
        if request.extension not in {"Python", "C++"}:
            return JSONResponse(status_code=400, content={"error": True, "message": "Invalid extension"})

        file_extension = "py" if request.extension == "Python" else "cpp"
        file_name = f"{uuid.uuid4()}.{file_extension}"
        
        file_path = MakeFileUtils.make_file(request.code, file_name)
        if not file_path:
            raise HTTPException(status_code=500, detail="Failed to create file for execution")

        if request.extension == "Python":
            output = ExecuteUtils.execute_py(file_path, request.time, request.memory, request.input)
        else:
            output = ExecuteUtils.execute_cpp(file_path, "c++17", request.time, request.memory, request.input)

        MakeFileUtils.delete_file(file_path)

        if isinstance(output, str):
            return JSONResponse(status_code=200, content={"error": False, "output": output})
        else:
            output_code, exec_time, memory_used = output
            return JSONResponse(status_code=200, content={
                "error": False,
                "output": output_code,
                "time": exec_time,
                "memory": memory_used
            })

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": True, "message": str(e)})

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
            generator_file_name = f"{uuid.uuid4()}.{generator_extension.lower()}"
            generator_file_path = MakeFileUtils.make_file(generator_code, generator_file_name)
            if not generator_file_path:
                raise HTTPException(status_code=500, detail="Failed to create generator file for test case generation")

            generator_output = ExecuteUtils.execute_py(generator_file_path, time_limit=1, memory_limit_mb=256) if generator_extension == "Python" else ExecuteUtils.execute_cpp(generator_file_path, "c++17", time_limit=1, memory_limit_mb=256)
            MakeFileUtils.delete_file(generator_file_path)

            if isinstance(generator_output, str):
                return JSONResponse(status_code=500, content={"error": True, "message": f"Error in generator execution: {generator_output}"})
            test_case, _, _ = generator_output

        correct_file_name = f"{uuid.uuid4()}.{request.correctExtension.lower()}"
        correct_file_path = MakeFileUtils.make_file(request.correctCode, correct_file_name)
        if not correct_file_path:
            raise HTTPException(status_code=500, detail="Failed to create file for correct code execution")

        new_file_name = f"{uuid.uuid4()}.{request.newExtension.lower()}"
        new_file_path = MakeFileUtils.make_file(request.newCode, new_file_name)
        if not new_file_path:
            MakeFileUtils.delete_file(correct_file_path)
            raise HTTPException(status_code=500, detail="Failed to create file for new code execution")

        correct_output = ExecuteUtils.execute_py(correct_file_path, 1, 256, test_case) if request.correctExtension == "Python" else ExecuteUtils.execute_cpp(correct_file_path, "c++17", 1, 256, test_case)
        new_output = ExecuteUtils.execute_py(new_file_path, 1, 256, test_case) if request.newExtension == "Python" else ExecuteUtils.execute_cpp(new_file_path, "c++17", 1, 256, test_case)

        MakeFileUtils.delete_file(correct_file_path)
        MakeFileUtils.delete_file(new_file_path)

        if isinstance(correct_output, str) or isinstance(new_output, str):
            error_message = correct_output if isinstance(correct_output, str) else new_output
            return JSONResponse(status_code=500, content={"error": True, "message": error_message})

        correct_code_output, correct_exec_time, correct_memory = correct_output
        new_code_output, new_exec_time, new_memory = new_output

        if correct_code_output != new_code_output:
            return JSONResponse(status_code=200, content={
                "error": False,
                "hackSuccessful": True,
                "message": "Hack successful! Outputs mismatch.",
                "correctCodeOutput": correct_code_output,
                "newCodeOutput": new_code_output,
                "correctCodeTime": correct_exec_time,
                "correctCodeMemory": correct_memory,
                "newCodeTime": new_exec_time,
                "newCodeMemory": new_memory
            })

        return JSONResponse(status_code=200, content={
            "error": False,
            "hackSuccessful": False,
            "message": "Hack unsuccessful. Outputs match.",
            "correctCodeTime": correct_exec_time,
            "correctCodeMemory": correct_memory,
            "newCodeTime": new_exec_time,
            "newCodeMemory": new_memory
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": True, "message": str(e)})
    
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