# file: agents/qa_executor.py

import docker
import os
import tempfile
from graph.state import AgentState

def detect_language(code):
    """วิเคราะห์ภาษาจากโครงสร้างโค้ดแบบง่าย (Heuristics)"""
    if "public class" in code and "static void main" in code:
        return "java"
    if "console.log" in code or "require(" in code or "import " in code:
        if "const " in code or "let " in code: return "javascript"
    if "fmt.Print" in code or "package main" in code:
        return "go"
    if "#include <iostream>" in code or "using namespace std" in code:
        return "cpp"
    return "python"

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
    
    # 🔥 FIX: ย้ายการเชื่อมต่อ Docker มาไว้ตรงนี้ (Try to connect every time)
    try:
        client = docker.from_env()
        client.ping() # เช็คว่าคุยกันรู้เรื่องไหม
    except Exception as e:
        print(f"❌ Docker Connection Error: {e}")
        return {
            "test_output": "Docker not running! Please start Docker Desktop.",
            "is_success": False
        }

    code_to_test = state['code_base']
    
    # 1. วิเคราะห์ภาษาและดึงการตั้งค่า
    lang = detect_language(code_to_test)
    suffix, run_cmd = get_exec_config(lang)
    
    filename = "Solution" + suffix if lang == "java" else "code" + suffix
    print(f"--- Detected Language: {lang.upper()} ---")

    # 3. สร้างไฟล์ชั่วคราว
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False, mode='w', encoding='utf-8') as temp_script:
        temp_script.write(code_to_test)
        temp_path = temp_script.name

    try:
        # 4. รัน Docker
        container = client.containers.run(
            image="polyglot-sandbox", 
            command=run_cmd,
            volumes={os.path.abspath(temp_path): {'bind': f'/app/{filename}', 'mode': 'ro'}},
            network_disabled=True, 
            mem_limit="256m",
            detach=True
        )

        result = container.wait(timeout=30)
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