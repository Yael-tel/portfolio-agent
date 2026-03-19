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

st.subheader("Macro & Market Insights")

macro_insights = []

if uploaded_file is not None:

    # Cash
    cash_exposure = df[df["sector"].astype(str).str.contains("Cash", case=False, na=False)]["portfolio_percent"].sum()
    if cash_exposure > 40:
        macro_insights.append("High cash exposure – benefits from high interest rates, but limits growth.")

    # Technology
    tech_exposure = df[df["sector"].astype(str).str.contains("Tech", case=False, na=False)]["portfolio_percent"].sum()
    if tech_exposure > 20:
        macro_insights.append("High exposure to tech – sensitive to interest rate changes.")

    # US exposure
    us_exposure = df[df["country"].astype(str).str.upper().isin(["US"])]["portfolio_percent"].sum()
    if us_exposure > 30:
        macro_insights.append("Significant US exposure – affected by Fed policy and USD movement.")

    # Gold
    gold_exposure = df[df["sector"].astype(str).str.contains("Gold", case=False, na=False)]["portfolio_percent"].sum()
    if gold_exposure > 0:
        macro_insights.append("Gold exposure – acts as hedge during geopolitical stress.")

    if macro_insights:
        for m in macro_insights:
            st.info(m)
    else:
        st.success("No major macro signals detected.")

def safe_number(x, default=0):
    try:
        if pd.isna(x):
            return default
        return float(x)
    except Exception:
        return default


st.subheader("Daily P&L and Recommendations")

if uploaded_file is not None:
    work_df = df.copy()

    # נוודא שהעמודות קיימות
    if "portfolio_percent" not in work_df.columns:
        work_df["portfolio_percent"] = 0

    if "purchase_price" not in work_df.columns:
        work_df["purchase_price"] = 0

    # חישוב יומי משוער לפי אחוז שינוי
    # כרגע אין לנו מחיר שוק חי לכל נייר, אז נשתמש בקירוב:
    # אם בעתיד נוסיף מחיר חי - נחליף את החלק הזה
    if "daily_change_percent" not in work_df.columns:
        work_df["daily_change_percent"] = 0

    if "current_value" not in work_df.columns:
        # אם אין שווי נוכחי, נחשב הערכה גסה מתוך אחוזי תיק
        total_portfolio_value_est = 100000
        work_df["current_value"] = work_df["portfolio_percent"].apply(lambda x: safe_number(x) / 100 * total_portfolio_value_est)

    work_df["daily_pnl"] = work_df["current_value"] * (work_df["daily_change_percent"].apply(safe_number) / 100)

    # רווח/הפסד כולל משוער אם יש quantity + purchase_price
    if "quantity" in work_df.columns:
        work_df["estimated_cost"] = work_df["quantity"].apply(safe_number) * work_df["purchase_price"].apply(safe_number)
        work_df["total_pnl"] = work_df["current_value"] - work_df["estimated_cost"]
    else:
        work_df["total_pnl"] = 0

    # לוגיקת המלצות
    def suggest_action(row, sector_exposure_map):
        weight = safe_number(row.get("portfolio_percent", 0))
        sector = str(row.get("sector", ""))
        asset_name = str(row.get("asset_name", ""))
        daily_change = safe_number(row.get("daily_change_percent", 0))

        reasons = []
        action = "Hold"
        confidence = "Medium"

        if weight > 20:
            action = "Reduce"
            confidence = "High"
            reasons.append("Position exceeds your 20% single-asset limit")

        sector_weight = sector_exposure_map.get(sector, 0)
        if sector_weight > 40:
            if action == "Hold":
                action = "Reduce"
            confidence = "High"
            reasons.append("Sector exceeds your 40% sector limit")

        if "Cash" in sector or "Money Market" in sector:
            if weight > 20:
                action = "Review"
                confidence = "High"
                reasons.append("Large cash allocation may reduce long-term growth")

        if daily_change <= -3 and action == "Hold":
            action = "Watch"
            confidence = "Medium"
            reasons.append("Large negative daily move")

        if daily_change >= 2 and weight < 5 and action == "Hold":
            action = "Add"
            confidence = "Low"
            reasons.append("Positive move in a small position")

        if not reasons:
            reasons.append("No major rule breach detected")

        return pd.Series([action, confidence, "; ".join(reasons)])

    sector_exposure = work_df.groupby("sector", dropna=False)["portfolio_percent"].sum().to_dict()
    work_df[["suggested_action", "confidence", "reason"]] = work_df.apply(
        lambda row: suggest_action(row, sector_exposure), axis=1
    )

    # סיכום יומי
    total_daily_pnl = work_df["daily_pnl"].sum()
    total_total_pnl = work_df["total_pnl"].sum()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Estimated Daily P&L", f"{total_daily_pnl:,.0f}")
    with col2:
        st.metric("Estimated Total P&L", f"{total_total_pnl:,.0f}")

    # תורמים עיקריים
    st.subheader("Top Daily Movers")
    movers = work_df[["asset_name", "symbol", "daily_change_percent", "daily_pnl"]].copy()
    movers = movers.sort_values("daily_pnl", ascending=False)
    st.dataframe(movers.head(5), use_container_width=True)

    st.subheader("Daily Recommendations")
    recommendations = work_df[["asset_name", "symbol", "portfolio_percent", "suggested_action", "confidence", "reason"]].copy()
    recommendations = recommendations.sort_values(["suggested_action", "portfolio_percent"], ascending=[True, False])
    st.dataframe(recommendations, use_container_width=True)

    # תובנות יומיות
    st.subheader("Daily Insights")

    insights = []

    max_weight = work_df["portfolio_percent"].apply(safe_number).max()
    if max_weight > 20:
        largest = work_df.loc[work_df["portfolio_percent"].apply(safe_number).idxmax()]
        insights.append(f"Largest position is {largest['asset_name']} at {safe_number(largest['portfolio_percent']):.2f}% — above your limit.")

    cash_exposure = work_df[work_df["sector"].astype(str).str.contains("Cash|Money Market", case=False, na=False)]["portfolio_percent"].apply(safe_number).sum()
    if cash_exposure > 40:
        insights.append(f"Cash exposure is {cash_exposure:.2f}% — portfolio is very defensive.")

    tech_exposure = work_df[work_df["sector"].astype(str).str.contains("Tech", case=False, na=False)]["portfolio_percent"].apply(safe_number).sum()
    if tech_exposure > 20:
        insights.append(f"Technology exposure is {tech_exposure:.2f}% — portfolio is sensitive to growth and interest-rate moves.")

    if total_daily_pnl < 0:
        insights.append("Portfolio is estimated to be down on the day.")
    elif total_daily_pnl > 0:
        insights.append("Portfolio is estimated to be up on the day.")

    if insights:
        for item in insights:
            st.info(item)
    else:
        st.success("No unusual daily insights detected.")
