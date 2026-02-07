from typing import TypedDict, List, Annotated
import operator

# นี่คือโครงสร้างข้อมูลกลาง (Shared Memory) ที่เอเจนต์ทุกตัวจะใช้งานร่วมกัน [cite: 27]
class AgentState(TypedDict):
    
    # 1. Current Code Base: ซอร์สโค้ดปัจจุบันที่กำลังแก้ไข [cite: 28]
    # เก็บเป็น string ยาวๆ ของไฟล์ code ทั้งไฟล์
    code_base: str 
    
    # 2. Error Context: ข้อมูล Stack Trace หรือ Log ของข้อผิดพลาด [cite: 29]
    # เอเจนต์จะใช้สิ่งนี้เพื่อรู้ว่าต้องแก้ตรงไหน
    error_context: str 
    
    # 3. Reflection Log: คำวิจารณ์จาก Reviewer [cite: 30]
    # ใช้ Annotated + operator.add เพื่อให้ข้อมูลใหม่ถูก "ต่อท้าย" (Append) ไม่ใช่เขียนทับ
    # ทำให้เราเก็บประวัติการวิจารณ์ได้ทุกรอบ
    reflection_logs: Annotated[List[str], operator.add]
    
    # 4. Iteration Counter: ตัวนับรอบเพื่อป้องกันการทำงานวนซ้ำไม่สิ้นสุด [cite: 31]
    iteration_count: int
    
    # เพิ่มเติม: สถานะความสำเร็จ (เพื่อให้ Graph รู้ว่าควรจบหรือไปต่อ)
    is_success: bool
    
    # เพิ่มเติม: ข้อมูลสำหรับรันใน Sandbox (ถ้าจำเป็น)
    test_output: str