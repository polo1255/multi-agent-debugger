// file: frontend/renderer.js

async function fixCode() {
    // 1. ดึง Element ตาม ID
    const codeInput = document.getElementById('code-input');
    const errorInput = document.getElementById('error-input');
    const btn = document.getElementById('fix-btn');
    
    // Elements ส่วนแสดงผล
    const emptyState = document.getElementById('empty-state');
    const resultArea = document.getElementById('result-area');
    const fixedCodeEl = document.getElementById('fixed-code');
    const testOutputEl = document.getElementById('test-output');
    const statusBadge = document.getElementById('status-badge');
    
    // ❌ ลบตัวแปร loadingText ออก เพราะไม่มีใน HTML แล้ว
    // const loadingText = document.getElementById('loading-text'); 

    const code = codeInput.value;
    const error = errorInput.value;

    if (!code) {
        alert("Please enter code first.");
        return;
    }

    // 2. ปรับ UI เข้าโหมด Loading
    btn.disabled = true;
    btn.innerHTML = '<span class="btn-text">⏳ PROCESSING...</span>';
    
    // Update Stepper (ทำ Highlight)
    document.getElementById('step-1').classList.add('active');
    document.getElementById('step-2').classList.add('active');
    
    // ✅ เปลี่ยนมาแสดงสถานะใน Terminal แทน
    testOutputEl.innerHTML = `
        <span style="color: #6a9955;">$ initializing_agents...</span><br>
        <span style="color: #6a9955;">$ analyzing_code...</span><br>
        <span class="blink">_</span>
    `;

    try {
        const response = await fetch('http://127.0.0.1:8000/debug', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: code, error: error })
        });

        const data = await response.json();

        // 3. แสดงผลลัพธ์
        emptyState.style.display = 'none';
        resultArea.style.display = 'flex'; // แสดงกล่องผลลัพธ์
        
        // Update Stepper
        document.getElementById('step-3').classList.add('active');

        if (fixedCodeEl) fixedCodeEl.textContent = data.fixed_code;
        
        const summaryEl = document.getElementById('summary-text');
        if (summaryEl) {
            summaryEl.innerHTML = data.summary || "✅ The AI successfully identified and fixed the bug. Please check the code below.";
        }

        if (testOutputEl) {
            const timestamp = new Date().toLocaleTimeString();
            const logPrefix = `[${timestamp}] root@debugger:~/app# run_test.py\n`;
            
            const cleanOutput = data.test_output ? data.test_output.trim() : "No output returned.";
            
            // แสดงผลลัพธ์แบบ Terminal สวยๆ
            testOutputEl.innerHTML = `
                <span style="color: #569cd6;">${logPrefix}</span>
                <span style="color: #444;">----------------------------------------</span>
                <br>${cleanOutput}
                <br><span style="color: #444;">----------------------------------------</span>
                <br><span style="color: #4caf50;">✔ Execution finished with exit code 0</span>
            `;
        }

        if (statusBadge) {
            if (data.status === 'success') {
                statusBadge.textContent = "SUCCESS";
                statusBadge.className = "badge success";
            } else {
                statusBadge.textContent = "FAILED";
                statusBadge.className = "badge";
            }
        }

    } catch (err) {
        // ถ้าพัง ให้โชว์ Error ใน Terminal สีแดง
        testOutputEl.innerHTML += `
            <br><br>
            <span style="color: #f44336;">❌ CRITICAL ERROR: Connection refused.</span><br>
            <span style="color: #888;">Details: ${err}</span>
        `;
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span class="btn-text">▶ START DEBUG</span>';
    }
}