# file: agents/reviewer.py

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv

load_dotenv()

# เลือก Model (ใช้ Logic เดียวกับ Developer)
if os.getenv("DEEPSEEK_API_KEY"):
    llm = ChatOpenAI(
        model="deepseek-coder", 
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
        temperature=0
    )
elif os.getenv("OPENAI_API_KEY"):
    llm = ChatOpenAI(
        model="gpt-3.5-turbo", 
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0
    )
else:
    raise ValueError("กรุณาใส่ API KEY ในไฟล์ .env")

def reviewer_node(state):
    """
    Reviewer Agent: ตรวจสอบโค้ดโดยอิงจากผลลัพธ์การรันจริง (Polyglot Version)
    """
    print("--- SENIOR REVIEWER IS WORKING ---")
    
    current_code = state['code_base']
    error_context = state['error_context']
    test_output = state.get('test_output', '') # 🔥 ดึงผลลัพธ์จาก Docker มาดูด้วย

    # 1. อัปเกรด Prompt ให้เป็น Polyglot (ตรวจได้ทุกภาษา)
    system_prompt = """You are a Senior Polyglot Code Reviewer. 
    
    CRITERIA FOR APPROVAL:
    1. Correctness: Does the code fix the specific error?
    2. Execution: Does the code run successfully in Docker?
    3. EFFICIENCY: Is the time complexity optimal? (Reject O(n^2) if O(n) is possible).
    4. Style: Is the code clean and strictly typed?
    
    OUTPUT FORMAT:
    - If perfect: "APPROVE"
    - If logic works but slow: "FEEDBACK: The solution is correct but inefficient. Please optimize using [suggested method]..."
    - If fails: "FEEDBACK: [Reason]..."
    """
    
    user_content = f"""
    ### ERROR TO FIX:
    {error_context}

    ### FIXED CODE:
    {current_code}

    ### EXECUTION LOGS (From Docker):
    {test_output}
    """

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content)
    ]
    
    response = llm.invoke(messages)
    content = response.content.strip()
    
    print(f"--- REVIEW RESULT: {content[:100]}... ---")

    # 2. ส่งค่ากลับพร้อมสถานะความสำเร็จ
    is_passed = "APPROVE" in content.upper()
    
    return {
        "reflection_logs": [content],
        "is_success": is_passed  # 🔥 ส่งสถานะนี้กลับเพื่อให้ Graph รู้ว่าควรหยุดวิ่ง
    }