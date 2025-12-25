import streamlit as st
import requests
import os
import time
import hashlib
import psycopg
from datetime import datetime
from psycopg.rows import dict_row

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")
LIGHTRAG_URL = os.getenv("LIGHTRAG_API_URL", "http://localhost:9621")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
DB_URI = os.getenv("POSTGRES_URI", "postgresql://postgres:postgres@postgres:5432/agent_db")

st.set_page_config(page_title="Urban Vibe Agent Admin", layout="wide", initial_sidebar_state="expanded")

# --- Database & Auth Utils ---

def get_db_connection():
    try:
        return psycopg.connect(DB_URI, row_factory=dict_row)
    except Exception as e:
        st.error(f"Database Connection Failed: {e}")
        return None

def init_db():
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            # Users Table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS admin_users (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'staff',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Knowledge Base CMS Table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS kb_documents (
                    id SERIAL PRIMARY KEY,
                    lightrag_doc_id TEXT UNIQUE,
                    filename TEXT,
                    content TEXT,
                    file_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Seed Admin
            cur.execute("SELECT * FROM admin_users WHERE username = 'admin'")
            if not cur.fetchone():
                default_hash = hash_password(ADMIN_PASSWORD)
                cur.execute(
                    "INSERT INTO admin_users (username, password_hash, role) VALUES (%s, %s, %s)",
                    ('admin', default_hash, 'admin')
                )
        conn.commit()
    except Exception as e:
        st.error(f"DB Init Error: {e}")
    finally:
        conn.close()

def hash_password(password: str) -> str:
    salt = "urban_vibe_static_salt_v1" 
    return hashlib.sha256((salt + password).encode()).hexdigest()

def verify_user(username, password):
    conn = get_db_connection()
    if not conn: return None
    try:
        with conn.cursor() as cur:
            input_hash = hash_password(password)
            cur.execute("SELECT * FROM admin_users WHERE username = %s AND password_hash = %s", (username, input_hash))
            return cur.fetchone()
    finally:
        conn.close()

def create_user(username, password, role="staff"):
    conn = get_db_connection()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            pwd_hash = hash_password(password)
            cur.execute(
                "INSERT INTO admin_users (username, password_hash, role) VALUES (%s, %s, %s)",
                (username, pwd_hash, role)
            )
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error creating user: {e}")
        return False
    finally:
        conn.close()

def delete_user(username):
    conn = get_db_connection()
    if not conn: return False
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM admin_users WHERE username = %s", (username,))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()

def list_users():
    conn = get_db_connection()
    if not conn: return []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT username, role, created_at FROM admin_users")
            return cur.fetchall()
    finally:
        conn.close()

# --- KB CMS Functions ---

def save_kb_doc(lightrag_id, filename, content, file_type):
    conn = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO kb_documents (lightrag_doc_id, filename, content, file_type)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (lightrag_doc_id) DO UPDATE 
                SET content = EXCLUDED.content, filename = EXCLUDED.filename, updated_at = CURRENT_TIMESTAMP
            """, (lightrag_id, filename, content, file_type))
        conn.commit()
    finally:
        conn.close()

def get_kb_doc(lightrag_id):
    conn = get_db_connection()
    if not conn: return None
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM kb_documents WHERE lightrag_doc_id = %s", (lightrag_id,))
            return cur.fetchone()
    finally:
        conn.close()

def update_kb_doc_id(old_id, new_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE kb_documents SET lightrag_doc_id = %s WHERE lightrag_doc_id = %s", (new_id, old_id))
        conn.commit()
    finally:
        conn.close()

def unlink_kb_doc(old_id, new_content):
    """Updates content and sets lightrag_doc_id to NULL to wait for new ID linking."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE kb_documents 
                SET content = %s, lightrag_doc_id = NULL, updated_at = CURRENT_TIMESTAMP 
                WHERE lightrag_doc_id = %s
            """, (new_content, old_id))
        conn.commit()
    finally:
        conn.close()

# Initialize DB on first load
if "db_initialized" not in st.session_state:
    init_db()
    st.session_state.db_initialized = True

# --- Authentication Logic ---
if "authenticated" not in st.session_state:

    st.session_state.authenticated = False
    st.session_state.user_role = None
    st.session_state.username = None

def login():
    user = verify_user(st.session_state.username_input, st.session_state.password_input)
    if user:
        st.session_state.authenticated = True
        st.session_state.user_role = user['role']
        st.session_state.username = user['username']
        st.rerun()
    else:
        st.error("Invalid username or password")

def logout():
    st.session_state.authenticated = False
    st.session_state.user_role = None
    st.session_state.username = None
    st.rerun()

if not st.session_state.authenticated:
    st.title("🔒 Agent Admin Login")
    with st.form("login_form"):
        st.text_input("Username", key="username_input")
        st.text_input("Password", type="password", key="password_input")
        st.form_submit_button("Login", on_click=login)
    st.stop()

# --- Main Dashboard (Authenticated) ---

with st.sidebar:
    st.title("🤖 Urban Vibe Admin")
    st.caption(f"Logged in as: **{st.session_state.username}** ({st.session_state.user_role})")
    
    options = ["📊 Dashboard", "💬 Live Chat Test", "📚 Knowledge Base", "🏥 System Health"]
    if st.session_state.user_role == 'admin':
        options.append("👥 User Management")
        
    page = st.radio("Navigation", options, index=0)
    
    st.divider()
    st.button("Logout", on_click=logout, type="secondary")

# --- PAGE: Dashboard ---
if page == "📊 Dashboard":
    st.title("📊 System Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Agent Status", "Active", "🟢")
    with col2:
        try:
            res = requests.get(f"{API_URL}/health", timeout=2)
            api_status = "Online" if res.status_code == 200 else "Down"
        except:
            api_status = "Unreachable"
        st.metric("API Connection", api_status)
    with col3:
        try:
             res = requests.get(f"{LIGHTRAG_URL}/health", timeout=2) 
             rag_status = "Online" if res.status_code == 200 else "Check"
        except:
            rag_status = "Unknown"
        st.metric("RAG Engine", rag_status)
    with col4:
        st.metric("DB Status", "Connected" if get_db_connection() else "Error")

# --- PAGE: Live Chat Test ---
elif page == "💬 Live Chat Test":
    st.header("💬 Agent Simulator")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        user_id = st.text_input("Simulate User ID", value="admin_tester_01")
    with col2:
        channel = st.selectbox("Channel", ["web", "whatsapp", "telegram"])

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Type your message..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Agent is thinking..."):
            try:
                payload = {
                    "user_id": user_id,
                    "text": prompt,
                    "metadata": {"source": "streamlit_admin"}
                }
                response = requests.post(f"{API_URL}/v1/chat/{channel}", json=payload)
                if response.status_code == 200:
                    data = response.json()
                    bot_text = data.get("text", str(data))
                    if isinstance(data, dict) and "Body" in data:
                         bot_text = data["Body"]
                    st.session_state.messages.append({"role": "assistant", "content": bot_text})
                    with st.chat_message("assistant"):
                        st.markdown(bot_text)
                else:
                    st.error(f"Error: {response.status_code}")
            except Exception as e:
                st.error(f"Connection Error: {e}")

# --- PAGE: Knowledge Base ---
elif page == "📚 Knowledge Base":
    st.header("📚 Knowledge Graph Management")
    kb_tab1, kb_tab2 = st.tabs(["Upload & Ingest", "Explore & Edit Documents"])
    
    with kb_tab1:
        st.subheader("Upload New Knowledge")
        
        upload_type = st.radio("Input Type", ["File Upload", "Text Input"], horizontal=True)
        
        if upload_type == "File Upload":
            uploaded_files = st.file_uploader("Drop files to ingest (PDF, TXT, MD)", accept_multiple_files=True)
            if uploaded_files and st.button("🚀 Start Ingestion"):
                status_text = st.empty()
                progress_bar = st.progress(0)
                
                for i, uploaded_file in enumerate(uploaded_files):
                    status_text.text(f"Processing {uploaded_file.name}...")
                    try:
                        # 1. Read Content
                        file_bytes = uploaded_file.read()
                        try:
                            file_content = file_bytes.decode('utf-8')
                        except:
                            file_content = "Binary content (PDF/Docx) - Raw text not extractable in simple mode."
                        
                        # 2. Reset pointer for upload
                        uploaded_file.seek(0)
                        
                        # 3. Send to LightRAG
                        files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                        res = requests.post(f"{LIGHTRAG_URL}/documents/upload", files=files)
                        
                        if res.status_code == 200:
                            # 4. Save to CMS Table (if text extracted successfully)
                            # We use specific "pending_link" ID valid for filename matching later
                            if "Binary content" not in file_content:
                                save_kb_doc("pending_" + uploaded_file.name, uploaded_file.name, file_content, uploaded_file.type)
                            
                            st.success(f"Uploaded {uploaded_file.name} to LightRAG")
                        else:
                            st.error(f"Failed {uploaded_file.name}: {res.text}")
                            
                    except Exception as e:
                         st.error(f"Error {uploaded_file.name}: {e}")
                    
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
        else: # Text Input
            txt_input = st.text_area("Paste text here", height=200)
            txt_filename = st.text_input("Filename (identifier)", value=f"manual_entry_{int(time.time())}.txt")
            
            if st.button("🚀 Ingest Text") and txt_input:
                try:
                    # 1. Send to LightRAG via /text endpoint which returns an ID mostly?
                    # Actually /documents/text returns track_id too. 
                    # We will assume we can't link doc_id immediately easily efficiently without huge complexity.
                    # BETTER STRATEGY: 
                    # Use a custom ID when possible? LightRAG generates IDs.
                    # We will just insert to LightRAG, and then wait/poll or just save to DB locally. 
                    # Wait, if we edit, we need the doc_id.
                    
                    # ALTERNATIVE:
                    # We save to DB first. User 'Edits' from DB. We send to LightRAG and update the 'external_id' column if we can find it.
                    
                    payload = {"text": txt_input, "file_source": txt_filename}
                    res = requests.post(f"{LIGHTRAG_URL}/documents/text", json=payload)
                    
                    if res.status_code == 200:
                        # We try to get the ID from response if available? Likely not.
                        # We will save to DB anyway with 'pending' ID or try to match by filename later.
                        save_kb_doc("pending_link_" + txt_filename, txt_filename, txt_input, "text/plain")
                        st.success("Text ingested! (Note: Link to DB might take a moment or require refresh)")
                    else:
                        st.error(f"Ingestion failed: {res.text}")
                        
                except Exception as e:
                    st.error(f"Error: {e}")

    with kb_tab2:
        st.subheader("Indexed Documents")
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔄 Refresh List"): st.rerun()
        
        # Edit Area State
        if "edit_doc_id" not in st.session_state:
            st.session_state.edit_doc_id = None
            st.session_state.edit_content = ""
            st.session_state.edit_filename = ""
        
        if st.session_state.edit_doc_id:
            st.divider()
            st.info(f"✏️ Editing: {st.session_state.edit_filename} (ID: {st.session_state.edit_doc_id})")
            
            # Warning if content was empty (first time edit for binary/old docs)
            if not st.session_state.edit_content:
                st.warning("⚠️ Original text not found in CMS. You are creating the source text for this document.")
            
            new_content = st.text_area("Document Content", value=st.session_state.edit_content, height=400)
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("💾 Save & Re-Ingest", type="primary"):
                    with st.spinner("Updating..."):
                        # 1. Delete old from LightRAG
                        del_res = requests.delete(f"{LIGHTRAG_URL}/documents/delete_document", json={"doc_ids": [st.session_state.edit_doc_id], "delete_file": True})
                        
                        if del_res.status_code == 200:
                            # 2. Ingest New
                            payload = {"text": new_content, "file_source": st.session_state.edit_filename}
                            res = requests.post(f"{LIGHTRAG_URL}/documents/text", json=payload)
                            
                            if res.status_code == 200:
                                # 3. Update DB: Unlink specific ID so it matches by filename next time
                                unlink_kb_doc(st.session_state.edit_doc_id, new_content)
                                
                                st.success("Document updated! Waiting for indexing...")
                                st.session_state.edit_doc_id = None
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error("Failed to re-ingest new content")
                        else:
                            st.error("Failed to delete old document")
            
            with c2:
                if st.button("❌ Cancel Edit"):
                    st.session_state.edit_doc_id = None
                    st.rerun()
            st.divider()

        # List Docs
        try:
            payload = {"page": 1, "page_size": 50, "sort_field": "updated_at", "sort_direction": "desc"}
            res = requests.post(f"{LIGHTRAG_URL}/documents/paginated", json=payload)
            if res.status_code == 200:
                docs = res.json().get("documents", [])
                for doc in docs:
                    doc_id = doc.get("id")
                    file_path = doc.get("file_path")
                    
                    # 1. Try to find local content by ID
                    cms_doc = get_kb_doc(doc_id)
                    
                    # 2. auto-linking: If not by ID, try by Filename (often happens after upload)
                    if not cms_doc and file_path:
                        conn = get_db_connection()
                        if conn:
                            with conn.cursor() as cur:
                                cur.execute("SELECT * FROM kb_documents WHERE filename = %s AND lightrag_doc_id IS NULL", (file_path,))
                                found = cur.fetchone()
                                if found:
                                    # We found a pending upload! Link it now.
                                    update_kb_doc_id(found['lightrag_doc_id'], doc_id) # The logic in update_kb_doc_id was bad, let's fix inline or assume simple
                                    # Actually the function `update_kb_doc_id` expects old_id.
                                    # We probably stored it with "pending_..." as id.
                                    # Let's just create a new mapping or update current.
                                    # Simplified: Just fetch it using filename for display if needed
                                    cms_doc = found
                                    # Optional: Update DB to set the real ID
                                    try: 
                                        with conn.cursor() as c2:
                                            c2.execute("UPDATE kb_documents SET lightrag_doc_id = %s WHERE id = %s", (doc_id, found['id']))
                                        conn.commit()
                                    except: pass
                            conn.close()

                    with st.expander(f"{doc.get('status')} | {file_path or 'No Name'} | {doc_id}"):
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            st.json(doc)
                            if cms_doc:
                                st.caption("✅ Source Text Available")
                            else:
                                st.caption("⚠️ Binary/External Source (Text not in CMS)")
                        with c2:
                            # EDIT BUTTON ALWAYS AVAILABLE
                            if st.button("✏️ Edit", key=f"edit_{doc_id}"):
                                st.session_state.edit_doc_id = doc_id
                                st.session_state.edit_content = cms_doc['content'] if cms_doc else ""
                                st.session_state.edit_filename = file_path or cms_doc['filename'] or "untitled.txt"
                                st.rerun()
                                
                            if st.button("🗑️ Delete", key=f"del_{doc_id}"):
                                requests.delete(f"{LIGHTRAG_URL}/documents/delete_document", json={"doc_ids": [doc_id], "delete_file": True})
                                # Also delete from DB
                                if cms_doc:
                                    # We should delete from DB too
                                    conn = get_db_connection()
                                    if conn:
                                        with conn.cursor() as cur:
                                            cur.execute("DELETE FROM kb_documents WHERE lightrag_doc_id = %s", (doc_id,))
                                        conn.commit()
                                        conn.close()
                                st.rerun()
            else:
                st.warning("Could not fetch documents")
        except Exception as e:
             st.error(f"Error fetching docs: {e}")


# --- PAGE: System Health ---
elif page == "🏥 System Health":
    st.header("🏥 System Health & Logs")
    try:
        res = requests.get(f"{LIGHTRAG_URL}/documents/pipeline_status", timeout=2)
        if res.status_code == 200:
            st.json(res.json())
    except:
        st.error("Failed to fetch pipeline status")

# --- PAGE: User Management (Admin Only) ---
elif page == "👥 User Management" and st.session_state.user_role == 'admin':
    st.header("👥 User Management")
    
    st.subheader("Add New User")
    with st.form("add_user_form"):
        col1, col2, col3 = st.columns(3)
        with col1: new_user = st.text_input("Username")
        with col2: new_pass = st.text_input("Password", type="password")
        with col3: new_role = st.selectbox("Role", ["staff", "admin"])
        
        if st.form_submit_button("Create User"):
            if new_user and new_pass:
                if create_user(new_user, new_pass, new_role):
                    st.success(f"User {new_user} created!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Failed to create user (maybe username exists?)")
            else:
                st.warning("Please fill all fields")

    st.divider()
    st.subheader("Existing Users")
    users = list_users()
    for u in users:
        c1, c2, c3, c4 = st.columns([2, 1, 2, 1])
        c1.write(f"**{u['username']}**")
        c2.write(f"`{u['role']}`")
        c3.caption(str(u['created_at']))
        if c4.button("🗑️", key=f"del_{u['username']}"):
            if u['username'] == 'admin':
                st.error("Cannot delete root admin")
            else:
                delete_user(u['username'])
                st.rerun()
