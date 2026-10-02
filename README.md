Markdown
# JioHotstar: Cricket Event Churn & Subscription Pass Optimization

An end-to-end data analytics and pricing strategy project analyzing post-cricket churn dynamics and simulating tournament pass unit economics for JioHotstar.

---

## Business Question
> *Why do users churn aggressively after premier sporting tournaments (IPL/World Cup), and would a fixed-duration event pass outperform traditional monthly auto-renew plans in revenue capture and customer retention?*

---

## Tech Stack & Methods
- **Database & Querying:** SQLite / PostgreSQL (Window functions, cohort aggregations, user segmentation)
- **Data Modeling & Analytics:** Python (`pandas`, `numpy`, `scipy`)
- **NLP & Sentiment Analysis:** Topic modeling framework, Play Store review scraping
- **Financial Simulation:** Cohort LTV modeling and multi-variable pricing sensitivity analysis
- **Data Visualization:** `matplotlib`, `seaborn`, Looker Studio dashboard architecture

---

## Repository Structure

```text
├── schema.md              # Database DDL, table relationships, and data dictionary
├── generate_data.py       # Realistic synthetic data generator (10K users, 5 tables)
├── run_analysis.py        # SQL queries, cohort retention simulation, & chart generator
├── findings.md            # Analytical case study, churn breakdown, & recommendations
├── figures/               # Output analytical visualizations
│   ├── revenue_trajectory_comparison.png
│   └── cumulative_cashflow.png
└── README.md              # Portfolio overview and reproduction steps
Step-by-Step Reproduction Guide
1. Set Up Environment
Bash
git clone [https://github.com/annikota26-ship-it/jiostar-churn-analysis.git](https://github.com/annikota26-ship-it/jiostar-churn-analysis.git)
cd jiostar-churn-analysis
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install pandas numpy matplotlib
2. Generate the Dataset
Run the data generator to create the database (jiostar_ott.db):

Bash
python generate_data.py
3. Run Analysis & Financial Modeling
Execute the analytics pipeline to print SQL outputs, cohort models, sensitivity tables, and generate figures:

Bash
python run_analysis.py
Summary of Analytical Results
Plaintext
================================================================================
FINANCIAL MODEL: RECURRING MONTHLY VS. ₹129 SEASON PASS COHORT SIMULATION
================================================================================
Month               Monthly_Plan_Users  Monthly_Plan_Rev_INR  Season_Pass_Users  Season_Pass_Rev_INR
Month 1 (IPL Start)             100000            7900000.00             118000          15222000.00
Month 2 (IPL Finals)             43680            3450720.00             118000                 0.00
Month 3 (Post-IPL)               12000             948000.00              17700           1398300.00
Month 4 (Steady-State)            8000             632000.00              11800            932200.00

Total 4-Month Gross Revenue (Monthly Plan): INR 12,930,720.00
Total 4-Month Gross Revenue (Season Pass):   INR 17,552,500.00
Net Revenue Lift from Season Pass:          +35.74%
Key Insights
The Post-Finals Churn Cliff: Over 68% of sports-acquired monthly subscribers on the ₹79 Mobile tier cancel within 14 days of tournament completion.

UPI Mandate Breakage: Between 8% and 11% of renewals fail involuntarily due to banking auto-pay e-mandate declines and insufficient balances.

Pass Economics: A ₹129 non-renewing 75-day Season Pass captures revenue upfront, avoids payment friction, and delivers a +35.7% net revenue lift over a standard monthly recurring model.
---
## Author
**Anushka Bhatt**  
*Aspiring Data & Business Analyst* | B.Tech Mechanical Engineering  
[GitHub Profile](https://github.com/annikota26-ship-it)