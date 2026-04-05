import streamlit as st
import streamlit_authenticator as stauth
import sqlite3
import pandas as pd
from app import app 
import time
import difflib

# --- 1. DATABASE SYSTEM ---
def init_db():
    conn = sqlite3.connect('nexus.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, name TEXT, password TEXT, email TEXT)''')
    
    # History Table with project_name support
    c.execute('''CREATE TABLE IF NOT EXISTS history 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT, 
                  project_name TEXT,
                  raw_input TEXT, 
                  requirements TEXT, 
                  gap_analysis TEXT, 
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def save_to_history(username, proj_name, raw_in, reqs, gaps):
    conn = sqlite3.connect('nexus.db')
    c = conn.cursor()
    c.execute("INSERT INTO history (username, project_name, raw_input, requirements, gap_analysis) VALUES (?, ?, ?, ?, ?)",
              (username, proj_name, raw_in, reqs, gaps))
    conn.commit()
    conn.close()

def delete_history_item(history_id):
    conn = sqlite3.connect('nexus.db')
    c = conn.cursor()
    c.execute("DELETE FROM history WHERE id=?", (history_id,))
    conn.commit()
    conn.close()

def get_user_history(username):
    conn = sqlite3.connect('nexus.db')
    df = pd.read_sql_query("SELECT * FROM history WHERE username=? ORDER BY timestamp DESC", conn, params=(username,))
    conn.close()
    
    if not df.empty:
        # Create a dynamic display name for UI
        df['display_name'] = df.apply(
            lambda row: f"{row['timestamp']} | {row['project_name'] if row['project_name'] else row['requirements'][:30] + '...'}", 
            axis=1
        )
    return df

def prepare_download_text(reqs, gaps):
    """Formats the AI output into a clean document for export."""
    report = f"NexusBA Requirements Report\n"
    report += f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    report += f"Draft Requirements\n{reqs}\n\n"
    report += f"---\n\nTechnical Audit and Gaps\n{gaps}\n"
    return report

def add_user(username, name, password, email):
    try:
        conn = sqlite3.connect('nexus.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, name, password, email) VALUES (?, ?, ?, ?)",
                  (username, name, password, email))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def get_all_users():
    conn = sqlite3.connect('nexus.db')
    try:
        df = pd.read_sql_query("SELECT * FROM users", conn)
        conn.close()
    except:
        conn.close()
        return {"usernames": {}}
    
    credentials = {"usernames": {}}
    if not df.empty:
        for _, row in df.iterrows():
            credentials["usernames"][str(row['username'])] = {
                "name": str(row['name']),
                "password": str(row['password']),
                "email": str(row['email']),
                "logged_in": False 
            }
    return credentials

# Initialization
init_db()
user_credentials = get_all_users()

# --- 2. AUTHENTICATION ---
authenticator = stauth.Authenticate(
    user_credentials,
    'nexus_final_v3', 
    'nexus_key_v3',
    cookie_expiry_days=1
)

# --- 3. UI CONFIG ---
st.set_page_config(page_title="NexusBA", layout="wide")

if "is_guest" not in st.session_state:
    st.session_state["is_guest"] = False
if "compare_mode" not in st.session_state:
    st.session_state["compare_mode"] = False

# --- 4. LOGIN / SIGNUP ---
if not st.session_state.get("authentication_status") and not st.session_state["is_guest"]:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("NexusBA")
        tab_login, tab_signup = st.tabs(["Login", "Create Account"])
        with tab_login:
            if not user_credentials["usernames"]:
                st.info("No accounts found. Please create one.")
            else:
                authenticator.login(location='main', key='Login_Form')
            st.divider()
            if st.button("Continue as Guest", use_container_width=True):
                st.session_state["is_guest"] = True
                st.rerun()
        with tab_signup:
            with st.form("register_form"):
                reg_email = st.text_input("Email")
                reg_user = st.text_input("Username")
                reg_name = st.text_input("Full Name")
                reg_pw = st.text_input("Password", type="password")
                if st.form_submit_button("Register"):
                    if reg_user and reg_pw:
                        hashed_password = stauth.Hasher.hash(reg_pw)
                        if add_user(reg_user, reg_name, hashed_password, reg_email):
                            st.success("Success! Please log in.")
                            time.sleep(1)
                            st.rerun()

# --- 5. MAIN DASHBOARD ---
if st.session_state.get("authentication_status") or st.session_state["is_guest"]:
    is_member = st.session_state.get("authentication_status")
    username = st.session_state.get("username", "guest_user")
    display_name = st.session_state.get("name", "Guest")
    
    with st.sidebar:
        st.title("NexusBA")
        st.write(f"Logged in: **{display_name}**")
        
        if is_member:
            authenticator.logout('Logout', 'sidebar')
            st.divider()
            st.subheader("Version History")
            history_df = get_user_history(username)
            
            if not history_df.empty:
                selected_label = st.selectbox("Select past version:", history_df['display_name'].tolist())
                past_row = history_df[history_df['display_name'] == selected_label].iloc[0]
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("Compare", use_container_width=True):
                        st.session_state['compare_mode'] = True
                        st.session_state['past_reqs'] = past_row['requirements']
                with col_btn2:
                    if st.button("Delete", use_container_width=True):
                        delete_history_item(past_row['id'])
                        st.rerun()
                
                if st.session_state['compare_mode']:
                    if st.button("Clear Comparison", use_container_width=True):
                        st.session_state['compare_mode'] = False
                        st.rerun()
            else:
                st.caption("No history saved yet.")
        else:
            st.warning("Guest Mode: History and Search disabled.")
            if st.button("Sign In / Register"):
                st.session_state["is_guest"] = False
                st.rerun()

    st.title("Requirements Dashboard")
    
    # SEARCH BAR LOGIC
    if is_member:
        search_query = st.text_input("Search past projects...")
        if search_query:
            results = history_df[history_df['requirements'].str.contains(search_query, case=False, na=False)]
            if not results.empty:
                st.caption(f"Showing {len(results[:3])} results:")
                for idx, row in results.head(3).iterrows():
                    with st.expander(f"Folder: {row['display_name']}"):
                        st.markdown(row['requirements'])
            else:
                st.error("No matches found.")
    else:
        st.text_input("Search past projects", placeholder="Login to search history", disabled=True)

    # INPUT SECTION
    col_name, col_spacer = st.columns([1, 1])
    with col_name:
        project_name = st.text_input("Project Name (Optional):", placeholder="e.g., Q3 Payment Update")

    user_input = st.text_area("Stakeholder Notes:", height=200, placeholder="Paste raw notes, transcripts, or ideas here...")

    if st.button("Process Requirements", use_container_width=True):
        if user_input:
            with st.spinner("Agentic BA at work..."):
                result = app.invoke({"raw_input": user_input})
                
                if is_member:
                    save_to_history(username, project_name, user_input, result['draft_requirements'], result['gap_analysis'])
                
                st.session_state['current_reqs'] = result['draft_requirements']
                st.session_state['current_gaps'] = result['gap_analysis']
        else:
            st.error("Please enter stakeholder notes to continue.")

    # --- RESULTS DISPLAY ---
    if 'current_reqs' in st.session_state:
        # Prepare the file content
        final_report = prepare_download_text(
            st.session_state['current_reqs'], 
            st.session_state['current_gaps']
        )
        
        col_header, col_download = st.columns([3, 1])
        with col_header:
            st.subheader("Analysis Results")
        with col_download:
            st.download_button(
                label="Export as .md",
                data=final_report,
                file_name=f"NexusBA_{project_name.replace(' ', '_') if project_name else 'Export'}.md",
                mime="text/markdown",
                use_container_width=True
            )

        if st.session_state.get('compare_mode'):
            st.subheader("Version Comparison")
            diff = difflib.ndiff(
                st.session_state['past_reqs'].splitlines(), 
                st.session_state['current_reqs'].splitlines()
            )
            st.code("\n".join(diff)) 
        
        t1, t2 = st.tabs(["Requirements Doc", "Audit and Gaps"])
        with t1:
            st.markdown(st.session_state['current_reqs'])
        with t2:
            st.markdown(st.session_state['current_gaps'])