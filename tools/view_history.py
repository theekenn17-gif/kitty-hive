import os
import sys
import chromadb

# Ensure absolute project boundaries load smoothly
PROJECT_ROOT = "/root/KITTY_HIVE"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def view_hive_memory_history():
    db_path = os.path.join(PROJECT_ROOT, "memory/database")
    if not os.path.exists(db_path):
        print(f"❌ Error: ChromaDB database directory not found at '{db_path}'.")
        return

    print("🧠 Initializing ChromaDB Storage Reader...")
    try:
        # Initialize native persistent storage connection matrix
        client = chromadb.PersistentClient(path=db_path)
        collections = client.list_collections()
        
        if not collections:
            print("📂 Memory Database is currently empty. Run some tasks inside queen.py first!")
            return

        print(f"📂 Found {len(collections)} active agent memory collections.\n")
        
        for collection in collections:
            print(f"════════════════════════════════════════════════════════════════")
            print(f"🐝 COLLECTION CHANNEL: {collection.name.upper()}")
            print(f"════════════════════════════════════════════════════════════════")
            
            # Fetch all stored items inside this explicit agent bucket space
            data = collection.get()
            docs = data.get("documents", [])
            ids = data.get("ids", [])
            
            if not docs:
                print("   (No recorded experiences stored inside this module yet.)\n")
                continue
                
            # Loop through records and print clean outputs
            for idx, (record_id, document) in enumerate(zip(ids, docs), 1):
                print(f"\n📍 Record [{idx}] | ID: {record_id}")
                print(f"----------------------------------------------------------------")
                print(document.strip())
                print(f"----------------------------------------------------------------")
            print("\n")

    except Exception as e:
        print(f"❌ History Extraction Exception encountered: {e}")

if __name__ == "__main__":
    view_hive_memory_history()
