import streamlit as st
import pandas as pd
import io
from datetime import date, datetime
from streamlit_gsheets import GSheetsConnection

# MUST be the first Streamlit command
st.set_page_config(page_title="Restaurant Management Ledger", layout="wide")

# -------------------------------------------------------------
# Google Sheets Connection Setup
# -------------------------------------------------------------
conn = st.connection("gsheets", type=GSheetsConnection)

def get_sheet_data(worksheet_name, expected_cols):
    try:
        df = conn.read(worksheet=worksheet_name, ttl=0)
        if df is None or df.empty:
            return pd.DataFrame(columns=expected_cols)
        df = df.dropna(how='all')
        for col in expected_cols:
            if col not in df.columns:
                df[col] = None
        return df[expected_cols]
    except Exception:
        return pd.DataFrame(columns=expected_cols)

def update_sheet_data(worksheet_name, df):
    # Convert all columns to standard types to prevent Google Sheets casting errors
    df_clean = df.copy()
    conn.update(worksheet=worksheet_name, data=df_clean)

# Default Schemas
USERS_COLS = ["username", "password", "role"]
SALES_COLS = ["id", "entry_date", "counter_type", "product_name", "quantity", "amount"]
EXPENSES_COLS = ["id", "entry_date", "category", "particulars", "amount"]
CAPITAL_COLS = ["id", "entry_date", "partner_name", "amount"]
INVENTORY_COLS = ["id", "entry_date", "item_name", "opening_stock", "added_stock", "closing_stock", "sold_quantity"]

# -------------------------------------------------------------
# Authentication Flow
# -------------------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""

def login():
    st.markdown("### 🔐 Restaurant Management Login")
    st.info("Google Sheets Connected Cloud Ledger")
    
    with st.form("login_form"):
        user = st.text_input("Username").strip().lower()
        pwd = st.text_input("Password", type="password").strip()
        btn = st.form_submit_button("Log In", type="primary")
        
        if btn:
            df_users = get_sheet_data("users", USERS_COLS)
            df_users['username'] = df_users['username'].astype(str).str.strip().str.lower()
            df_users['password'] = df_users['password'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            
            user_row = df_users[df_users['username'] == user]
            
            if not user_row.empty and user_row.iloc[0]['password'] == pwd:
                st.session_state.logged_in = True
                st.session_state.username = user
                st.session_state.role = str(user_row.iloc[0]['role']).strip().lower()
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid Username or Password. Please try again.")

def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.rerun()

if not st.session_state.logged_in:
    login()
    st.stop()

is_admin = (st.session_state.role == "admin")

# -------------------------------------------------------------
# Main Application UI
# -------------------------------------------------------------
st.title("🍽️ Restaurant & Counter - Cloud Accounts Ledger")

role_badge = "👑 Admin (Full Access)" if is_admin else "👁️ Viewer (Read Only)"
st.sidebar.markdown(f"👤 Logged in as: **{st.session_state.username.capitalize()}**")
st.sidebar.caption(f"Role: {role_badge}")

with st.sidebar.expander("🔑 Change My Password"):
    with st.form("change_pwd_form", clear_on_submit=True):
        old_p = st.text_input("Current Password", type="password")
        new_p = st.text_input("New Password", type="password")
        conf_p = st.text_input("Confirm New Password", type="password")
        update_p_btn = st.form_submit_button("Update Password")
        
        if update_p_btn:
            df_users = get_sheet_data("users", USERS_COLS)
            # Ensure all columns are treated as string/object dtype
            df_users = df_users.astype({"username": str, "password": str, "role": str})
            df_users['username_clean'] = df_users['username'].str.strip().str.lower()
            df_users['password_clean'] = df_users['password'].str.replace(r'\.0$', '', regex=True).str.strip()
            
            user_idx = df_users[df_users['username_clean'] == st.session_state.username].index
            
            if not user_idx.empty:
                curr_pwd = df_users.loc[user_idx[0], 'password_clean']
                if old_p.strip() != curr_pwd:
                    st.error("Current password is incorrect.")
                elif not new_p.strip():
                    st.error("New password cannot be empty.")
                elif new_p.strip() != conf_p.strip():
                    st.error("New passwords do not match.")
                else:
                    # Update password cleanly
                    df_users_save = df_users[['username', 'password', 'role']].copy()
                    df_users_save.loc[user_idx[0], 'password'] = str(new_p.strip())
                    update_sheet_data("users", df_users_save)
                    st.success("✅ Password updated in Google Sheet!")

if is_admin:
    menu = ["Daily Entry", "Daily Stock Register", "Reports & Analytics", "Capital Management"]
else:
    menu = ["Reports & Analytics", "Daily Stock Register", "Capital Management"]

choice = st.sidebar.selectbox("Select Menu", menu)

if st.sidebar.button("🚪 Logout"):
    logout()
st.sidebar.markdown("---")

PARTNERS_LIST = ["Abhijit", "Jit", "Debasis", "Sumit"]
EXPENSE_CATEGORIES = [
    "Raw Materials (Chicken, Fish, Eggs, Veg)", 
    "Grocery & Spices", 
    "Rent & Utility Bills", 
    "Staff Salary & Daily Allowance", 
    "Transportation & Marketing",
    "Other Miscellaneous Expenses"
]
TRACKED_ITEMS = [
    "Egg (পিস)", 
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
# 1. Daily Entry Section (Sales & Expenses) - Admin Only
# -------------------------------------------------------------
if choice == "Daily Entry":
    if not is_admin:
        st.warning("⚠️ You have Read-Only access.")
        st.stop()

    st.subheader("📝 Daily Sales & Expense Entry")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💰 Sales Entry")
        with st.form("sale_form", clear_on_submit=True):
            s_date = st.date_input("Date", value=date.today(), key="s_date")
            counter = st.selectbox("Counter / Location", ["Inside Counter / Dining", "Outside Stall"])
            product = st.text_input("Product Name (e.g. Total Sale, Chicken Pakoda, Water)")
            quantity = st.number_input("Quantity", min_value=0, value=1, step=1)
            amount = st.number_input("Total Sale Amount (Rs.)", min_value=0.0, value=0.0, step=10.0)
            
            submit_sale = st.form_submit_button("Save Sale to Google Sheets")
            if submit_sale:
                if product.strip():
                    df_sales = get_sheet_data("sales", SALES_COLS)
                    new_id = 1 if df_sales.empty else int(pd.to_numeric(df_sales['id'], errors='coerce').fillna(0).max() + 1)
                    new_row = pd.DataFrame([{
                        "id": new_id,
                        "entry_date": str(s_date),
                        "counter_type": counter,
                        "product_name": product.strip(),
                        "quantity": int(quantity),
                        "amount": float(amount)
                    }])
                    df_sales = pd.concat([df_sales, new_row], ignore_index=True)
                    update_sheet_data("sales", df_sales)
                    st.success("✅ Sale record saved permanently to Google Sheets!")
                    st.rerun()
                else:
                    st.error("Please enter a valid product name.")

    with col2:
        st.markdown("### 💸 Expense Entry")
        with st.form("expense_form", clear_on_submit=True):
            e_date = st.date_input("Date", value=date.today(), key="e_date")
            category = st.selectbox("Expense Category", EXPENSE_CATEGORIES)
            particulars = st.text_input("Particulars / Details (e.g. Chicken, Grocery, Gas)")
            e_amount = st.number_input("Expense Amount (Rs.)", min_value=0.0, value=0.0, step=10.0)
            
            submit_exp = st.form_submit_button("Save Expense to Google Sheets")
            if submit_exp:
                if particulars.strip():
                    df_exp = get_sheet_data("expenses", EXPENSES_COLS)
                    new_id = 1 if df_exp.empty else int(pd.to_numeric(df_exp['id'], errors='coerce').fillna(0).max() + 1)
                    new_row = pd.DataFrame([{
                        "id": new_id,
                        "entry_date": str(e_date),
                        "category": category,
                        "particulars": particulars.strip(),
                        "amount": float(e_amount)
                    }])
                    df_exp = pd.concat([df_exp, new_row], ignore_index=True)
                    update_sheet_data("expenses", df_exp)
                    st.success("✅ Expense record saved permanently to Google Sheets!")
                    st.rerun()
                else:
                    st.error("Please enter particulars details.")

# -------------------------------------------------------------
# 2. Daily Stock Register
# -------------------------------------------------------------
elif choice == "Daily Stock Register":
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
                            "sold_quantity": int(calc_sold)
                        }])
                        df_stk = pd.concat([df_stk, new_row], ignore_index=True)
                        update_sheet_data("inventory_log", df_stk)
                        st.success(f"✅ Stock record saved! ({calc_sold} pcs sold)")
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
            df_stock_filtered = df_stock[(df_stock['entry_date_parsed'] >= stk_start) & (df_stock['entry_date_parsed'] <= stk_end)].copy()
            df_stock_filtered = df_stock_filtered.sort_values(by=['entry_date', 'id'], ascending=[False, False])
            
            if not df_stock_filtered.empty:
                display_cols = {
                    'id': 'ID', 'entry_date': 'Date', 'item_name': 'Item',
                    'opening_stock': 'Opening', 'added_stock': 'Added',
                    'closing_stock': 'Closing', 'sold_quantity': 'Sold (Pcs)'
                }
                st.dataframe(df_stock_filtered[list(display_cols.keys())].rename(columns=display_cols), use_container_width=True)
                
                st.markdown("#### 📊 Total Quantity Sold in Period")
                df_stock_filtered['sold_quantity'] = pd.to_numeric(df_stock_filtered['sold_quantity'], errors='coerce').fillna(0)
                sold_sum = df_stock_filtered.groupby('item_name')['sold_quantity'].sum().reset_index()
                st.dataframe(sold_sum.rename(columns={'item_name': 'Item', 'sold_quantity': 'Total Sold (Pcs)'}), use_container_width=True)
                
                if is_admin:
                    st.markdown("---")
                    act_col1, act_col2 = st.columns(2)
                    with act_col1:
                        st.markdown("##### ✏️ Edit Stock Entry")
                        edit_stock_id = st.selectbox("Select Stock ID to Edit", df_stock_filtered['id'].tolist(), key="edit_stk_sel")
                        row_stk = df_stock[df_stock['id'] == edit_stock_id].iloc[0]
                        
                        with st.form("edit_stock_form"):
                            e_stk_date = st.date_input("Date", value=parse_db_date(row_stk['entry_date']), key="e_stk_d")
                            current_item_val = row_stk['item_name'] if row_stk['item_name'] in TRACKED_ITEMS else TRACKED_ITEMS[0]
                            e_stk_item = st.selectbox("Item", TRACKED_ITEMS, index=TRACKED_ITEMS.index(current_item_val), key="e_stk_i")
                            e_op = st.number_input("Opening Stock", min_value=0, value=int(row_stk['opening_stock']), step=1)
                            e_add = st.number_input("Added Stock", min_value=0, value=int(row_stk['added_stock']), step=1)
                            e_cl = st.number_input("Closing Stock", min_value=0, value=int(row_stk['closing_stock']), step=1)
                            
                            e_tot = e_op + e_add
                            e_sold = max(0, e_tot - e_cl)
                            
                            if st.form_submit_button("Update Stock Record"):
                                idx = df_stock[df_stock['id'] == edit_stock_id].index[0]
                                df_stock.loc[idx, ['entry_date', 'item_name', 'opening_stock', 'added_stock', 'closing_stock', 'sold_quantity']] = [
                                    str(e_stk_date), e_stk_item, int(e_op), int(e_add), int(e_cl), int(e_sold)
                                ]
                                df_stock_to_save = df_stock.drop(columns=['entry_date_parsed'], errors='ignore')
                                update_sheet_data("inventory_log", df_stock_to_save)
                                st.success("✅ Stock Record updated in Google Sheets!")
                                st.rerun()

                    with act_col2:
                        st.markdown("##### 🗑️ Delete Stock Entry")
                        del_stock_id = st.selectbox("Select Stock ID to Delete", df_stock_filtered['id'].tolist(), key="del_stk_sel")
                        if st.button("Delete Stock Record", type="primary"):
                            df_stock = df_stock[df_stock['id'] != del_stock_id]
                            df_stock_to_save = df_stock.drop(columns=['entry_date_parsed'], errors='ignore')
                            update_sheet_data("inventory_log", df_stock_to_save)
                            st.success("Stock Record deleted from Google Sheets!")
                            st.rerun()
            else:
                st.info("No stock records found for this period.")
        else:
            st.info("No stock records found in Google Sheet.")

# -------------------------------------------------------------
# 3. Reports & Analytics Section
# -------------------------------------------------------------
elif choice == "Reports & Analytics":
    st.subheader("📊 Profit & Loss Summary & Excel Export")
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        start_date = st.date_input("Start Date", value=date(2026, 8, 1))
    with col_d2:
        end_date = st.date_input("End Date", value=date.today())
        
    if start_date <= end_date:
        df_sales_raw = get_sheet_data("sales", SALES_COLS)
        df_exp_raw = get_sheet_data("expenses", EXPENSES_COLS)
        df_stock_raw = get_sheet_data("inventory_log", INVENTORY_COLS)
        df_cap_raw = get_sheet_data("capital", CAPITAL_COLS)

        if not df_sales_raw.empty:
            df_sales_raw['amount'] = pd.to_numeric(df_sales_raw['amount'], errors='coerce').fillna(0.0)
            df_sales_raw['date_parsed'] = pd.to_datetime(df_sales_raw['entry_date'], errors='coerce').dt.date
            df_sales = df_sales_raw[(df_sales_raw['date_parsed'] >= start_date) & (df_sales_raw['date_parsed'] <= end_date)].copy()
        else:
            df_sales = pd.DataFrame(columns=SALES_COLS)

        if not df_exp_raw.empty:
            df_exp_raw['amount'] = pd.to_numeric(df_exp_raw['amount'], errors='coerce').fillna(0.0)
            df_exp_raw['date_parsed'] = pd.to_datetime(df_exp_raw['entry_date'], errors='coerce').dt.date
            df_exp = df_exp_raw[(df_exp_raw['date_parsed'] >= start_date) & (df_exp_raw['date_parsed'] <= end_date)].copy()
        else:
            df_exp = pd.DataFrame(columns=EXPENSES_COLS)

        total_sale = df_sales['amount'].sum() if not df_sales.empty else 0.0
        total_exp = df_exp['amount'].sum() if not df_exp.empty else 0.0
        net_profit = total_sale - total_exp
        
        # Excel Generator
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df_summary = pd.DataFrame({
                "Report Metric": ["Period Start", "Period End", "Total Sales", "Total Expenses", "Net Profit / Loss"],
                "Value": [str(start_date), str(end_date), total_sale, total_exp, net_profit]
            })
            df_summary.to_excel(writer, sheet_name='P&L Summary', index=False)
            df_sales.drop(columns=['date_parsed'], errors='ignore').to_excel(writer, sheet_name='Sales Register', index=False)
            df_exp.drop(columns=['date_parsed'], errors='ignore').to_excel(writer, sheet_name='Expense Register', index=False)
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
            <div style="background-color: #f0fdf4; border: 1px solid #86efac; padding: 15px; border-radius: 8px;">
                <p style="margin: 0; color: #166534; font-size: 14px; font-weight: bold;">TOTAL SALES</p>
                <h2 style="margin: 5px 0 0 0; color: #15803d;">Rs. {total_sale:,.2f}</h2>
            </div>
            """, unsafe_allow_html=True)
            
        with card_col2:
            st.markdown(f"""
            <div style="background-color: #fff1f2; border: 1px solid #fecdd3; padding: 15px; border-radius: 8px;">
                <p style="margin: 0; color: #9f1239; font-size: 14px; font-weight: bold;">TOTAL EXPENSES</p>
                <h2 style="margin: 5px 0 0 0; color: #be123c;">Rs. {total_exp:,.2f}</h2>
            </div>
            """, unsafe_allow_html=True)
            
        with card_col3:
            if net_profit >= 0:
                st.markdown(f"""
                <div style="background-color: #dcfce7; border: 2px solid #22c55e; padding: 15px; border-radius: 8px;">
                    <p style="margin: 0; color: #14532d; font-size: 14px; font-weight: bold;">NET PROFIT (SURPLUS)</p>
                    <h2 style="margin: 5px 0 0 0; color: #16a34a;">+ Rs. {net_profit:,.2f}</h2>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background-color: #fee2e2; border: 2px solid #ef4444; padding: 15px; border-radius: 8px;">
                    <p style="margin: 0; color: #7f1d1d; font-size: 14px; font-weight: bold;">NET LOSS (DEFICIT)</p>
                    <h2 style="margin: 5px 0 0 0; color: #dc2626;">- Rs. {abs(net_profit):,.2f}</h2>
                </div>
                """, unsafe_allow_html=True)
                
        st.markdown("---")
        tab1, tab2 = st.tabs(["Sales Breakdown", "Expense Breakdown"])
        
        with tab1:
            if not df_sales.empty:
                df_sales_disp = df_sales.copy()
                df_sales_disp['amount_fmt'] = df_sales_disp['amount'].apply(lambda x: f"Rs. {x:,.2f}")
                st.dataframe(df_sales_disp[['id', 'entry_date', 'counter_type', 'product_name', 'quantity', 'amount_fmt']].rename(
                    columns={'id': 'ID', 'entry_date': 'Date', 'counter_type': 'Counter', 'product_name': 'Product', 'quantity': 'Qty', 'amount_fmt': 'Amount'}
                ), use_container_width=True)
                
                if is_admin:
                    st.markdown("---")
                    s_act1, s_act2 = st.columns(2)
                    with s_act1:
                        st.markdown("##### ✏️ Edit Sale Entry")
                        edit_sale_id = st.selectbox("Select Sale ID to Edit", df_sales['id'].tolist(), key="edit_s_sel")
                        row_s = df_sales_raw[df_sales_raw['id'] == edit_sale_id].iloc[0]
                        
                        with st.form("edit_sale_form"):
                            es_date = st.date_input("Date", value=parse_db_date(row_s['entry_date']), key="es_d")
                            counters = ["Inside Counter / Dining", "Outside Stall"]
                            es_c_idx = counters.index(row_s['counter_type']) if row_s['counter_type'] in counters else 0
                            es_counter = st.selectbox("Counter", counters, index=es_c_idx, key="es_c")
                            es_prod = st.text_input("Product Name", value=str(row_s['product_name']), key="es_p")
                            es_qty = st.number_input("Quantity", min_value=0, value=int(row_s['quantity']), step=1, key="es_q")
                            es_amt = st.number_input("Amount (Rs.)", min_value=0.0, value=float(row_s['amount']), step=10.0, key="es_a")
                            
                            if st.form_submit_button("Update Sale Record"):
                                idx = df_sales_raw[df_sales_raw['id'] == edit_sale_id].index[0]
                                df_sales_raw.loc[idx, ['entry_date', 'counter_type', 'product_name', 'quantity', 'amount']] = [
                                    str(es_date), es_counter, es_prod.strip(), int(es_qty), float(es_amt)
                                ]
                                df_to_save = df_sales_raw.drop(columns=['date_parsed'], errors='ignore')
                                update_sheet_data("sales", df_to_save)
                                st.success("✅ Sale Record updated in Google Sheets!")
                                st.rerun()
                                
                    with s_act2:
                        st.markdown("##### 🗑️ Delete Sale Entry")
                        del_sale_id = st.selectbox("Select Sale ID to Delete", df_sales['id'].tolist(), key="del_s_sel")
                        if st.button("Delete Sale Record", type="primary", key="btn_del_sale"):
                            df_sales_raw = df_sales_raw[df_sales_raw['id'] != del_sale_id]
                            df_to_save = df_sales_raw.drop(columns=['date_parsed'], errors='ignore')
                            update_sheet_data("sales", df_to_save)
                            st.success("Sale record deleted from Google Sheets!")
                            st.rerun()
            else:
                st.info("No sales records found for this period.")
                
        with tab2:
            if not df_exp.empty:
                df_exp_disp = df_exp.copy()
                df_exp_disp['amount_fmt'] = df_exp_disp['amount'].apply(lambda x: f"Rs. {x:,.2f}")
                st.dataframe(df_exp_disp[['id', 'entry_date', 'category', 'particulars', 'amount_fmt']].rename(
                    columns={'id': 'ID', 'entry_date': 'Date', 'category': 'Category', 'particulars': 'Particulars', 'amount_fmt': 'Amount'}
                ), use_container_width=True)
                
                if is_admin:
                    st.markdown("---")
                    e_act1, e_act2 = st.columns(2)
                    with e_act1:
                        st.markdown("##### ✏️ Edit Expense Entry")
                        edit_exp_id = st.selectbox("Select Expense ID to Edit", df_exp['id'].tolist(), key="edit_e_sel")
                        row_e = df_exp_raw[df_exp_raw['id'] == edit_exp_id].iloc[0]
                        
                        with st.form("edit_expense_form"):
                            ee_date = st.date_input("Date", value=parse_db_date(row_e['entry_date']), key="ee_d")
                            ee_cat_idx = EXPENSE_CATEGORIES.index(row_e['category']) if row_e['category'] in EXPENSE_CATEGORIES else 0
                            ee_cat = st.selectbox("Expense Category", EXPENSE_CATEGORIES, index=ee_cat_idx, key="ee_c")
                            ee_part = st.text_input("Particulars / Details", value=str(row_e['particulars']), key="ee_p")
                            ee_amt = st.number_input("Amount (Rs.)", min_value=0.0, value=float(row_e['amount']), step=10.0, key="ee_a")
                            
                            if st.form_submit_button("Update Expense Record"):
                                idx = df_exp_raw[df_exp_raw['id'] == edit_exp_id].index[0]
                                df_exp_raw.loc[idx, ['entry_date', 'category', 'particulars', 'amount']] = [
                                    str(ee_date), ee_cat, ee_part.strip(), float(ee_amt)
                                ]
                                df_to_save = df_exp_raw.drop(columns=['date_parsed'], errors='ignore')
                                update_sheet_data("expenses", df_to_save)
                                st.success("✅ Expense Record updated in Google Sheets!")
                                st.rerun()
                                
                    with e_act2:
                        st.markdown("##### 🗑️ Delete Expense Entry")
                        del_exp_id = st.selectbox("Select Expense ID to Delete", df_exp['id'].tolist(), key="del_e_sel")
                        if st.button("Delete Expense Record", type="primary", key="btn_del_exp"):
                            df_exp_raw = df_exp_raw[df_exp_raw['id'] != del_exp_id]
                            df_to_save = df_exp_raw.drop(columns=['date_parsed'], errors='ignore')
                            update_sheet_data("expenses", df_to_save)
                            st.success("Expense record deleted from Google Sheets!")
                            st.rerun()
            else:
                st.info("No expense records found for this period.")
    else:
        st.error("Start Date must be before or equal to End Date.")

# -------------------------------------------------------------
# 4. Capital Management Section
# -------------------------------------------------------------
elif choice == "Capital Management":
    st.subheader("💼 Partner Capital & Investment Ledger")
    
    col_c1, col_c2 = st.columns([1, 1.5]) if is_admin else (None, st.container())
    
    if is_admin:
        with col_c1:
            st.markdown("### Add Partner Capital")
            with st.form("capital_form", clear_on_submit=True):
                c_date = st.date_input("Date", value=date.today())
                partner = st.selectbox("Partner Name", PARTNERS_LIST)
                cap_amount = st.number_input("Amount (Rs.)", min_value=0.0, value=0.0, step=500.0)
                
                if st.form_submit_button("Record Capital"):
                    df_cap = get_sheet_data("capital", CAPITAL_COLS)
                    new_id = 1 if df_cap.empty else int(pd.to_numeric(df_cap['id'], errors='coerce').fillna(0).max() + 1)
                    new_row = pd.DataFrame([{
                        "id": new_id,
                        "entry_date": str(c_date),
                        "partner_name": partner,
                        "amount": float(cap_amount)
                    }])
                    df_cap = pd.concat([df_cap, new_row], ignore_index=True)
                    update_sheet_data("capital", df_cap)
                    st.success(f"✅ Capital for {partner} saved to Google Sheets!")
                    st.rerun()
                    
    with (col_c2 if is_admin else col_c2):
        st.markdown("### Current Capital Summary")
        df_cap = get_sheet_data("capital", CAPITAL_COLS)
        
        if not df_cap.empty:
            df_cap['amount'] = pd.to_numeric(df_cap['amount'], errors='coerce').fillna(0.0)
            summary_cap = df_cap.groupby('partner_name')['amount'].sum().reset_index()
            total_invested = summary_cap['amount'].sum()
            
            summary_cap_disp = summary_cap.copy()
            summary_cap_disp['amount'] = summary_cap_disp['amount'].apply(lambda x: f"Rs. {x:,.2f}")
            st.dataframe(summary_cap_disp.rename(columns={'partner_name': 'Partner', 'amount': 'Total Capital'}), use_container_width=True)
            
            st.info(f"**Total Capital Invested:** Rs. {total_invested:,.2f}")
            
            st.markdown("#### Capital Contribution History")
            df_cap_disp = df_cap.sort_values(by=['entry_date', 'id'], ascending=[False, False]).copy()
            df_cap_disp['amount'] = df_cap_disp['amount'].apply(lambda x: f"Rs. {x:,.2f}")
            st.dataframe(df_cap_disp[['id', 'entry_date', 'partner_name', 'amount']].rename(
                columns={'id': 'ID', 'entry_date': 'Date', 'partner_name': 'Partner', 'amount': 'Amount'}
            ), use_container_width=True)
            
            if is_admin:
                st.markdown("---")
                cap_act1, cap_act2 = st.columns(2)
                with cap_act1:
                    st.markdown("##### ✏️ Edit Capital Entry")
                    edit_cap_id = st.selectbox("Select Capital ID to Edit", df_cap['id'].tolist(), key="edit_cap_sel")
                    row_cap = df_cap[df_cap['id'] == edit_cap_id].iloc[0]
                    
                    with st.form("edit_cap_form"):
                        ec_date = st.date_input("Date", value=parse_db_date(row_cap['entry_date']), key="ec_d")
                        ec_p_idx = PARTNERS_LIST.index(row_cap['partner_name']) if row_cap['partner_name'] in PARTNERS_LIST else 0
                        ec_partner = st.selectbox("Partner Name", PARTNERS_LIST, index=ec_p_idx, key="ec_p")
                        ec_amt = st.number_input("Amount (Rs.)", min_value=0.0, value=float(row_cap['amount']), step=500.0, key="ec_a")
                        
                        if st.form_submit_button("Update Capital Record"):
                            idx = df_cap[df_cap['id'] == edit_cap_id].index[0]
                            df_cap.loc[idx, ['entry_date', 'partner_name', 'amount']] = [
                                str(ec_date), ec_partner, float(ec_amt)
                            ]
                            update_sheet_data("capital", df_cap)
                            st.success("✅ Capital Record updated in Google Sheets!")
                            st.rerun()
                            
                with cap_act2:
                    st.markdown("##### 🗑️ Delete Capital Entry")
                    del_id = st.selectbox("Select Capital ID to Delete", df_cap['id'].tolist(), key="del_cap_sel")
                    if st.button("Delete Capital Record", type="primary", key="btn_del_cap"):
                        df_cap = df_cap[df_cap['id'] != del_id]
                        update_sheet_data("capital", df_cap)
                        st.success("Capital Record deleted from Google Sheets!")
                        st.rerun()
        else:
            st.info("No capital contributions found in Google Sheet.")
