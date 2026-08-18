import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# ডেটাবেস সেটআপ
conn = sqlite3.connect('munshirhat_restaurant.db', check_same_thread=False)
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

# পেজ কনফিগারেশন
st.set_page_config(page_title="Bar & Restaurant Accounts", layout="wide")
st.title("🍽️ Restaurant & Snacks Counter - Manager & Ledger")

menu = ["Daily Entry (বিক্রি ও খরচ)", "Reports & Analytics (রিপোর্ট)", "Capital Management (মূলধন)"]
choice = st.sidebar.selectbox("মেনু নির্বাচন করুন", menu)

# ১. ডেইলি এন্ট্রি সেকশন
if choice == "Daily Entry (বিক্রি ও খরচ)":
    st.subheader("📝 প্রতিদিনের বিক্রি ও খরচের হিসাব এন্ট্রি")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💰 বিক্রির এন্ট্রি (Sale Entry)")
        with st.form("sale_form", clear_on_submit=True):
            s_date = st.date_input("তারিখ", value=date.today(), key="s_date")
            counter = st.selectbox("কাউন্টার", ["Outside Stall (বাইরের স্টল)", "Inside Restaurant (ভেতরের কাউন্টার)"])
            product = st.text_input("প্রোডাক্টের নাম (যেমন: Chicken Pakoda, Gile-Mete, Cigarette, Water)")
            quantity = st.number_input("পরিমাণ (Quantity/Plate)", min_value=1, value=1)
            amount = st.number_input("মোট বিক্রির টাকা (Total Sale Amount ₹)", min_value=0.0, step=10.0)
            
            submit_sale = st.form_submit_button("বিক্রি সেভ করুন")
            if submit_sale:
                if product and amount > 0:
                    c.execute("INSERT INTO sales (entry_date, product_name, quantity, amount, counter_type) VALUES (?, ?, ?, ?, ?)",
                              (s_date, product.strip(), quantity, amount, counter))
                    conn.commit()
                    st.success("✅ বিক্রি সফলভাবে সেভ হয়েছে!")
                else:
                    st.error("অনুগ্রহ করে প্রোডাক্ট ও টাকার পরিমাণ সঠিকভাবে লিখুন।")

    with col2:
        st.markdown("### 💸 খরচের এন্ট্রি (Expense Entry)")
        with st.form("expense_form", clear_on_submit=True):
            e_date = st.date_input("তারিখ", value=date.today(), key="e_date")
            category = st.selectbox("খরচের বিভাগ", ["Raw Material (চিকেন, মাছ, ডিম)", "Grocery & Spices", "Liquor Counter / Rent / Bill", "Staff Salary & Daily Allowance", "Other Expenses"])
            particulars = st.text_input("খরচের বিবরণ (Particulars)")
            e_amount = st.number_input("খরচের টাকা (Expense Amount ₹)", min_value=0.0, step=10.0)
            
            submit_exp = st.form_submit_button("খরচ সেভ করুন")
            if submit_exp:
                if particulars and e_amount > 0:
                    c.execute("INSERT INTO expenses (entry_date, particulars, category, amount) VALUES (?, ?, ?, ?)",
                              (e_date, particulars.strip(), category, e_amount))
                    conn.commit()
                    st.success("✅ খরচ সফলভাবে সেভ হয়েছে!")
                else:
                    st.error("অনুগ্রহ করে বিবরণ ও খরচের পরিমাণ সঠিকভাবে লিখুন।")

# ২. রিপোর্ট সেকশন
elif choice == "Reports & Analytics (রিপোর্ট)":
    st.subheader("📊 ডেট রেঞ্জ অনুযায়ী ব্যবসার রিপোর্ট ও লাভ-লোকসান")
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        start_date = st.date_input("শুরুর তারিখ (Start Date)", value=date.today().replace(day=1))
    with col_d2:
        end_date = st.date_input("শেষ তারিখ (End Date)", value=date.today())
        
    if start_date <= end_date:
        # ফেচিং ডেটা
        df_sales = pd.read_sql_query("SELECT entry_date as Date, counter_type as Counter, product_name as Product, quantity as Qty, amount as Amount FROM sales WHERE entry_date BETWEEN ? AND ?", conn, params=(start_date, end_date))
        df_exp = pd.read_sql_query("SELECT entry_date as Date, category as Category, particulars as Particulars, amount as Amount FROM expenses WHERE entry_date BETWEEN ? AND ?", conn, params=(start_date, end_date))
        
        total_sale = df_sales['Amount'].sum() if not df_sales.empty else 0.0
        total_exp = df_exp['Amount'].sum() if not df_exp.empty else 0.0
        net_profit = total_sale - total_exp
        
        # কার্ড মেট্রিক্স
        st.markdown("---")
        m1, m2, m3 = st.columns(3)
        m1.metric("মোট বিক্রি (Total Sale)", f"₹ {total_sale:,.2f}")
        m2.metric("মোট খরচ (Total Expense)", f"₹ {total_exp:,.2f}")
        m3.metric("মোট লাভ (Net Profit)", f"₹ {net_profit:,.2f}", delta=f"{net_profit:,.2f}")
        st.markdown("---")
        
        # আইটেমওয়াইজ ডিটেইলস
        tab1, tab2 = st.tabs(["বিক্রির বিস্তারিত (Sales Breakdown)", "খরচের বিস্তারিত (Expense Breakdown)"])
        
        with tab1:
            st.markdown("#### প্রোডাক্ট অনুযায়ী বিক্রির সারসংক্ষেপ")
            if not df_sales.empty:
                prod_summary = df_sales.groupby('Product').agg({'Qty': 'sum', 'Amount': 'sum'}).reset_index()
                st.dataframe(prod_summary, use_container_width=True)
                st.markdown("#### সম্পূর্ণ বিক্রির তালিকা")
                st.dataframe(df_sales, use_container_width=True)
            else:
                st.info("এই সময়ে কোনো বিক্রির রেকর্ড নেই।")
                
        with tab2:
            st.markdown("#### ক্যাটাগরি অনুযায়ী খরচের সারসংক্ষেপ")
            if not df_exp.empty:
                cat_summary = df_exp.groupby('Category').agg({'Amount': 'sum'}).reset_index()
                st.dataframe(cat_summary, use_container_width=True)
                st.markdown("#### সম্পূর্ণ খরচের বিবরণ (Particulars)")
                st.dataframe(df_exp, use_container_width=True)
            else:
                st.info("এই সময়ে কোনো খরচের রেকর্ড নেই।")
    else:
        st.error("শুরুর তারিখ শেষ তারিখের চেয়ে আগে হতে হবে।")

# ৩. ক্যাপিটাল সেকশন
elif choice == "Capital Management (মূলধন)":
    st.subheader("💼 পার্টনারদের ক্যাপিটাল ও ইনভেস্টমেন্ট হিসাব")
    
    col_c1, col_c2 = st.columns([1, 1.5])
    
    with col_c1:
        st.markdown("### মূলধন যোগ করুন")
        with st.form("capital_form", clear_on_submit=True):
            c_date = st.date_input("তারিখ", value=date.today())
            partner = st.selectbox("পার্টনারের নাম", ["Partner 1", "Partner 2", "Partner 3", "Partner 4"])
            cap_amount = st.number_input("টাকার পরিমাণ (₹)", min_value=0.0, step=500.0)
            
            submit_cap = st.form_submit_button("ক্যাপিটাল জমা করুন")
            if submit_cap:
                if cap_amount > 0:
                    c.execute("INSERT INTO capital (entry_date, partner_name, amount) VALUES (?, ?, ?)",
                              (c_date, partner, cap_amount))
                    conn.commit()
                    st.success("✅ মূলধন রেকর্ড সেভ হয়েছে!")
                else:
                    st.error("টাকার পরিমাণ লিখুন।")
                    
    with col_c2:
        st.markdown("### পার্টনারদের মোট ক্যাপিটাল স্ট্যাটাস")
        df_cap = pd.read_sql_query("SELECT partner_name as Partner, SUM(amount) as Total_Capital FROM capital GROUP BY partner_name", conn)
        df_cap_all = pd.read_sql_query("SELECT entry_date as Date, partner_name as Partner, amount as Amount FROM capital ORDER BY entry_date DESC", conn)
        
        if not df_cap.empty:
            st.dataframe(df_cap, use_container_width=True)
            total_invested = df_cap['Total_Capital'].sum()
            st.info(f"**ব্যবসার সর্বমোট ইনভেস্টমেন্ট:** ₹ {total_invested:,.2f}")
            
            st.markdown("#### ক্যাপিটাল জমার হিস্ট্রি")
            st.dataframe(df_cap_all, use_container_width=True)
        else:
            st.info("এখনো কোনো মূলধন এন্ট্রি করা হয়নি।")
