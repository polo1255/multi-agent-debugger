# file: server.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from graph.workflow import app  # ดึง Workflow ที่เราทำไว้มาใช้
import uuid

# สร้าง Server
api = FastAPI(title="Multi-Agent Debugger API")

# กำหนดหน้าตาข้อมูลที่จะรับเข้ามา (Request Body)
class DebugRequest(BaseModel):
    code: str
    error: str

@api.get("/")
def read_root():
    return {"status": "Agent System is Ready!"}

@api.post("/debug")
def debug_code(request: DebugRequest):
    """
    รับโค้ดพังๆ จาก Electron -> ส่งให้ Agent แก้ -> ส่งผลลัพธ์กลับไป
    """
    print(f"--- RECEIVING REQUEST ---")
    
    # 1. เตรียมข้อมูลเข้า Graph
    initial_state = {
        "code_base": request.code,
        "error_context": request.error,
        "reflection_logs": [],
        "iteration_count": 0,
        "is_success": False,
        "test_output": ""
    }
    
    # 2. รันระบบ Agent
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 20}
    
    try:
        # สั่งให้ทำงาน (รอจนเสร็จ)
        result = app.invoke(initial_state, config=config)
        
        # 3. ส่งผลลัพธ์กลับไปให้ Electron
        if result['is_success']:
            return {
                "status": "success",
                "fixed_code": result['code_base'],
                "test_output": result['test_output'],
                "logs": result.get('reflection_logs', [])
            }
        else:
            return {
                "status": "failed",
                "fixed_code": result['code_base'],
                "test_output": result['test_output'],
                "logs": result.get('reflection_logs', [])
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # สั่งรัน Server ที่ Port 8000
    uvicorn.run(api, host="0.0.0.0", port=8000)