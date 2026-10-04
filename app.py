import streamlit as st
import pandas as pd
import io
import os
import time
import base64
from PIL import Image
from datetime import date, datetime
from streamlit_gsheets import GSheetsConnection

# -------------------------------------------------------------
# Favicon and Page Config with PIL Image
# -------------------------------------------------------------
logo_img = None
logo_b64 = ""

if os.path.exists("logo.png"):
    try:
        logo_img = Image.open("logo.png")
        with open("logo.png", "rb") as img_f:
            logo_b64 = base64.b64encode(img_f.read()).decode("utf-8")
    except Exception:
        logo_img = "🍽️"
else:
    logo_img = "🍽️"

st.set_page_config(
    page_title="The 4-Way Kitchen Ledger",
    page_icon=logo_img,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -------------------------------------------------------------
# Mobile Home Screen Icon (PWA Touch Icon) & Custom CSS
# -------------------------------------------------------------
if logo_b64:
    st.markdown(f"""
    <head>
        <link rel="icon" type="image/png" href="data:image/png;base64,{logo_b64}">
        <link rel="apple-touch-icon" href="data:image/png;base64,{logo_b64}">
        <link rel="shortcut icon" href="data:image/png;base64,{logo_b64}">
    </head>
    """, unsafe_allow_html=True)

st.markdown("""
<style>
@keyframes blinker {
    0% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.3; transform: scale(0.85); }
    100% { opacity: 1; transform: scale(1); }
}
.blink-dot {
    display: inline-block;
    width: 9px;
    height: 9px;
    background-color: #22c55e;
    border-radius: 50%;
    margin-right: 6px;
    box-shadow: 0 0 8px #22c55e;
    animation: blinker 1.4s infinite ease-in-out;
}
.off-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    background-color: #94a3b8;
    border-radius: 50%;
    margin-right: 6px;
}

/* Light-On Navigation Buttons */
div[data-testid="stButton"] button {
    height: 48px !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    border: 1.5px solid #cbd5e1 !important;
    background-color: #f8fafc !important;
    color: #334155 !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.04) !important;
    transition: all 0.25s ease-in-out !important;
}

div[data-testid="stButton"] button:hover {
    border-color: #94a3b8 !important;
    background-color: #f1f5f9 !important;
    color: #0f172a !important;
}

/* Glowing Neon Active State */
div[data-testid="stButton"] button[kind="primary"] {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
    color: #38bdf8 !important;
    border: 1.5px solid #38bdf8 !important;
    box-shadow: 0 0 16px rgba(56, 189, 248, 0.45), inset 0 0 8px rgba(56, 189, 248, 0.2) !important;
    text-shadow: 0 0 10px rgba(56, 189, 248, 0.75) !important;
    font-weight: 700 !important;
}
html, body, [data-testid="stAppViewContainer"] {
    overscroll-behavior-y: contain !important;
    overscroll-behavior: contain !important;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# Google Sheets Connection Setup
# -------------------------------------------------------------
conn = st.connection("gsheets", type=GSheetsConnection)

def get_sheet_data(worksheet_name, expected_cols):
    try:
        df = conn.read(worksheet=worksheet_name, ttl=3600)
        if df is None or df.empty:
            return pd.DataFrame(columns=expected_cols)
        df = df.dropna(how='all')
        for col in expected_cols:
            if col not in df.columns:
                df[col] = "-"
        return df[expected_cols]
    except Exception:
        return pd.DataFrame(columns=expected_cols)

def update_sheet_data(worksheet_name, df):
    df_clean = df.copy()
    try:
        conn.update(worksheet=worksheet_name, data=df_clean)
    except Exception:
        try:
            conn._instance._spreadsheet.add_worksheet(title=worksheet_name, rows=100, cols=10)
            conn.update(worksheet=worksheet_name, data=df_clean)
        except Exception:
            pass
    st.cache_data.clear()


# Default Schemas
USERS_COLS = ["username", "password", "role", "last_seen"]
SALES_COLS = ["id", "entry_date", "counter_type", "product_name", "quantity", "amount", "created_by"]
EXPENSES_COLS = ["id", "entry_date", "category", "particulars", "amount", "created_by"]
CAPITAL_COLS = ["id", "entry_date", "partner_name", "amount", "created_by"]
INVENTORY_COLS = ["id", "entry_date", "item_name", "opening_stock", "added_stock", "closing_stock", "sold_quantity", "created_by"]
SETTLEMENTS_COLS = ["id", "entry_date", "amount", "note", "created_by"]

ALL_PARTNERS = ["Abhijit", "Jit", "Debasis", "Sumit"]

PRODUCT_OPTIONS = [
    "Total Food",
    "Chicken Pakora Full (Rs. 120)",
    "Chicken Pakora Half (Rs. 80)",
    "Chicken Gola Mete Jhal",
    "Chana Masala / Chat",
    "Dim Curry / Boil",
    "Cigarette",
    "Gutkha",
    "Water & Cold Drinks",
    "Badam Chaat (Rs. 60)",
    "Papad Roast (Rs. 10)",
    "French Fries (Rs. 60)",
    "Green Salad (Rs. 50)",
    "Veg Pakora (Rs. 90)",
    "Crispy Chilli Babycorn (Rs. 140)",
    "Chilli Mushroom (Rs. 160)",
    "Egg Omelette (Rs. 40)",
    "Egg Poach (Rs. 40)",
    "Egg Bhujia (Rs. 40)",
    "Egg Pakora (Rs. 60)",
    "Chicken Fry (Rs. 160)",
    "Crispy Chicken (Rs. 160)",
    "Chicken 65 (Rs. 160)",
    "Chicken Chatpata (Rs. 160)",
    "Chicken Kosha Full (Rs. 120)",
    "Chicken Kosha Half (Rs. 70)",
    "Chilli Chicken Full (Rs. 150)",
    "Chilli Chicken Half (Rs. 90)",
    "Chicken Bharta (Rs. 150)",
    "Chicken Do Pyaza (Rs. 150)",
    "Chicken Masala (Rs. 150)",
    "Roti (Rs. 5)",
    "Other"
]

EXPENSE_CATEGORIES = [
    "Chicken",
    "Fish",
    "Mushroom & Babycorn",
    "Green Vegetables",
    "Grocery & Spices",
    "Water Bottle",
    "Cold Drinks",
    "Gas Cylinder",
    "Rent & Utility Bill",
    "Staff Salary",
    "Staff Advance",
    "Plates & Cutlery",
    "Petty Cash",
    "Partner Profit Withdrawal",
    "Miscellaneous"
]

TRACKED_ITEMS = [
    "Egg (Pcs)", 
    "Water Bottle 1L", 
    "Water Bottle 500 ml", 
    "Campa Rs. 20", 
    "Campa Rs. 10"
]

def parse_db_date(val):
    if isinstance(val, date):
        return val
    try:
        return datetime.strptime(str(val)[:10], "%Y-%m-%d").date()
    except Exception:
        return date.today()

# -------------------------------------------------------------
# Authentication Flow & Login Screen
# -------------------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""

if "current_nav_section" not in st.session_state:
    st.session_state.current_nav_section = "📊 Reports & Analytics"

def update_user_heartbeat(username):
    try:
        df_u = get_sheet_data("users", USERS_COLS)
        df_u['username_clean'] = df_u['username'].astype(str).str.strip().str.lower()
        idx = df_u[df_u['username_clean'] == username.lower()].index
        if not idx.empty:
            df_u.loc[idx[0], 'last_seen'] = int(time.time())
            save_cols = [c for c in USERS_COLS if c in df_u.columns]
            update_sheet_data("users", df_u[save_cols])
    except Exception:
        pass

def login():
    l_c1, l_c2, l_c3 = st.columns([1, 1.8, 1])
    with l_c2:
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        if os.path.exists("logo.png"):
            st.image("logo.png", use_container_width=True)
        else:
            st.markdown("<h2 style='text-align: center; color: #f59e0b;'>🍽️ THE 4-WAY KITCHEN</h2>", unsafe_allow_html=True)
            
        st.markdown("<p style='text-align: center; color: #94a3b8; font-weight: 500; margin-top: -10px;'>Where Ideas Become Flavour • Cloud Ledger</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            user = st.text_input("Username").strip().lower()
            pwd = st.text_input("Password", type="password").strip()
            btn = st.form_submit_button("Log In", type="primary", use_container_width=True)
            
            if btn:
                df_users = get_sheet_data("users", USERS_COLS)
                df_users['username'] = df_users['username'].astype(str).str.strip().str.lower()
                df_users['password'] = df_users['password'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                
                user_row = df_users[df_users['username'] == user]
                
                if not user_row.empty and user_row.iloc[0]['password'] == pwd:
                    st.session_state.logged_in = True
                    st.session_state.username = user
                    st.session_state.role = str(user_row.iloc[0]['role']).strip().lower()
                    st.session_state.current_nav_section = "📊 Reports & Analytics"
                    update_user_heartbeat(user)
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid Username or Password. Please try again.")

def logout():
    try:
        df_u = get_sheet_data("users", USERS_COLS)
        df_u['username_clean'] = df_u['username'].astype(str).str.strip().str.lower()
        idx = df_u[df_u['username_clean'] == st.session_state.username.lower()].index
        if not idx.empty:
            df_u.loc[idx[0], 'last_seen'] = 0
            save_cols = [c for c in USERS_COLS if c in df_u.columns]
            update_sheet_data("users", df_u[save_cols])
    except Exception:
        pass
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.current_nav_section = "📊 Reports & Analytics"
    st.rerun()

if not st.session_state.logged_in:
    login()
    st.stop()

is_admin = (st.session_state.role == "admin")

def get_user_initials(uname):
    u = str(uname).strip().lower()
    if "abhijit" in u:
        return "AA"
    elif "jit" in u:
        return "JB"
    return u[:2].upper()

current_user_tag = get_user_initials(st.session_state.username)

# -------------------------------------------------------------
# Modals: Edit & Delete Dialogs
# -------------------------------------------------------------
@st.dialog("✏️ Edit Sale Record")
def edit_sale_dialog(del_id):
    df_sales_raw = get_sheet_data("sales", SALES_COLS)
    matched = df_sales_raw[df_sales_raw['id'] == del_id]
    if matched.empty:
        st.error("Record not found.")
        return
    row_s = matched.iloc[0]
    
    with st.form("modal_edit_sale_form"):
        es_date = st.date_input("Date", value=parse_db_date(row_s['entry_date']))
        counters = ["Inside Counter / Dining", "Outside Stall"]
        es_c_idx = counters.index(row_s['counter_type']) if row_s['counter_type'] in counters else 0
        es_counter = st.selectbox("Counter", counters, index=es_c_idx)
        
        curr_prod = str(row_s['product_name'])
        prod_idx = PRODUCT_OPTIONS.index(curr_prod) if curr_prod in PRODUCT_OPTIONS else (len(PRODUCT_OPTIONS) - 1)
        e_prod_sel = st.selectbox("Product Category", PRODUCT_OPTIONS, index=prod_idx)
        e_other_val = curr_prod if prod_idx == (len(PRODUCT_OPTIONS) - 1) else ""
        e_other_prod = st.text_input("Specify if 'Other'", value=e_other_val)
        
        es_qty = st.number_input("Quantity", min_value=0, value=int(row_s['quantity']), step=1)
        es_amt = st.number_input("Amount (Rs.)", min_value=0.0, value=float(row_s['amount']), step=1.0, format="%.2f")
        
        if st.form_submit_button("Save Changes", type="primary", use_container_width=True):
            final_edit_prod = e_other_prod.strip() if e_prod_sel == "Other" and e_other_prod.strip() else e_prod_sel
            idx = df_sales_raw[df_sales_raw['id'] == del_id].index[0]
            df_sales_raw.loc[idx, ['entry_date', 'counter_type', 'product_name', 'quantity', 'amount', 'created_by']] = [
                str(es_date), es_counter, final_edit_prod, int(es_qty), float(es_amt), current_user_tag
            ]
            update_sheet_data("sales", df_sales_raw)
            update_user_heartbeat(st.session_state.username)
            st.success("✅ Sale Record updated successfully!")
            st.rerun()

@st.dialog("⚠️ Confirm Deletion")
def confirm_delete_sale_dialog(del_id):
    st.write("Are you sure you want to permanently delete this sale record?")
    st.caption("This action cannot be undone.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes, Delete", type="primary", use_container_width=True):
            df_sales_raw = get_sheet_data("sales", SALES_COLS)
            df_sales_raw = df_sales_raw[df_sales_raw['id'] != del_id]
            update_sheet_data("sales", df_sales_raw)
            update_user_heartbeat(st.session_state.username)
            st.success("Record deleted successfully!")
            st.rerun()
    with col2:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

@st.dialog("✏️ Edit Expense Record")
def edit_expense_dialog(del_id):
    df_exp_raw = get_sheet_data("expenses", EXPENSES_COLS)
    matched = df_exp_raw[df_exp_raw['id'] == del_id]
    if matched.empty:
        st.error("Record not found.")
        return
    row_e = matched.iloc[0]
    
    with st.form("modal_edit_exp_form"):
        ee_date = st.date_input("Date", value=parse_db_date(row_e['entry_date']))
        curr_e_cat = row_e['category']
        ee_cat_idx = EXPENSE_CATEGORIES.index(curr_e_cat) if curr_e_cat in EXPENSE_CATEGORIES else 0
        ee_cat = st.selectbox("Expense Category", EXPENSE_CATEGORIES, index=ee_cat_idx)
        ee_part = st.text_input("Particulars / Details", value=str(row_e['particulars']))
        ee_amt = st.number_input("Amount (Rs.)", min_value=0.0, value=float(row_e['amount']), step=1.0, format="%.2f")
        
        if st.form_submit_button("Save Changes", type="primary", use_container_width=True):
            idx = df_exp_raw[df_exp_raw['id'] == del_id].index[0]
            df_exp_raw.loc[idx, ['entry_date', 'category', 'particulars', 'amount', 'created_by']] = [
                str(ee_date), ee_cat, ee_part.strip(), float(ee_amt), current_user_tag
            ]
            update_sheet_data("expenses", df_exp_raw)
            update_user_heartbeat(st.session_state.username)
            st.success("✅ Expense Record updated successfully!")
            st.rerun()

@st.dialog("⚠️ Confirm Deletion")
def confirm_delete_exp_dialog(del_id):
    st.write("Are you sure you want to permanently delete this expense record?")
    st.caption("This action cannot be undone.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes, Delete", type="primary", use_container_width=True):
            df_exp_raw = get_sheet_data("expenses", EXPENSES_COLS)
            df_exp_raw = df_exp_raw[df_exp_raw['id'] != del_id]
            update_sheet_data("expenses", df_exp_raw)
            update_user_heartbeat(st.session_state.username)
            st.success("Record deleted successfully!")
            st.rerun()
    with col2:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

@st.dialog("✏️ Edit Settlement Record")
def edit_settlement_dialog(del_id):
    df_set_raw = get_sheet_data("settlements", SETTLEMENTS_COLS)
    matched = df_set_raw[df_set_raw['id'] == del_id]
    if matched.empty:
        st.error("Record not found.")
        return
    row_set = matched.iloc[0]
    
    with st.form("modal_edit_set_form"):
        eset_date = st.date_input("Date", value=parse_db_date(row_set['entry_date']))
        eset_amt = st.number_input("Amount (Rs.)", min_value=0.0, value=float(row_set['amount']), step=500.0, format="%.2f")
        eset_note = st.text_input("Note / Details", value=str(row_set['note']))
        
        if st.form_submit_button("Save Changes", type="primary", use_container_width=True):
            idx = df_set_raw[df_set_raw['id'] == del_id].index[0]
            df_set_raw.loc[idx, ['entry_date', 'amount', 'note', 'created_by']] = [
                str(eset_date), float(eset_amt), eset_note.strip(), current_user_tag
            ]
            update_sheet_data("settlements", df_set_raw)
            update_user_heartbeat(st.session_state.username)
            st.success("✅ Settlement Record updated successfully!")
            st.rerun()

@st.dialog("⚠️ Confirm Settlement Deletion")
def confirm_delete_settlement_dialog(del_id):
    st.write("Are you sure you want to permanently delete this landlord cash payout record?")
    st.caption("This action cannot be undone.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes, Delete", type="primary", use_container_width=True):
            df_set_raw = get_sheet_data("settlements", SETTLEMENTS_COLS)
            df_set_raw = df_set_raw[df_set_raw['id'] != del_id]
            update_sheet_data("settlements", df_set_raw)
            update_user_heartbeat(st.session_state.username)
            st.success("Record deleted successfully!")
            st.rerun()
    with col2:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

# -------------------------------------------------------------
# Main Header & Navigation
# -------------------------------------------------------------
head_c1, head_c2 = st.columns([0.8, 4.2])
with head_c1:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=95)
    else:
        st.markdown("### 🍽️")
with head_c2:
    st.markdown("<h2 style='margin-bottom: 0px; color: #0f172a;'>THE 4-WAY KITCHEN</h2>", unsafe_allow_html=True)
    st.markdown("<p style='margin-top: -5px; color: #64748b; font-weight: 500;'>Where Ideas Become Flavour • Cloud Accounts Ledger</p>", unsafe_allow_html=True)

# Status Bar
now_ts = int(time.time())
df_u_status = get_sheet_data("users", USERS_COLS)
online_users = []
offline_users = []

for partner in ALL_PARTNERS:
    matched_row = df_u_status[df_u_status['username'].astype(str).str.strip().str.lower() == partner.lower()]
    if not matched_row.empty:
        try:
            last_ts = float(matched_row.iloc[0]['last_seen'])
            if (now_ts - last_ts) < 300:
                online_users.append(partner)
            else:
                offline_users.append(partner)
        except Exception:
            offline_users.append(partner)
    else:
        offline_users.append(partner)

curr_name_cap = st.session_state.username.capitalize()
if curr_name_cap in ALL_PARTNERS:
    if curr_name_cap not in online_users:
        online_users.append(curr_name_cap)
    if curr_name_cap in offline_users:
        offline_users.remove(curr_name_cap)

online_html = " ".join([f"<span style='background:#dcfce7; color:#15803d; padding:3px 10px; border-radius:12px; font-weight:600; margin-right:5px; display:inline-flex; align-items:center;'><span class='blink-dot'></span>{u}</span>" for u in online_users])
offline_html = " ".join([f"<span style='background:#f1f5f9; color:#64748b; padding:3px 10px; border-radius:12px; font-weight:500; margin-right:5px; display:inline-flex; align-items:center;'><span class='off-dot'></span>{u}</span>" for u in offline_users])

st.markdown(f"""
<div style="background-color:#ffffff; border:1px solid #e2e8f0; padding:8px 14px; border-radius:10px; margin-bottom:14px; display:flex; flex-wrap:wrap; align-items:center; gap:8px;">
    <div style="display:flex; align-items:center;">
        <b style="color:#0f172a; margin-right:8px; font-size: 13px;">Online ({len(online_users)}):</b> {online_html if online_users else '<span style=\"color:#94a3b8;\">None</span>'}
    </div>
    <div style="color:#cbd5e1; margin:0 5px;">|</div>
    <div style="display:flex; align-items:center;">
        <b style="color:#64748b; margin-right:8px; font-size: 13px;">Offline ({len(offline_users)}):</b> {offline_html if offline_users else '<span style=\"color:#94a3b8;\">None</span>'}
    </div>
</div>
""", unsafe_allow_html=True)

# Navigation
if is_admin:
    nav_btn_cols = st.columns(4)
    nav_items = [
        ("📊 Reports & Analytics", "📊 Reports & Analytics"),
        ("📝 Daily Entry", "📝 Daily Entry"),
        ("📦 Daily Stock Register", "📦 Daily Stock Register"),
        ("💼 Capital Management", "💼 Capital Management")
    ]
    for idx, (label, val) in enumerate(nav_items):
        with nav_btn_cols[idx]:
            is_active = (st.session_state.current_nav_section == val)
            btn_type = "primary" if is_active else "secondary"
            if st.button(label, key=f"top_nav_{idx}", type=btn_type, use_container_width=True):
                st.session_state.current_nav_section = val
                st.rerun()
else:
    nav_btn_cols = st.columns(3)
    nav_items = [
        ("📊 Reports & Analytics", "📊 Reports & Analytics"),
        ("📦 Daily Stock Register", "📦 Daily Stock Register"),
        ("💼 Capital Management", "💼 Capital Management")
    ]
    for idx, (label, val) in enumerate(nav_items):
        with nav_btn_cols[idx]:
            is_active = (st.session_state.current_nav_section == val)
            btn_type = "primary" if is_active else "secondary"
            if st.button(label, key=f"top_nav_viewer_{idx}", type=btn_type, use_container_width=True):
                st.session_state.current_nav_section = val
                st.rerun()

choice = st.session_state.current_nav_section

# Sidebar
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", width=110)
    
role_badge = f"👑 Admin ({current_user_tag})" if is_admin else f"👁️ Viewer ({current_user_tag})"
st.sidebar.markdown(f"👤 Logged in as: **{st.session_state.username.capitalize()}** (`{current_user_tag}`)")
st.sidebar.caption(f"Role: {role_badge}")

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Logout", use_container_width=True):
    logout()

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 1. Reports & Analytics Section
# -------------------------------------------------------------
if choice == "📊 Reports & Analytics":
    st.subheader("📊 Profit & Loss Summary & Excel Export")
    
    # Fetch Data
    df_sales_raw = get_sheet_data("sales", SALES_COLS)
    df_exp_raw = get_sheet_data("expenses", EXPENSES_COLS)
    df_stock_raw = get_sheet_data("inventory_log", INVENTORY_COLS)
    df_cap_raw = get_sheet_data("capital", CAPITAL_COLS)
    df_settle_raw = get_sheet_data("settlements", SETTLEMENTS_COLS)

    if not df_cap_raw.empty:
        df_cap_raw['amount'] = pd.to_numeric(df_cap_raw['amount'], errors='coerce').fillna(0.0)
    if not df_sales_raw.empty:
        df_sales_raw['amount'] = pd.to_numeric(df_sales_raw['amount'], errors='coerce').fillna(0.0)
    if not df_exp_raw.empty:
        df_exp_raw['amount'] = pd.to_numeric(df_exp_raw['amount'], errors='coerce').fillna(0.0)
    if not df_settle_raw.empty:
        df_settle_raw['amount'] = pd.to_numeric(df_settle_raw['amount'], errors='coerce').fillna(0.0)

    # Core Figures
    lifetime_capital = df_cap_raw['amount'].sum() if not df_cap_raw.empty else 0.0
    lifetime_sales = df_sales_raw['amount'].sum() if not df_sales_raw.empty else 0.0
    lifetime_expenses = df_exp_raw['amount'].sum() if not df_exp_raw.empty else 0.0
    lifetime_profit = lifetime_sales - lifetime_expenses

    # ---------------------------------------------------------
    # DATE BOUNDARY RULE (Cutoff: October 1, 2026)
    # ---------------------------------------------------------
    cutoff_date = date(2026, 10, 1)

    if not df_sales_raw.empty:
        df_sales_calc = df_sales_raw.copy()
        df_sales_calc['date_obj'] = pd.to_datetime(df_sales_calc['entry_date'], errors='coerce').dt.date

        # Rule A: Up to 30th Sept, ALL sales (Inside + Outside) belonged to Landlord
        sales_pre_oct = df_sales_calc[df_sales_calc['date_obj'] < cutoff_date]['amount'].sum()

        # Rule B: From 1st Oct onwards, ONLY Inside Counter goes to Landlord
        sales_post_oct_inside = df_sales_calc[
            (df_sales_calc['date_obj'] >= cutoff_date) & 
            (df_sales_calc['counter_type'] == "Inside Counter / Dining")
        ]['amount'].sum()

        # Rule C: From 1st Oct onwards, Outside Stall STAYS IN HAND (Cash Drawer)
        outside_sales_in_hand = df_sales_calc[
            (df_sales_calc['date_obj'] >= cutoff_date) & 
            (df_sales_calc['counter_type'] == "Outside Stall")
        ]['amount'].sum()

        # Total sales collected/held by Landlord
        total_sales_routed_to_landlord = sales_pre_oct + sales_post_oct_inside
    else:
        total_sales_routed_to_landlord = 0.0
        outside_sales_in_hand = 0.0

    # Total Cash Collected from Landlord
    if not df_settle_raw.empty:
        total_cash_collected_from_landlord = df_settle_raw['amount'].sum()
    else:
        # Fallback: Up to 31st August sales if no explicit settlement record added yet
        df_s_aug = df_sales_raw.copy()
        if not df_s_aug.empty:
            df_s_aug['date_p'] = pd.to_datetime(df_s_aug['entry_date'], errors='coerce')
            total_cash_collected_from_landlord = df_s_aug[df_s_aug['date_p'] <= '2026-08-31']['amount'].sum()
        else:
            total_cash_collected_from_landlord = 0.0

    # Exact Balances
    sales_with_landlord = max(0.0, total_sales_routed_to_landlord - total_cash_collected_from_landlord)
    actual_cash_in_hand = (lifetime_capital + total_cash_collected_from_landlord + outside_sales_in_hand) - lifetime_expenses

    # Top Overview Metrics (3 Cards)
    top_c1, top_c2, top_c3 = st.columns(3)
    with top_c1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #ffffff; padding: 14px 16px; border-radius: 10px; margin-bottom: 15px; border: 1px solid #334155;">
            <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #38bdf8;">🌟 Lifetime Profit</div>
            <div style="font-size: 22px; font-weight: 800; margin-top: 3px; color: {'#4ade80' if lifetime_profit >= 0 else '#f87171'};">
                {'+ ' if lifetime_profit >= 0 else '- '}Rs. {abs(lifetime_profit):,.2f}
            </div>
            <div style="font-size: 10px; color: #94a3b8;">Total Lifetime Sales − Expenses</div>
        </div>
        """, unsafe_allow_html=True)

    with top_c2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #065f46 0%, #047857 100%); color: #ffffff; padding: 14px 16px; border-radius: 10px; margin-bottom: 15px;">
            <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #a7f3d0;">💰 Drawer Cash in Hand</div>
            <div style="font-size: 22px; font-weight: 800; margin-top: 3px; color: #ffffff;">
                Rs. {actual_cash_in_hand:,.2f}
            </div>
            <div style="font-size: 10px; color: #d1fae5;">Capital + Landlord Cash + Oct Outside Sales − Exp</div>
        </div>
        """, unsafe_allow_html=True)

    with top_c3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #854d0e 0%, #a16207 100%); color: #ffffff; padding: 14px 16px; border-radius: 10px; margin-bottom: 15px;">
            <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #fef08a;">🏦 Pending with Landlord</div>
            <div style="font-size: 22px; font-weight: 800; margin-top: 3px; color: #ffffff;">
                Rs. {sales_with_landlord:,.2f}
            </div>
            <div style="font-size: 10px; color: #fef9c3;">Eligible Landlord Sales − Cash Collected</div>
        </div>
        """, unsafe_allow_html=True)

    # MoM Table
    if not df_sales_raw.empty or not df_exp_raw.empty:
        df_s_mom = df_sales_raw.copy()
        df_s_mom['month'] = pd.to_datetime(df_s_mom['entry_date'], errors='coerce').dt.strftime('%Y-%m')
        m_sales = df_s_mom.groupby('month')['amount'].sum().reset_index().rename(columns={'amount': 'Sales'})

        df_e_mom = df_exp_raw.copy()
        df_e_mom['month'] = pd.to_datetime(df_e_mom['entry_date'], errors='coerce').dt.strftime('%Y-%m')
        m_exp = df_e_mom.groupby('month')['amount'].sum().reset_index().rename(columns={'amount': 'Expenses'})

        df_mom = pd.merge(m_sales, m_exp, on='month', how='outer').fillna(0.0)
        df_mom = df_mom.dropna(subset=['month'])
        df_mom = df_mom[df_mom['month'] != 'NaT'].sort_values(by='month', ascending=False).reset_index(drop=True)
        df_mom['Profit'] = df_mom['Sales'] - df_mom['Expenses']

        df_mom_disp = df_mom.copy()
        df_mom_disp['Sales'] = df_mom_disp['Sales'].apply(lambda x: f"Rs. {x:,.2f}")
        df_mom_disp['Expenses'] = df_mom_disp['Expenses'].apply(lambda x: f"Rs. {x:,.2f}")
        df_mom_disp['Profit'] = df_mom_disp['Profit'].apply(lambda x: f"+ Rs. {x:,.2f}" if x >= 0 else f"- Rs. {abs(x):,.2f}")
        df_mom_disp = df_mom_disp.rename(columns={'month': 'Month (YYYY-MM)', 'Sales': 'Total Sales', 'Expenses': 'Total Expenses', 'Profit': 'Net Profit / Loss'})

        with st.expander("📅 Month-on-Month (MoM) Profit Ledger", expanded=True):
            st.dataframe(df_mom_disp, use_container_width=True, hide_index=True)

    # Date Range Filter
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        start_date = st.date_input("Start Date", value=date(2026, 8, 1))
    with col_d2:
        end_date = st.date_input("End Date", value=date.today())
        
    if start_date <= end_date:
        if not df_sales_raw.empty:
            df_sales_raw['created_by'] = df_sales_raw['created_by'].fillna("-")
            df_sales_raw['date_parsed'] = pd.to_datetime(df_sales_raw['entry_date'], errors='coerce').dt.date
            df_sales = df_sales_raw[(df_sales_raw['date_parsed'] >= start_date) & (df_sales_raw['date_parsed'] <= end_date)].copy()
        else:
            df_sales = pd.DataFrame(columns=SALES_COLS)

        if not df_exp_raw.empty:
            df_exp_raw['created_by'] = df_exp_raw['created_by'].fillna("-")
            df_exp_raw['date_parsed'] = pd.to_datetime(df_exp_raw['entry_date'], errors='coerce').dt.date
            df_exp = df_exp_raw[(df_exp_raw['date_parsed'] >= start_date) & (df_exp_raw['date_parsed'] <= end_date)].copy()
        else:
            df_exp = pd.DataFrame(columns=EXPENSES_COLS)

        if not df_settle_raw.empty:
            df_settle_raw['created_by'] = df_settle_raw['created_by'].fillna("-")
            df_settle_raw['date_parsed'] = pd.to_datetime(df_settle_raw['entry_date'], errors='coerce').dt.date
            df_settle = df_settle_raw[(df_settle_raw['date_parsed'] >= start_date) & (df_settle_raw['date_parsed'] <= end_date)].copy()
        else:
            df_settle = pd.DataFrame(columns=SETTLEMENTS_COLS)

        total_sale = df_sales['amount'].sum() if not df_sales.empty else 0.0
        total_exp = df_exp['amount'].sum() if not df_exp.empty else 0.0
        net_profit = total_sale - total_exp
        
        num_days = max(1, (end_date - start_date).days + 1)
        avg_sale_day = total_sale / num_days
        avg_exp_day = total_exp / num_days
        
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df_summary = pd.DataFrame({
                "Report Metric": ["Period Start", "Period End", "Total Sales", "Total Expenses", "Net Profit / Loss", "Avg Sale/Day", "Avg Exp/Day", "Lifetime Profit", "Cash in Hand", "Pending with Landlord"],
                "Value": [str(start_date), str(end_date), total_sale, total_exp, net_profit, avg_sale_day, avg_exp_day, lifetime_profit, actual_cash_in_hand, sales_with_landlord]
            })
            df_summary.to_excel(writer, sheet_name='P&L Summary', index=False)
            df_sales.drop(columns=['date_parsed'], errors='ignore').to_excel(writer, sheet_name='Sales Register', index=False)
            df_exp.drop(columns=['date_parsed'], errors='ignore').to_excel(writer, sheet_name='Expense Register', index=False)
            df_settle_raw.drop(columns=['date_parsed'], errors='ignore').to_excel(writer, sheet_name='Landlord Settlements', index=False)
            df_stock_raw.to_excel(writer, sheet_name='Stock Register', index=False)
            df_cap_raw.to_excel(writer, sheet_name='Capital Register', index=False)

        st.download_button(
            label="📥 Download Full Account Book (.xlsx)",
            data=excel_buffer.getvalue(),
            file_name=f"Accounts_Report_{start_date}_to_{end_date}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.markdown("---")
        card_col1, card_col2, card_col3 = st.columns(3)
        with card_col1:
            st.markdown(f"""
            <div style="background-color: #f0fdf4; border: 1px solid #86efac; padding: 14px; border-radius: 8px;">
                <p style="margin: 0; color: #166534; font-size: 13px; font-weight: bold;">TOTAL SALES (PERIOD)</p>
                <h2 style="margin: 5px 0 0 0; color: #15803d; font-size: 26px;">Rs. {total_sale:,.2f}</h2>
            </div>
            """, unsafe_allow_html=True)
            
        with card_col2:
            st.markdown(f"""
            <div style="background-color: #fff1f2; border: 1px solid #fecdd3; padding: 14px; border-radius: 8px;">
                <p style="margin: 0; color: #9f1239; font-size: 13px; font-weight: bold;">TOTAL EXPENSES (PERIOD)</p>
                <h2 style="margin: 5px 0 0 0; color: #be123c; font-size: 26px;">Rs. {total_exp:,.2f}</h2>
            </div>
            """, unsafe_allow_html=True)
            
        with card_col3:
            if net_profit >= 0:
                st.markdown(f"""
                <div style="background-color: #dcfce7; border: 2px solid #22c55e; padding: 14px; border-radius: 8px;">
                    <p style="margin: 0; color: #14532d; font-size: 13px; font-weight: bold;">NET PROFIT (PERIOD)</p>
                    <h2 style="margin: 5px 0 0 0; color: #16a34a; font-size: 26px;">+ Rs. {net_profit:,.2f}</h2>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background-color: #fee2e2; border: 2px solid #ef4444; padding: 14px; border-radius: 8px;">
                    <p style="margin: 0; color: #7f1d1d; font-size: 13px; font-weight: bold;">NET LOSS (PERIOD)</p>
                    <h2 style="margin: 5px 0 0 0; color: #dc2626; font-size: 26px;">- Rs. {abs(net_profit):,.2f}</h2>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        avg_col1, avg_col2 = st.columns(2)
        
        is_avg_sale_higher = (avg_sale_day >= avg_exp_day)
        sale_card_bg = "#f0fdf4" if is_avg_sale_higher else "#fff1f2"
        sale_card_border = "#86efac" if is_avg_sale_higher else "#fecdd3"
        sale_card_txt = "#15803d" if is_avg_sale_higher else "#dc2626"
        sale_card_title = "#166534" if is_avg_sale_higher else "#9f1239"

        with avg_col1:
            st.markdown(f"""
            <div style="background-color: {sale_card_bg}; border: 1.5px solid {sale_card_border}; padding: 12px; border-radius: 8px;">
                <p style="margin: 0; color: {sale_card_title}; font-size: 12px; font-weight: bold; text-transform: uppercase;">Average Sale / Day ({num_days} Days)</p>
                <h3 style="margin: 4px 0 0 0; color: {sale_card_txt}; font-size: 20px;">Rs. {avg_sale_day:,.2f} <span style="font-size: 13px; font-weight: normal; color: {sale_card_title};">/ day</span></h3>
            </div>
            """, unsafe_allow_html=True)

        with avg_col2:
            st.markdown(f"""
            <div style="background-color: #fff1f2; border: 1.5px solid #fecdd3; padding: 12px; border-radius: 8px;">
                <p style="margin: 0; color: #9f1239; font-size: 12px; font-weight: bold; text-transform: uppercase;">Average Expense / Day ({num_days} Days)</p>
                <h3 style="margin: 4px 0 0 0; color: #be123c; font-size: 20px;">Rs. {avg_exp_day:,.2f} <span style="font-size: 13px; font-weight: normal; color: #9f1239;">/ day</span></h3>
            </div>
            """, unsafe_allow_html=True)
                
        st.markdown("---")
        tab1, tab2, tab3 = st.tabs(["Sales Breakdown", "Expense Breakdown", "🏦 Landlord Payouts History"])
        
        with tab1:
            if not df_sales.empty:
                df_sales_disp = df_sales.sort_values(by=['entry_date', 'id'], ascending=[False, False]).reset_index(drop=True).copy()
                df_sales_disp['amount_fmt'] = df_sales_disp['amount'].apply(lambda x: f"Rs. {x:,.2f}")
                df_sales_disp['Sl No'] = range(1, len(df_sales_disp) + 1)
                
                table_disp_s = df_sales_disp[['Sl No', 'entry_date', 'counter_type', 'product_name', 'quantity', 'amount_fmt', 'created_by']].rename(
                    columns={'entry_date': 'Date', 'counter_type': 'Counter', 'product_name': 'Product', 'quantity': 'Qty', 'amount_fmt': 'Amount', 'created_by': 'By'}
                )
                
                st.caption("👆 **Tip:** Tap on any row to select it, then tap Edit or Delete below.")
                event_s = st.dataframe(table_disp_s, use_container_width=True, on_select="rerun", selection_mode="single-row", key="table_sales_sel", hide_index=True)
                
                if is_admin:
                    selected_rows_s = event_s.selection.rows if hasattr(event_s, 'selection') else []
                    sel_s_id = df_sales_disp.iloc[selected_rows_s[0]]['id'] if selected_rows_s else None
                    
                    st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
                    btn_c1, btn_c2 = st.columns(2)
                    with btn_c1:
                        if st.button("✏️ Edit Selected Sale", use_container_width=True, key="btn_edit_s_tap"):
                            if sel_s_id is not None:
                                edit_sale_dialog(sel_s_id)
                            else:
                                st.warning("Please tap on a row in the table above first.")
                    with btn_c2:
                        if st.button("🗑️ Delete Selected Sale", use_container_width=True, key="btn_del_s_tap"):
                            if sel_s_id is not None:
                                confirm_delete_sale_dialog(sel_s_id)
                            else:
                                st.warning("Please tap on a row in the table above first.")
            else:
                st.info("No sales records found for this period.")
                
        with tab2:
            if not df_exp.empty:
                df_exp_disp = df_exp.sort_values(by=['entry_date', 'id'], ascending=[False, False]).reset_index(drop=True).copy()
                df_exp_disp['amount_fmt'] = df_exp_disp['amount'].apply(lambda x: f"Rs. {x:,.2f}")
                df_exp_disp['Sl No'] = range(1, len(df_exp_disp) + 1)
                
                table_disp_e = df_exp_disp[['Sl No', 'entry_date', 'category', 'particulars', 'amount_fmt', 'created_by']].rename(
                    columns={'entry_date': 'Date', 'category': 'Category', 'particulars': 'Particulars', 'amount_fmt': 'Amount', 'created_by': 'By'}
                )
                
                st.caption("👆 **Tip:** Tap on any row to select it, then tap Edit or Delete below.")
                event_e = st.dataframe(table_disp_e, use_container_width=True, on_select="rerun", selection_mode="single-row", key="table_exp_sel", hide_index=True)
                
                if is_admin:
                    selected_rows_e = event_e.selection.rows if hasattr(event_e, 'selection') else []
                    sel_e_id = df_exp_disp.iloc[selected_rows_e[0]]['id'] if selected_rows_e else None
                    
                    st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
                    btn_c1, btn_c2 = st.columns(2)
                    with btn_c1:
                        if st.button("✏️ Edit Selected Expense", use_container_width=True, key="btn_edit_e_tap"):
                            if sel_e_id is not None:
                                edit_expense_dialog(sel_e_id)
                            else:
                                st.warning("Please tap on a row in the table above first.")
                    with btn_c2:
                        if st.button("🗑️ Delete Selected Expense", use_container_width=True, key="btn_del_e_tap"):
                            if sel_e_id is not None:
                                confirm_delete_exp_dialog(sel_e_id)
                            else:
                                st.warning("Please tap on a row in the table above first.")
            else:
                st.info("No expense records found for this period.")

        with tab3:
            if not df_settle.empty:
                df_settle_disp = df_settle.sort_values(by=['entry_date', 'id'], ascending=[False, False]).reset_index(drop=True).copy()
                df_settle_disp['amount_fmt'] = df_settle_disp['amount'].apply(lambda x: f"Rs. {x:,.2f}")
                df_settle_disp['Sl No'] = range(1, len(df_settle_disp) + 1)
                
                table_disp_set = df_settle_disp[['Sl No', 'entry_date', 'amount_fmt', 'note', 'created_by']].rename(
                    columns={'entry_date': 'Payout Date', 'amount_fmt': 'Cash Received', 'note': 'Note / Period Details', 'created_by': 'Received By'}
                )
                
                st.caption("👆 **Tip:** Tap on any payout row to select it, then tap Edit or Delete below.")
                event_set = st.dataframe(table_disp_set, use_container_width=True, on_select="rerun", selection_mode="single-row", key="table_set_sel", hide_index=True)
                
                if is_admin:
                    selected_rows_set = event_set.selection.rows if hasattr(event_set, 'selection') else []
                    sel_set_id = df_settle_disp.iloc[selected_rows_set[0]]['id'] if selected_rows_set else None
                    
                    st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
                    btn_c1, btn_c2 = st.columns(2)
                    with btn_c1:
                        if st.button("✏️ Edit Selected Settlement", use_container_width=True, key="btn_edit_set_tap"):
                            if sel_set_id is not None:
                                edit_settlement_dialog(sel_set_id)
                            else:
                                st.warning("Please tap on a settlement row above first.")
                    with btn_c2:
                        if st.button("🗑️ Delete Selected Settlement", use_container_width=True, key="btn_del_set_tap"):
                            if sel_set_id is not None:
                                confirm_delete_settlement_dialog(sel_set_id)
                            else:
                                st.warning("Please tap on a settlement row above first.")
            else:
                st.info("No landlord cash payouts recorded for this period.")
    else:
        st.error("Start Date must be before or equal to End Date.")

# -------------------------------------------------------------
# 2. Daily Entry Section (With Date-Wise Settlement History)
# -------------------------------------------------------------
elif choice == "📝 Daily Entry":
    if not is_admin:
        st.warning("⚠️ You have Read-Only access.")
        st.stop()

    st.subheader("📝 Daily Sales, Expense & Landlord Settlements")
    
    # Landlord Cash Settlement Form & Live History
    with st.expander("🏦 Record & View Landlord Cash Payouts", expanded=False):
        st.markdown("##### 📥 New Cash Collection from Landlord")
        with st.form("landlord_settle_form", clear_on_submit=True):
            set_date = st.date_input("Settlement Date", value=date.today())
            set_amount = st.number_input("Cash Received Amount (Rs.)", min_value=0.0, value=None, placeholder="0.00", step=500.0, format="%.2f")
            set_note = st.text_input("Note / Period Details", placeholder="e.g. Sales cash collected from 1st to 15th Sept")
            
            if st.form_submit_button("Save Landlord Cash Payout", type="primary"):
                final_set_amt = float(set_amount) if set_amount is not None else 0.0
                if final_set_amt > 0:
                    df_set = get_sheet_data("settlements", SETTLEMENTS_COLS)
                    new_id = 1 if df_set.empty else int(pd.to_numeric(df_set['id'], errors='coerce').fillna(0).max() + 1)
                    new_row = pd.DataFrame([{
                        "id": new_id,
                        "entry_date": str(set_date),
                        "amount": float(final_set_amt),
                        "note": set_note.strip() if set_note else "Landlord Sales Payout",
                        "created_by": current_user_tag
                    }])
                    df_set = pd.concat([df_set, new_row], ignore_index=True)
                    update_sheet_data("settlements", df_set)
                    update_user_heartbeat(st.session_state.username)
                    st.success(f"✅ Cash Payout of Rs. {final_set_amt:,.2f} received on {set_date} recorded!")
                    st.rerun()
                else:
                    st.error("Please enter a valid cash amount.")

        # Live Table of Past Payouts
        df_set_hist = get_sheet_data("settlements", SETTLEMENTS_COLS)
        if not df_set_hist.empty:
            st.markdown("---")
            st.markdown("##### 📋 Recent Landlord Payout History (Date-Wise)")
            df_set_hist['amount_fmt'] = pd.to_numeric(df_set_hist['amount'], errors='coerce').fillna(0.0).apply(lambda x: f"Rs. {x:,.2f}")
            df_set_hist = df_set_hist.sort_values(by=['entry_date', 'id'], ascending=[False, False]).reset_index(drop=True)
            df_set_hist['Sl No'] = range(1, len(df_set_hist) + 1)
            
            st.dataframe(
                df_set_hist[['Sl No', 'entry_date', 'amount_fmt', 'note', 'created_by']].rename(
                    columns={'entry_date': 'Date', 'amount_fmt': 'Cash Collected', 'note': 'Details / Period', 'created_by': 'By'}
                ),
                use_container_width=True,
                hide_index=True
            )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 💰 Sales Entry")
        with st.form("sale_form", clear_on_submit=True):
            s_date = st.date_input("Date", value=date.today(), key="s_date")
            counter = st.selectbox("Counter / Location", ["Inside Counter / Dining", "Outside Stall"])
            
            product_sel = st.selectbox("Product Category / Dish", PRODUCT_OPTIONS, key="sale_prod_sel")
            other_product = st.text_input("Specify if 'Other'", key="sale_other_prod", placeholder="e.g. Special Dish")
            
            quantity = st.number_input("Quantity", min_value=0, value=1, step=1)
            amount = st.number_input("Total Sale Amount (Rs.)", min_value=0.0, value=None, placeholder="0.00", step=1.0, format="%.2f")
            
            submit_sale = st.form_submit_button("Save Sale to Google Sheets")
            if submit_sale:
                final_prod = other_product.strip() if product_sel == "Other" and other_product.strip() else product_sel
                final_amt = float(amount) if amount is not None else 0.0
                
                if final_prod:
                    df_sales = get_sheet_data("sales", SALES_COLS)
                    new_id = 1 if df_sales.empty else int(pd.to_numeric(df_sales['id'], errors='coerce').fillna(0).max() + 1)
                    new_row = pd.DataFrame([{
                        "id": new_id,
                        "entry_date": str(s_date),
                        "counter_type": counter,
                        "product_name": final_prod,
                        "quantity": int(quantity),
                        "amount": float(final_amt),
                        "created_by": current_user_tag
                    }])
                    df_sales = pd.concat([df_sales, new_row], ignore_index=True)
                    update_sheet_data("sales", df_sales)
                    update_user_heartbeat(st.session_state.username)
                    st.success(f"✅ Sale of Rs. {final_amt:,.2f} ({final_prod}) recorded by {current_user_tag}!")
                    st.rerun()
                else:
                    st.error("Please enter a valid product name.")

    with col2:
        st.markdown("### 💸 Expense Entry")
        with st.form("expense_form", clear_on_submit=True):
            e_date = st.date_input("Date", value=date.today(), key="e_date")
            category = st.selectbox("Expense Category", EXPENSE_CATEGORIES)
            particulars = st.text_input("Particulars / Details (e.g. 5kg Chicken, Spices, Vegetables)")
            e_amount = st.number_input("Expense Amount (Rs.)", min_value=0.0, value=None, placeholder="0.00", step=1.0, format="%.2f")
            
            submit_exp = st.form_submit_button("Save Expense to Google Sheets")
            if submit_exp:
                final_e_amt = float(e_amount) if e_amount is not None else 0.0
                if particulars.strip():
                    df_exp = get_sheet_data("expenses", EXPENSES_COLS)
                    new_id = 1 if df_exp.empty else int(pd.to_numeric(df_exp['id'], errors='coerce').fillna(0).max() + 1)
                    new_row = pd.DataFrame([{
                        "id": new_id,
                        "entry_date": str(e_date),
                        "category": category,
                        "particulars": particulars.strip(),
                        "amount": float(final_e_amt),
                        "created_by": current_user_tag
                    }])
                    df_exp = pd.concat([df_exp, new_row], ignore_index=True)
                    update_sheet_data("expenses", df_exp)
                    update_user_heartbeat(st.session_state.username)
                    st.success(f"✅ Expense of Rs. {final_e_amt:,.2f} ({category}) recorded by {current_user_tag}!")
                    st.rerun()
                else:
                    st.error("Please enter particulars details.")

# -------------------------------------------------------------
# 3. Daily Stock Register
# -------------------------------------------------------------
elif choice == "📦 Daily Stock Register":
    st.subheader("📦 Daily Stock & Automated Sales Tracker")
    st.caption("Auto-synced with Google Sheets")
    
    col_st1, col_st2 = st.columns([1.1, 1.9]) if is_admin else (None, st.container())
    
    if is_admin:
        with col_st1:
            st.markdown("### 📥 Record Daily Stock")
            with st.form("stock_form", clear_on_submit=True):
                stk_date = st.date_input("Date", value=date.today(), key="stk_date")
                stk_item = st.selectbox("Select Item", TRACKED_ITEMS)
                op_stock = st.number_input("Opening Stock (Pcs)", min_value=0, value=0, step=1)
                add_stock = st.number_input("Stock Added / Purchased (Pcs)", min_value=0, value=0, step=1)
                cl_stock = st.number_input("Closing Stock (Pcs)", min_value=0, value=0, step=1)
                
                total_available = op_stock + add_stock
                calc_sold = max(0, total_available - cl_stock)
                st.info(f"💡 Daily Sold: **{calc_sold} Pcs**")
                
                submit_stock = st.form_submit_button("Save Stock Record")
                if submit_stock:
                    if cl_stock > total_available:
                        st.error(f"Closing stock cannot exceed Total Available ({total_available})!")
                    else:
                        df_stk = get_sheet_data("inventory_log", INVENTORY_COLS)
                        new_id = 1 if df_stk.empty else int(pd.to_numeric(df_stk['id'], errors='coerce').fillna(0).max() + 1)
                        new_row = pd.DataFrame([{
                            "id": new_id,
                            "entry_date": str(stk_date),
                            "item_name": stk_item,
                            "opening_stock": int(op_stock),
                            "added_stock": int(add_stock),
                            "closing_stock": int(cl_stock),
                            "sold_quantity": int(calc_sold),
                            "created_by": current_user_tag
                        }])
                        df_stk = pd.concat([df_stk, new_row], ignore_index=True)
                        update_sheet_data("inventory_log", df_stk)
                        update_user_heartbeat(st.session_state.username)
                        st.success(f"✅ Stock record saved by {current_user_tag}! ({calc_sold} pcs sold)")
                        st.rerun()

    with (col_st2 if is_admin else col_st2):
        st.markdown("### 📋 Stock & Sales History")
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            stk_start = st.date_input("From Date", value=date(2026, 8, 1), key="stk_start")
        with f_col2:
            stk_end = st.date_input("To Date", value=date.today(), key="stk_end")
            
        df_stock = get_sheet_data("inventory_log", INVENTORY_COLS)
        if not df_stock.empty:
            df_stock['entry_date_parsed'] = pd.to_datetime(df_stock['entry_date'], errors='coerce').dt.date
            df_stock['created_by'] = df_stock['created_by'].fillna("-")
            df_stock_filtered = df_stock[(df_stock['entry_date_parsed'] >= stk_start) & (df_stock['entry_date_parsed'] <= stk_end)].reset_index(drop=True).copy()
            df_stock_filtered = df_stock_filtered.sort_values(by=['entry_date', 'id'], ascending=[False, False]).reset_index(drop=True)
            
            if not df_stock_filtered.empty:
                df_stock_filtered['Sl No'] = range(1, len(df_stock_filtered) + 1)
                display_cols = {
                    'Sl No': 'Sl No', 'entry_date': 'Date', 'item_name': 'Item',
                    'opening_stock': 'Opening', 'added_stock': 'Added',
                    'closing_stock': 'Closing', 'sold_quantity': 'Sold (Pcs)',
                    'created_by': 'By'
                }
                
                st.caption("👆 **Tip:** Tap on any row to select it, then tap Edit or Delete below.")
                event_stk = st.dataframe(df_stock_filtered[list(display_cols.keys())].rename(columns=display_cols), use_container_width=True, on_select="rerun", selection_mode="single-row", key="table_stk_sel", hide_index=True)
                
                if is_admin:
                    selected_rows_stk = event_stk.selection.rows if hasattr(event_stk, 'selection') else []
                    sel_stk_id = df_stock_filtered.iloc[selected_rows_stk[0]]['id'] if selected_rows_stk else None
                    
                    st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
                    btn_c1, btn_c2 = st.columns(2)
                    with btn_c1:
                        if st.button("✏️ Edit Selected Stock", use_container_width=True, key="btn_edit_stk_tap"):
                            if sel_stk_id is not None:
                                edit_stock_dialog(sel_stk_id)
                            else:
                                st.warning("Please tap on a row in the table above first.")
                    with btn_c2:
                        if st.button("🗑️ Delete Selected Stock", use_container_width=True, key="btn_del_stk_tap"):
                            if sel_stk_id is not None:
                                confirm_delete_stock_dialog(sel_stk_id)
                            else:
                                st.warning("Please tap on a row in the table above first.")
                
                st.markdown("---")
                st.markdown("#### 📊 Total Quantity Sold in Period")
                df_stock_filtered['sold_quantity'] = pd.to_numeric(df_stock_filtered['sold_quantity'], errors='coerce').fillna(0)
                sold_sum = df_stock_filtered.groupby('item_name')['sold_quantity'].sum().reset_index()
                st.dataframe(sold_sum.rename(columns={'item_name': 'Item', 'sold_quantity': 'Total Sold (Pcs)'}), use_container_width=True)
            else:
                st.info("No stock records found for this period.")
        else:
            st.info("No stock records found in Google Sheet.")

# -------------------------------------------------------------
# 4. Capital Management Section
# -------------------------------------------------------------
elif choice == "💼 Capital Management":
    st.subheader("💼 Partner Capital & Investment Ledger")
    
    col_c1, col_c2 = st.columns([1, 1.5]) if is_admin else (None, st.container())
    
    if is_admin:
        with col_c1:
            st.markdown("### Add Partner Capital")
            with st.form("capital_form", clear_on_submit=True):
                c_date = st.date_input("Date", value=date.today())
                partner = st.selectbox("Partner Name", ALL_PARTNERS)
                cap_amount = st.number_input("Amount (Rs.)", min_value=0.0, value=None, placeholder="0.00", step=100.0, format="%.2f")
                
                if st.form_submit_button("Record Capital"):
                    final_cap_amt = float(cap_amount) if cap_amount is not None else 0.0
                    df_cap = get_sheet_data("capital", CAPITAL_COLS)
                    new_id = 1 if df_cap.empty else int(pd.to_numeric(df_cap['id'], errors='coerce').fillna(0).max() + 1)
                    new_row = pd.DataFrame([{
                        "id": new_id,
                        "entry_date": str(c_date),
                        "partner_name": partner,
                        "amount": float(final_cap_amt),
                        "created_by": current_user_tag
                    }])
                    df_cap = pd.concat([df_cap, new_row], ignore_index=True)
                    update_sheet_data("capital", df_cap)
                    update_user_heartbeat(st.session_state.username)
                    st.success(f"✅ Capital of Rs. {final_cap_amt:,.2f} for {partner} saved by {current_user_tag}!")
                    st.rerun()
                    
    with (col_c2 if is_admin else col_c2):
        st.markdown("### Current Capital Summary")
        df_cap = get_sheet_data("capital", CAPITAL_COLS)
        
        if not df_cap.empty:
            df_cap['amount'] = pd.to_numeric(df_cap['amount'], errors='coerce').fillna(0.0)
            df_cap['created_by'] = df_cap['created_by'].fillna("-")
            summary_cap = df_cap.groupby('partner_name')['amount'].sum().reset_index()
            total_invested = summary_cap['amount'].sum()
            
            summary_cap_disp = summary_cap.copy()
            summary_cap_disp['amount'] = summary_cap_disp['amount'].apply(lambda x: f"Rs. {x:,.2f}")
            st.dataframe(summary_cap_disp.rename(columns={'partner_name': 'Partner', 'amount': 'Total Capital'}), use_container_width=True)
            
            st.info(f"**Total Capital Invested:** Rs. {total_invested:,.2f}")
            
            st.markdown("#### Capital Contribution History")
            df_cap_disp = df_cap.sort_values(by=['entry_date', 'id'], ascending=[False, False]).reset_index(drop=True).copy()
            df_cap_disp['amount_fmt'] = df_cap_disp['amount'].apply(lambda x: f"Rs. {x:,.2f}")
            df_cap_disp['Sl No'] = range(1, len(df_cap_disp) + 1)
            
            table_disp_cap = df_cap_disp[['Sl No', 'entry_date', 'partner_name', 'amount_fmt', 'created_by']].rename(
                columns={'entry_date': 'Date', 'partner_name': 'Partner', 'amount_fmt': 'Amount', 'created_by': 'By'}
            )
            
            st.caption("👆 **Tip:** Tap on any row to select it, then tap Edit or Delete below.")
            event_cap = st.dataframe(table_disp_cap, use_container_width=True, on_select="rerun", selection_mode="single-row", key="table_cap_sel", hide_index=True)
        else:
            st.info("No capital contributions found in Google Sheet.")
