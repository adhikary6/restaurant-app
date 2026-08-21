import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Populating Capital & Stock...", layout="centered")
conn = st.connection("gsheets", type=GSheetsConnection)

st.header("⏳ Capital ও Stock রেজিস্টার গুগল শিটে সেভ হচ্ছে...")

# পার্টনারদের ক্যাপিটাল এন্ট্রি
capital_data = [
    {"id": 1, "entry_date": "2026-08-01", "partner_name": "Abhijit", "amount": 25000.0},
    {"id": 2, "entry_date": "2026-08-01", "partner_name": "Jit", "amount": 25000.0},
    {"id": 3, "entry_date": "2026-08-01", "partner_name": "Debasis", "amount": 25000.0},
    {"id": 4, "entry_date": "2026-08-01", "partner_name": "Sumit", "amount": 25000.0}
]

# ১৮ আগস্ট পর্যন্ত বেসিক ট্র্যাকড স্টক লগ
stock_data = [
    {"id": 1, "entry_date": "2026-08-14", "item_name": "Egg (পিস)", "opening_stock": 100, "added_stock": 100, "closing_stock": 140, "sold_quantity": 60},
    {"id": 2, "entry_date": "2026-08-14", "item_name": "Water Bottle 1L", "opening_stock": 24, "added_stock": 24, "closing_stock": 30, "sold_quantity": 18},
    {"id": 3, "entry_date": "2026-08-16", "item_name": "Egg (পিস)", "opening_stock": 140, "added_stock": 0, "closing_stock": 85, "sold_quantity": 55},
    {"id": 4, "entry_date": "2026-08-17", "item_name": "Campa Rs. 20", "opening_stock": 48, "added_stock": 24, "closing_stock": 50, "sold_quantity": 22},
    {"id": 5, "entry_date": "2026-08-18", "item_name": "Egg (পিস)", "opening_stock": 85, "added_stock": 100, "closing_stock": 115, "sold_quantity": 70}
]

try:
    df_cap = pd.DataFrame(capital_data)
    df_stk = pd.DataFrame(stock_data)
    
    conn.update(worksheet="capital", data=df_cap)
    conn.update(worksheet="inventory_log", data=df_stk)
    
    st.success("✅ Capital এবং Inventory Log সফলভাবে গুগল শিটে সেভ হয়ে গেছে!")
    st.info("এবার আপনি মূল পূর্ণাঙ্গ `app.py` কোডটি ফিরিয়ে দিন।")
except Exception as e:
    st.error(f"ত্রুটি: {e}")
