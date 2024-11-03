import json
import psutil
import platform
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from config import Config
from pipe.ExecutePipelines import ExecutePipelines

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.ALLOWED_ORIGINS,  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/execute")
async def execute(request: Config.ExecuteRequest):
    try:
        return ExecutePipelines.execute(request.code, request.extension, request.memory, request.time, request.input, "Execution Error")
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": True, "message": str(e)})
    
@app.post("/hack")
async def hack(request: Config.HackRequest):
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
            generator_response = ExecutePipelines.execute(generator_code, generator_extension, 1024, 10, "", "Generator Code Error")
            if generator_response.status_code != 200:
                return generator_response
            try:
                test_case = json.loads(generator_response.body.decode())["output"]
            except KeyError:
                return JSONResponse(status_code=500, content={"error": True, "message": "Generator Respone Error `KeyError`"})
        corrected_response = ExecutePipelines.execute(request.correctCode, request.correctExtension, request.correctCodeTimeAndMemory.memory, request.correctCodeTimeAndMemory.time, test_case, "Correct Code Execution Error")
        new_response = ExecutePipelines.execute(request.newCode, request.newExtension, request.newCodeTimeAndMemory.memory, request.newCodeTimeAndMemory.time, test_case, "New Code Execution Error")
        if corrected_response.status_code != 200:
            return corrected_response
        if new_response.status_code != 200:
            return new_response
        
        corrected_response_json = json.loads(corrected_response.body.decode())
        new_response_json = json.loads(new_response.body.decode())
        
        if corrected_response_json["output"] != new_response_json["output"]:
            return JSONResponse(status_code=200, content={
                    "error": False,
                    "hackSuccessful": True,
                    "message": "Hack successful🎉 Outputs mismatch.",
                    "correctCodeOutput": corrected_response_json["output"] ,
                    "newCodeOutput": new_response_json["output"],
                    "correctCodeTime": corrected_response_json["time"],
                    "correctCodeMemory": corrected_response_json["memory"],
                    "newCodeTime": new_response_json["time"],
                    "newCodeMemory": new_response_json["memory"]
                })
        return JSONResponse(status_code=200, content={
                    "error": False,
                    "hackSuccessful": False,
                    "message": "Hack unsuccessful🥺 Outputs match.",
                    "correctCodeTime": corrected_response_json["time"],
                    "correctCodeMemory": corrected_response_json["memory"],
                    "newCodeTime": new_response_json["time"],
                    "newCodeMemory": new_response_json["memory"]
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