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
    Upgraded function version: Extract code in any language.
    Whether it's JavaScript, Python, or Java.
    """
    # 1. ค้นหา Pattern ```python ... ```
    pattern = r"```(?:\w+)?\s*\n?(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    
    if match:
        # ถ้าเจอ ให้เอาแค่ข้างในออกมา
        return match.group(1).strip()
    
    # 2. ถ้าไม่เจอ Markdown ให้ลองดูว่ามีคำอธิบายนำหน้าไหม
    # ถ้าบรรทัดแรกไม่ใช่ def หรือ import อาจจะเป็นคำพูด
    lines = text.strip().split('\n')
    clean_lines = []
    started = False
    code_starters = ('def ', 'class ', 'import ', 'from ', '@', 'function ', 'const ', 'let ', 'var ', 'package ')
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
    Developer Agent: ทำหน้าที่วิเคราะห์ Error และแก้ไขโค้ด โดยใช้ความรู้จากอดีต (RAG)
    """
    current_iteration = state.get('iteration_count', 0) + 1

    print(f"--- DEVELOPER AGENT IS WORKING (Round: {current_iteration}) ---")

    current_code = state['code_base']
    error = state['error_context']
    feedback = state.get('reflection_logs', [])
    
    # 🔥 ดึงข้อมูล Knowledge Context ที่ส่งมาจาก Server
    knowledge = state.get('knowledge_context', "")
    
    # 1. ปรับปรุง System Prompt ให้ AI รู้จักใช้ Reference
    system_prompt = """You are a Universal Software Engineer expert.
    Your task is to fix bugs while OPTIMIZING performance.
    
    GUIDELINES:
        1. Identify the programming language.
        2. Analyze the bug and the Time/Space Complexity of the original code.
        3. Fix the bug using the MOST EFFICIENT algorithm (e.g., prefer O(n) over O(n^2)).
        4. If using loops, ensure they are necessary. Use hash maps (dict) for lookups instead of lists where possible.
        5. Return ONLY the fixed code in markdown code blocks.
    """
    
    # 2. ปรับปรุง User Content เพื่อใส่ความรู้จาก ChromaDB เข้าไป
    user_content = f"### BROKEN CODE:\n{current_code}\n\n### ERROR CONTEXT:\n{error}"
    
    # 🔥 ถ้ามีข้อมูลความรู้เก่า ให้ฉีดเข้าไปใน Prompt ตรงนี้
    if knowledge:
        user_content += f"\n\n### PAST KNOWLEDGE (Use as reference):\n{knowledge}"
    
    if feedback:
        user_content += f"\n\n### FEEDBACK FROM REVIEWER:\n{feedback[-1]}"

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content)
    ]
    
    response = llm.invoke(messages)
    raw_content = response.content
    
    fixed_code = extract_code_content(raw_content)
            
    print("--- DEVELOPER AGENT FINISHED ---")

    return {
        "code_base": fixed_code,
        "iteration_count": current_iteration
    }