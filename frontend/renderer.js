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
    const summaryEl = document.getElementById('summary-text');
    const knowledgeContainer = document.getElementById('knowledge-container');

    const code = codeInput.value;
    const error = errorInput.value;

    if (!code) {
        alert("Please enter code first.");
        return;
    }

    // 2. ปรับ UI เข้าโหมด Loading
    btn.disabled = true;
    btn.innerHTML = '<span class="btn-text">⏳ PROCESSING...</span>';
    
    document.getElementById('step-1').classList.add('active');
    document.getElementById('step-2').classList.add('active');
    
    // แสดงสถานะใน Terminal
    testOutputEl.innerHTML = `
        <span style="color: #6a9955;">$ initializing_agents...</span><br>
        <span style="color: #6a9955;">$ querying_knowledge_base...</span><br>
        <span style="color: #6a9955;">$ analyzing_code...</span><br>
        <span class="blink">_</span>
    `;
    
    // เคลียร์ Knowledge เก่า และโชว์สถานะรอ
    if (knowledgeContainer) {
        knowledgeContainer.innerHTML = `<div class="empty-knowledge">Scanning database...</div>`;
    }

    try {
        const response = await fetch('http://127.0.0.1:8000/debug', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: code, error: error })
        });

        const data = await response.json();

        // 3. แสดงผลลัพธ์
        emptyState.style.display = 'none';
        resultArea.style.display = 'flex'; 
        
        document.getElementById('step-3').classList.add('active');

        // แสดง Fixed Code
        if (fixedCodeEl) fixedCodeEl.textContent = data.fixed_code;
        
        // แสดง Summary
        if (summaryEl) {
            summaryEl.innerHTML = data.summary || "✅ The AI successfully identified and fixed the bug.";
        }
        
        // 🔥 ส่วนแสดง Knowledge Context (ใส่ตรงนี้ครับ)
        if (knowledgeContainer) {
            knowledgeContainer.innerHTML = ""; // เคลียร์ของเก่า

            if (data.knowledge && data.knowledge.length > 0) {
                data.knowledge.forEach(item => {
                    let scoreColor = '#64748b'; // สีเทา (Low)
                    let scoreText = 'Low Match';
                    
                    if (item.score >= 85) {
                        scoreColor = '#4ade80'; // สีเขียว (High Confidence)
                        scoreText = 'High Match';
                    } else if (item.score >= 60) {
                        scoreColor = '#facc15'; // สีเหลือง (Medium)
                        scoreText = 'Medium Match';
                    }

                    // สร้างการ์ด HTML
                    const card = document.createElement('div');
                    card.className = 'knowledge-card';
                    card.innerHTML = `
                        <div class="k-header">
                            <span class="k-title">📄 ${item.title}</span>
                            <span class="k-score" style="color: ${scoreColor}; border-color: ${scoreColor};">
                                ${item.score}% (${scoreText})
                            </span>
                        </div>
                        <div class="k-body">
                            ${item.summary}
                        </div>
                    `;
                    knowledgeContainer.appendChild(card);
                });
            } else {
                knowledgeContainer.innerHTML = `
                    <div class="empty-knowledge">
                        No similar bugs found in memory.<br>
                        (I will learn from this one!)
                    </div>
                `;
            }
        }

        // แสดง Terminal Output
        if (testOutputEl) {
            const timestamp = new Date().toLocaleTimeString();
            const logPrefix = `[${timestamp}] root@debugger:~/app# run_test.py\n`;
            const cleanOutput = data.test_output ? data.test_output.trim() : "No output returned.";
            
            testOutputEl.innerHTML = `
                <span style="color: #569cd6;">${logPrefix}</span>
                <span style="color: #444;">----------------------------------------</span>
                <br>${cleanOutput}
                <br><span style="color: #444;">----------------------------------------</span>
                <br><span style="color: #4caf50;">✔ Execution finished with exit code 0</span>
            `;
        }

        // อัปเดตสถานะ Badge
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