# file: database/vector_store.py

import os
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()

# ตั้งค่า Client และที่เก็บข้อมูล
PERSIST_PATH = os.path.join(os.getcwd(), "chroma_db_store")
client = chromadb.PersistentClient(path=PERSIST_PATH)

# เลือก Embedding Function (ใช้ OpenAI เป็นมาตรฐาน เพราะเสถียรสุดสำหรับ Vector)
# แต่ถ้าไม่มี Key ให้ fallback ไปใช้แบบ Local (จะได้ไม่ error)
try:
    if os.getenv("OPENAI_API_KEY"):
        ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_name="text-embedding-3-small"
        )
    else:
        # กรณีไม่มี OpenAI Key ให้ใช้ default (all-MiniLM-L6-v2) ฟรีและรันในเครื่อง
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
except Exception as e:
    print(f"⚠️ Embedding Setup Warning: {e}")
    ef = None # เดี๋ยวไป handle ต่อ

# สร้าง Collection
collection = client.get_or_create_collection(
    name="debug_knowledge_base",
    embedding_function=ef
)

def search_similar_bugs(error_msg, code_snippet, limit=3):
    """ค้นหาบั๊กที่คล้ายกันจากฐานข้อมูล"""
    query = f"Error: {error_msg}\nCode: {code_snippet[:300]}" # เอาแค่ 300 ตัวแรกพอ
    
    try:
        results = collection.query(
            query_texts=[query],
            n_results=limit
        )
        
        knowledge_items = []
        if results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                meta = results['metadatas'][0][i]
                dist = results['distances'][0][i]
                
                # แปลง Distance เป็น % ความเหมือน (คร่าวๆ)
                score = max(0, min(100, int((1.5 - dist) * 100))) 
                
                knowledge_items.append({
                    "title": meta.get("title", "Unknown Issue"),
                    "summary": doc,
                    "score": score,
                    "fix_id": results['ids'][0][i]
                })
        return knowledge_items
        
    except Exception as e:
        print(f"❌ Vector Search Error: {e}")
        return []

def save_bug_report(error_msg, code, fixed_code, summary):
    """บันทึกข้อมูลลงฐานข้อมูล"""
    import uuid
    import datetime
    
    # สกัดชื่อ Error เช่น "IndexError"
    title = error_msg.split(":")[0] if ":" in error_msg else "Runtime Error"
    
    doc_content = f"Summary: {summary}\nOriginal Code: {code}\nFixed Code: {fixed_code}"
    
    try:
        collection.add(
            documents=[doc_content],
            metadatas=[{
                "title": title,
                "timestamp": str(datetime.datetime.now()),
                "error_type": title
            }],
            ids=[str(uuid.uuid4())]
        )
        print(f"💾 Knowledge Saved: {title}")
    except Exception as e:
        print(f"❌ Save Knowledge Error: {e}")