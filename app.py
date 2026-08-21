def login():
    st.set_page_config(page_title="Login - Restaurant Ledger", layout="centered")
    st.markdown("### 🔐 Restaurant Management Login")
    st.info("Google Sheets Connected Cloud Ledger")
    
    with st.form("login_form"):
        user = st.text_input("Username").strip().lower()
        pwd = st.text_input("Password", type="password").strip()
        btn = st.form_submit_button("Log In", type="primary")
        
        if btn:
            df_users = get_sheet_data("users", USERS_COLS)
            
            # Format columns cleanly to string
            df_users['username_clean'] = df_users['username'].astype(str).str.strip().str.lower()
            df_users['password_clean'] = df_users['password'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            
            user_row = df_users[df_users['username_clean'] == user]
            
            if not user_row.empty and user_row.iloc[0]['password_clean'] == pwd:
                st.session_state.logged_in = True
                st.session_state.username = user
                st.session_state.role = str(user_row.iloc[0]['role']).strip().lower()
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid Username or Password. Please try again.")
