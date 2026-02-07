from graph.workflow import app
import uuid
from dotenv import load_dotenv
import os

load_dotenv()
print("DEBUG KEY:", os.getenv("ANTHROPIC_API_KEY"))

def main():
    # โค้ดตัวอย่างที่มีบั๊ก (Infinite Loop & Logic Error)
    buggy_code = """
def calculate_sum(n):
    total = 0
    i = 0
    while i < n: # Bug: This might be infinite loop if i isn't incremented
        total += i
    return total
    """

    error_log = "TimeLimitExceeded: Your program took too long to execute."

    print("--- STARTING MULTI-AGENT DEBUGGING SYSTEM ---")
    
    # กำหนดค่าเริ่มต้นให้กับ State (Ingestion Phase) [cite: 59]
    initial_state = {
        "code_base": buggy_code,
        "error_context": error_log,
        "reflection_logs": [],
        "iteration_count": 0,
        "is_success": False,
        "test_output": ""
    }

    # สั่งให้กราฟทำงาน
    # config={"recursion_limit": 50} เพื่ออนุญาตให้วนลูปได้เยอะๆ
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 20}
    
    result = app.invoke(initial_state, config=config)

    # แสดงผลลัพธ์สุดท้าย [cite: 74]
    print("\n\n================ FINAL RESULT ================")
    if result['is_success']:
        print("✅ SUCCESS! Fixed Code:")
        print(result['code_base'])
        print("\nTest Output:", result['test_output'])
    else:
        print("❌ FAILED after max iterations.")
        print("Last Code:", result['code_base'])

if __name__ == "__main__":
    main()