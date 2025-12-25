import requests
import sys

LIGHTRAG_URL = "http://localhost:9621"

def reset_lightrag():
    print(f"Connecting to LightRAG at {LIGHTRAG_URL}...")
    
    # 1. Clear all documents
    try:
        print("Attempting to delete all documents...")
        response = requests.delete(f"{LIGHTRAG_URL}/documents")
        if response.status_code == 200:
            print("Successfully cleared all documents.")
        else:
            print(f"Error clearing documents: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    # 2. Clear cache
    try:
        print("Clearing cache...")
        response = requests.post(f"{LIGHTRAG_URL}/documents/clear_cache", json={})
        if response.status_code == 200:
            print("Successfully cleared cache.")
        else:
            print(f"Error clearing cache: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Cache clear failed: {e}")

if __name__ == "__main__":
    reset_lightrag()
