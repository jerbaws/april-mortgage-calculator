
import streamlit as st
import pandas as pd
import math
from datetime import datetime, timedelta

st.set_page_config(page_title="Mortgage Model (April & Standard)", layout="wide")

st.title("📊 Mortgage Calculator – April Mortgages & Standard")

# ---- Sidebar Input Section ----
st.sidebar.header("Input Mortgage Details")

loan_amount = st.sidebar.number_input("Loan Amount (£)", min_value=10000, step=1000)
property_value = st.sidebar.number_input("Property Value (£)", min_value=10000, step=1000)

term_years = st.sidebar.number_input("Mortgage Term – Years", min_value=0, max_value=40, step=1)
term_months = st.sidebar.number_input("Mortgage Term – Additional Months", min_value=0, max_value=11, step=1)
total_term_months = term_years * 12 + term_months

lender_type = st.sidebar.selectbox("Lender Calculation Type", ["April", "Standard"])

if lender_type == "April":
    fixed_term_years = st.sidebar.selectbox("Fixed Product Term (Years)", [5, 10, 15])
    fixed_term_months = fixed_term_years * 12
else:
    fixed_term_custom = st.sidebar.number_input("Fixed Product Term", min_value=1, max_value=360, step=1)
    fixed_term_unit = st.sidebar.selectbox("Term Unit", ["Years", "Months"])
    fixed_term_months = fixed_term_custom * 12 if fixed_term_unit == "Years" else fixed_term_custom

repayment_type = st.sidebar.selectbox("Repayment Method", ["Repayment", "Interest-Only", "Part and Part"])

add_fees = st.sidebar.checkbox("Add Fees to Loan")
fees = 995 if lender_type == "April" and add_fees else 0
if add_fees and lender_type != "April":
    fees = st.sidebar.number_input("Fee Amount to Add (£)", min_value=0, step=50)
loan_amount += fees

calculate = st.sidebar.button("🔍 Calculate")

# ---- Rate Tables ----
april_rates_10yr = {
    0.60: 0.0535,
    0.75: 0.0540,
    0.80: 0.0545,
    0.85: 0.0555,
    0.90: 0.0565,
    0.95: 0.0590
}

standard_fixed_rate = 0.059  # For demo; user input could be added for real logic

# ---- Core Calculation ----
if calculate and loan_amount and property_value and total_term_months:
    schedule = []
    balance = loan_amount
    current_rate = standard_fixed_rate if lender_type == "Standard" else april_rates_10yr[0.95]
    start_date = datetime.today().replace(day=1)

    def get_april_rate(ltv):
        for band in sorted(april_rates_10yr):
            if ltv <= band:
                return april_rates_10yr[band]
        return april_rates_10yr[0.95]

    blended_numerator = 0
    blended_months = 0
    previous_rate = None

    for month in range(1, fixed_term_months + 1):
        ltv = balance / property_value
        if lender_type == "April":
            rate = get_april_rate(ltv)
        else:
            rate = current_rate

        if rate != previous_rate or month == 1:
            remaining_term = fixed_term_months - month + 1
            monthly_rate = rate / 12
            if repayment_type == "Repayment":
                payment = balance * (monthly_rate * (1 + monthly_rate) ** remaining_term) / ((1 + monthly_rate) ** remaining_term - 1)
            elif repayment_type == "Interest-Only":
                payment = balance * monthly_rate
            else:
                payment = balance * monthly_rate * 0.8 + (balance * 0.2 * (monthly_rate * (1 + monthly_rate) ** remaining_term) / ((1 + monthly_rate) ** remaining_term - 1))
            previous_rate = rate

        interest = balance * (rate / 12)
        capital = payment - interest if repayment_type != "Interest-Only" else 0
        balance -= capital

        blended_numerator += rate * 100
        blended_months += 1

        schedule.append({
            "Month": month,
            "Date": (start_date + timedelta(days=30 * (month - 1))).strftime("%b/%Y"),
            "Rate (%)": round(rate * 100, 2),
            "Payment": round(payment, 2),
            "Interest": round(interest, 2),
            "Capital": round(capital, 2),
            "LTV (%)": round(ltv * 100, 2),
            "Remaining Balance": round(balance, 2)
        })

    df_schedule = pd.DataFrame(schedule)
    df_milestones = df_schedule[df_schedule["Rate (%)"].diff() != 0].copy()
    blended_rate = round(blended_numerator / blended_months, 2)

    st.subheader("📉 Rate Drop Milestones (if applicable)")
    st.dataframe(df_milestones[["Month", "Date", "Rate (%)", "Payment", "LTV (%)", "Remaining Balance"]])

    st.subheader(f"📅 Full Payment Schedule – Blended Rate: {blended_rate}%")
    st.dataframe(df_schedule)

    csv = df_schedule.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Full Schedule as CSV", csv, "mortgage_schedule.csv", "text/csv")
