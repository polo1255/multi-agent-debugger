# file: agents/qa_executor.py (เวอร์ชัน Polyglot)

import docker
import os
import tempfile
import re
from graph.state import AgentState

try:
    client = docker.from_env()
except Exception as e:
    print(f"Docker Error: {e}")
    client = None

def detect_language(code):
    """วิเคราะห์ภาษาจากโครงสร้างโค้ดแบบง่าย (Heuristics)"""
    if "public class" in code and "static void main" in code:
        return "java"
    if "console.log" in code or "require(" in code or "import " in code:
        # เช็คเพิ่มเติมว่าเป็น JS หรือเปล่า (มองข้าม Python import)
        if "const " in code or "let " in code: return "javascript"
    if "fmt.Print" in code or "package main" in code:
        return "go"
    if "#include <iostream>" in code or "using namespace std" in code:
        return "cpp"
    return "python" # Default

def get_exec_config(language):
    """คืนค่า (Extension, Command) ตามประเภทภาษา"""
    configs = {
        "python":     (".py",   ["python", "/app/code.py"]),
        "javascript": (".js",   ["node", "/app/code.js"]),
        "java":       (".java", ["sh", "-c", "javac /app/Solution.java && java -cp /app Solution"]),
        "go":         (".go",   ["go", "run", "/app/code.go"]),
        "cpp":        (".cpp",  ["sh", "-c", "g++ /app/code.cpp -o /app/app && /app/app"])
    }
    return configs.get(language, (".py", ["python", "/app/code.py"]))

def qa_executor_node(state: AgentState):
    print("--- QA AGENT IS RUNNING POLYGLOT TESTS ---")
    
    code_to_test = state['code_base']
    if not client:
        return {"test_output": "Docker not running!", "is_success": False}

    # 1. วิเคราะห์ภาษาและดึงการตั้งค่า
    lang = detect_language(code_to_test)
    suffix, run_cmd = get_exec_config(lang)
    
    # 2. จัดการเรื่องชื่อไฟล์ (กรณี Java ต้องใช้ Solution.java ตามคำสั่ง javac)
    filename = "Solution" + suffix if lang == "java" else "code" + suffix

    print(f"--- Detected Language: {lang.upper()} ---")

    # 3. สร้างไฟล์ชั่วคราวตามนามสกุลภาษา
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False, mode='w', encoding='utf-8') as temp_script:
        temp_script.write(code_to_test)
        temp_path = temp_script.name

    try:
        # 4. รัน Docker โดยใช้ Image 'polyglot-sandbox' ที่เรา Build ไว้
        container = client.containers.run(
            image="polyglot-sandbox", # 🔥 ต้อง Build ชื่อนี้ไว้ก่อน
            command=run_cmd,
            volumes={os.path.abspath(temp_path): {'bind': f'/app/{filename}', 'mode': 'ro'}},
            network_disabled=True, 
            mem_limit="256m", # เพิ่ม RAM นิดหน่อยสำหรับ Java/C++
            detach=True
        )

        result = container.wait(timeout=30) # ตั้ง Timeout ป้องกันค้าง
        exit_code = result['StatusCode']
        logs = container.logs().decode('utf-8')
        container.remove()
        
        print(f"--- DOCKER LOGS ({lang}) ---\n{logs}\n---------------------")

    except Exception as e:
        exit_code = 1
        logs = f"Execution Error: {str(e)}"
        print(f"--- EXECUTION ERROR: {e} ---")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    # 5. ส่งผลลัพธ์กลับ
    if exit_code == 0:
        return {"test_output": logs, "is_success": True}
    else:
        return {
            "error_context": f"Runtime Error ({lang}):\n{logs}",
            "is_success": False,
            "test_output": logs
        }