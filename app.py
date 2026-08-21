import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Auto Populating Sheets...", layout="centered")
conn = st.connection("gsheets", type=GSheetsConnection)

st.header("⏳ পুরনো ডেটা গুগল শিটে অটোমেটিক সেভ হচ্ছে...")

# ১৮ আগস্ট পর্যন্ত সেলস ডেটা
sales_data = [
    {"id": 1, "entry_date": "2026-08-14", "counter_type": "Inside Counter / Dining", "product_name": "Opening Day Sale", "quantity": 1, "amount": 1920},
    {"id": 2, "entry_date": "2026-08-16", "counter_type": "Inside Counter / Dining", "product_name": "Counter Sale", "quantity": 1, "amount": 2522},
    {"id": 3, "entry_date": "2026-08-17", "counter_type": "Inside Counter / Dining", "product_name": "Counter Sale", "quantity": 1, "amount": 2010},
    {"id": 4, "entry_date": "2026-08-18", "counter_type": "Inside Counter / Dining", "product_name": "Counter Sale", "quantity": 1, "amount": 2800}
]

# ১৮ আগস্ট পর্যন্ত খরচের ডেটা
expenses_data = [
    {"id": 1, "entry_date": "2026-08-14", "category": "Raw Materials (Chicken, Fish, Eggs, Veg)", "particulars": "Raw Materials & Groceries", "amount": 5500},
    {"id": 2, "entry_date": "2026-08-16", "category": "Other Miscellaneous Expenses", "particulars": "Gas, Cutlery & Misc", "amount": 3200},
    {"id": 3, "entry_date": "2026-08-17", "category": "Grocery & Spices", "particulars": "Daily Grocery & Spices", "amount": 1850},
    {"id": 4, "entry_date": "2026-08-18", "category": "Raw Materials (Chicken, Fish, Eggs, Veg)", "particulars": "Raw Materials", "amount": 1557}
]

try:
    df_sales = pd.DataFrame(sales_data)
    df_exp = pd.DataFrame(expenses_data)
    
    conn.update(worksheet="sales", data=df_sales)
    conn.update(worksheet="expenses", data=df_exp)
    
    st.success("✅ সফল হয়েছে! ১৮ তারিখ পর্যন্ত সমস্ত ডেটা গুগল শিটে সেভ হয়ে গেছে।")
    st.info("এবার আপনি আগের পূর্ণাঙ্গ `app.py` কোডটি ফিরিয়ে দিতে পারেন।")
except Exception as e:
    st.error(f"Error: {e}")
