import streamlit as st
import pandas as pd

st.set_page_config(page_title="Portfolio Dashboard", layout="wide")

st.title("📊 Portfolio Dashboard")

uploaded_file = st.file_uploader("Upload your portfolio CSV", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    st.subheader("Portfolio table")
    st.dataframe(df, use_container_width=True)

    if "portfolio_percent" in df.columns:
        st.subheader("Top holdings")
        top_holdings = df.sort_values("portfolio_percent", ascending=False).head(10)
        st.dataframe(top_holdings, use_container_width=True)

    if "sector" in df.columns and "portfolio_percent" in df.columns:
        st.subheader("Exposure by sector")
        sector_df = df.groupby("sector", dropna=False)["portfolio_percent"].sum().sort_values(ascending=False)
        st.bar_chart(sector_df)

    if "asset_type" in df.columns and "portfolio_percent" in df.columns:
        st.subheader("Exposure by asset type")
        asset_df = df.groupby("asset_type", dropna=False)["portfolio_percent"].sum().sort_values(ascending=False)
        st.bar_chart(asset_df)

    st.subheader("Alerts")
    alerts = []

    if "portfolio_percent" in df.columns:
        max_position = df.loc[df["portfolio_percent"].idxmax()]
        if max_position["portfolio_percent"] > 20:
            alerts.append(
                f"Asset concentration alert: {max_position['asset_name']} is {max_position['portfolio_percent']:.2f}% of the portfolio."
            )

    if "sector" in df.columns and "portfolio_percent" in df.columns:
        sector_exposure = df.groupby("sector")["portfolio_percent"].sum()
        high_sectors = sector_exposure[sector_exposure > 40]
        for sector_name, exposure in high_sectors.items():
            alerts.append(f"Sector concentration alert: {sector_name} is {exposure:.2f}% of the portfolio.")

    if "country" in df.columns and "portfolio_percent" in df.columns:
        usd_like = df[df["country"].astype(str).str.upper().isin(["US", "USA", "UNITED STATES"])]["portfolio_percent"].sum()
        if usd_like > 80:
            alerts.append(f"USD exposure alert: US exposure is {usd_like:.2f}% of the portfolio.")

    if alerts:
        for alert in alerts:
            st.warning(alert)
    else:
        st.success("No rule breaches found.")
else:
    st.info("Upload your portfolio CSV to begin.")

st.subheader("AI Insights")

if uploaded_file is not None:
    insights = []

    # Cash detection
    cash_exposure = df[df["sector"].str.contains("Cash", case=False, na=False)]["portfolio_percent"].sum()
    if cash_exposure > 40:
        insights.append(f"High cash exposure: {cash_exposure:.2f}%. Portfolio may be too conservative.")

    # Tech exposure
    tech_exposure = df[df["sector"].str.contains("Tech", case=False, na=False)]["portfolio_percent"].sum()
    if tech_exposure > 25:
        insights.append(f"High technology exposure: {tech_exposure:.2f}%.")

    # Diversification
    if len(df) < 5:
        insights.append("Portfolio may be under-diversified.")

    # Output
    if insights:
        for i in insights:
            st.info(i)
    else:
        st.success("Portfolio looks balanced.")
