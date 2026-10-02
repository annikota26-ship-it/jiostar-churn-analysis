# Database Schema & Data Dictionary: JioHotstar Churn & Subscription Pass Study

The analytical database is hosted in SQLite / PostgreSQL and models the user journey from tournament-driven acquisition through post-tournament churn or renewal.

## Entity Relationship Summary

- `users` (1) ───< `subscriptions` (N)
- `users` (1) ───< `stream_sessions` (N)
- `users` (1) ───0..1 `survey_responses` (N)
- `app_reviews` (Independent sentiment & feedback source)

---

## Data Dictionary

### Table: `users`
Captures demographic and acquisition attributes.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `user_id` | INTEGER | PRIMARY KEY | Unique identifier for each consumer. |
| `signup_date` | DATE | NOT NULL | Date account was created. |
| `acquisition_channel` | VARCHAR(50) | NOT NULL | Organic, Cricket Ad Campaign, Referral, Telecom Bundle (Jio/Airtel). |
| `state_circle` | VARCHAR(50) | NOT NULL | Telecom circle (e.g., Maharashtra, Delhi-NCR, Karnataka, UP-East). |
| `primary_device` | VARCHAR(30) | NOT NULL | Android, iOS, Android TV, FireTV, Web. |

### Table: `subscriptions`
Tracks transaction history, billing tiers, and cancellation dates.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `sub_id` | INTEGER | PRIMARY KEY | Unique transaction record. |
| `user_id` | INTEGER | FOREIGN KEY | Associated user ID. |
| `plan_tier` | VARCHAR(20) | NOT NULL | `Mobile`, `Super`, `Premium`. |
| `billing_cycle` | VARCHAR(20) | NOT NULL | `Monthly`, `Quarterly`, `Annual`. |
| `price_paid` | NUMERIC(8,2)| NOT NULL | Amount paid in INR (e.g., 79.00, 149.00, 499.00). |
| `start_date` | DATE | NOT NULL | Plan entitlement start date. |
| `end_date` | DATE | NOT NULL | Scheduled expiration date. |
| `auto_renew_status` | BOOLEAN | NOT NULL | 1 = UPI e-mandate active, 0 = revoked / cancelled. |
| `payment_method` | VARCHAR(30) | NOT NULL | UPI AutoPay, Credit Card, NetBanking, Google Play Billing. |
| `churn_date` | DATE | NULL | Date cancellation or mandate revocation was logged. |

### Table: `stream_sessions`
Captures granular consumption behavior across content catalogs.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `session_id` | INTEGER | PRIMARY KEY | Unique streaming session ID. |
| `user_id` | INTEGER | FOREIGN KEY | Associated user ID. |
| `session_date` | DATE | NOT NULL | Date of stream. |
| `content_type` | VARCHAR(30) | NOT NULL | `Live Sports`, `Specials/Series`, `Movies`, `Live News`. |
| `content_id` | VARCHAR(50) | NOT NULL | Content identifier (e.g., `IPL_2026_M45`, `HBO_HOTD_S02`). |
| `watch_time_minutes`| INTEGER | NOT NULL | Duration of playback. |
| `bitrate_breach`| BOOLEAN | NOT NULL | 1 if buffering/resolution drops were triggered during peak traffic. |

### Table: `survey_responses`
Primary survey data evaluating willingness to pay (WTP) and churn drivers (N=80).

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `response_id` | INTEGER | PRIMARY KEY | Survey record ID. |
| `user_id` | INTEGER | FOREIGN KEY | Linked respondent. |
| `primary_signup_reason`| VARCHAR(60) | NOT NULL | Specific tournament, Regular movies/shows, General entertainment. |
| `cancellation_trigger` | VARCHAR(60) | NOT NULL | Tournament ended, Price too high, Buffering issues, Annoying ads. |
| `wtp_season_pass_129` | BOOLEAN | NOT NULL | Willing to buy ₹129 75-day Pass instead of ₹79 recurring monthly. |
| `preferred_retention_perk`| VARCHAR(60)| NOT NULL | Discounted entertainment bridge, Ad-free upgrade, Multi-camera feeds. |

### Table: `app_reviews`
Play Store and App Store reviews pulled across tournament periods.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `review_id` | INTEGER | PRIMARY KEY | Review log ID. |
| `review_date` | DATE | NOT NULL | Submission date. |
| `star_rating` | INTEGER | NOT NULL | 1 to 5 stars. |
| `review_text` | TEXT | NOT NULL | Consumer feedback text. |
| `assigned_topic` | VARCHAR(40) | NOT NULL | BERTopic cluster: `Buffering/Latency`, `Excessive Ads`, `Auto-Debit Dispute`, `Content Cliff`. |