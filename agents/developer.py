# file: agents/developer.py

import os
import re
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

# นำเข้าโครงสร้าง State
from graph.state import AgentState

load_dotenv()

# เช็คว่ามี API Key ไหนให้ใช้บ้าง (DeepSeek หรือ OpenAI)
if os.getenv("DEEPSEEK_API_KEY"):
    llm = ChatOpenAI(
        model="deepseek-coder", 
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
        temperature=0.2
    )
else:
    # Fallback กรณีไม่มี DeepSeek
    llm = ChatOpenAI(
        model="gpt-3.5-turbo", 
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.2
    )

def extract_code_content(text):
    """
    ฟังก์ชันสำหรับดึงเฉพาะโค้ด Python ออกจาก Markdown Quote
    เช่น ตัดคำว่า 'Here is the code:' ทิ้งไป
    """
    # 1. ค้นหา Pattern ```python ... ```
    pattern = r"```(?:python)?\s*(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    
    if match:
        # ถ้าเจอ ให้เอาแค่ข้างในออกมา
        return match.group(1).strip()
    
    # 2. ถ้าไม่เจอ Markdown ให้ลองดูว่ามีคำอธิบายนำหน้าไหม
    # ถ้าบรรทัดแรกไม่ใช่ def หรือ import อาจจะเป็นคำพูด
    lines = text.strip().split('\n')
    clean_lines = []
    started = False
    for line in lines:
        # เริ่มเก็บเมื่อเจอ def, class, import หรือ from
        if line.strip().startswith(('def ', 'class ', 'import ', 'from ', '@')):
            started = True
        if started:
            clean_lines.append(line)
            
    if clean_lines:
        return '\n'.join(clean_lines)

    # 3. ถ้าไม่มีอะไรเลย ก็ส่งกลับไปดื้อๆ (เผื่อมันส่งมาแต่โค้ดล้วน)
    return text.strip()

def developer_node(state: AgentState):
    """
    Developer Agent: ทำหน้าที่วิเคราะห์ Error และแก้ไขโค้ด
    """
    print("--- DEVELOPER AGENT IS WORKING ---")
    
    current_code = state['code_base']
    error = state['error_context']
    feedback = state.get('reflection_logs', [])
    
    # Prompt สั่งให้ทำงาน และย้ำว่าขอ Code เท่านั้น
    system_prompt = """You are an expert Python software developer.
    Your task is to fix bugs in the provided code based on the error context.
    
    RULES:
    1. Analyze the logic and error.
    2. Fix the code.
    3. Return ONLY the complete fixed Python code inside markdown code blocks.
    4. DO NOT change the function name or signature unless necessary.
    5. Ensure the logic matches: Sum of integers from 0 to n-1.
    """
    
    user_content = f"### BROKEN CODE:\n{current_code}\n\n### ERROR CONTEXT:\n{error}"
    
    if feedback:
        user_content += f"\n\n### FEEDBACK FROM REVIEWER:\n{feedback[-1]}"

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content)
    ]
    
    response = llm.invoke(messages)
    raw_content = response.content
    
    # --- จุดสำคัญ: เรียกใช้ฟังก์ชันแกะโค้ด ---
    fixed_code = extract_code_content(raw_content)
            
    print("--- DEVELOPER AGENT FINISHED ---")

    return {
        "code_base": fixed_code,
        "iteration_count": state["iteration_count"] + 1
    }