
import streamlit as st
import pandas as pd
import math
from datetime import datetime
from dateutil.relativedelta import relativedelta

st.set_page_config(page_title="April Mortgage Calculator", layout="wide")
st.title("📊 Mortgage Calculator – April Mortgages & Standard")

st.sidebar.header("Input Mortgage Details")

loan_amount = st.sidebar.number_input("Loan Amount (£)", min_value=10000, step=1000)
property_value = st.sidebar.number_input("Property Value (£)", min_value=10000, step=1000)
term_years = st.sidebar.number_input("Mortgage Term – Years", min_value=0, max_value=40, step=1)
term_months = st.sidebar.number_input("Mortgage Term – Additional Months", min_value=0, max_value=11, step=1)
total_term_months = term_years * 12 + term_months

lender_type = st.sidebar.selectbox("Lender Calculation Type", ["April", "Standard"])

if lender_type == "April":
    transaction_type = st.sidebar.selectbox("Transaction Type", ["Purchase", "Remortgage"])
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

april_rates_purchase = {
    5: {0.60: 0.0510, 0.75: 0.0515, 0.80: 0.0520, 0.85: 0.0530, 0.90: 0.0540, 0.95: 0.0565},
    10: {0.60: 0.0535, 0.75: 0.0540, 0.80: 0.0545, 0.85: 0.0555, 0.90: 0.0565, 0.95: 0.0590},
    15: {0.60: 0.0550, 0.75: 0.0555, 0.80: 0.0560, 0.85: 0.0570, 0.90: 0.0580, 0.95: 0.0604}
}

april_rates_remortgage = {
    5: {0.60: 0.0510, 0.75: 0.0515, 0.80: 0.0520, 0.85: 0.0530},
    10: {0.60: 0.0535, 0.75: 0.0540, 0.80: 0.0545, 0.85: 0.0555},
    15: {0.60: 0.0550, 0.75: 0.0555, 0.80: 0.0560, 0.85: 0.0570}
}

standard_fixed_rate = 0.059

def calculate_payment(balance, rate, months):
    monthly_rate = rate / 12
    return balance * (monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)

if calculate and loan_amount and property_value and total_term_months:
    balance = loan_amount
    schedule = []

    if lender_type == "Standard":
        rate = standard_fixed_rate
        payment = calculate_payment(balance, rate, total_term_months)
        for month in range(1, total_term_months + 1):
            interest = balance * (rate / 12)
            capital = payment - interest
            balance -= capital
            schedule.append({
                "Month": month,
                "Rate": round(rate * 100, 2),
                "Payment": round(payment, 2),
                "Interest": round(interest, 2),
                "Capital": round(capital, 2),
                "LTV (%)": round((balance / property_value) * 100, 4),
                "Balance": round(balance, 2)
            })
    else:
        selected_rates = april_rates_purchase[fixed_term_years] if transaction_type == "Purchase" else april_rates_remortgage[fixed_term_years]
        rate = selected_rates[0.95]
        monthly_payment_initial = calculate_payment(loan_amount, rate, total_term_months)

        capital_schedule = []
        temp_balance = loan_amount
        for _ in range(total_term_months):
            interest = temp_balance * (rate / 12)
            capital = monthly_payment_initial - interest
            capital_schedule.append(capital)
            temp_balance -= capital

        for month in range(1, total_term_months + 1):
            ltv = balance / property_value
            rounded_ltv = round(ltv * 100)
            for band, band_rate in selected_rates.items():
                if rounded_ltv <= int(band * 100):
                    rate = band_rate
                    break
            capital = capital_schedule[month - 1]
            interest = balance * (rate / 12)
            payment = capital + interest
            balance -= capital
            schedule.append({
                "Month": month,
                "Rate": round(rate * 100, 2),
                "Payment": round(payment, 2),
                "Interest": round(interest, 2),
                "Capital": round(capital, 2),
                "LTV (%)": round((balance / property_value) * 100, 4),
                "Balance": round(balance, 2)
            })

    df_schedule = pd.DataFrame(schedule)
    st.subheader("📅 Full Payment Schedule")
    st.dataframe(df_schedule)

    csv = df_schedule.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Full Schedule as CSV", csv, "mortgage_schedule.csv", "text/csv")
