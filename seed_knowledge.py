# file: seed_knowledge.py

from database.vector_store import save_bug_report
import time

# --- คลังความรู้เทพ (God-Tier Knowledge) ---
# คุณสามารถเพิ่ม Pattern ที่อยากให้ AI รู้จักที่นี่
knowledge_base = [
    {
        "title": "Optimized Search (Binary Search)",
        "error": "PerformanceWarning: Linear search is O(n), too slow for large sorted lists.",
        "buggy_code": """
def find_item(sorted_list, target):
    for i, item in enumerate(sorted_list):
        if item == target:
            return i
    return -1
""",
        "fixed_code": """
import bisect

def find_item(sorted_list, target):
    # Use Binary Search O(log n) instead of Linear Search O(n)
    i = bisect.bisect_left(sorted_list, target)
    if i != len(sorted_list) and sorted_list[i] == target:
        return i
    return -1
""",
        "summary": "Replaced O(n) loop with Python's built-in bisect module (Binary Search) for O(log n) performance on sorted data."
    },
    {
        "title": "Thread-Safe Singleton Pattern",
        "error": "RaceCondition: Singleton instance created multiple times in multi-threaded env.",
        "buggy_code": """
class Singleton:
    _instance = None
    
    @staticmethod
    def get_instance():
        if Singleton._instance == None:
            Singleton._instance = Singleton()
        return Singleton._instance
""",
        "fixed_code": """
import threading

class Singleton:
    _instance = None
    _lock = threading.Lock()
    
    @staticmethod
    def get_instance():
        # Double-checked locking pattern
        if Singleton._instance is None:
            with Singleton._lock:
                if Singleton._instance is None:
                    Singleton._instance = Singleton()
        return Singleton._instance
""",
        "summary": "Implemented Double-Checked Locking mechanism to ensure Singleton is thread-safe and efficient."
    },
    {
        "title": "SQL Injection Prevention",
        "error": "SecurityVulnerability: SQL Injection detected in raw query string.",
        "buggy_code": """
def get_user(username):
    # DANGEROUS: Direct string formatting
    query = f"SELECT * FROM users WHERE name = '{username}'"
    cursor.execute(query)
""",
        "fixed_code": """
def get_user(username):
    # SAFE: Use parameterized queries
    query = "SELECT * FROM users WHERE name = %s"
    cursor.execute(query, (username,))
""",
        "summary": "Replaced f-string SQL construction with parameterized queries to prevent SQL Injection attacks."
    }
]

def seed_data():
    print("🌱 Starting Knowledge Seeding...")
    print(f"📦 Found {len(knowledge_base)} God-Tier patterns.")
    
    count = 0
    for item in knowledge_base:
        print(f"   - Injecting: {item['title']}...")
        
        # เรียกใช้ฟังก์ชันเดิมที่เรามีอยู่แล้ว
        success = save_bug_report(
            error_msg=item['error'],
            code=item['buggy_code'].strip(),
            fixed_code=item['fixed_code'].strip(),
            summary=item['summary']
        )
        
        if success:
            count += 1
            
    print(f"\n✅ Seeding Complete! Added {count} new patterns to ChromaDB.")
    print("🧠 Now your AI knows Kung Fu.")

if __name__ == "__main__":
    seed_data()