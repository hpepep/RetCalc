import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# ==========================================
# 1. PAGE SETUP & THEME INJECTION
# ==========================================
st.set_page_config(
    page_title="Retirement Ecosystem India",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS injector to precisely capture the high-contrast dark-mode theme
st.markdown("""
    <style>
        /* Main background overrides */
        .stApp {
            background-color: #0a0e17;
            color: #f3f4f6;
        }
        
        /* Sidebar styling */
        section[data-testid="stSidebar"] {
            background-color: #141b2d !important;
            border-right: 1px solid #2e3d60;
        }
        
        /* Container Cards styling */
        div[data-testid="stVerticalBlock"] > div {
            background-color: transparent;
        }
        
        .panel-card {
            background-color: #141b2d;
            border: 1px solid #2e3d60;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        /* Typography overrides */
        h1 {
            background: linear-gradient(90deg, #3b82f6, #10b981);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 700 !important;
        }
        
        h3 {
            color: #3b82f6 !important;
            font-size: 16px !important;
            font-weight: 600 !important;
            margin-bottom: 12px !important;
        }
        
        /* KPI Banner styling */
        .kpi-card {
            background-color: #141b2d;
            border: 1px solid #2e3d60;
            border-radius: 10px;
            padding: 16px;
            border-left: 4px solid #3b82f6;
            margin-bottom: 15px;
        }
        .kpi-card.success { border-left-color: #10b981; }
        .kpi-card.warning { border-left-color: #f59e0b; }
        .kpi-card.danger { border-left-color: #ef4444; }
        
        .kpi-label {
            font-size: 12px;
            color: #9ca3af;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .kpi-val {
            font-size: 22px;
            font-weight: 700;
            color: #f3f4f6;
            margin-top: 4px;
        }
    </style>
""", unsafe_allow_html=True)

# Indian Rupee Formatting Function (Lakhs/Crores layout separator)
def format_to_indian_rupees(val):
    if pd.isna(val) or val is None:
        return "₹0"
    sign = "-" if val < 0 else ""
    value_str = str(abs(round(val)))
    if len(value_str) > 3:
        last_three = value_str[-3:]
        remaining = value_str[:-3]
        chunks = []
        while len(remaining) > 0:
            if len(remaining) > 2:
                chunks.insert(0, remaining[-2:])
                remaining = remaining[:-2]
            else:
                chunks.insert(0, remaining)
                remaining = ""
        return f"₹{sign}{','.join(chunks)},{last_three}"
    return f"₹{sign}{value_str}"

# ==========================================
# 2. APP SIDEBAR INPUT CONTROLS
# ==========================================
st.sidebar.markdown("<h2 style='color:#3b82f6; font-size:20px; font-weight:700;'>Parameters Workspace</h2>", unsafe_allow_html=True)

st.sidebar.markdown("### Demographics & Base Expenses")
current_age = st.sidebar.number_input("Current Age", min_value=1, max_value=100, value=43)
retirement_age = st.sidebar.number_input("Retirement Age", min_value=1, max_value=100, value=60)
current_year = st.sidebar.number_input("Current Calendar Year", min_value=2000, max_value=2100, value=2026)
max_age = st.sidebar.number_input("Life Expectancy (Max Age)", min_value=1, max_value=110, value=90)
base_monthly_expense = st.sidebar.number_input("Current Monthly Expenses (₹)", min_value=0, step=500, value=75000)

st.sidebar.markdown("### Macro Market Return Profiles (% P.A.)")
inflation_rate = st.sidebar.number_input("Annual Inflation Rate (%)", value=6.0, step=0.1) / 100.0
rate_equity = st.sidebar.number_input("Equity Bucket Expected Return (%)", value=10.0, step=0.1) / 100.0
rate_debt = st.sidebar.number_input("Debt/Bond Expected Return (%)", value=6.0, step=0.1) / 100.0
rate_liquid = st.sidebar.number_input("Liquid Cash Expected Return (%)", value=6.0, step=0.1) / 100.0

# Dynamic Asset Table Base Editor
st.sidebar.markdown("### Existing Asset Base")
assets_data = [
    {"name": "Equity Mutual Funds", "val": 7100000, "rate": 10.0, "category": "equity"},
    {"name": "EPF & Fixed Debt", "val": 6600000, "rate": 7.0, "category": "debt"},
    {"name": "NPS", "val": 1900000, "rate": 9.0, "category": "equity"}
]
edited_assets = st.sidebar.data_editor(
    pd.DataFrame(assets_data),
    num_rows="dynamic",
    key="assets_editor"
)

# Dynamic Discretionary Event Milestone Editor
st.sidebar.markdown("### Discretionary Event Milestones")
discretionary_data = [
    {"name": "Mobile", "amount": 40000, "freq": 3, "inflation": 6.0},
    {"name": "Vehicle Upgrade", "amount": 2000000, "freq": 13, "inflation": 6.0},
    {"name": "Laptop", "amount": 100000, "freq": 4, "inflation": 6.0},
    {"name": "Medical Insurance", "amount": 50000, "freq": 3, "inflation": 10.0}
]
edited_disc = st.sidebar.data_editor(
    pd.DataFrame(discretionary_data),
    num_rows="dynamic",
    key="disc_editor"
)

# ==========================================
# 3. MATHEMATICAL COMPUTATION ENGINE
# ==========================================
build_up_years = retirement_age - current_age

if build_up_years >= 0:
    # --- Phase 1: Accumulation Phase ---
    accum_years = list(range(current_year, current_year + build_up_years + 1))
    accum_ages = [current_age + i for i in range(build_up_years + 1)]
    
    accum_equity = []
    accum_debt = []
    accum_total = []
    
    for i in range(build_up_years + 1):
        total_equity_this_year = 0
        total_debt_this_year = 0
        
        for _, asset in edited_assets.iterrows():
            try:
                compounded_val = float(asset['val']) * ((1 + (float(asset['rate']) / 100.0)) ** i)
                if asset['category'] == 'equity':
                    total_equity_this_year += compounded_val
                else:
                    total_debt_this_year += compounded_val
            except:
                pass
                
        accum_equity.append(total_equity_this_year)
        accum_debt.append(total_debt_this_year)
        accum_total.append(total_equity_this_year + total_debt_this_year)
        
    exact_terminal_corpus = accum_total[-1]
    inflation_multiplier = (1 + inflation_rate) ** build_up_years
    monthly_expense_at_retire = base_monthly_expense * inflation_multiplier
    base_annual_expense_at_retire = monthly_expense_at_retire * 12

    # --- Phase 2: Structural Bucket Asset Allocations ---
    st.markdown("<h1 style='margin-bottom:0px;'>Retirement Ecosystem India</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#9ca3af; font-size:14px; margin-bottom:25px;'>Advanced multi-asset, multi-bucket drawdown lifecycle simulator</p>", unsafe_allow_html=True)
    
    st.markdown("### Interactive Bucket Optimization Control Override")
    c_b1, c_b2, c_b3 = st.columns(3)
    with c_b1: alloc_b1_pct = st.number_input("Liquid (B1) Alloc %", value=40)
    with c_b2: alloc_b2_pct = st.number_input("Debt (B2) Alloc %", value=30)
    with c_b3: alloc_b3_pct = st.number_input("Equity (B3) Alloc %", value=30)
    
    total_sum = alloc_b1_pct + alloc_b2_pct + alloc_b3_pct
    if abs(total_sum - 100) > 0.01:
        st.markdown(f"<span style='color:#ef4444; font-weight:600;'>⚠️ Total Allocation is {total_sum}%. Must equal 100%!</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span style='color:#10b981; font-weight:600;'>✅ Allocation balanced properly at 100%</span>", unsafe_allow_html=True)
        
    initial_b1 = exact_terminal_corpus * (alloc_b1_pct / 100.0)
    initial_b2 = exact_terminal_corpus * (alloc_b2_pct / 100.0)
    initial_b3 = exact_terminal_corpus * (alloc_b3_pct / 100.0)

    # --- Phase 3: Drawdown Simulation Lifecycle ---
    retirement_duration = max_age - retirement_age
    post_retire_years = []
    post_retire_ages = []
    regular_expenses = []
    disc_expenses = []
    combined_drawdown = []
    portfolio_balances = []
    
    b1_tracker = initial_b1
    b2_tracker = initial_b2
    b3_tracker = initial_b3
    
    portfolio_depleted = False
    portfolio_survives_till_age = max_age
    
    b1_trend, b2_trend, b3_trend = [], [], []
    
    for y in range(retirement_duration + 1):
        curr_eval_age = retirement_age + y
        curr_eval_year = current_year + build_up_years + y
        
        post_retire_years.append(curr_eval_year)
        post_retire_ages.append(f"Age {curr_eval_age}")
        
        base_annual_inflated = (base_monthly_expense * 12) * ((1 + inflation_rate) ** (build_up_years + y))
        
        discretionary_outflow = 0
        for _, item in edited_disc.iterrows():
            try:
                freq = int(item['freq'])
                if y > 0 and y % freq == 0:
                    discretionary_outflow += float(item['amount']) * ((1 + (float(item['inflation']) / 100.0)) ** (build_up_years + y))
            except:
                pass
                
        gross_demand = base_annual_inflated + discretionary_outflow
        regular_expenses.append(base_annual_inflated)
        disc_expenses.append(discretionary_outflow)
        combined_drawdown.append(gross_demand)
        
        if not portfolio_depleted:
            b1_tracker *= (1 + rate_liquid)
            b2_tracker *= (1 + rate_debt)
            b3_tracker *= (1 + rate_equity)
            
            rem_demand = gross_demand
            
            if b1_tracker >= rem_demand:
                b1_tracker -= rem_demand
                rem_demand = 0
            else:
                rem_demand -= b1_tracker
                b1_tracker = 0
                
            if rem_demand > 0:
                if b2_tracker >= rem_demand:
                    b2_tracker -= rem_demand
                    rem_demand = 0
                else:
                    rem_demand -= b2_tracker
                    b2_tracker = 0
                    
            if rem_demand > 0:
                if b3_tracker >= rem_demand:
                    b3_tracker -= rem_demand
                    rem_demand = 0
                else:
                    rem_demand -= b3_tracker
                    b3_tracker = 0
                    
            if b1_tracker == 0 and (b2_tracker > 0 or b3_tracker > 0):
                target_refill = base_annual_inflated * 2
                if b2_tracker >= target_refill:
                    b2_tracker -= target_refill
                    b1_tracker = target_refill
                else:
                    total_reserves = b2_tracker + b3_tracker
                    if total_reserves >= target_refill:
                        gap = target_refill - b2_tracker
                        b1_tracker = target_refill
                        b2_tracker = 0
                        b3_tracker -= gap
                        
            total_portfolio_snapshot = b1_tracker + b2_tracker + b3_tracker
            if rem_demand > 0 or total_portfolio_snapshot <= 0:
                portfolio_depleted = True
                portfolio_survives_till_age = curr_eval_age
                portfolio_balances.append(0)
                b1_trend.append(0)
                b2_trend.append(0)
                b3_trend.append(0)
            else:
                portfolio_balances.append(total_portfolio_snapshot)
                b1_trend.append(b1_tracker)
                b2_trend.append(b2_tracker)
                b3_trend.append(b3_tracker)
        else:
            portfolio_balances.append(0)
            b1_trend.append(0)
            b2_trend.append(0)
            b3_trend.append(0)

    # --- Phase 4: Monte Carlo Engine Simulation ---
    iterations_count = 500
    survival_success_count = 0
    run_ending_balances = []
    
    mean_equity, std_dev_equity = 0.12, 0.16
    mean_debt, std_dev_debt = 0.07, 0.04
    sample_trajectories = []
    
    for i in range(iterations_count):
        sim_portfolio_val = exact_terminal_corpus
        sim_failed = False
        single_trajectory = []
        
        for y in range(retirement_duration + 1):
            norm_rand = np.random.normal(0, 1)
            eq_ret = mean_equity + (std_dev_equity * norm_rand)
            db_ret = mean_debt + (std_dev_debt * (norm_rand * 0.3))
            blended_return = (eq_ret * 0.4) + (db_ret * 0.6)
            
            base_annual_inflated = (base_monthly_expense * 12) * ((1 + inflation_rate) ** (build_up_years + y))
            discretionary_outflow = 0
            for _, item in edited_disc.iterrows():
                try:
                    if y > 0 and y % int(item['freq']) == 0:
                        discretionary_outflow += float(item['amount']) * ((1 + (float(item['inflation']) / 100.0)) ** (build_up_years + y))
                except:
                    pass
            comp_demand = base_annual_inflated + discretionary_outflow
            
            if not sim_failed:
                sim_portfolio_val *= (1 + blended_return)
                sim_portfolio_val -= comp_demand
                if sim_portfolio_val <= 0:
                    sim_portfolio_val = 0
                    sim_failed = True
            single_trajectory.append(sim_portfolio_val)
            
        if not sim_failed and sim_portfolio_val > 0:
            survival_success_count += 1
        run_ending_balances.append(sim_portfolio_val)
        if i < 8:
            sample_trajectories.append(single_trajectory)
            
    run_ending_balances.sort()
    success_rate = round((survival_success_count / iterations_count) * 100)
    pessimistic_quantile = run_ending_balances[int(iterations_count * 0.25)]
    optimistic_quantile = run_ending_balances[int(iterations_count * 0.75)]

    # ==========================================
    # 4. VIEW RENDERING PIPELINE (TABS)
    # ==========================================
    tab_accum, tab_buckets, tab_cashflow, tab_montecarlo = st.tabs([
        "Accumulation Phase", "Bucket Strategy Allocations", "Post-Retirement Cashflows", "Sequence Risk (Monte Carlo)"
    ])
    
    # --- Tab 1: Accumulation Phase View ---
    with tab_accum:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f'<div class="kpi-card"><div class="kpi-label">Target Corpus Needed</div><div class="kpi-val">{format_to_indian_rupees(exact_terminal_corpus)}</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="kpi-card warning"><div class="kpi-label">Inflation-Adjusted Monthly Spend</div><div class="kpi-val">{format_to_indian_rupees(monthly_expense_at_retire)}</div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="kpi-card success"><div class="kpi-label">Net Initial Year Real Withdrawal</div><div class="kpi-val">{format_to_indian_rupees(base_annual_expense_at_retire)}</div></div>', unsafe_allow_html=True)
            
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=accum_ages, y=accum_total, name="Total Combined Portfolio", line=dict(color='#3b82f6', width=3), fill='tozeroy', fillcolor='rgba(59, 130, 246, 0.05)'))
        fig1.add_trace(go.Scatter(x=accum_ages, y=accum_equity, name="Equity Component", line=dict(color='#10b981', dash='dash')))
        fig1.add_trace(go.Scatter(x=accum_ages, y=accum_debt, name="Fixed Debt Component", line=dict(color='#8b5cf6', dash='dot')))
        fig1.update_layout(title="Pre-Retirement Corpus Growth Timeline", template="plotly_dark", paper_bgcolor='#141b2d', plot_bgcolor='#141b2d', margin=dict(l=40, r=40, t=40, b=40))
        st.plotly_chart(fig1, use_container_width=True)
        
        df_accum = pd.DataFrame({
            "Year": accum_years, "Age": [f"Age {a}" for a in accum_ages],
            "Equity Comp Value": [format_to_indian_rupees(x) for x in accum_equity],
            "Debt Comp Value": [format_to_indian_rupees(x) for x in accum_debt],
            "Total Portfolio Value": [format_to_indian_rupees(x) for x in accum_total]
        })
        st.markdown("### Accumulation Schedule Table")
        st.dataframe(df_accum, use_container_width=True, hide_index=True)

    # --- Tab 2: Bucket Strategy Allocations View ---
    with tab_buckets:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f'<div class="kpi-card" style="border-left-color:#f59e0b;"><div class="kpi-label">Proposed Liquid Bucket (B1)</div><div class="kpi-val" style="color:#f59e0b;">{format_to_indian_rupees(initial_b1)}</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="kpi-card"><div class="kpi-label">Proposed Fixed Income Debt (B2)</div><div class="kpi-val" style="color:#3b82f6;">{format_to_indian_rupees(initial_b2)}</div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="kpi-card success"><div class="kpi-label">Proposed Equity Component (B3)</div><div class="kpi-val" style="color:#10b981;">{format_to_indian_rupees(initial_b3)}</div></div>', unsafe_allow_html=True)
            
        sust_text = f"Corpus Runs Dry at Age {portfolio_survives_till_age}" if portfolio_depleted else f"Sustains Fully to Target Life Expectancy ({max_age})"
        color_class = "danger" if portfolio_depleted else "success"
        st.markdown(f'<div class="kpi-card {color_class}"><div class="kpi-label">Simulated Post-Retirement Sustenance Lifespan</div><div class="kpi-val">{sust_text}</div></div>', unsafe_allow_html=True)
        
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=post_retire_ages, y=b1_trend, name="Liquid Cash Vault (B1)", line=dict(color='#f59e0b'), fill='tozeroy', fillcolor='rgba(245, 158, 11, 0.1)'))
        fig2.add_trace(go.Scatter(x=post_retire_ages, y=b2_trend, name="Income Bonds Fixed (B2)", line=dict(color='#3b82f6'), fill='tozeroy', fillcolor='rgba(59, 130, 246, 0.1)'))
        fig2.add_trace(go.Scatter(x=post_retire_ages, y=b3_trend, name="Equity Compounder Growth (B3)", line=dict(color='#10b981'), fill='tozeroy', fillcolor='rgba(16, 185, 129, 0.1)'))
        fig2.update_layout(title="Decaying Strategic Component Asset Balances Over Time", template="plotly_dark", paper_bgcolor='#141b2d', plot_bgcolor='#141b2d')
        st.plotly_chart(fig2, use_container_width=True)

    # --- Tab 3: Post-Retirement Cashflows View ---
    with tab_cashflow:
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(x=post_retire_ages, y=combined_drawdown, name="Gross Cash Demand Outflow", marker_color='#8b5cf6'))
        fig3.update_layout(title="Annualized Dynamic Real Cash Outflow Timeline", template="plotly_dark", paper_bgcolor='#141b2d', plot_bgcolor='#141b2d')
        st.plotly_chart(fig3, use_container_width=True)
        
        df_cash = pd.DataFrame({
            "Year": post_retire_years, "Age": post_retire_ages,
            "Inflation Index Regular Expense": [format_to_indian_rupees(x) for x in regular_expenses],
            "Discretionary Milestones Due": [format_to_indian_rupees(x) for x in disc_expenses],
            "Gross Aggregated Drawdown Demand": [format_to_indian_rupees(x) for x in combined_drawdown],
            "Remaining Assets Year End Balance": [format_to_indian_rupees(x) for x in portfolio_balances]
        })
        st.markdown("### Post-Retirement Annual Outflow Statement Ledger")
        st.dataframe(df_cash, use_container_width=True, hide_index=True)

    # --- Tab 4: Monte Carlo View ---
    with tab_montecarlo:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f'<div class="kpi-card success"><div class="kpi-label">Probability of Lifecycle Success</div><div class="kpi-val">{success_rate}%</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="kpi-card"><div class="kpi-label">Optimistic Outcome (75th Percentile)</div><div class="kpi-val" style="color:#10b981;">{format_to_indian_rupees(optimistic_quantile)}</div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="kpi-card warning"><div class="kpi-label">Pessimistic Outcome (25th Percentile)</div><div class="kpi-val" style="color:#ef4444;">{format_to_indian_rupees(pessimistic_quantile)}</div></div>', unsafe_allow_html=True)
            
        fig4 = go.Figure()
        for idx, traj in enumerate(sample_trajectories):
            color = 'rgba(16, 185, 129, 0.4)' if idx % 2 == 0 else 'rgba(239, 68, 68, 0.4)'
            fig4.add_trace(go.Scatter(x=post_retire_ages, y=traj, mode='lines', line=dict(color=color, width=1.5), showlegend=False))
        fig4.update_layout(title="Monte Carlo Security Boundary Simulations (500 Randomized Asset Runs)", template="plotly_dark", paper_bgcolor='#141b2d', plot_bgcolor='#141b2d')
        st.plotly_chart(fig4, use_container_width=True)
else:
    st.error("Retirement Age must be higher than or equal to Current Age.")
