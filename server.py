# file: server.py
from fastapi.responses import StreamingResponse
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from graph.workflow import app
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import uuid
import os
import json
import asyncio
from dotenv import load_dotenv
from database.vector_store import search_similar_bugs, save_bug_report

# โหลดตัวแปรจากไฟล์ .env
load_dotenv()

# สร้าง Server
api = FastAPI(title="Multi-Agent Debugger API")

class DebugRequest(BaseModel):
    code: str
    error: str

# --- ส่วนตั้งค่า AI สำหรับทำสรุป (รองรับทั้ง DeepSeek และ OpenAI) ---
summarizer_llm = None

if os.getenv("DEEPSEEK_API_KEY"):
    # ใช้ DeepSeek (ประหยัด)
    summarizer_llm = ChatOpenAI(
        model="deepseek-coder", 
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
        temperature=0.5
    )
    print("✅ Summarizer Agent: Using DeepSeek")
elif os.getenv("OPENAI_API_KEY"):
    # ใช้ OpenAI
    summarizer_llm = ChatOpenAI(
        model="gpt-3.5-turbo", 
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.5
    )
    print("✅ Summarizer Agent: Using OpenAI")
else:
    print("⚠️ Warning: No API Key found for Summarizer. Summary feature will be disabled.")

@api.get("/")
def read_root():
    return {"status": "Agent System is Ready!"}

@api.post("/debug")
async def debug_code(request: DebugRequest): # 1. เปลี่ยนเป็น async def
    print(f"--- RECEIVING REQUEST (STREAMING MODE) ---")

    # ส่วนนี้ยังคงเดิมเหมือนที่คุณเขียนไว้
    print("🧠 Searching Vector Store...")
    similar_cases = search_similar_bugs(request.error, request.code)
    
    knowledge_str = ""
    if similar_cases:
        knowledge_str = "\n".join([
            f"--- Reference Case ---\n{c['summary']}" 
            for c in similar_cases
        ])

    initial_state = {
        "code_base": request.code,
        "error_context": request.error,
        "knowledge_context": knowledge_str,
        "reflection_logs": [],
        "iteration_count": 0,
        "is_success": False,
        "test_output": ""
    }
    
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 25}

    # 🔥 นี่คือส่วนที่คุณถามว่าเอาไว้ตรงไหน: ใส่ไว้ข้างใน debug_code เลยครับ
    async def event_generator():
        final_result = {} # ตัวแปรสำหรับเก็บผลลัพธ์สุดท้ายเพื่อเอาไปทำ Summary
        
        try:
            # 2. เปลี่ยนจาก .invoke เป็น .astream เพื่อดึงข้อมูลทีละขั้นตอน
            async for event in app.astream(initial_state, config=config):
                for node_name, output in event.items():
                    # เก็บสถานะล่าสุดไว้เสมอ
                    final_result.update(output)
                    
                    # 3. ส่งข้อมูลชื่อ Node และรอบการทำงานปัจจุบันไปที่ UI ทันที
                    data = {
                        "node": node_name,
                        "iteration": output.get("iteration_count", 0),
                        "is_success": output.get("is_success", False),
                        "test_output": output.get("test_output", "")
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                    await asyncio.sleep(0.1) # ป้องกันการส่งข้อมูลเร็วเกินไป

            # 4. เมื่อจบการทำงาน (Stream จบ) ค่อยทำส่วน Summary และ Save Knowledge
            is_success = final_result.get('is_success', False)
            fixed_code = final_result.get('code_base', '')
            
            summary_text = "Analysis complete."
            if is_success and summarizer_llm:
                # ทำ Summary เหมือนเดิมที่คุณเคยเขียน
                summary_prompt = f"Explain this fix briefly: {fixed_code}"
                ai_msg = summarizer_llm.invoke([HumanMessage(content=summary_prompt)])
                summary_text = ai_msg.content
                
                # บันทึกความรู้ลง Vector Store
                print("💾 Saving knowledge...")
                save_bug_report(request.error, request.code, fixed_code, summary_text)

            # 5. ส่งสถานะ Completed พร้อมข้อมูลทั้งหมดรอบสุดท้าย
            final_data = {
                "status": "completed",
                "fixed_code": fixed_code,
                "summary": summary_text,
                "is_success": is_success,
                "knowledge": similar_cases,
                "test_output": final_result.get("test_output", "")
            }
            yield f"data: {json.dumps(final_data)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    # 6. คืนค่าเป็น StreamingResponse
    return StreamingResponse(event_generator(), media_type="text/event-stream")
            
   

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(api, host="0.0.0.0", port=8000)