from langgraph.graph import StateGraph, END
from graph.state import AgentState

# นำเข้าเอเจนต์ที่เราสร้างไว้
from agents.developer import developer_node
from agents.reviewer import reviewer_node
from agents.qa_executor import qa_executor_node

# --- 1. กำหนดเงื่อนไขการตัดสินใจ (Routing Logic) ---

def decide_after_review(state: AgentState):
    """
    ตัดสินใจหลังจากการตรวจของ Senior Reviewer (Reflection Loop)
    """
    # ดึงผลการรีวิวล่าสุด
    last_feedback = state['reflection_logs'][-1]
    iteration = state['iteration_count']
    
    # ป้องกัน Infinite Loop: ถ้ารวนเกิน 5 รอบ ให้หยุดทำงาน [cite: 31]
    if iteration > 5:
        return "end"

    # ถ้า Reviewer บอกว่า "APPROVE" ให้ไปต่อที่ QA [cite: 66]
    if "APPROVE" in last_feedback:
        return "qa_executor"
    
    # ถ้ายังไม่ผ่าน ให้วนกลับไปหา Developer [cite: 63]
    return "developer"

def decide_after_qa(state: AgentState):
    """
    ตัดสินใจหลังจากการรัน Docker (Validation Loop)
    """
    is_success = state.get('is_success', False)
    iteration = state['iteration_count']

    if iteration > 5:
        return "end"

    # ถ้ารันผ่าน (Tests Pass) -> จบงาน [cite: 71]
    if is_success:
        return "end"
    
    # ถ้ารันไม่ผ่าน (Runtime Error) -> วนกลับไปหา Developer พร้อม Error ใหม่ [cite: 56, 76]
    return "developer"


# --- 2. สร้างกราฟ (Graph Construction) ---

# เริ่มต้นกราฟด้วย State ที่เราออกแบบ
workflow = StateGraph(AgentState)

# เพิ่ม Node (คนทำงาน) เข้าไปในกราฟ [cite: 22]
workflow.add_node("developer", developer_node)
workflow.add_node("reviewer", reviewer_node)
workflow.add_node("qa_executor", qa_executor_node)

# --- 3. เชื่อมเส้น (Edges) ---

# เริ่มต้นที่ Developer เสมอ (Drafting Phase) [cite: 61]
workflow.set_entry_point("developer")

# Developer ทำเสร็จ -> ส่งให้ Reviewer ตรวจเสมอ
workflow.add_edge("developer", "reviewer")

# Reviewer ตรวจเสร็จ -> ตัดสินใจ (วนลูป หรือ ไปต่อ)
workflow.add_conditional_edges(
    "reviewer",
    decide_after_review,
    {
        "developer": "developer",   # Feedback loop
        "qa_executor": "qa_executor", # Approved
        "end": END
    }
)

# QA รันเสร็จ -> ตัดสินใจ (ผ่าน หรือ ไม่ผ่าน)
workflow.add_conditional_edges(
    "qa_executor",
    decide_after_qa,
    {
        "end": END,          # Success -> Finish
        "developer": "developer" # Failure -> Fix again
    }
)

# Compile กราฟให้พร้อมใช้งาน
app = workflow.compile()