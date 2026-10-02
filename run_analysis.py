"""
run_analysis.py
Performs SQL queries, cohort retention modeling, sensitivity analysis,
and generates performance charts for the JioHotstar analytics project.
"""

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

DB_NAME = "jiostar_ott.db"

def run_sql_queries():
    conn = sqlite3.connect(DB_NAME)
    
    print("\n" + "="*80)
    print("SQL ANALYSIS 1: USER PERSONA SEGMENTATION & POST-TOURNAMENT CHURN RATE")
    print("="*80)
    
    query1 = """
    WITH user_viewing AS (
        SELECT 
            user_id,
            SUM(CASE WHEN content_type = 'Live Sports' THEN watch_time_minutes ELSE 0 END) AS sports_mins,
            SUM(CASE WHEN content_type != 'Live Sports' THEN watch_time_minutes ELSE 0 END) AS non_sports_mins
        FROM stream_sessions
        GROUP BY user_id
    ),
    categorized_users AS (
        SELECT 
            u.user_id,
            s.plan_tier,
            s.billing_cycle,
            CASE 
                WHEN uv.non_sports_mins = 0 AND uv.sports_mins > 0 THEN 'Pure Event-Only'
                WHEN uv.sports_mins > uv.non_sports_mins THEN 'Hybrid (Sports-Heavy)'
                ELSE 'General Entertainment'
            END AS persona,
            CASE 
                WHEN s.churn_date BETWEEN '2026-05-28' AND '2026-06-15' THEN 1 
                ELSE 0 
            END AS post_event_churn
        FROM users u
        JOIN subscriptions s ON u.user_id = s.user_id
        LEFT JOIN user_viewing uv ON u.user_id = uv.user_id
    )
    SELECT 
        persona,
        billing_cycle,
        COUNT(*) AS total_subscribers,
        ROUND(AVG(post_event_churn) * 100.0, 2) AS post_tournament_churn_pct
    FROM categorized_users
    GROUP BY persona, billing_cycle
    ORDER BY total_subscribers DESC;
    """
    df_persona = pd.read_sql_query(query1, conn)
    print(df_persona.to_string(index=False))

    print("\n" + "="*80)
    print("SQL ANALYSIS 2: PLAY STORE REVIEW TOPIC BREAKDOWN & DISSATISFACTION DRIVERS")
    print("="*80)
    
    query2 = """
    SELECT 
        assigned_topic AS complaint_cluster,
        COUNT(*) AS review_count,
        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM app_reviews), 2) AS share_pct,
        ROUND(AVG(star_rating), 2) AS avg_rating
    FROM app_reviews
    GROUP BY assigned_topic
    ORDER BY review_count DESC;
    """
    df_reviews = pd.read_sql_query(query2, conn)
    print(df_reviews.to_string(index=False))

    print("\n" + "="*80)
    print("SQL ANALYSIS 3: SURVEY WILLINGNESS TO PAY (WTP) FOR ₹129 PASS")
    print("="*80)
    
    query3 = """
    SELECT 
        primary_signup_reason,
        COUNT(*) AS sample_size,
        SUM(wtp_season_pass_129) AS willing_to_buy_pass,
        ROUND(AVG(wtp_season_pass_129) * 100.0, 2) AS wtp_acceptance_pct
    FROM survey_responses
    GROUP BY primary_signup_reason;
    """
    df_survey = pd.read_sql_query(query3, conn)
    print(df_survey.to_string(index=False))
    
    conn.close()
    return df_persona, df_reviews

def run_cohort_and_sensitivity_model():
    print("\n" + "="*80)
    print("FINANCIAL MODEL: RECURRING MONTHLY VS. ₹129 SEASON PASS COHORT SIMULATION")
    print("="*80)

    cohort_leads = 100000

    # 1. Recurring Monthly Strategy (₹79/mo)
    # Month 1: Initial tournament acquisition
    # Month 2: Tournament continues (retention ~48%, 9% e-mandate dropouts)
    # Month 3: Post-tournament drop-off (retention ~12%)
    # Month 4: Residual entertainment retention (~8%)
    monthly_retention = [1.00, 0.48 * (1 - 0.09), 0.12, 0.08]
    price_monthly = 79.0
    
    rev_monthly = []
    users_monthly = []
    for ret in monthly_retention:
        active = cohort_leads * ret
        rev = active * price_monthly
        users_monthly.append(active)
        rev_monthly.append(rev)

    # 2. Season Pass Strategy (₹129 upfront for 75 days)
    # Conversion lift: +18% higher conversion due to zero auto-pay commitment
    # Post-season bridge retention at Month 3 into ₹79 entertainment plan: 15%
    pass_conversion_lift = 1.18
    initial_pass_users = cohort_leads * pass_conversion_lift
    price_pass = 129.0
    
    users_pass = [initial_pass_users, initial_pass_users, initial_pass_users * 0.15, initial_pass_users * 0.10]
    rev_pass = [
        initial_pass_users * price_pass,
        0.0,  # Pre-paid in Month 1
        (initial_pass_users * 0.15) * 79.0,
        (initial_pass_users * 0.10) * 79.0
    ]

    months = ["Month 1 (IPL Start)", "Month 2 (IPL Finals)", "Month 3 (Post-IPL)", "Month 4 (Steady-State)"]
    df_cohort = pd.DataFrame({
        "Month": months,
        "Monthly_Plan_Users": [int(u) for u in users_monthly],
        "Monthly_Plan_Rev_INR": [round(r, 2) for r in rev_monthly],
        "Season_Pass_Users": [int(u) for u in users_pass],
        "Season_Pass_Rev_INR": [round(r, 2) for r in rev_pass]
    })
    print(df_cohort.to_string(index=False))
    
    total_rev_monthly = sum(rev_monthly)
    total_rev_pass = sum(rev_pass)
    lift = ((total_rev_pass - total_rev_monthly) / total_rev_monthly) * 100.0

    print(f"\nTotal 4-Month Gross Revenue (Monthly Plan): INR {total_rev_monthly:,.2f}")
    print(f"Total 4-Month Gross Revenue (Season Pass):   INR {total_rev_pass:,.2f}")
    print(f"Net Revenue Lift from Season Pass:          +{lift:.2f}%\n")

    # 3. Sensitivity Matrix
    # Testing Pass Price points against post-tournament bridge retention
    print("="*80)
    print("SENSITIVITY MATRIX: 4-MONTH GROSS REVENUE (INR Millions)")
    print("="*80)

    pass_prices = [109, 119, 129, 139, 149]
    bridge_rates = [0.08, 0.12, 0.15, 0.20]
    
    matrix_data = []
    for p in pass_prices:
        row = {"Pass Price (INR)": f"₹{p}"}
        for b in bridge_rates:
            rev_total = (initial_pass_users * p) + (initial_pass_users * b * 79.0) + (initial_pass_users * (b * 0.67) * 79.0)
            row[f"Bridge {int(b*100)}%"] = f"₹{rev_total / 1e6:.2f}M"
        matrix_data.append(row)
        
    df_sensitivity = pd.DataFrame(matrix_data)
    print(df_sensitivity.to_string(index=False))

    generate_plots(df_cohort, total_rev_monthly, total_rev_pass)

def generate_plots(df_cohort, total_m, total_p):
    os.makedirs("figures", exist_ok=True)
    
    # Chart 1: Revenue Trajectory Comparison
    plt.figure(figsize=(10, 5))
    x = np.arange(len(df_cohort["Month"]))
    width = 0.35
    
    plt.bar(x - width/2, df_cohort["Monthly_Plan_Rev_INR"] / 1e6, width, label="Recurring ₹79 Monthly", color="#1f77b4")
    plt.bar(x + width/2, df_cohort["Season_Pass_Rev_INR"] / 1e6, width, label="Upfront ₹129 Season Pass", color="#ff7f0e")
    
    plt.xticks(x, df_cohort["Month"])
    plt.ylabel("Revenue (INR Millions)")
    plt.title("Revenue Capture Trajectory: Monthly Subscription vs. Tournament Pass")
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig("figures/revenue_trajectory_comparison.png", dpi=300)
    plt.close()
    
    # Chart 2: Cumulative Cash Flow
    cum_m = np.cumsum(df_cohort["Monthly_Plan_Rev_INR"]) / 1e6
    cum_p = np.cumsum(df_cohort["Season_Pass_Rev_INR"]) / 1e6
    
    plt.figure(figsize=(10, 5))
    plt.plot(df_cohort["Month"], cum_m, marker='o', linewidth=2.5, label=f"Monthly Total: ₹{total_m/1e6:.2f}M", color="#1f77b4")
    plt.plot(df_cohort["Month"], cum_p, marker='s', linewidth=2.5, label=f"Pass Total: ₹{total_p/1e6:.2f}M", color="#2ca02c")
    plt.ylabel("Cumulative Cash Flow (INR Millions)")
    plt.title("Cumulative Cash Flow Front-Loading (Per 100K Lead Pool)")
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig("figures/cumulative_cashflow.png", dpi=300)
    plt.close()
    print("Charts successfully saved to `figures/` directory.")

if __name__ == "__main__":
    run_sql_queries()
    run_cohort_and_sensitivity_model()