"""
generate_data.py
Generates synthetic data for the JioHotstar Churn & Subscription Pass Study.
Outputs: jiostar_ott.db
"""

import sqlite3
import random
import datetime
import numpy as np
import pandas as pd

random.seed(42)
np.random.seed(42)

DB_NAME = "jiostar_ott.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    cur.executescript("""
    DROP TABLE IF EXISTS users;
    DROP TABLE IF EXISTS subscriptions;
    DROP TABLE IF EXISTS stream_sessions;
    DROP TABLE IF EXISTS survey_responses;
    DROP TABLE IF EXISTS app_reviews;

    CREATE TABLE users (
        user_id INTEGER PRIMARY KEY,
        signup_date DATE,
        acquisition_channel VARCHAR(50),
        state_circle VARCHAR(50),
        primary_device VARCHAR(30)
    );

    CREATE TABLE subscriptions (
        sub_id INTEGER PRIMARY KEY,
        user_id INTEGER,
        plan_tier VARCHAR(20),
        billing_cycle VARCHAR(20),
        price_paid NUMERIC(8,2),
        start_date DATE,
        end_date DATE,
        auto_renew_status INTEGER,
        payment_method VARCHAR(30),
        churn_date DATE,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );

    CREATE TABLE stream_sessions (
        session_id INTEGER PRIMARY KEY,
        user_id INTEGER,
        session_date DATE,
        content_type VARCHAR(30),
        content_id VARCHAR(50),
        watch_time_minutes INTEGER,
        bitrate_breach INTEGER,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );

    CREATE TABLE survey_responses (
        response_id INTEGER PRIMARY KEY,
        user_id INTEGER,
        primary_signup_reason VARCHAR(60),
        cancellation_trigger VARCHAR(60),
        wtp_season_pass_129 INTEGER,
        preferred_retention_perk VARCHAR(60)
    );

    CREATE TABLE app_reviews (
        review_id INTEGER PRIMARY KEY,
        review_date DATE,
        star_rating INTEGER,
        review_text TEXT,
        assigned_topic VARCHAR(40)
    );
    """)
    conn.commit()
    conn.close()

def populate_database():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    # Tournament parameters
    ipl_start = datetime.date(2026, 3, 25)
    ipl_end = datetime.date(2026, 5, 28)
    
    channels = ["Cricket Ad Campaign", "Organic", "Telecom Bundle", "Referral"]
    channel_weights = [0.55, 0.20, 0.15, 0.10]
    circles = ["Maharashtra", "Delhi-NCR", "Karnataka", "Tamil Nadu", "UP-East", "West Bengal"]
    devices = ["Android", "iOS", "Android TV", "FireTV", "Web"]
    device_weights = [0.65, 0.15, 0.10, 0.05, 0.05]

    num_users = 10000
    user_rows = []
    sub_rows = []
    
    sub_id_counter = 1
    
    for uid in range(1, num_users + 1):
        # Peak tournament signups
        if random.random() < 0.70:
            signup = ipl_start + datetime.timedelta(days=random.randint(-7, 20))
        else:
            signup = datetime.date(2026, 1, 15) + datetime.timedelta(days=random.randint(0, 150))
            
        channel = random.choices(channels, weights=channel_weights)[0]
        circle = random.choice(circles)
        device = random.choices(devices, weights=device_weights)[0]
        user_rows.append((uid, signup.isoformat(), channel, circle, device))
        
        # Determine plan tier and billing cycle
        is_cricket_intent = channel == "Cricket Ad Campaign" or (signup >= ipl_start and signup <= ipl_start + datetime.timedelta(days=30))
        if is_cricket_intent:
            plan_tier = random.choices(["Mobile", "Super", "Premium"], weights=[0.75, 0.20, 0.05])[0]
            billing_cycle = random.choices(["Monthly", "Quarterly", "Annual"], weights=[0.80, 0.15, 0.05])[0]
        else:
            plan_tier = random.choices(["Mobile", "Super", "Premium"], weights=[0.40, 0.40, 0.20])[0]
            billing_cycle = random.choices(["Monthly", "Quarterly", "Annual"], weights=[0.35, 0.35, 0.30])[0]
            
        prices = {
            ("Mobile", "Monthly"): 79.0, ("Mobile", "Quarterly"): 149.0, ("Mobile", "Annual"): 499.0,
            ("Super", "Monthly"): 149.0, ("Super", "Quarterly"): 349.0, ("Super", "Annual"): 1099.0,
            ("Premium", "Monthly"): 299.0, ("Premium", "Quarterly"): 699.0, ("Premium", "Annual"): 2199.0
        }
        price = prices[(plan_tier, billing_cycle)]
        
        # Subscription start
        sub_start = signup
        duration_days = 30 if billing_cycle == "Monthly" else (90 if billing_cycle == "Quarterly" else 365)
        sub_end = sub_start + datetime.timedelta(days=duration_days)
        
        # Churn dynamics: Tournament subscribers heavily churn post-IPL final (2026-05-28)
        auto_renew = 1
        churn_date = None
        payment_method = random.choices(["UPI AutoPay", "Credit Card", "NetBanking"], weights=[0.75, 0.15, 0.10])[0]
        
        if is_cricket_intent and billing_cycle == "Monthly":
            # 68% churn immediately around tournament completion
            if random.random() < 0.68:
                auto_renew = 0
                churn_offset = random.randint(0, 10)
                churn_date = (ipl_end + datetime.timedelta(days=churn_offset)).isoformat()
            else:
                # 10% fail due to UPI auto-debit friction
                if random.random() < 0.10:
                    auto_renew = 0
                    churn_date = sub_end.isoformat()
        elif billing_cycle == "Monthly":
            if random.random() < 0.25:
                auto_renew = 0
                churn_date = sub_end.isoformat()

        sub_rows.append((
            sub_id_counter, uid, plan_tier, billing_cycle, price,
            sub_start.isoformat(), sub_end.isoformat(), auto_renew,
            payment_method, churn_date
        ))
        sub_id_counter += 1

    cur.executemany("INSERT INTO users VALUES (?,?,?,?,?)", user_rows)
    cur.executemany("INSERT INTO subscriptions VALUES (?,?,?,?,?,?,?,?,?,?)", sub_rows)
    conn.commit()

    # Generate Stream Sessions
    session_rows = []
    session_id = 1
    
    for uid in range(1, num_users + 1):
        is_cricket_focused = user_rows[uid - 1][2] == "Cricket Ad Campaign"
        num_sessions = random.randint(15, 45) if is_cricket_focused else random.randint(10, 30)
        
        for _ in range(num_sessions):
            if is_cricket_focused:
                # Active heavily during tournament
                if random.random() < 0.85:
                    s_date = ipl_start + datetime.timedelta(days=random.randint(0, 64))
                    c_type = "Live Sports"
                    c_id = f"IPL_MATCH_{random.randint(1, 74)}"
                    watch_mins = random.randint(25, 160)
                    bitrate_breach = 1 if (watch_mins > 80 and random.random() < 0.22) else 0
                else:
                    s_date = ipl_end + datetime.timedelta(days=random.randint(1, 30))
                    c_type = random.choice(["Specials/Series", "Movies"])
                    c_id = f"ENT_{random.randint(101, 199)}"
                    watch_mins = random.randint(15, 60)
                    bitrate_breach = 0
            else:
                s_date = datetime.date(2026, 3, 1) + datetime.timedelta(days=random.randint(0, 110))
                c_type = random.choices(["Live Sports", "Specials/Series", "Movies", "Live News"], weights=[0.25, 0.40, 0.25, 0.10])[0]
                c_id = f"CONTENT_{random.randint(200, 499)}"
                watch_mins = random.randint(20, 120)
                bitrate_breach = 1 if (c_type == "Live Sports" and random.random() < 0.18) else 0

            session_rows.append((
                session_id, uid, s_date.isoformat(), c_type, c_id, watch_mins, bitrate_breach
            ))
            session_id += 1

    cur.executemany("INSERT INTO stream_sessions VALUES (?,?,?,?,?,?,?)", session_rows)
    conn.commit()

    # Generate Survey Responses (N=80)
    survey_reasons = ["Tournament only (IPL/World Cup)", "Movies & HBO Shows", "General family entertainment"]
    churn_triggers = ["Tournament finished", "Annoying ads on paid tier", "Buffering & quality drops", "Billing/Auto-pay issue"]
    retention_perks = ["₹129 Tournament Match Pass (no auto-debit)", "Ad-free sports bundle", "Post-IPL 50% entertainment discount"]
    
    survey_rows = []
    for resp_id in range(1, 81):
        u_id = random.randint(1, num_users)
        reason = random.choices(survey_reasons, weights=[0.72, 0.18, 0.10])[0]
        trigger = random.choices(churn_triggers, weights=[0.60, 0.20, 0.12, 0.08])[0]
        wtp = 1 if random.random() < 0.69 else 0  # 69% willing to take a ₹129 non-renewing pass
        perk = random.choices(retention_perks, weights=[0.55, 0.25, 0.20])[0]
        survey_rows.append((resp_id, u_id, reason, trigger, wtp, perk))
        
    cur.executemany("INSERT INTO survey_responses VALUES (?,?,?,?,?,?)", survey_rows)
    conn.commit()

    # Generate App Reviews (N=500)
    review_templates = [
        ("Buffering/Latency", 1, "Extreme lag during the last overs! Live match keeps buffering despite 100 Mbps fiber connection."),
        ("Excessive Ads", 2, "I paid for the Mobile tier and still get bombarded with 6 unskippable betting and car ads every over."),
        ("Auto-Debit Dispute", 1, "Tournament is over but Hotstar deducted 79 rupees from UPI without sending any warning notification!"),
        ("Content Cliff", 3, "Only used it for IPL. There is nothing fresh or engaging to watch once the cricket matches end.")
    ]
    
    review_rows = []
    for r_id in range(1, 501):
        topic, rating, text = random.choices(review_templates, weights=[0.38, 0.32, 0.18, 0.12])[0]
        # Cluster review dates around tournament window
        r_date = ipl_start + datetime.timedelta(days=random.randint(0, 75))
        review_rows.append((r_id, r_date.isoformat(), rating, text, topic))

    cur.executemany("INSERT INTO app_reviews VALUES (?,?,?,?,?)", review_rows)
    conn.commit()
    conn.close()
    print("Database generation complete: jiostar_ott.db successfully created.")

if __name__ == "__main__":
    init_db()
    populate_database()