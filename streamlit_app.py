import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

from dcf_model import DCF

st.set_page_config(
    page_title="DCF Valuation Model",
    page_icon="📈",
    layout="wide",
)

st.title(" DCF Valuation Model")
st.caption("Discounted Cash Flow analysis — estimate intrinsic value per share")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Inputs")

    st.subheader("Core FCF Assumptions")
    latest_fcf = st.number_input("Latest FCF ($M)", value=1000.0, step=50.0)
    growth_rate = st.slider("FCF Growth Rate (%)", 0.0, 40.0, 8.0, 0.5) / 100
    terminal_growth_rate = st.slider("Terminal Growth Rate (%)", 0.0, 10.0, 2.5, 0.1) / 100
    projection_years = st.slider("Projection Years", 3, 15, 5)

    st.subheader("Discount Rate")
    rate_mode = st.radio("Mode", ["Direct", "WACC (CAPM)"], horizontal=True)

    discount_rate = None
    wacc_inputs = {}

    if rate_mode == "Direct":
        discount_rate = st.slider("Discount Rate (%)", 1.0, 30.0, 10.0, 0.5) / 100
    else:
        st.markdown("**CAPM**")
        risk_free_rate = st.number_input("Risk-Free Rate (%)", value=4.5, step=0.1) / 100
        beta = st.number_input("Beta", value=1.2, step=0.05)
        erp = st.number_input("Equity Risk Premium (%)", value=5.5, step=0.1) / 100
        st.markdown("**Capital Structure**")
        cost_of_debt = st.number_input("Pre-Tax Cost of Debt (%)", value=5.0, step=0.1) / 100
        tax_rate = st.number_input("Tax Rate (%)", value=21.0, step=0.5) / 100
        market_cap = st.number_input("Market Cap ($M)", value=5000.0, step=100.0)
        total_debt = st.number_input("Total Debt ($M)", value=1000.0, step=100.0)
        wacc_inputs = dict(
            risk_free_rate=risk_free_rate,
            beta=beta,
            equity_risk_premium=erp,
            cost_of_debt=cost_of_debt,
            tax_rate=tax_rate,
            market_cap=market_cap,
            total_debt=total_debt,
        )

    st.subheader("Equity Bridge")
    cash = st.number_input("Cash & Equivalents ($M)", value=500.0, step=50.0)
    if rate_mode == "Direct":
        total_debt = st.number_input("Total Debt ($M)", value=1000.0, step=100.0)
    else:
        total_debt = wacc_inputs["total_debt"]
        st.caption(f"Total Debt: ${total_debt:,.0f}M (from WACC inputs above)")
    shares = st.number_input("Shares Outstanding (M)", value=250.0, step=10.0)

# ── Build model ────────────────────────────────────────────────────────────────
try:
    model_kwargs = dict(
        latest_fcf=latest_fcf,
        growth_rate=growth_rate,
        terminal_growth_rate=terminal_growth_rate,
        discount_rate=discount_rate,
        projection_years=projection_years,
        cash_and_equivalents=cash,
        shares_outstanding=shares,
        **wacc_inputs,
    )
    if rate_mode == "Direct":
        model_kwargs["total_debt"] = total_debt
    model = DCF(**model_kwargs)

    r = model.get_discount_rate()
    fcfs = model.free_cash_flows()
    tv = model.terminal_value()
    ev = model.enterprise_value()
    eq = model.equity_value()
    pps = model.price_per_share()

    # ── KPI cards ──────────────────────────────────────────────────────────────
    if rate_mode == "WACC (CAPM)":
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Cost of Equity", f"{model.cost_of_equity():.2%}")
        col2.metric("WACC", f"{r:.2%}")
        col3.metric("Enterprise Value", f"${ev:,.0f}M")
        col4.metric("Equity Value", f"${eq:,.0f}M")
        col5.metric("Intrinsic Price / Share", f"${pps:,.2f}")
    else:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Discount Rate", f"{r:.2%}")
        col2.metric("Enterprise Value", f"${ev:,.0f}M")
        col3.metric("Equity Value", f"${eq:,.0f}M")
        col4.metric("Intrinsic Price / Share", f"${pps:,.2f}")

    st.divider()

    left, right = st.columns(2)

    # ── Projected FCFs bar chart ───────────────────────────────────────────────
    with left:
        st.subheader("Projected Free Cash Flows")
        years = [f"Year {i}" for i in range(1, projection_years + 1)]
        fig_fcf = go.Figure(
            go.Bar(x=years, y=fcfs, marker_color="#4f8ef7", text=[f"${v:,.0f}" for v in fcfs], textposition="outside")
        )
        fig_fcf.update_layout(yaxis_title="FCF ($M)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=20))
        st.plotly_chart(fig_fcf, use_container_width=True)

    # ── EV waterfall ──────────────────────────────────────────────────────────
    with right:
        st.subheader("Enterprise Value Bridge")
        pv_fcfs = sum(fcfs[t] / (1 + r) ** (t + 1) for t in range(projection_years))
        pv_tv = tv / (1 + r) ** projection_years
        net_debt = total_debt - cash

        fig_wf = go.Figure(
            go.Waterfall(
                orientation="v",
                measure=["relative", "relative", "total", "relative", "total"],
                x=["PV FCFs", "PV Terminal Value", "Enterprise Value", "Net Debt", "Equity Value"],
                y=[pv_fcfs, pv_tv, 0, -net_debt, 0],
                connector={"line": {"color": "rgb(63,63,63)"}},
                increasing={"marker": {"color": "#22c55e"}},
                decreasing={"marker": {"color": "#ef4444"}},
                totals={"marker": {"color": "#4f8ef7"}},
            )
        )
        fig_wf.update_layout(plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=20), yaxis_title="Value ($M)")
        st.plotly_chart(fig_wf, use_container_width=True)

    st.divider()

    # ── Sensitivity analysis ──────────────────────────────────────────────────
    st.subheader(" Sensitivity Analysis — Price per Share")
    sa_col1, sa_col2 = st.columns(2)
    with sa_col1:
        g_spread = st.slider("Growth Rate spread (±%)", 1.0, 5.0, 2.0, 0.5) / 100
        g_steps = st.slider("Growth Rate steps", 3, 9, 5, 2)
    with sa_col2:
        r_spread = st.slider("Discount Rate spread (±%)", 1.0, 5.0, 2.0, 0.5) / 100
        r_steps = st.slider("Discount Rate steps", 3, 9, 5, 2)

    growth_rates = np.linspace(growth_rate - g_spread, growth_rate + g_spread, g_steps)
    discount_rates = np.linspace(r - r_spread, r + r_spread, r_steps)

    grid = model.sensitivity_analysis(growth_rates=growth_rates, discount_rates=discount_rates)

    df_heat = pd.DataFrame(
        grid,
        index=[f"{v:.1%}" for v in discount_rates],
        columns=[f"{v:.1%}" for v in growth_rates],
    )

    fig_heat = px.imshow(
        df_heat,
        text_auto=".2f",
        color_continuous_scale="RdYlGn",
        labels=dict(x="Growth Rate", y="Discount Rate", color="Price ($)"),
        aspect="auto",
    )
    fig_heat.update_layout(margin=dict(t=20))
    st.plotly_chart(fig_heat, use_container_width=True)

    # ── Raw data table ────────────────────────────────────────────────────────
    with st.expander(" Projected FCF Table"):
        t_arr = np.arange(1, projection_years + 1)
        pv_arr = fcfs / (1 + r) ** t_arr
        df_fcf = pd.DataFrame(
            {"Year": t_arr, "Projected FCF ($M)": fcfs, "PV of FCF ($M)": pv_arr}
        ).set_index("Year")
        st.dataframe(df_fcf.style.format("${:,.2f}"), use_container_width=True)

except ValueError as e:
    st.error(f"⚠️ {e}")
except ZeroDivisionError:
    st.error("⚠️ Division by zero — check your capital structure inputs.")
