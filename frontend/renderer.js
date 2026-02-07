// file: frontend/renderer.js

async function fixCode() {
    const code = document.getElementById('code-input').value;
    const error = document.getElementById('error-input').value;
    const btn = document.getElementById('fix-btn');
    const loading = document.getElementById('loading');
    const resultArea = document.getElementById('result-area');

    if (!code) {
        alert("Please enter some code!");
        return;
    }

    // เปิดโหมดโหลด
    btn.disabled = true;
    loading.style.display = 'block';
    resultArea.style.display = 'none';

    try {
        // ยิง Request ไปหา Python Server (API)
        const response = await fetch('http://127.0.0.1:8000/debug', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ code: code, error: error })
        });

        const data = await response.json();

        // แสดงผลลัพธ์
        resultArea.style.display = 'block';
        document.getElementById('fixed-code').textContent = data.fixed_code;
        document.getElementById('test-output').textContent = data.test_output || "No test output";

        const statusText = document.getElementById('status-text');
        if (data.status === 'success') {
            statusText.textContent = "SUCCESS ✅";
            statusText.className = "success";
        } else {
            statusText.textContent = "FAILED ❌";
            statusText.className = "error";
        }

    } catch (err) {
        alert("Error connecting to server: " + err);
    } finally {
        // ปิดโหมดโหลด
        btn.disabled = false;
        loading.style.display = 'none';
    }
}