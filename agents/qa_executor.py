# file: agents/qa_executor.py (เวอร์ชันปลดล็อก Debug ได้ทั่วจักรวาล)

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
    print("--- QA AGENT IS RUNNING TESTS ---")
    
    code_to_test = state['code_base']
    
    if not client:
        return {"test_output": "Docker not running!", "is_success": False}

    # 🟢 แก้ตรงนี้: ไม่ต้องยัดไส้ test_harness แบบเจาะจงแล้ว
    # เราจะรันโค้ดที่ Developer ส่งมาเพียวๆ เลย
    # (สมมติว่าในโค้ดนั้นมี print test ของมันเองอยู่แล้ว เช่นในตัวอย่างที่คุณส่งมา)
    
    full_script = code_to_test

    print("================ DEBUG: CODE SENT TO DOCKER ================")
    print(full_script)
    print("============================================================")

    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode='w', encoding='utf-8') as temp_script:
        temp_script.write(full_script)
        temp_path = temp_script.name

    try:
        # รัน Docker
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
        
        print(f"--- DOCKER LOGS ---\n{logs}\n---------------------")

    except Exception as e:
        exit_code = 1
        logs = str(e)
        print(f"--- EXECUTION ERROR: {e} ---")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    print(f"--- QA RESULT: Exit Code {exit_code} ---")

    # ถ้า Exit Code 0 แปลว่าโปรแกรมรันจบโดยไม่ Crash -> ถือว่าผ่าน
    if exit_code == 0:
        return {
            "test_output": logs,
            "is_success": True 
        }
    else:
        return {
            "error_context": f"Runtime Error:\n{logs}",
            "is_success": False,
            "test_output": logs
        }