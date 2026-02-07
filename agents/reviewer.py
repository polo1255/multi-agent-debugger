import os
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

# นำเข้าโครงสร้าง State
from graph.state import AgentState

load_dotenv()

# ตั้งค่า Claude 3.5 Sonnet 
# โมเดลนี้มีความสามารถในการตรวจสอบ Logic และ Security ได้ดีเยี่ยม
llm = ChatAnthropic(
    model="claude-3-haiku-20240307",
    api_key=os.getenv("CLAUDE_API_KEY"),
    temperature=0  # ตั้งเป็น 0 เพื่อให้การตรวจสอบคงเส้นคงวาที่สุด
)

def reviewer_node(state: AgentState):
    """
    Senior Reviewer Agent: ทำหน้าที่ตรวจสอบคุณภาพโค้ด (Static Analysis) 
    """
    print("--- SENIOR REVIEWER IS WORKING ---")
    
    # 1. ดึงโค้ดล่าสุดจาก Developer มาตรวจ
    current_code = state['code_base']
    
    # 2. สร้าง Prompt สำหรับการตรวจสอบ (The Reflector) [cite: 37]
    system_prompt = """You are a Senior Software Engineer acting as a Code Reviewer.
    Your task is to review the provided code for:
    1. Logical Correctness: Does it actually fix the bug?
    2. Security Vulnerabilities: Are there any unsafe practices? [cite: 40]
    3. Code Quality: Is it clean and maintainable?
    
    Response Format:
    - If the code is good and safe, reply ONLY with: "APPROVE"
    - If there are issues, provide a concise list of feedback to the developer. Start your response with "FEEDBACK:"
    """
    
    user_content = f"### CODE TO REVIEW:\n{current_code}"
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content)
    ]
    
    # 3. ให้ AI ประมวลผล
    response = llm.invoke(messages)
    review_result = response.content
    
    print(f"--- REVIEW RESULT: {review_result[:50]}... ---")

    # 4. อัปเดต State
    # เราจะบันทึกผลการรีวิวลงใน reflection_logs เพื่อให้ Developer อ่านในรอบถัดไป
    # ถ้าผ่าน (APPROVE) ข้อมูลนี้จะถูกใช้เพื่อตัดสินใจส่งไป QA ต่อ
    return {
        "reflection_logs": [review_result] 
    }