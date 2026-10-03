import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="தானியங்கி வரவு-செலவு டிராக்கர்", layout="wide")

st.title("🏦 பல வங்கி தானியங்கி வரவு-செலவு மேனேஜர்")
st.caption("Axis Bank | Canara Bank | Kotak Bank | Indian Overseas Bank (IOB)")

# 1. விதிகள் மற்றும் கலர் குறியீடுகள் (Auto-Categorization Rules)
CATEGORIES = {
    "பச்சை (Green - முதலீடு & EMI)": [
        "LOAN", "EMI", "ICICI", "INSURANCE", "HEALTH", "TERM", 
        "MUTUAL FUND", "ZERODHA", "ANGEL", "UPSTOX", "EQUITY", "SIP"
    ],
    "மஞ்சள் (Yellow - அத்தியாவசிய வீட்டுச் செலவுகள்)": [
        "RENT", "GROCERY", "SUPERMARKET", "MILK", "GAS", "CYLINDER", 
        "ELECTRICITY", "TNEB", "EB", "RECHARGE", "VEGETABLE", "PROVISION"
    ],
    "சிவப்பு (Red - கட்டுப்படுத்த வேண்டிய வீண் செலவுகள்)": [
        "SWIGGY", "ZOMATO", "CINEMA", "HOTEL", "RESTAURANT", 
        "ONLINE SHOPPING", "AMAZON", "FLIPKART", "SNACKS"
    ]
}

def categorize_transaction(description):
    desc_upper = str(description).upper()
    for cat, keywords in CATEGORIES.items():
        if any(keyword in desc_upper for keyword in keywords):
            return cat
    return "மஞ்சள் (Yellow - அத்தியாவசிய வீட்டுச் செலவுகள்)" # இயல்பான இதர வீட்டுச் செலவு

# 2. மாதிரி தரவு (Sample Data) அல்லது நேரடி உள்ளீடு
st.subheader("1. பரிவர்த்தனைப் பதிவு (SMS Text / Statement Data)")
sample_sms_text = st.text_area(
    "வங்கி SMS அல்லது பரிவர்த்தனைகளை இங்கே பேஸ்ட் செய்யவும்:",
    height=120,
    placeholder="Axis Bank: Debited Rs.12500 for Personal Loan EMI on 01-Oct\nCanara Bank: Debited Rs.6500 for Grocery Supermarket on 02-Oct\nKotak Bank: Credited Rs.65000 towards Salary on 01-Oct\nIOB: Debited Rs.1100 at Swiggy on 03-Oct"
)

# மாதிரி அட்டவணை
data = [
    {"Bank": "Axis Bank", "Date": "2026-10-01", "Description": "Personal Loan EMI (Investment)", "Type": "Debit", "Amount": 12500},
    {"Bank": "Kotak Bank", "Date": "2026-10-01", "Description": "Company Monthly Salary", "Type": "Credit", "Amount": 65000},
    {"Bank": "Canara Bank", "Date": "2026-10-02", "Description": "ICICI Prudential Insurance", "Type": "Debit", "Amount": 4000},
    {"Bank": "Canara Bank", "Date": "2026-10-02", "Description": "House Rent Payment", "Type": "Debit", "Amount": 12000},
    {"Bank": "IOB", "Date": "2026-10-02", "Description": "Grocery & Supermarket", "Type": "Debit", "Amount": 6500},
    {"Bank": "IOB", "Date": "2026-10-03", "Description": "LPG Gas Cylinder Refill", "Type": "Debit", "Amount": 950},
    {"Bank": "Axis Bank", "Date": "2026-10-03", "Description": "ITC Share Dividend", "Type": "Credit", "Amount": 2500},
    {"Bank": "Axis Bank", "Date": "2026-10-03", "Description": "Online Shopping Impulse", "Type": "Debit", "Amount": 2200},
    {"Bank": "Kotak Bank", "Date": "2026-10-03", "Description": "Restaurant / Snacks", "Type": "Debit", "Amount": 1100},
]

df = pd.DataFrame(data)

# தானாக வகைப்படுத்துதல் (Auto Tagging)
df["Category"] = df.apply(lambda r: "வருமானம் (Income)" if r["Type"] == "Credit" else categorize_transaction(r["Description"]), axis=1)

# 3. நிதிச் சுருக்கம் & சதவீதங்கள் (Calculations)
total_income = df[df["Type"] == "Credit"]["Amount"].sum()
total_expense = df[df["Type"] == "Debit"]["Amount"].sum()
net_savings = total_income - total_expense

st.markdown("---")
st.subheader("2. மாதாந்திர நிதி நிலை (Monthly Summary)")
col1, col2, col3 = st.columns(3)
col1.metric("மொத்த வருமானம்", f"₹{total_income:,.2f}")
col2.metric("மொத்த செலவுகள்", f"₹{total_expense:,.2f}")
col3.metric("கையில் மீதம் (Savings)", f"₹{net_savings:,.2f}")

# 4. சதவீதப் பகுப்பாய்வு அட்டவணை (Percentage Breakdown)
st.markdown("---")
st.subheader("3. செலவுப் பிரிவு & சதவீதப் பகுப்பாய்வு")

exp_df = df[df["Type"] == "Debit"]
summary = exp_df.groupby("Category")["Amount"].sum().reset_index()
summary["வருமானத்தில் %"] = (summary["Amount"] / total_income * 100).round(1).astype(str) + " %"

st.dataframe(summary, use_container_width=True)

# 5. முழுப் பரிவர்த்தனைப் பட்டியல்
st.markdown("---")
st.subheader("4. அனைத்து வங்கிப் பரிவர்த்தனைகள்")
st.dataframe(df, use_container_width=True)
