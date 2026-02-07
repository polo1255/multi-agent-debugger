# file: agents/reviewer.py

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()

# --- ส่วนเลือก Model (ให้เหมือนกับ Developer) ---
if os.getenv("DEEPSEEK_API_KEY"):
    # ใช้ DeepSeek ถ้ามี Key (ประหยัดและเก่ง)
    llm = ChatOpenAI(
        model="deepseek-coder", 
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
        temperature=0
    )
elif os.getenv("OPENAI_API_KEY"):
    # ใช้ GPT-4o หรือ 3.5 ถ้ามีแต่ OpenAI Key
    llm = ChatOpenAI(
        model="gpt-3.5-turbo", # หรือ gpt-4o ถ้าสู้ราคาไหว
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0
    )
else:
    # ถ้าไม่มี Key อะไรเลย
    raise ValueError("กรุณาใส่ DEEPSEEK_API_KEY หรือ OPENAI_API_KEY ในไฟล์ .env")

def reviewer_node(state):
    """
    Reviewer Agent: ตรวจสอบโค้ด
    """
    print("--- SENIOR REVIEWER IS WORKING ---")
    
    current_code = state['code_base']
    error_context = state['error_context']
    
    # Prompt สั่งให้ Reviewer ใจดีหน่อย
    system_prompt = """You are a Senior Python Code Reviewer.
    
    YOUR GOAL: 
    Check if the provided code fixes the reported error. 
    
    CRITERIA FOR APPROVAL:
    1. If the code logic seems to fix the specific error mentioned -> APPROVE.
    2. If the code is valid Python and runnable -> APPROVE.
    3. DO NOT complain about best practices unless they cause errors.

    OUTPUT FORMAT:
    - If the code is good enough: Respond with exactly "APPROVE".
    - If there is a CRITICAL bug: Start with "FEEDBACK:" followed by the issue.
    """
    
    user_content = f"### CODE TO REVIEW:\n{current_code}\n\n### ERROR TO FIX:\n{error_context}"

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content)
    ]
    
    # เรียกใช้งาน AI
    response = llm.invoke(messages)
    content = response.content.strip()
    
    print(f"--- REVIEW RESULT: {content[:50]}... ---")

    return {
        "reflection_logs": [content] 
    }