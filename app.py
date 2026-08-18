import streamlit as st
import sqlite3
import pandas as pd
import io
from datetime import date, datetime

# -------------------------------------------------------------
# Database Setup & User Table
# -------------------------------------------------------------
conn = sqlite3.connect('restaurant_accounts.db', check_same_thread=False)
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT,
    role TEXT
)''')

default_users = [
    ("abhijit", "1234", "admin"),
    ("jit", "1234", "admin"),
    ("debasis", "1234", "viewer"),
    ("sumit", "1234", "viewer")
]
for u, p, r in default_users:
    c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)", (u, p, r))

c.execute('''
CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_date DATE,
    product_name TEXT,
    quantity INTEGER,
    amount REAL,
    counter_type TEXT
)''')

c.execute('''
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_date DATE,
    particulars TEXT,
    category TEXT,
    amount REAL
)''')

c.execute('''
CREATE TABLE IF NOT EXISTS capital (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_date DATE,
    partner_name TEXT,
    amount REAL
)''')

c.execute('''
CREATE TABLE IF NOT EXISTS inventory_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_date DATE,
    item_name TEXT,
    opening_stock INTEGER,
    added_stock INTEGER,
    closing_stock INTEGER,
    sold_quantity INTEGER
)''')
conn.commit()

# -------------------------------------------------------------
# Authentication Flow
# -------------------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""

def login():
    st.set_page_config(page_title="Login - Restaurant Ledger", layout="centered")
    st.markdown("### 🔐 Restaurant Management Login")
    st.info("Please enter your credentials to access the accounts.")
    
    with st.form("login_form"):
        user = st.text_input("Username").strip().lower()
        pwd = st.text_input("Password", type="password")
        btn = st.form_submit_button("Log In", type="primary")
        
        if btn:
            c.execute("SELECT password, role FROM users WHERE username = ?", (user,))
            user_data = c.fetchone()
            if user_data and user_data[0] == pwd:
                st.session_state.logged_in = True
                st.session_state.username = user
                st.session_state.role = user_data[1]
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
st.set_page_config(page_title="Accounts & Stock Ledger", layout="wide")
st.title("🍽️ Restaurant & Counter - Accounts & Inventory Ledger")

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
            c.execute("SELECT password FROM users WHERE username = ?", (st.session_state.username,))
            curr_db_pwd = c.fetchone()[0]
            
            if old_p != curr_db_pwd:
                st.error("Current password is incorrect.")
            elif not new_p.strip():
                st.error("New password cannot be empty.")
            elif new_p != conf_p:
                st.error("New passwords do not match.")
            else:
                c.execute("UPDATE users SET password = ? WHERE username = ?", (new_p.strip(), st.session_state.username))
                conn.commit()
                st.success("✅ Password changed successfully!")

if is_admin:
    with st.sidebar.expander("🛠️ Admin: Reset User Password"):
        with st.form("admin_reset_form", clear_on_submit=True):
            target_user = st.selectbox("Select User to Reset", ["abhijit", "jit", "debasis", "sumit"])
            admin_new_pwd = st.text_input("Set New Password", value="1234")
            reset_btn = st.form_submit_button("Reset Password Now")
            
            if reset_btn:
                if admin_new_pwd.strip():
                    c.execute("UPDATE users SET password = ? WHERE username = ?", (admin_new_pwd.strip(), target_user))
                    conn.commit()
                    st.success(f"✅ Password for {target_user.capitalize()} reset to: {admin_new_pwd.strip()}")
                else:
                    st.error("Password cannot be empty.")

if st.sidebar.button("🚪 Logout"):
    logout()
st.sidebar.markdown("---")

if is_admin:
    menu = ["Daily Entry", "Daily Stock Register", "Reports & Analytics", "Capital Management"]
else:
    menu = ["Reports & Analytics", "Daily Stock Register", "Capital Management"]

choice = st.sidebar.selectbox("Select Menu", menu)

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
        return datetime.strptime(str(val), "%Y-%m-%d").date()
    except Exception:
        return date.today()

# -------------------------------------------------------------
# 1. Daily Entry Section (Sales & Expenses) - Admin Only
# -------------------------------------------------------------
if choice == "Daily Entry":
    if not is_admin:
        st.warning("⚠️ You have Read-Only access. You cannot add or modify entries.")
        st.stop()

    st.subheader("📝 Daily Sales & Expense Entry")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💰 Sales Entry")
        with st.form("sale_form", clear_on_submit=True):
            s_date = st.date_input("Date", value=date.today(), key="s_date")
            counter = st.selectbox("Counter / Location", ["Outside Stall", "Inside Counter / Dining"])
            product = st.text_input("Product Name (e.g. Chicken Pakoda, Gile-Mete, Cigarette)")
            quantity = st.number_input("Quantity", min_value=0, value=1, step=1)
            amount = st.number_input("Total Sale Amount (Rs.)", min_value=0.0, value=0.0, step=10.0)
            
            submit_sale = st.form_submit_button("Save Sale Record")
            if submit_sale:
                if product.strip():
                    c.execute("INSERT INTO sales (entry_date, product_name, quantity, amount, counter_type) VALUES (?, ?, ?, ?, ?)",
                              (s_date, product.strip(), quantity, amount, counter))
                    conn.commit()
                    st.success("✅ Sale record saved successfully!")
                    st.rerun()
                else:
                    st.error("Please enter a valid product name.")

    with col2:
        st.markdown("### 💸 Expense Entry")
        with st.form("expense_form", clear_on_submit=True):
            e_date = st.date_input("Date", value=date.today(), key="e_date")
            category = st.selectbox("Expense Category", EXPENSE_CATEGORIES)
            particulars = st.text_input("Particulars / Details (e.g. 5kg Chicken, Mustard Oil, Gas Cylinder)")
            e_amount = st.number_input("Expense Amount (Rs.)", min_value=0.0, value=0.0, step=10.0)
            
            submit_exp = st.form_submit_button("Save Expense Record")
            if submit_exp:
                if particulars.strip():
                    c.execute("INSERT INTO expenses (entry_date, particulars, category, amount) VALUES (?, ?, ?, ?)",
                              (e_date, particulars.strip(), category, e_amount))
                    conn.commit()
                    st.success("✅ Expense record saved successfully!")
                    st.rerun()
                else:
                    st.error("Please enter particulars details.")

# -------------------------------------------------------------
# 2. Daily Stock Register
# -------------------------------------------------------------
elif choice == "Daily Stock Register":
    st.subheader("📦 Daily Stock & Automated Sales Tracker")
    st.caption("Track stock movement: Daily Sold = (Opening + Added) - Closing")
    
    if is_admin:
        col_st1, col_st2 = st.columns([1.1, 1.9])
    else:
        col_st1, col_st2 = None, st.container()
    
    if is_admin:
        with col_st1:
            st.markdown("### 📥 Record Daily Stock")
            with st.form("stock_form", clear_on_submit=True):
                stk_date = st.date_input("Date", value=date.today(), key="stk_date")
                stk_item = st.selectbox("Select Item", TRACKED_ITEMS)
                
                op_stock = st.number_input("Opening Stock (Pcs)", min_value=0, value=0, step=1)
                add_stock = st.number_input("Stock Added / Purchased Today (Pcs)", min_value=0, value=0, step=1)
                cl_stock = st.number_input("Closing Stock at End of Day (Pcs)", min_value=0, value=0, step=1)
                
                total_available = op_stock + add_stock
                calc_sold = max(0, total_available - cl_stock)
                
                st.info(f"💡 Calculated Daily Sold: **{calc_sold} Pcs**")
                
                submit_stock = st.form_submit_button("Save Stock Record")
                if submit_stock:
                    if cl_stock > total_available:
                        st.error(f"Closing stock ({cl_stock}) cannot be greater than Total Available ({total_available})!")
                    else:
                        c.execute("""
                            INSERT INTO inventory_log (entry_date, item_name, opening_stock, added_stock, closing_stock, sold_quantity)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (stk_date, stk_item, op_stock, add_stock, cl_stock, calc_sold))
                        conn.commit()
                        st.success(f"✅ Stock record for {stk_item} saved! ({calc_sold} pcs sold)")
                        st.rerun()

    with (col_st2 if is_admin else col_st2):
        st.markdown("### 📋 Daily Stock & Sales Register")
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            stk_start = st.date_input("From Date", value=date.today().replace(day=1), key="stk_start")
        with f_col2:
            stk_end = st.date_input("To Date", value=date.today(), key="stk_end")
            
        df_stock = pd.read_sql_query("""
            SELECT id as ID, entry_date as Date, item_name as Item, 
                   opening_stock as "Opening", added_stock as "Added", 
                   closing_stock as "Closing", sold_quantity as "Sold (Pcs)"
            FROM inventory_log
            WHERE entry_date BETWEEN ? AND ?
            ORDER BY entry_date DESC, id DESC
        """, conn, params=(stk_start, stk_end))
        
        if not df_stock.empty:
            st.dataframe(df_stock, use_container_width=True)
            st.markdown("#### 📊 Total Quantity Sold in Selected Period")
            sold_sum = df_stock.groupby('Item')['Sold (Pcs)'].sum().reset_index()
            st.dataframe(sold_sum, use_container_width=True)
            
            if is_admin:
                st.markdown("---")
                act_col1, act_col2 = st.columns(2)
                
                with act_col1:
                    st.markdown("##### ✏️ Edit Stock Entry")
                    edit_stock_id = st.selectbox("Select Stock ID to Edit", df_stock['ID'].tolist(), key="edit_stk_sel")
                    row_stk = df_stock[df_stock['ID'] == edit_stock_id].iloc[0]
                    
                    with st.form("edit_stock_form"):
                        e_stk_date = st.date_input("Date", value=parse_db_date(row_stk['Date']), key="e_stk_d")
                        current_item_val = row_stk['Item'] if row_stk['Item'] in TRACKED_ITEMS else TRACKED_ITEMS[0]
                        e_stk_item = st.selectbox("Item", TRACKED_ITEMS, index=TRACKED_ITEMS.index(current_item_val), key="e_stk_i")
                        e_op = st.number_input("Opening Stock", min_value=0, value=int(row_stk['Opening']), step=1, key="e_stk_op")
                        e_add = st.number_input("Added Stock", min_value=0, value=int(row_stk['Added']), step=1, key="e_stk_add")
                        e_cl = st.number_input("Closing Stock", min_value=0, value=int(row_stk['Closing']), step=1, key="e_stk_cl")
                        
                        e_tot = e_op + e_add
                        e_sold = max(0, e_tot - e_cl)
                        
                        update_stk_btn = st.form_submit_button("Update Stock Record")
                        if update_stk_btn:
                            if e_cl > e_tot:
                                st.error(f"Closing stock ({e_cl}) cannot be greater than Total Available ({e_tot})!")
                            else:
                                c.execute("""
                                    UPDATE inventory_log 
                                    SET entry_date = ?, item_name = ?, opening_stock = ?, added_stock = ?, closing_stock = ?, sold_quantity = ?
                                    WHERE id = ?
                                """, (e_stk_date, e_stk_item, e_op, e_add, e_cl, e_sold, edit_stock_id))
                                conn.commit()
                                st.success(f"✅ Stock Record ID {edit_stock_id} updated successfully!")
                                st.rerun()

                with act_col2:
                    st.markdown("##### 🗑️ Delete Stock Entry")
                    del_stock_id = st.selectbox("Select Stock ID to Delete", df_stock['ID'].tolist(), key="del_stk_sel")
                    if st.button("Delete Stock Record", type="primary", key="btn_del_stk"):
                        c.execute("DELETE FROM inventory_log WHERE id = ?", (del_stock_id,))
                        conn.commit()
                        st.success(f"Stock Record ID {del_stock_id} deleted successfully!")
                        st.rerun()
        else:
            st.info("No stock records found for the selected period.")

# -------------------------------------------------------------
# 3. Reports & Analytics Section (with Excel Export)
# -------------------------------------------------------------
elif choice == "Reports & Analytics":
    st.subheader("📊 Business Summary & Profit / Loss Statement")
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        start_date = st.date_input("Start Date", value=date.today().replace(day=1))
    with col_d2:
        end_date = st.date_input("End Date", value=date.today())
        
    if start_date <= end_date:
        df_sales = pd.read_sql_query("SELECT id as ID, entry_date as Date, counter_type as Counter, product_name as Product, quantity as Qty, amount as Amount FROM sales WHERE entry_date BETWEEN ? AND ?", conn, params=(start_date, end_date))
        df_exp = pd.read_sql_query("SELECT id as ID, entry_date as Date, category as Category, particulars as Particulars, amount as Amount FROM expenses WHERE entry_date BETWEEN ? AND ?", conn, params=(start_date, end_date))
        df_stock_exp = pd.read_sql_query("SELECT entry_date as Date, item_name as Item, opening_stock as Opening, added_stock as Added, closing_stock as Closing, sold_quantity as Sold_Qty FROM inventory_log WHERE entry_date BETWEEN ? AND ?", conn, params=(start_date, end_date))
        df_cap_exp = pd.read_sql_query("SELECT entry_date as Date, partner_name as Partner, amount as Amount FROM capital ORDER BY entry_date DESC", conn)

        total_sale = df_sales['Amount'].sum() if not df_sales.empty else 0.0
        total_exp = df_exp['Amount'].sum() if not df_exp.empty else 0.0
        net_profit = total_sale - total_exp
        
        # --- Excel Generator ---
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            # Summary Sheet
            df_summary = pd.DataFrame({
                "Report Metric": ["Period Start", "Period End", "Total Sales", "Total Expenses", "Net Profit / Loss"],
                "Value": [str(start_date), str(end_date), total_sale, total_exp, net_profit]
            })
            df_summary.to_excel(writer, sheet_name='P&L Summary', index=False)
            
            # Sales & Expenses
            df_sales.to_excel(writer, sheet_name='Sales Register', index=False)
            df_exp.to_excel(writer, sheet_name='Expense Register', index=False)
            df_stock_exp.to_excel(writer, sheet_name='Stock Register', index=False)
            df_cap_exp.to_excel(writer, sheet_name='Capital Register', index=False)

        excel_data = excel_buffer.getvalue()
        
        st.download_button(
            label="📥 Download Full Account Book (.xlsx)",
            data=excel_data,
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
            st.markdown("#### Product-wise Sales Summary")
            if not df_sales.empty:
                prod_summary = df_sales.groupby('Product').agg({'Qty': 'sum', 'Amount': 'sum'}).reset_index()
                prod_summary_disp = prod_summary.copy()
                prod_summary_disp['Amount'] = prod_summary_disp['Amount'].apply(lambda x: f"Rs. {x:,.2f}")
                st.dataframe(prod_summary_disp, use_container_width=True)
                
                st.markdown("#### Detailed Sales Register")
                df_sales_disp = df_sales.copy()
                df_sales_disp['Amount'] = df_sales_disp['Amount'].apply(lambda x: f"Rs. {x:,.2f}")
                st.dataframe(df_sales_disp, use_container_width=True)
                
                if is_admin:
                    st.markdown("---")
                    s_act1, s_act2 = st.columns(2)
                    
                    with s_act1:
                        st.markdown("##### ✏️ Edit Sale Entry")
                        edit_sale_id = st.selectbox("Select Sale ID to Edit", df_sales['ID'].tolist(), key="edit_s_sel")
                        row_s = df_sales[df_sales['ID'] == edit_sale_id].iloc[0]
                        
                        with st.form("edit_sale_form"):
                            es_date = st.date_input("Date", value=parse_db_date(row_s['Date']), key="es_d")
                            counters = ["Outside Stall", "Inside Counter / Dining"]
                            es_c_idx = counters.index(row_s['Counter']) if row_s['Counter'] in counters else 0
                            es_counter = st.selectbox("Counter", counters, index=es_c_idx, key="es_c")
                            es_prod = st.text_input("Product Name", value=str(row_s['Product']), key="es_p")
                            es_qty = st.number_input("Quantity", min_value=0, value=int(row_s['Qty']), step=1, key="es_q")
                            es_amt = st.number_input("Total Sale Amount (Rs.)", min_value=0.0, value=float(row_s['Amount']), step=10.0, key="es_a")
                            
                            update_sale_btn = st.form_submit_button("Update Sale Record")
                            if update_sale_btn:
                                if es_prod.strip():
                                    c.execute("""
                                        UPDATE sales 
                                        SET entry_date = ?, counter_type = ?, product_name = ?, quantity = ?, amount = ?
                                        WHERE id = ?
                                    """, (es_date, es_counter, es_prod.strip(), es_qty, es_amt, edit_sale_id))
                                    conn.commit()
                                    st.success(f"✅ Sale Record ID {edit_sale_id} updated successfully!")
                                    st.rerun()
                                else:
                                    st.error("Product name cannot be empty.")
                                    
                    with s_act2:
                        st.markdown("##### 🗑️ Delete Sale Entry")
                        del_sale_id = st.selectbox("Select Sale ID to Delete", df_sales['ID'].tolist(), key="del_s_sel")
                        if st.button("Delete Sale Record", type="primary", key="btn_del_sale"):
                            c.execute("DELETE FROM sales WHERE id = ?", (del_sale_id,))
                            conn.commit()
                            st.success(f"Sale record ID {del_sale_id} deleted successfully!")
                            st.rerun()
            else:
                st.info("No sales records found for this period.")
                
        with tab2:
            st.markdown("#### Category-wise Expense Summary")
            if not df_exp.empty:
                cat_summary = df_exp.groupby('Category').agg({'Amount': 'sum'}).reset_index()
                cat_summary_disp = cat_summary.copy()
                cat_summary_disp['Amount'] = cat_summary_disp['Amount'].apply(lambda x: f"Rs. {x:,.2f}")
                st.dataframe(cat_summary_disp, use_container_width=True)
                
                st.markdown("#### Detailed Expense Register")
                df_exp_disp = df_exp.copy()
                df_exp_disp['Amount'] = df_exp_disp['Amount'].apply(lambda x: f"Rs. {x:,.2f}")
                st.dataframe(df_exp_disp, use_container_width=True)
                
                if is_admin:
                    st.markdown("---")
                    e_act1, e_act2 = st.columns(2)
                    
                    with e_act1:
                        st.markdown("##### ✏️ Edit Expense Entry")
                        edit_exp_id = st.selectbox("Select Expense ID to Edit", df_exp['ID'].tolist(), key="edit_e_sel")
                        row_e = df_exp[df_exp['ID'] == edit_exp_id].iloc[0]
                        
                        with st.form("edit_expense_form"):
                            ee_date = st.date_input("Date", value=parse_db_date(row_e['Date']), key="ee_d")
                            ee_cat_idx = EXPENSE_CATEGORIES.index(row_e['Category']) if row_e['Category'] in EXPENSE_CATEGORIES else 0
                            ee_cat = st.selectbox("Expense Category", EXPENSE_CATEGORIES, index=ee_cat_idx, key="ee_c")
                            ee_part = st.text_input("Particulars / Details", value=str(row_e['Particulars']), key="ee_p")
                            ee_amt = st.number_input("Expense Amount (Rs.)", min_value=0.0, value=float(row_e['Amount']), step=10.0, key="ee_a")
                            
                            update_exp_btn = st.form_submit_button("Update Expense Record")
                            if update_exp_btn:
                                if ee_part.strip():
                                    c.execute("""
                                        UPDATE expenses 
                                        SET entry_date = ?, category = ?, particulars = ?, amount = ?
                                        WHERE id = ?
                                    """, (ee_date, ee_cat, ee_part.strip(), ee_amt, edit_exp_id))
                                    conn.commit()
                                    st.success(f"✅ Expense Record ID {edit_exp_id} updated successfully!")
                                    st.rerun()
                                else:
                                    st.error("Particulars details cannot be empty.")
                                    
                    with e_act2:
                        st.markdown("##### 🗑️ Delete Expense Entry")
                        del_exp_id = st.selectbox("Select Expense ID to Delete", df_exp['ID'].tolist(), key="del_e_sel")
                        if st.button("Delete Expense Record", type="primary", key="btn_del_exp"):
                            c.execute("DELETE FROM expenses WHERE id = ?", (del_exp_id,))
                            conn.commit()
                            st.success(f"Expense record ID {del_exp_id} deleted successfully!")
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
    
    if is_admin:
        col_c1, col_c2 = st.columns([1, 1.5])
    else:
        col_c1, col_c2 = None, st.container()
    
    if is_admin:
        with col_c1:
            st.markdown("### Add Partner Capital")
            with st.form("capital_form", clear_on_submit=True):
                c_date = st.date_input("Date", value=date.today())
                partner = st.selectbox("Partner Name", PARTNERS_LIST)
                cap_amount = st.number_input("Amount (Rs.)", min_value=0.0, value=0.0, step=500.0)
                
                submit_cap = st.form_submit_button("Record Capital")
                if submit_cap:
                    c.execute("INSERT INTO capital (entry_date, partner_name, amount) VALUES (?, ?, ?)",
                              (c_date, partner, cap_amount))
                    conn.commit()
                    st.success(f"✅ Capital record for {partner} saved successfully!")
                    st.rerun()
                    
    with (col_c2 if is_admin else col_c2):
        st.markdown("### Current Capital Summary")
        df_cap = pd.read_sql_query("SELECT partner_name as Partner, SUM(amount) as Total_Capital FROM capital GROUP BY partner_name", conn)
        df_cap_all = pd.read_sql_query("SELECT id as ID, entry_date as Date, partner_name as Partner, amount as Amount FROM capital ORDER BY entry_date DESC", conn)
        
        if not df_cap.empty:
            total_invested = df_cap['Total_Capital'].sum()
            df_cap_disp = df_cap.copy()
            df_cap_disp['Total_Capital'] = df_cap_disp['Total_Capital'].apply(lambda x: f"Rs. {x:,.2f}")
            st.dataframe(df_cap_disp, use_container_width=True)
            
            st.info(f"**Total Capital Invested:** Rs. {total_invested:,.2f}")
            
            st.markdown("#### Capital Contribution History")
            df_cap_all_disp = df_cap_all.copy()
            df_cap_all_disp['Amount'] = df_cap_all_disp['Amount'].apply(lambda x: f"Rs. {x:,.2f}")
            st.dataframe(df_cap_all_disp, use_container_width=True)
            
            if is_admin:
                st.markdown("---")
                cap_act1, cap_act2 = st.columns(2)
                
                with cap_act1:
                    st.markdown("##### ✏️ Edit Capital Entry")
                    edit_cap_id = st.selectbox("Select Capital ID to Edit", df_cap_all['ID'].tolist(), key="edit_cap_sel")
                    row_cap = df_cap_all[df_cap_all['ID'] == edit_cap_id].iloc[0]
                    
                    with st.form("edit_cap_form"):
                        ec_date = st.date_input("Date", value=parse_db_date(row_cap['Date']), key="ec_d")
                        ec_p_idx = PARTNERS_LIST.index(row_cap['Partner']) if row_cap['Partner'] in PARTNERS_LIST else 0
                        ec_partner = st.selectbox("Partner Name", PARTNERS_LIST, index=ec_p_idx, key="ec_p")
                        ec_amt = st.number_input("Amount (Rs.)", min_value=0.0, value=float(row_cap['Amount']), step=500.0, key="ec_a")
                        
                        update_cap_btn = st.form_submit_button("Update Capital Record")
                        if update_cap_btn:
                            c.execute("""
                                UPDATE capital 
                                SET entry_date = ?, partner_name = ?, amount = ?
                                WHERE id = ?
                            """, (ec_date, ec_partner, ec_amt, edit_cap_id))
                            conn.commit()
                            st.success(f"✅ Capital Record ID {edit_cap_id} updated successfully!")
                            st.rerun()
                            
                with cap_act2:
                    st.markdown("##### 🗑️ Delete Capital Entry")
                    del_id = st.selectbox("Select Capital ID to Delete", df_cap_all['ID'].tolist(), key="del_cap_sel")
                    if st.button("Delete Capital Record", type="primary", key="btn_del_cap"):
                        c.execute("DELETE FROM capital WHERE id = ?", (del_id,))
                        conn.commit()
                        st.success(f"Capital Record ID {del_id} deleted successfully!")
                        st.rerun()
        else:
            st.info("No capital contributions recorded yet.")
