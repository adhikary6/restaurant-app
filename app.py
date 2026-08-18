import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# Database Setup
conn = sqlite3.connect('restaurant_accounts.db', check_same_thread=False)
c = conn.cursor()

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
conn.commit()

# Page Configuration
st.set_page_config(page_title="Accounts & Ledger", layout="wide")
st.title("🍽️ Restaurant & Counter - Daily Accounts & Ledger")

menu = ["Daily Entry", "Reports & Analytics", "Capital Management"]
choice = st.sidebar.selectbox("Select Menu", menu)

# 1. Daily Entry Section
if choice == "Daily Entry":
    st.subheader("📝 Daily Sales & Expense Entry")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💰 Sales Entry")
        with st.form("sale_form", clear_on_submit=True):
            s_date = st.date_input("Date", value=date.today(), key="s_date")
            counter = st.selectbox("Counter / Location", ["Outside Stall", "Inside Counter / Dining"])
            product = st.text_input("Product Name (e.g. Chicken Pakoda, Gile-Mete, Water, Cigarette)")
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
            category = st.selectbox("Expense Category", [
                "Raw Materials (Chicken, Fish, Eggs, Veg)", 
                "Grocery & Spices", 
                "Rent & Utility Bills", 
                "Staff Salary & Daily Allowance", 
                "Transportation & Marketing",
                "Other Miscellaneous Expenses"
            ])
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

# 2. Reports & Analytics Section
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
        
        total_sale = df_sales['Amount'].sum() if not df_sales.empty else 0.0
        total_exp = df_exp['Amount'].sum() if not df_exp.empty else 0.0
        net_profit = total_sale - total_exp
        
        st.markdown("---")
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Sales", f"Rs. {total_sale:,.2f}")
        m2.metric("Total Expenses", f"Rs. {total_exp:,.2f}")
        m3.metric("Net Profit", f"Rs. {net_profit:,.2f}", delta=f"Rs. {net_profit:,.2f}")
        st.markdown("---")
        
        tab1, tab2 = st.tabs(["Sales Breakdown & Management", "Expense Breakdown & Management"])
        
        with tab1:
            st.markdown("#### Product-wise Sales Summary")
            if not df_sales.empty:
                prod_summary = df_sales.groupby('Product').agg({'Qty': 'sum', 'Amount': 'sum'}).reset_index()
                prod_summary['Amount'] = prod_summary['Amount'].apply(lambda x: f"Rs. {x:,.2f}")
                st.dataframe(prod_summary, use_container_width=True)
                
                st.markdown("#### Detailed Sales Register")
                df_sales_disp = df_sales.copy()
                df_sales_disp['Amount'] = df_sales_disp['Amount'].apply(lambda x: f"Rs. {x:,.2f}")
                st.dataframe(df_sales_disp, use_container_width=True)
                
                st.markdown("##### 🗑️ Delete Incorrect Sale Entry")
                del_sale_id = st.selectbox("Select Sale ID to Delete", df_sales['ID'].tolist())
                if st.button("Delete Sale Record", type="primary"):
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
                cat_summary['Amount'] = cat_summary['Amount'].apply(lambda x: f"Rs. {x:,.2f}")
                st.dataframe(cat_summary, use_container_width=True)
                
                st.markdown("#### Detailed Expense Register")
                df_exp_disp = df_exp.copy()
                df_exp_disp['Amount'] = df_exp_disp['Amount'].apply(lambda x: f"Rs. {x:,.2f}")
                st.dataframe(df_exp_disp, use_container_width=True)
                
                st.markdown("##### 🗑️ Delete Incorrect Expense Entry")
                del_exp_id = st.selectbox("Select Expense ID to Delete", df_exp['ID'].tolist())
                if st.button("Delete Expense Record", type="primary"):
                    c.execute("DELETE FROM expenses WHERE id = ?", (del_exp_id,))
                    conn.commit()
                    st.success(f"Expense record ID {del_exp_id} deleted successfully!")
                    st.rerun()
            else:
                st.info("No expense records found for this period.")
    else:
        st.error("Start Date must be before or equal to End Date.")

# 3. Capital Management Section
elif choice == "Capital Management":
    st.subheader("💼 Partner Capital & Investment Ledger")
    
    col_c1, col_c2 = st.columns([1, 1.5])
    
    with col_c1:
        st.markdown("### Add Partner Capital")
        with st.form("capital_form", clear_on_submit=True):
            c_date = st.date_input("Date", value=date.today())
            partner = st.selectbox("Partner Name", ["Abhijit", "Jit", "Debasis", "Sumit"])
            cap_amount = st.number_input("Amount (Rs.)", min_value=0.0, value=0.0, step=500.0)
            
            submit_cap = st.form_submit_button("Record Capital")
            if submit_cap:
                c.execute("INSERT INTO capital (entry_date, partner_name, amount) VALUES (?, ?, ?)",
                          (c_date, partner, cap_amount))
                conn.commit()
                st.success(f"✅ Capital record for {partner} saved successfully!")
                st.rerun()
                    
    with col_c2:
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
            
            st.markdown("---")
            st.markdown("##### 🗑️ Delete Incorrect Capital Entry")
            del_id = st.selectbox("Select Capital ID to Delete", df_cap_all['ID'].tolist())
            if st.button("Delete Selected Capital Record", type="primary"):
                c.execute("DELETE FROM capital WHERE id = ?", (del_id,))
                conn.commit()
                st.success(f"Capital Record ID {del_id} deleted successfully!")
                st.rerun()
        else:
            st.info("No capital contributions recorded yet.")
