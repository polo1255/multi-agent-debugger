# file: server.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from graph.workflow import app
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import uuid
import os
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
def debug_code(request: DebugRequest):
    print(f"--- RECEIVING REQUEST ---")

    # 1. 🔍 ค้นหาความรู้เก่า (คุณมีบรรทัดนี้แล้ว ดีมากครับ)
    print("🧠 Searching Vector Store...")
    similar_cases = search_similar_bugs(request.error, request.code)
    
    initial_state = {
        "code_base": request.code,
        "error_context": request.error,
        "reflection_logs": [],
        "iteration_count": 0,
        "is_success": False,
        "test_output": ""
    }
    
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 20}
    
    try:
        # รันระบบแก้บั๊ก
        result = app.invoke(initial_state, config=config)
        
        fixed_code = result['code_base']
        is_success = result['is_success']
        
        # สร้างบทสรุป
        summary_text = "Analysis complete."
        
        if summarizer_llm:
            try:
                summary_prompt = f"""
                You are a Technical Lead. Explain this bug fix briefly to a developer.
                
                Original Error: {request.error}
                Fixed Code:
                {fixed_code}
                
                OUTPUT FORMAT (Use HTML tags for bolding):
                - <b>Bug:</b> [Explain what caused the error in 1 sentence]
                - <b>Fix:</b> [Explain how you fixed it in 1 sentence]
                """
                ai_msg = summarizer_llm.invoke([HumanMessage(content=summary_prompt)])
                summary_text = ai_msg.content
            except Exception as e:
                print(f"Summarization failed: {e}")
                summary_text = "Analysis complete (Summary unavailable)."
        else:
             summary_text = "Analysis complete (No AI configured for summary)."

        # ---------------------------------------------------------
        # 🔥 จุดที่ 1: เติมส่วนบันทึกความรู้ (ถ้าแก้สำเร็จ ให้จำไว้)
        # ---------------------------------------------------------
        if is_success:
            print("💾 Saving new knowledge to Vector Store...")
            save_bug_report(request.error, request.code, fixed_code, summary_text)

        # ---------------------------------------------------------
        # 🔥 จุดที่ 2: ส่ง knowledge กลับไปให้ Frontend โชว์
        # ---------------------------------------------------------
        return {
            "status": "success" if is_success else "failed",
            "fixed_code": fixed_code,
            "test_output": result['test_output'],
            "summary": summary_text,
            "logs": result.get('reflection_logs', []),
            "knowledge": similar_cases  # <--- อย่าลืมบรรทัดนี้!
        }
            
    except Exception as e:
        print(f"❌ Critical Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(api, host="0.0.0.0", port=8000)