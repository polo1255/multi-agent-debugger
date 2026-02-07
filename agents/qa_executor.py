# file: agents/qa_executor.py

import docker
import os
import tempfile
from graph.state import AgentState

try:
    client = docker.from_env()
except Exception as e:
    print(f"Docker Error: {e}")
    client = None

def qa_executor_node(state: AgentState):
    """
    QA Agent: รันโค้ดใน Docker Sandbox พร้อม Test Case อัตโนมัติ
    """
    print("--- QA AGENT IS RUNNING TESTS ---")
    
    code_to_test = state['code_base']
    
    if not client:
        return {"test_output": "Docker not running!", "is_success": False}

    # --- ส่วนที่เพิ่มมา: สร้าง Test Harness (ข้อสอบ) ---
    # เราจะเติมส่วนนี้ต่อท้ายโค้ดของ Developer เพื่อลองเรียกใช้งานจริง
    test_harness = """
import sys

# Test Script Auto-Generated
if __name__ == "__main__":
    try:
        print("Running Test: calculate_sum(5)")
        # โจทย์: ผลบวก 0 ถึง 4 (0+1+2+3+4) ต้องได้ 10
        result = calculate_sum(5)
        print(f"Actual Result: {result}")
        
        expected = 10
        if result == expected:
            print("✅ TEST PASSED")
            sys.exit(0) # แจ้งว่าผ่าน
        else:
            print(f"❌ TEST FAILED: Expected {expected}, got {result}")
            sys.exit(1) # แจ้งว่าพัง
            
    except Exception as e:
        print(f"❌ RUNTIME ERROR: {e}")
        sys.exit(1)
"""
    
    # รวมร่างโค้ด (User Code + Test Harness)
    full_script = code_to_test + "\n" + test_harness

    print("================ DEBUG: CODE SENT TO DOCKER ================")
    print(full_script)
    print("============================================================")

    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode='w', encoding='utf-8') as temp_script:
        temp_script.write(full_script)
        temp_path = temp_script.name

    try:
        # สั่งรัน Docker
        container = client.containers.run(
            image="python:3.10-slim",
            command=["python", "/app/test_script.py"],
            volumes={os.path.abspath(temp_path): {'bind': '/app/test_script.py', 'mode': 'ro'}},
            network_disabled=True, 
            mem_limit="128m",
            detach=True
        )

        result = container.wait()
        exit_code = result['StatusCode']
        logs = container.logs().decode('utf-8')
        container.remove()

        # --- Print Log ออกมาดูให้เห็นกับตา ---
        print(f"--- DOCKER LOGS ---\n{logs}\n---------------------")

    except Exception as e:
        exit_code = 1
        logs = str(e)
        print(f"--- EXECUTION ERROR: {e} ---")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    print(f"--- QA RESULT: Exit Code {exit_code} ---")

    # ส่งผลลัพธ์กลับเข้า Loop
    if exit_code == 0:
        return {
            "test_output": logs,
            "is_success": True 
        }
    else:
        return {
            "error_context": f"Runtime Error or Test Failed:\n{logs}",
            "is_success": False,
            "test_output": logs
        }