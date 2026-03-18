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

st.subheader("Suggested Actions")

actions = []

if uploaded_file is not None:
    if "portfolio_percent" in df.columns:
        max_position = df.loc[df["portfolio_percent"].idxmax()]
        if max_position["portfolio_percent"] > 20:
            actions.append(
                f"Consider reducing {max_position['asset_name']} because it exceeds your 20% single-asset limit."
            )

    if "sector" in df.columns and "portfolio_percent" in df.columns:
        sector_exposure = df.groupby("sector")["portfolio_percent"].sum()
        high_sectors = sector_exposure[sector_exposure > 40]
        for sector_name, exposure in high_sectors.items():
            actions.append(
                f"Consider reducing exposure to {sector_name}, which is {exposure:.2f}% of the portfolio."
            )

    if "country" in df.columns and "portfolio_percent" in df.columns:
        usd_like = df[df["country"].astype(str).str.upper().isin(["US", "USA", "UNITED STATES"])]["portfolio_percent"].sum()
        if usd_like > 80:
            actions.append(
                f"Consider lowering US/USD exposure. Current exposure is {usd_like:.2f}%."
            )

    cash_exposure = df[df["sector"].astype(str).str.contains("Cash", case=False, na=False)]["portfolio_percent"].sum()
    if cash_exposure > 40:
        actions.append(
            f"Consider whether your cash allocation of {cash_exposure:.2f}% is intentional or temporary."
        )

    if actions:
        for action in actions:
            st.info(action)
    else:
        st.success("No portfolio changes suggested right now.")

st.subheader("Portfolio Score")

score = 100

if uploaded_file is not None:
    
    # Penalty: concentration
    if "portfolio_percent" in df.columns:
        max_position = df["portfolio_percent"].max()
        if max_position > 20:
            score -= 20

    # Penalty: sector concentration
    if "sector" in df.columns and "portfolio_percent" in df.columns:
        sector_exposure = df.groupby("sector")["portfolio_percent"].sum()
        if any(sector_exposure > 40):
            score -= 15

    # Penalty: USD exposure
    if "country" in df.columns and "portfolio_percent" in df.columns:
        usd_like = df[df["country"].astype(str).str.upper().isin(["US", "USA", "UNITED STATES"])]["portfolio_percent"].sum()
        if usd_like > 80:
            score -= 10

    # Penalty: too much cash
    cash_exposure = df[df["sector"].astype(str).str.contains("Cash", case=False, na=False)]["portfolio_percent"].sum()
    if cash_exposure > 40:
        score -= 15

    # Penalty: low diversification
    if len(df) < 5:
        score -= 10

    # Boundaries
    score = max(0, score)

    # Display
    if score >= 80:
        st.success(f"Portfolio Score: {score}/100 (Strong)")
    elif score >= 60:
        st.warning(f"Portfolio Score: {score}/100 (Moderate)")
    else:
        st.error(f"Portfolio Score: {score}/100 (Needs attention)")

import requests

def get_fmp_analyst_recommendation(symbol):
    api_key = st.secrets["FMP_API_KEY"]
    url = f"https://financialmodelingprep.com/api/v3/analyst-stock-recommendations/{symbol}?apikey={api_key}"

    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return {"error": f"HTTP {r.status_code}", "raw": r.text[:300]}

        data = r.json()

        if isinstance(data, list) and len(data) > 0:
            return data[0]

        return {"error": "No data returned", "raw": data}

    except Exception as e:
        return {"error": str(e), "raw": None}

def classify_recommendation(analyst_row):
    if not analyst_row:
        return "No data"

    if isinstance(analyst_row, dict) and "error" in analyst_row:
        return "No data"

    buy = analyst_row.get("buy", 0) or 0
    hold = analyst_row.get("hold", 0) or 0
    sell = analyst_row.get("sell", 0) or 0
    total = buy + hold + sell

    if total == 0:
        return "No data"

    score = (buy - sell) / total

    if score > 0.3:
        return "Positive"
    elif score < -0.2:
        return "Negative"
    return "Mixed"


st.subheader("Market-Based Recommendations")

if uploaded_file is not None:
    found_any_market_data = False
    market_messages = []

    for _, row in df.iterrows():
        symbol = str(row.get("symbol", "")).strip()
        if not symbol:
            continue

        asset_name = row.get("asset_name", symbol)
        weight = row.get("portfolio_percent", 0)

        analyst = get_fmp_analyst_recommendation(symbol)
        sentiment = classify_recommendation(analyst)

        if sentiment != "No data":
            found_any_market_data = True

        if sentiment == "Negative":
            market_messages.append(("warning", f"{asset_name} ({symbol}) -> Negative analyst sentiment"))

        elif sentiment == "Positive" and weight < 5:
            market_messages.append(("info", f"{asset_name} ({symbol}) -> Positive sentiment, small position"))

        elif sentiment == "Mixed":
            market_messages.append(("text", f"{asset_name} ({symbol}) -> Mixed analyst view"))

    if market_messages:
        for level, message in market_messages:
            if level == "warning":
                st.warning(message)
            elif level == "info":
                st.info(message)
            else:
                st.write(message)
    else:
        st.info("No analyst data was returned for the current symbols. This usually means the API has no analyst coverage for these securities, or the symbols are ETFs/funds/Israeli instruments rather than covered stocks.")
