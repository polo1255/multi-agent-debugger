// file: frontend/renderer.js

async function fixCode() {
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
    const errorMsg = errorInput.value;

    if (!code) {
        alert("Please enter code first.");
        return;
    }

    // 1. เริ่มต้น: ล็อกปุ่ม
    btn.disabled = true;
    btn.innerHTML = `<span class="btn-spinner"></span> <span>PROCESSING...</span>`;

    // 2. เคลียร์หน้าจอ (Reset UI) 🧹
    if (resultArea) resultArea.style.display = 'none'; // ซ่อนผลลัพธ์เก่าทันที
    if (emptyState) emptyState.style.display = 'flex'; // โชว์หน้าว่างรอไว้ก่อน
    
    // ล้างข้อความเก่าทิ้งให้หมด
    if (fixedCodeEl) fixedCodeEl.textContent = "";
    if (summaryEl) summaryEl.innerHTML = "";
    
    // รีเซ็ต Knowledge Card
    if (knowledgeContainer) {
        knowledgeContainer.innerHTML = `<div class="empty-knowledge">Scanning database...</div>`;
    }

    // รีเซ็ต Step Progress Bar
    document.getElementById('step-3').classList.remove('active');
       
    document.getElementById('step-1').classList.add('active');
    document.getElementById('step-2').classList.add('active');
    
    // Clear Console
    testOutputEl.innerHTML = `
        <span style="color: #6a9955;">$ initializing_agents...</span><br>
        <span style="color: #6a9955;">$ querying_knowledge_base...</span><br>
        <span style="color: #6a9955;">$ analyzing_code...</span><br>
        <span class="blink">_</span>
    `;
    
    if (knowledgeContainer) {
        knowledgeContainer.innerHTML = `<div class="empty-knowledge">Scanning database...</div>`;
    }

    try {
        const response = await fetch('http://127.0.0.1:8000/debug', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: code, error: errorMsg })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            
            // ใช้เทคนิค split('\n') ที่แม่นยำกว่า
            const lines = buffer.split('\n'); 
            buffer = lines.pop() || ""; 

            for (const line of lines) {
                const trimmedLine = line.trim();
                if (!trimmedLine || !trimmedLine.startsWith("data:")) continue;

                const jsonStr = trimmedLine.replace(/^data:\s*/, '').trim();
                if (!jsonStr) continue;

                try {
                    const data = JSON.parse(jsonStr);

                    // --- อัปเดต UI ตามข้อมูลที่ได้ ---
                    
                    if (data.iteration) {
                        const loopEl = document.getElementById('loop-number');
                        if (loopEl) loopEl.textContent = data.iteration;
                    }

                    if (data.node) {
                        const nodeColor = data.node === 'qa_executor' ? '#bd93f9' : '#6a9955';
                        const logLine = `<div style="color: ${nodeColor}">$ running_${data.node}...</div>`;
                        
                        // เติม Log แบบไม่ลบ Blink Cursor
                        const currentHTML = testOutputEl.innerHTML;
                        testOutputEl.innerHTML = currentHTML.replace('<span class="blink">_</span>', '') + logLine + '<span class="blink">_</span>';
                        testOutputEl.scrollTop = testOutputEl.scrollHeight;
                    }

                    if (data.status === 'completed') {
                        emptyState.style.display = 'none';
                        resultArea.style.display = 'flex';
                        document.getElementById('step-3').classList.add('active');

                        if (fixedCodeEl) fixedCodeEl.textContent = data.fixed_code;
                        if (summaryEl) summaryEl.innerHTML = data.summary;

                        // 1. ดึง Elements กล่องเปรียบเทียบ
                        const originalErrorEl = document.getElementById('original-error-display');
                        const finalOutputEl = document.getElementById('final-output-display');
                        
                        // 2. เอาค่า Error เดิมมาโชว์ (กล่องแดง)
                        if (originalErrorEl) originalErrorEl.textContent = errorMsg; 
                        
                        // 3. เอาผลรัน Output ใหม่มาโชว์ (กล่องเขียว)
                        if (finalOutputEl) {
                            finalOutputEl.textContent = data.test_output || "No output returned (Check logs)";
                        }
                        
                        if (knowledgeContainer && data.knowledge) {
                            knowledgeContainer.innerHTML = ""; 
                            data.knowledge.forEach(item => {
                                const card = document.createElement('div');
                                card.className = 'knowledge-card';
                                card.innerHTML = `
                                    <div class="k-header">
                                        <span class="k-title">📄 ${item.title}</span>
                                        <span class="k-score">${item.score}% Match</span>
                                    </div>
                                    <div class="k-body">${item.summary}</div>
                                `;
                                knowledgeContainer.appendChild(card);
                            });
                        }
                        
                        // ✅ โค้ดที่ถูกต้อง (ใส่แทนของเดิม)
                        if (statusBadge) {
                            if (data.is_success) {
                                // ถ้าสำเร็จ ให้ขึ้นสีเขียว
                                statusBadge.innerHTML = "SUCCESS";
                                statusBadge.className = "badge success";
                            } else {
                                // ถ้าล้มเหลว ให้กลับเป็นสีปกติ (หรือสีแดง)
                                statusBadge.innerHTML = "FAILED";
                                statusBadge.className = "badge"; // หรือเพิ่ม class .error ใน css ถ้าอยากได้สีแดง
                                statusBadge.style.borderColor = "#ff5555"; // แถมสีแดงให้เผื่อยังไม่มี class error
                                statusBadge.style.color = "#ff5555";
                            }
                        }
                    }

                } catch (jsonError) {
                    console.warn("Skipping invalid JSON line:", jsonStr);
                }
            }
        }

    } catch (err) {
        // กรณี Error จริงๆ เช่น ต่อ Server ไม่ได้
        testOutputEl.innerHTML += `
            <br><br>
            <span style="color: #f44336;">❌ CRITICAL ERROR: Connection failed.</span><br>
            <span style="color: #888;">Details: ${err}</span>
        `;
    } finally {
        // 🔥 ส่วนสำคัญ: คืนสถานะปุ่มเสมอ ไม่ว่าจะสำเร็จหรือพัง
        btn.disabled = false;
        btn.innerHTML = `<span class="btn-text">▶ START DEBUG</span>`;
    }
}