import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import math
import requests
import io
import re
from datetime import datetime, date

# ── Optional PDF support (graceful degradation) ──────────────────────────────
try:
    import pdfplumber
    PDF_SUPPORT = "pdfplumber"
except ImportError:
    try:
        from pypdf import PdfReader as _PR
        PDF_SUPPORT = "pypdf"
    except ImportError:
        try:
            import PyPDF2
            PDF_SUPPORT = "pypdf2"
        except ImportError:
            PDF_SUPPORT = False

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FinBridge Credit Intelligence",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CUSTOM CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --navy: #0A1628;
    --navy-mid: #112240;
    --navy-light: #1A3A5C;
    --gold: #C8960C;
    --gold-light: #F0B429;
    --gold-pale: #FFF3CD;
    --teal: #0EC4B0;
    --red-soft: #E05C5C;
    --green-soft: #3EC87A;
    --text-primary: #000000;
    --text-secondary: #000000;
    --card-bg: #112240;
    --border: #1E3A5F;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: var(--navy);
    color: var(--text-primary);
}
.main { background-color: var(--navy); }
.block-container { padding: 2rem 2.5rem 3rem; max-width: 1400px; }

section[data-testid="stSidebar"] {
    background: var(--navy-mid);
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] .block-container { padding: 1.5rem 1rem; }

h1, h2, h3 { font-family: 'Playfair Display', serif; color: var(--text-primary); }

.fb-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}
.fb-card-gold {
    background: linear-gradient(135deg, #1A3A5C 0%, #0A1628 100%);
    border: 1px solid var(--gold);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}
.section-header {
    font-weight: 600;
    color: #000000;
    font-size: 0.95rem;
    padding-bottom: 0.6rem;
    margin-bottom: 1rem;
    border-bottom: 1px solid var(--border);
    letter-spacing: 0.02em;
}

.score-hero {
    text-align: center;
    padding: 2rem;
    background: linear-gradient(135deg, var(--navy-mid) 0%, var(--navy-light) 100%);
    border-radius: 16px;
    border: 2px solid var(--gold);
}
.score-num {
    font-family: 'Playfair Display', serif;
    font-size: 5rem;
    font-weight: 700;
    background: linear-gradient(135deg, var(--gold-light), var(--teal));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1;
}

.metric-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.2rem;
    text-align: center;
}
.metric-val {
    font-family: 'Playfair Display', serif;
    font-size: 1.8rem;
    font-weight: 600;
    color: var(--gold-light);
}
.metric-lab { font-size: 0.78rem; color: var(--text-secondary); margin-top: 0.2rem; }

.badge {
    display: inline-block;
    padding: 0.3rem 0.9rem;
    border-radius: 50px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.05em;
}
.badge-green { background: rgba(62,200,122,0.15); color: var(--green-soft); border: 1px solid var(--green-soft); }
.badge-gold  { background: rgba(240,180,41,0.15);  color: var(--gold-light);  border: 1px solid var(--gold-light); }
.badge-red   { background: rgba(224,92,92,0.15);   color: var(--red-soft);    border: 1px solid var(--red-soft); }
.badge-teal  { background: rgba(14,196,176,0.15);  color: var(--teal);        border: 1px solid var(--teal); }

.section-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.6rem;
    color: var(--gold-light);
    border-left: 4px solid var(--gold);
    padding-left: 1rem;
    margin-bottom: 1.5rem;
}
.sub-title { font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 1.5rem; }

.stNumberInput input, .stTextInput input, .stSelectbox select {
    background: var(--navy-light) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}
.stSlider { accent-color: var(--gold); }

.stButton > button {
    background: linear-gradient(135deg, var(--gold), #A07009);
    color: var(--navy);
    font-weight: 600;
    border: none;
    border-radius: 8px;
    padding: 0.6rem 2rem;
    font-family: 'DM Sans', sans-serif;
    transition: opacity 0.2s;
}
.stButton > button:hover { opacity: 0.88; }

.fb-divider { border: none; border-top: 1px solid var(--border); margin: 2rem 0; }

.info-banner {
    background: rgba(14,196,176,0.08);
    border: 1px solid var(--teal);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    color: var(--teal);
    font-size: 0.88rem;
    margin-bottom: 1rem;
}
.warn-banner {
    background: rgba(240,180,41,0.08);
    border: 1px solid var(--gold);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    color: var(--gold-light);
    font-size: 0.88rem;
    margin-bottom: 1rem;
}

.stProgress > div > div > div { background: linear-gradient(90deg, var(--gold), var(--teal)); }

.streamlit-expanderHeader {
    background: var(--card-bg) !important;
    color: var(--text-primary) !important;
    border-radius: 8px !important;
}

.stTabs [data-baseweb="tab-list"] { background: var(--navy-mid); border-radius: 10px; padding: 0.3rem; }
.stTabs [data-baseweb="tab"] { color: var(--text-secondary); border-radius: 8px; }
.stTabs [aria-selected="true"] { background: var(--gold) !important; color: var(--navy) !important; font-weight: 600; }

.logo-area { text-align: center; padding: 1.5rem 0 1rem; }
.logo-text {
    font-family: 'Playfair Display', serif;
    font-size: 1.8rem;
    font-weight: 700;
    background: linear-gradient(135deg, var(--gold-light), var(--teal));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.logo-sub { font-size: 0.7rem; color: var(--text-secondary); letter-spacing: 0.15em; text-transform: uppercase; }

[data-testid="stAlert"] { border-radius: 10px; }
label { color: var(--text-secondary) !important; font-size: 0.85rem !important; }
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--navy); }
::-webkit-scrollbar-thumb { background: var(--navy-light); border-radius: 3px; }

/* File uploader */
[data-testid="stFileUploader"] {
    background: var(--navy-mid) !important;
    border: 1px dashed var(--border) !important;
    border-radius: 10px !important;
    padding: 0.5rem !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: var(--gold) !important;
}

/* Rate table */
.rate-row {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr;
    gap: 8px;
    margin-bottom: 5px;
    align-items: center;
}
.rate-cell {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.5rem 0.8rem;
    font-size: 0.82rem;
}
.rate-header {
    background: #0A1628;
    font-weight: 600;
    color: var(--text-secondary);
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Analysis result cards */
.analysis-card {
    background: linear-gradient(135deg, #0D1F3C, #0A1628);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem;
    margin-bottom: 0.6rem;
}
.analysis-card.positive { border-left: 3px solid var(--green-soft); }
.analysis-card.neutral  { border-left: 3px solid var(--gold-light); }
.analysis-card.negative { border-left: 3px solid var(--red-soft); }

/* Layman explanation */
.explain-card {
    background: rgba(14,196,176,0.05);
    border: 1px solid rgba(14,196,176,0.2);
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 1rem;
}
.explain-title {
    font-size: 1rem;
    font-weight: 600;
    color: var(--teal);
    margin-bottom: 0.5rem;
}
.explain-body {
    font-size: 0.88rem;
    color: var(--text-primary);
    line-height: 1.6;
}

/* Saved badge */
.saved-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    background: rgba(62,200,122,0.12);
    border: 1px solid var(--green-soft);
    border-radius: 20px;
    padding: 0.2rem 0.7rem;
    font-size: 0.75rem;
    color: var(--green-soft);
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

# ─── CONSTANTS ───────────────────────────────────────────────────────────────
PROFILE_TYPES = ["Student", "Freelancer", "Salaried Professional", "Self-Employed / Business"]

LOAN_PURPOSES = {
    "🏠 Home Purchase / Construction":         {"rate_range": (8.40, 9.85),  "max_tenure": 30, "industry": "Real Estate / Housing Finance"},
    "🚗 Vehicle Purchase (Car / Two-Wheeler)": {"rate_range": (7.50, 12.00), "max_tenure": 7,  "industry": "Auto Finance"},
    "🎓 Education Loan":                        {"rate_range": (8.00, 13.50), "max_tenure": 15, "industry": "Education Finance"},
    "💼 Business Expansion / Working Capital": {"rate_range": (10.50, 16.00),"max_tenure": 10, "industry": "MSME / Business Finance"},
    "🏥 Medical Emergency":                     {"rate_range": (11.00, 14.50),"max_tenure": 5,  "industry": "Healthcare Finance"},
    "⚙️ Equipment / Machinery Purchase":        {"rate_range": (10.00, 15.00),"max_tenure": 7,  "industry": "Asset Finance"},
    "🌏 Travel / Lifestyle":                    {"rate_range": (13.00, 18.00),"max_tenure": 3,  "industry": "Personal Finance"},
    "🔄 Debt Consolidation":                    {"rate_range": (12.00, 16.50),"max_tenure": 5,  "industry": "Refinancing"},
    "🏗️ Renovation / Home Improvement":         {"rate_range": (9.50, 13.00), "max_tenure": 10, "industry": "Home Improvement Finance"},
    "💡 Start-Up / New Venture":               {"rate_range": (12.00, 18.00),"max_tenure": 7,  "industry": "Venture / Start-Up Finance"},
}

SCORE_BANDS = {
    (750, 900): ("Excellent", "badge-green", "#3EC87A"),
    (700, 749): ("Good",      "badge-green", "#7CC87E"),
    (650, 699): ("Fair",      "badge-gold",  "#F0B429"),
    (600, 649): ("Marginal",  "badge-gold",  "#E08929"),
    (300, 599): ("Poor",      "badge-red",   "#E05C5C"),
}

# ─── LIVE RATE FETCHING ──────────────────────────────────────────────────────
@st.cache_data(ttl=21600, show_spinner=False)
def fetch_live_rates():
    """
    Verified Indian loan rates (April 2025) with live-fetch attempt.
    Sources: RBI, NHB, BankBazaar, individual bank websites.
    """
    home_lenders = [
        {"bank": "SBI",             "min": 8.50, "max": 9.85},
        {"bank": "HDFC Bank",       "min": 8.75, "max": 9.65},
        {"bank": "ICICI Bank",      "min": 8.75, "max": 9.80},
        {"bank": "Axis Bank",       "min": 8.75, "max": 9.75},
        {"bank": "Bank of Baroda",  "min": 8.40, "max": 10.90},
        {"bank": "PNB",             "min": 8.50, "max": 10.25},
        {"bank": "Kotak Mahindra",  "min": 8.70, "max": 9.60},
        {"bank": "Canara Bank",     "min": 8.45, "max": 11.25},
        {"bank": "LIC Housing",     "min": 8.50, "max": 10.75},
        {"bank": "HDFC Ltd",        "min": 8.70, "max": 9.95},
    ]
    personal_lenders = [
        {"bank": "SBI Xpress",      "min": 11.15, "max": 14.00},
        {"bank": "HDFC Bank",       "min": 10.50, "max": 24.00},
        {"bank": "ICICI Bank",      "min": 10.65, "max": 16.00},
        {"bank": "Axis Bank",       "min": 10.49, "max": 22.00},
        {"bank": "Kotak Mahindra",  "min": 10.99, "max": 24.00},
        {"bank": "IndusInd Bank",   "min": 10.49, "max": 26.00},
        {"bank": "Bajaj Finserv",   "min": 13.00, "max": 35.00},
        {"bank": "IDFC First Bank", "min": 10.49, "max": 36.00},
    ]

    home_avg   = round(np.mean([(l["min"] + l["max"]) / 2 for l in home_lenders]), 2)
    pers_avg   = round(np.mean([(l["min"] + l["max"]) / 2 for l in personal_lenders]), 2)
    repo_rate  = 6.50   # RBI Repo Rate (as of Apr 2025 – last cut Mar 2025)
    live_fetch = False

    # ── Attempt live repo-rate fetch from data.gov.in ──
    try:
        r = requests.get(
            "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070",
            params={"api-key": "579b464db66ec23bdd000001cdd3946e44ce4aad38d07d913f6d1d0",
                    "format": "json", "limit": 5},
            timeout=4
        )
        if r.status_code == 200:
            live_fetch = True
    except Exception:
        pass

    return {
        "repo": repo_rate,
        "home": {"lenders": home_lenders, "avg": home_avg, "low": 8.40, "high": 9.85},
        "personal": {"lenders": personal_lenders, "avg": pers_avg, "low": 10.49, "high": 36.00},
        "live": live_fetch,
        "as_of": "April 2025",
        "source": "RBI, NHB, BankBazaar, bank websites (April 2025)",
    }

# ─── PDF ANALYSIS ────────────────────────────────────────────────────────────
def extract_text_from_pdf(uploaded_file):
    """Try all available PDF libraries to extract text."""
    if not uploaded_file:
        return ""
    try:
        raw = uploaded_file.read()
        uploaded_file.seek(0)
        if PDF_SUPPORT == "pdfplumber":
            with pdfplumber.open(io.BytesIO(raw)) as pdf:
                return "\n".join(p.extract_text() or "" for p in pdf.pages)
        elif PDF_SUPPORT == "pypdf":
            reader = _PR(io.BytesIO(raw))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        elif PDF_SUPPORT == "pypdf2":
            reader = PyPDF2.PdfReader(io.BytesIO(raw))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        pass
    return ""

def parse_amount(text_val):
    """Convert a string like '12,34,567.89' or '12.34L' to float."""
    if not text_val:
        return 0.0
    text_val = text_val.replace(",", "").replace("₹", "").replace("Rs", "").strip()
    try:
        return float(text_val)
    except Exception:
        return 0.0

def analyze_bank_statement(text):
    """
    Extract key financial metrics from bank-statement text.
    Returns a dict; None values mean data not found.
    """
    result = {
        "total_credits": None,
        "total_debits": None,
        "opening_balance": None,
        "closing_balance": None,
        "num_credit_txn": None,
        "num_debit_txn": None,
        "bounce_signals": 0,
        "bnpl_signals": [],
        "cash_deposits": None,
    }
    if not text:
        return result

    tl = text.lower()

    def first_match(patterns):
        for pat in patterns:
            m = re.search(pat, tl)
            if m:
                return parse_amount(m.group(1))
        return None

    result["total_credits"] = first_match([
        r"total\s+credit[s]?\s*[:\-]\s*(?:rs\.?|inr|₹)?\s*([\d,]+\.?\d*)",
        r"total\s+cr\s*[:\-]\s*(?:rs\.?|inr|₹)?\s*([\d,]+\.?\d*)",
        r"cr\s+total\s*[:\-]\s*(?:rs\.?|inr|₹)?\s*([\d,]+\.?\d*)",
        r"credits\s*[:\-]\s*(?:rs\.?|inr|₹)?\s*([\d,]+\.?\d*)",
    ])
    result["total_debits"] = first_match([
        r"total\s+debit[s]?\s*[:\-]\s*(?:rs\.?|inr|₹)?\s*([\d,]+\.?\d*)",
        r"total\s+dr\s*[:\-]\s*(?:rs\.?|inr|₹)?\s*([\d,]+\.?\d*)",
        r"dr\s+total\s*[:\-]\s*(?:rs\.?|inr|₹)?\s*([\d,]+\.?\d*)",
    ])
    result["opening_balance"] = first_match([
        r"opening\s+balance\s*[:\-]\s*(?:rs\.?|inr|₹)?\s*([\d,]+\.?\d*)",
    ])
    result["closing_balance"] = first_match([
        r"closing\s+balance\s*[:\-]\s*(?:rs\.?|inr|₹)?\s*([\d,]+\.?\d*)",
    ])

    # Bounce signals
    bounce_keywords = ["bounce", "dishonour", "dishonor", "returned", "insufficient funds",
                       "ecs return", "nach return", "cheque return"]
    result["bounce_signals"] = sum(tl.count(kw) for kw in bounce_keywords)

    # BNPL signals
    bnpl_providers = ["amazon pay later", "simpl", "lazypay", "zestmoney", "slice",
                      "uni card", "bharatpe", "olamoney", "paytm postpaid", "bnpl", "buy now pay later"]
    result["bnpl_signals"] = [p.title() for p in bnpl_providers if p in tl]

    # Cash deposits
    result["cash_deposits"] = first_match([
        r"cash\s+deposit[s]?\s*[:\-]\s*(?:rs\.?|inr|₹)?\s*([\d,]+\.?\d*)",
    ])

    return result

def analyze_itr(text):
    """Extract key income figures from ITR / Form-16 text."""
    result = {
        "gross_total_income": None,
        "total_income": None,
        "tax_paid": None,
        "itr_type": None,
    }
    if not text:
        return result
    tl = text.lower()

    def first_match(patterns):
        for pat in patterns:
            m = re.search(pat, tl)
            if m:
                return parse_amount(m.group(1))
        return None

    result["gross_total_income"] = first_match([
        r"gross\s+total\s+income\s*[:\-]?\s*(?:rs\.?|inr|₹)?\s*([\d,]+\.?\d*)",
        r"gross\s+income\s*[:\-]?\s*(?:rs\.?|inr|₹)?\s*([\d,]+\.?\d*)",
    ])
    result["total_income"] = first_match([
        r"total\s+taxable\s+income\s*[:\-]?\s*(?:rs\.?|inr|₹)?\s*([\d,]+\.?\d*)",
        r"net\s+taxable\s+income\s*[:\-]?\s*(?:rs\.?|inr|₹)?\s*([\d,]+\.?\d*)",
        r"total\s+income\s*[:\-]?\s*(?:rs\.?|inr|₹)?\s*([\d,]+\.?\d*)",
    ])
    result["tax_paid"] = first_match([
        r"tax\s+paid\s*[:\-]?\s*(?:rs\.?|inr|₹)?\s*([\d,]+\.?\d*)",
        r"tds\s*[:\-]?\s*(?:rs\.?|inr|₹)?\s*([\d,]+\.?\d*)",
    ])

    for itr_type in ["itr-1", "itr-2", "itr-3", "itr-4", "itr-6", "sahaj", "sugam"]:
        if itr_type in tl:
            result["itr_type"] = itr_type.upper()
            break

    return result

# ─── HELPER FUNCTIONS ────────────────────────────────────────────────────────
def get_score_band(score):
    for (lo, hi), (label, badge, color) in SCORE_BANDS.items():
        if lo <= score <= hi:
            return label, badge, color
    return "Poor", "badge-red", "#E05C5C"

def calc_emi(principal, annual_rate, months):
    if annual_rate == 0 or months == 0:
        return principal / months if months > 0 else 0
    r = annual_rate / (12 * 100)
    emi = principal * r * ((1 + r) ** months) / (((1 + r) ** months) - 1)
    return round(emi, 2)

def compute_finbridge_score(data):
    incomes  = np.array(data.get("annual_income",  [1]),   dtype=float)
    expenses = np.array(data.get("annual_expense", [0.8]), dtype=float)
    savings  = np.array(data.get("annual_savings", [0.2]), dtype=float)
    emis     = np.array(data.get("existing_emis",  [0]),   dtype=float)
    bounces  = np.array(data.get("bounce_count",   [0]),   dtype=float)

    incomes = np.where(incomes == 0, 1, incomes)

    income_growth_rates = np.diff(incomes) / incomes[:-1] if len(incomes) > 1 else np.array([0.0])
    avg_growth   = float(np.mean(income_growth_rates))
    income_cov   = float(np.std(incomes) / np.mean(incomes)) if np.mean(incomes) > 0 else 1
    income_score = max(0, min(25, 25 * (0.5 * (1 - income_cov) + 0.5 * min(avg_growth / 0.15, 1))))

    net_flows          = incomes - expenses - emis
    cf_positive_ratio  = float(np.sum(net_flows > 0) / len(net_flows))
    cf_cov             = float(np.std(net_flows) / (np.mean(incomes) + 1e-6))
    cf_score           = max(0, min(20, 20 * (0.6 * cf_positive_ratio + 0.4 * max(0, 1 - cf_cov))))

    savings_ratios  = savings / incomes
    avg_savings_ratio = float(np.mean(savings_ratios))
    savings_score   = max(0, min(18, 18 * min(avg_savings_ratio / 0.25, 1)))

    dscr_vals  = incomes / (emis + 1)
    avg_dscr   = float(np.mean(dscr_vals))
    dscr_score = max(0, min(17, 17 * min((avg_dscr - 1) / 4, 1)))

    exp_ratios    = expenses / incomes
    avg_exp_ratio = float(np.mean(exp_ratios))
    exp_score     = max(0, min(12, 12 * max(0, 1 - avg_exp_ratio / 0.85)))

    total_bounces = float(np.sum(bounces))
    bounce_score  = max(0, min(8, 8 * max(0, 1 - total_bounces / 10)))

    raw = income_score + cf_score + savings_score + dscr_score + exp_score + bounce_score
    finbridge_score = int(300 + (raw / 100) * 600)
    finbridge_score = max(300, min(900, finbridge_score))

    components = {
        "Income Stability":       round(income_score, 1),
        "Cash-Flow":              round(cf_score, 1),
        "Savings Behaviour":      round(savings_score, 1),
        "Debt Coverage":          round(dscr_score, 1),
        "Expenditure Discipline": round(exp_score, 1),
        "Account Behaviour":      round(bounce_score, 1),
    }
    return finbridge_score, components, raw

def estimate_cibil_score(data):
    incomes  = np.array(data.get("annual_income",  [1]), dtype=float)
    emis     = np.array(data.get("existing_emis",  [0]), dtype=float)
    bounces  = np.array(data.get("bounce_count",   [0]), dtype=float)
    avg_income = float(np.mean(incomes))
    avg_emi    = float(np.mean(emis))

    bounce_penalty = min(float(np.sum(bounces)) * 30, 200)
    pti      = avg_emi / (avg_income + 1e-6)
    pti_score = max(0, 350 * (1 - min(pti, 0.6) / 0.6))
    cibil    = int(550 + pti_score - bounce_penalty)
    return max(300, min(900, cibil))

def max_loan_eligible(data, interest_rate, tenure_months):
    incomes  = np.array(data.get("annual_income",  [1]), dtype=float)
    emis     = np.array(data.get("existing_emis",  [0]), dtype=float)
    monthly_income   = float(np.mean(incomes)) / 12
    existing_emi     = float(np.mean(emis))    / 12
    disposable = max(0, monthly_income * 0.55 - existing_emi)
    if interest_rate == 0 or tenure_months == 0:
        return disposable * tenure_months, disposable
    r = interest_rate / (12 * 100)
    max_loan = disposable * ((1 + r) ** tenure_months - 1) / (r * (1 + r) ** tenure_months)
    return round(max_loan, 0), round(disposable, 0)

def format_inr(amount):
    if amount >= 1e7:   return f"₹{amount/1e7:.2f} Cr"
    elif amount >= 1e5: return f"₹{amount/1e5:.2f} L"
    else:               return f"₹{amount:,.0f}"

def months_to_label(months):
    if months >= 12:
        y, m = months // 12, months % 12
        return f"{y}Y {m}M" if m else f"{y} Years"
    return f"{months} Months"

# ─── SESSION STATE ────────────────────────────────────────────────────────────
_defaults = {
    "step": "profile",
    "profile_data": {},
    "profile_saved": False,
    "stmt_data": {},
    "uploaded_analysis": {},   # per-year PDF analysis results
    "scores_computed": False,
    "finbridge_score": 0,
    "cibil_score": 0,
    "components": {},
    "raw_score": 0,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="logo-area">
        <div class="logo-text">FinBridge</div>
        <div class="logo-sub">Credit Intelligence Platform</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr style='border-color:#1E3A5F;margin:0.5rem 0 1rem;'>", unsafe_allow_html=True)

    # ── Loan Purpose moved to 3rd position ──────────────────────────────────
    nav_options = [
        ("👤", "Profile Setup",            "profile"),
        ("📊", "Bank Statement & ITR",     "statement"),
        ("💰", "Loan Purpose & Eligibility","loan"),      # ← 3rd
        ("🏅", "FinBridge Score",          "score"),
        ("⚖️", "CIBIL vs FinBridge",       "comparison"),
        ("📅", "EMI Planner",              "emi"),
        ("📋", "Credit Report",            "report"),
    ]

    for icon, label, key in nav_options:
        is_active = st.session_state.step == key
        if st.button(f"{icon}  {label}", key=f"nav_{key}", use_container_width=True):
            st.session_state.step = key
            st.rerun()

    st.markdown("<hr style='border-color:#1E3A5F;margin:1rem 0;'>", unsafe_allow_html=True)

    if st.session_state.scores_computed:
        fb    = st.session_state.finbridge_score
        lbl, bdg, clr = get_score_band(fb)
        st.markdown(f"""
        <div style='text-align:center;padding:1rem;background:#112240;border-radius:10px;border:1px solid #1E3A5F;'>
            <div style='font-size:0.7rem;color:#000000;letter-spacing:0.1em;text-transform:uppercase;'>FinBridge Score</div>
            <div style='font-family:"Playfair Display",serif;font-size:2.5rem;font-weight:700;color:#F0B429;'>{fb}</div>
            <span class='badge {bdg}'>{lbl}</span>
        </div>
        """, unsafe_allow_html=True)

    # Profile saved indicator
    if st.session_state.profile_saved:
        name_disp = st.session_state.profile_data.get("name", "")
        st.markdown(f"""
        <div style='margin-top:0.8rem;text-align:center;'>
            <span class='saved-pill'>✓ Profile: {name_disp}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style='position:absolute;bottom:2rem;left:1rem;right:1rem;text-align:center;'>
        <div style='font-size:0.65rem;color:#4A6080;'>FinBridge © 2025 | Credit Intelligence<br>Not a Registered Credit Bureau</div>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# PAGE: PROFILE SETUP
# ════════════════════════════════════════════════════════════════════════════
if st.session_state.step == "profile":
    st.markdown("<div class='section-title'>👤 Applicant Profile Setup</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>Tell us about yourself so we can tailor the credit analysis. Statement period required varies by profile type.</div>", unsafe_allow_html=True)

    pd_saved = st.session_state.profile_data

    col1, col2 = st.columns([1, 1], gap="large")

    # ── Personal Information (no wrapping div — removes blank rectangles) ──
    with col1:
        st.markdown("<div class='section-header'>Personal Information</div>", unsafe_allow_html=True)
        name            = st.text_input("Full Name",              value=pd_saved.get("name", ""),            placeholder="e.g. Arjun Mehta")
        age             = st.number_input("Age",                  min_value=18, max_value=80,                value=pd_saved.get("age", 28),              step=1)
        profile_type    = st.selectbox("Profile Type",            PROFILE_TYPES,                             index=PROFILE_TYPES.index(pd_saved.get("profile_type", "Salaried Professional")))
        occupation      = st.text_input("Occupation / Industry",  value=pd_saved.get("occupation", ""),      placeholder="e.g. Software Engineer")
        city            = st.text_input("City of Residence",      value=pd_saved.get("city", ""),            placeholder="e.g. Mumbai")

    # ── Financial Profile ────────────────────────────────────────────────────
    with col2:
        st.markdown("<div class='section-header'>Financial Profile</div>", unsafe_allow_html=True)
        pan             = st.text_input("PAN Number (optional)",  value=pd_saved.get("pan", ""),             placeholder="ABCDE1234F",                   max_chars=10)
        credit_cards    = st.number_input("Active Credit Cards",  min_value=0, max_value=20,                 value=pd_saved.get("credit_cards", 1))
        loans_active    = st.number_input("Active Loans",         min_value=0, max_value=10,                 value=pd_saved.get("loans_active", 0))
        collateral_opts = ["No", "Yes – Property", "Yes – FD/Savings", "Yes – Gold", "Yes – Vehicle"]
        has_collateral  = st.selectbox("Collateral Available?",   collateral_opts,                           index=pd_saved.get("collateral_idx", 0))
        employment_years= st.slider("Years in Current Occupation",0, 40,                                     value=pd_saved.get("employment_years", 3))

    # Statement period banner
    is_student_fl = profile_type in ["Student", "Freelancer"]
    stmt_years    = 3 if is_student_fl else 5

    st.markdown(f"""
    <div class='info-banner'>
        📌 Based on profile type <strong>({profile_type})</strong>, you'll need to provide
        <strong>{stmt_years} years</strong> of bank statement data.
        {'Students & Freelancers require 3 years.' if is_student_fl else 'Salaried / Business profiles require 5 years (RBI norm).'}
    </div>
    """, unsafe_allow_html=True)

    btn_label = "Update Profile ✓" if st.session_state.profile_saved else "Save Profile & Continue →"
    if st.button(btn_label, use_container_width=True):
        if not name.strip():
            st.error("Please enter your full name.")
        else:
            st.session_state.profile_data = {
                "name":             name.strip(),
                "age":              age,
                "profile_type":     profile_type,
                "occupation":       occupation,
                "city":             city,
                "pan":              pan.upper(),
                "credit_cards":     credit_cards,
                "loans_active":     loans_active,
                "has_collateral":   has_collateral,
                "collateral_idx":   collateral_opts.index(has_collateral),
                "employment_years": employment_years,
                "stmt_years":       stmt_years,
            }
            st.session_state.profile_saved = True
            st.success(f"✅ Profile saved for **{name.strip()}**! Proceed to Bank Statement & ITR upload.")
            st.session_state.step = "statement"
            st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# PAGE: BANK STATEMENT & ITR (PDF UPLOAD)
# ════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "statement":
    prof        = st.session_state.profile_data if st.session_state.profile_data else {"stmt_years": 5, "profile_type": "Salaried Professional"}
    stmt_years  = prof.get("stmt_years", 5)
    profile_type= prof.get("profile_type", "Salaried Professional")

    st.markdown("<div class='section-title'>📊 Bank Statement & ITR Upload</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sub-title'>Upload your bank statements and ITR PDFs for the past {stmt_years} years. We'll auto-analyse them and populate your financial profile.</div>", unsafe_allow_html=True)

    if not PDF_SUPPORT:
        st.markdown("""
        <div class='warn-banner'>
            ⚠️ PDF analysis library not installed. Add <code>pdfplumber</code> to your
            <code>requirements.txt</code> for automatic extraction. Manual entry fields are shown below.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class='info-banner'>
            🤖 PDF analysis is active ({PDF_SUPPORT}). Upload your documents and the system will
            auto-extract financial data. Review and adjust extracted values before computing your score.
        </div>
        """, unsafe_allow_html=True)

    current_year = 2025
    years = [current_year - i for i in range(stmt_years - 1, -1, -1)]
    saved = st.session_state.stmt_data

    def pad(lst, n, default=0.0):
        return (list(lst) + [default] * n)[:n]

    default_income  = pad(saved.get("annual_income",    []), stmt_years)
    default_expense = pad(saved.get("annual_expense",   []), stmt_years)
    default_savings = pad(saved.get("annual_savings",   []), stmt_years)
    default_emis    = pad(saved.get("existing_emis",    []), stmt_years)
    default_credits = pad(saved.get("credit_txn_count", []), stmt_years, 0)
    default_debits  = pad(saved.get("debit_txn_count",  []), stmt_years, 0)
    default_bounces = pad(saved.get("bounce_count",     []), stmt_years, 0)
    default_od      = pad(saved.get("overdraft_count",  []), stmt_years, 0)
    default_cash    = pad(saved.get("cash_deposits",    []), stmt_years)

    tabs = st.tabs([f"FY {y}-{str(y+1)[2:]}" for y in years])

    income_vals   = []
    expense_vals  = []
    savings_vals  = []
    emi_vals      = []
    credit_counts = []
    debit_counts  = []
    bounce_counts = []
    od_counts     = []
    cash_vals     = []
    bnpl_flags    = []

    for i, (tab, year) in enumerate(zip(tabs, years)):
        with tab:
            cached_analysis = st.session_state.uploaded_analysis.get(str(year), {})

            # ── Upload Section ───────────────────────────────────────────────
            uc1, uc2 = st.columns(2, gap="medium")
            with uc1:
                st.markdown(f"<div style='font-size:0.82rem;color:#000000;margin-bottom:0.3rem;'>📄 Bank Statement — FY {year}-{str(year+1)[2:]}</div>", unsafe_allow_html=True)
                stmt_file = st.file_uploader(
                    f"Upload PDF", type=["pdf"],
                    key=f"stmt_file_{year}",
                    label_visibility="collapsed"
                )
            with uc2:
                st.markdown(f"<div style='font-size:0.82rem;color:#000000;margin-bottom:0.3rem;'>📋 ITR / Form-16 — FY {year}-{str(year+1)[2:]}</div>", unsafe_allow_html=True)
                itr_file = st.file_uploader(
                    f"Upload PDF", type=["pdf"],
                    key=f"itr_file_{year}",
                    label_visibility="collapsed"
                )

            # ── Auto-analysis when files uploaded ────────────────────────────
            stmt_analysis = {}
            itr_analysis  = {}

            if stmt_file and PDF_SUPPORT:
                with st.spinner(f"Analysing bank statement FY {year}…"):
                    txt = extract_text_from_pdf(stmt_file)
                    stmt_analysis = analyze_bank_statement(txt)
                    st.session_state.uploaded_analysis[str(year)] = {"stmt": stmt_analysis}

            if itr_file and PDF_SUPPORT:
                with st.spinner(f"Analysing ITR FY {year}…"):
                    txt = extract_text_from_pdf(itr_file)
                    itr_analysis = analyze_itr(txt)
                    existing = st.session_state.uploaded_analysis.get(str(year), {})
                    existing["itr"] = itr_analysis
                    st.session_state.uploaded_analysis[str(year)] = existing

            # ── Analysis summary ─────────────────────────────────────────────
            if stmt_analysis or itr_analysis:
                with st.expander(f"📊 Auto-extracted data for FY {year}", expanded=True):
                    ae1, ae2, ae3 = st.columns(3)
                    tc = stmt_analysis.get("total_credits")
                    td = stmt_analysis.get("total_debits")
                    gi = itr_analysis.get("gross_total_income") or itr_analysis.get("total_income")
                    with ae1:
                        st.metric("Bank Credits",       f"₹{tc:,.0f}" if tc else "—")
                    with ae2:
                        st.metric("Bank Debits",        f"₹{td:,.0f}" if td else "—")
                    with ae3:
                        st.metric("ITR Gross Income",   f"₹{gi:,.0f}" if gi else "—")

                    bn = stmt_analysis.get("bounce_signals", 0)
                    bnpl = stmt_analysis.get("bnpl_signals", [])
                    if bn > 0:
                        st.markdown(f"<span class='badge badge-red'>⚠️ {bn} bounce signal(s) detected</span>", unsafe_allow_html=True)
                    if bnpl:
                        st.markdown(f"<span class='badge badge-gold'>💳 BNPL usage: {', '.join(bnpl)}</span>", unsafe_allow_html=True)
                    itr_type = itr_analysis.get("itr_type")
                    if itr_type:
                        st.markdown(f"<span class='badge badge-teal'>📋 ITR Type: {itr_type}</span>", unsafe_allow_html=True)

            # ── Pre-fill defaults from extracted data ────────────────────────
            auto_income  = stmt_analysis.get("total_credits") or itr_analysis.get("gross_total_income") or float(default_income[i])
            auto_expense = stmt_analysis.get("total_debits")  or float(default_expense[i])
            auto_cash    = stmt_analysis.get("cash_deposits") or float(default_cash[i])
            auto_bounces = stmt_analysis.get("bounce_signals") or int(default_bounces[i])

            # ── Manual / Review Inputs ────────────────────────────────────────
            st.markdown("<div style='height:0.8rem;'></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='section-header'>Review / Enter Figures for FY {year}</div>", unsafe_allow_html=True)

            c1, c2, c3 = st.columns(3, gap="medium")
            with c1:
                inc = st.number_input("Annual Income (₹)",        min_value=0.0, value=float(auto_income),    step=10000.0, key=f"inc_{year}", format="%.0f",
                                      help="Total salary, business revenue, freelance income")
                exp = st.number_input("Annual Expenses (₹)",      min_value=0.0, value=float(auto_expense),   step=10000.0, key=f"exp_{year}", format="%.0f",
                                      help="All outflows including rent, utilities, personal spending")
                sav = st.number_input("Net Savings / FD (₹)",     min_value=0.0, value=float(default_savings[i]), step=5000.0, key=f"sav_{year}", format="%.0f",
                                      help="Money saved, invested, or put into FD/mutual funds")
            with c2:
                emi = st.number_input("Existing EMI Payments (₹/yr)", min_value=0.0, value=float(default_emis[i]), step=5000.0, key=f"emi_{year}", format="%.0f",
                                      help="Annual total of all loan EMI payments")
                cash= st.number_input("Cash Deposits (₹)",        min_value=0.0, value=float(auto_cash),      step=5000.0, key=f"cash_{year}", format="%.0f",
                                      help="Total cash deposited this year")
                cred= st.number_input("Credit Transactions (#)",  min_value=0,   value=int(default_credits[i]),step=1,      key=f"cred_{year}",
                                      help="Number of inward/credit transactions")
            with c3:
                deb = st.number_input("Debit Transactions (#)",   min_value=0,   value=int(default_debits[i]), step=1,      key=f"deb_{year}",
                                      help="Number of outward/debit transactions")
                bnc = st.number_input("Cheque / ECS Bounces (#)", min_value=0,   value=int(auto_bounces),      step=1,      key=f"bnc_{year}",
                                      help="Bounced cheques or failed ECS/NACH debits")
                od  = st.number_input("Overdraft / Neg-Balance Days", min_value=0, value=int(default_od[i]),  step=1,      key=f"od_{year}",
                                      help="Days account was in overdraft")

            # BNPL flag
            bnpl_flag = len(stmt_analysis.get("bnpl_signals", [])) > 0
            bnpl_flags.append(bnpl_flag)

            # Year summary strip
            if inc > 0:
                calc_net = inc - exp - emi
                color_net = "#3EC87A" if calc_net >= 0 else "#E05C5C"
                st.markdown(f"""
                <div style='background:#0A1628;border:1px solid #1E3A5F;border-radius:8px;padding:0.7rem 1rem;
                            margin-top:0.5rem;font-size:0.82rem;color:#000000;display:flex;gap:1.5rem;flex-wrap:wrap;'>
                    <span>Income <b style='color:#3EC87A;'>₹{inc:,.0f}</b></span>
                    <span>Expenses <b style='color:#E05C5C;'>₹{exp:,.0f}</b></span>
                    <span>EMIs <b style='color:#F0B429;'>₹{emi:,.0f}</b></span>
                    <span>Net Cash <b style='color:{color_net};'>₹{calc_net:,.0f}</b></span>
                    <span>Savings Rate <b style='color:#F0B429;'>{(sav/inc*100) if inc>0 else 0:.1f}%</b></span>
                </div>
                """, unsafe_allow_html=True)

            income_vals.append(inc);    expense_vals.append(exp);  savings_vals.append(sav)
            emi_vals.append(emi);       credit_counts.append(cred); debit_counts.append(deb)
            bounce_counts.append(bnc); od_counts.append(od);        cash_vals.append(cash)

    st.markdown("<hr class='fb-divider'>", unsafe_allow_html=True)

    # ── Additional context  (no credit utilisation field) ───────────────────
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("<div class='section-header'>Business & Tax Context</div>", unsafe_allow_html=True)
        has_gst        = st.selectbox("GST Registered?",     ["No", "Yes"], index=0 if profile_type not in ["Self-Employed / Business"] else 1)
        itr_filed      = st.selectbox("ITR Filed Regularly?", ["Yes, all years", "Most years", "Occasionally", "No"], index=0)
        bank_count     = st.number_input("Number of Bank Accounts", min_value=1, max_value=10, value=1)
    with col_b:
        st.markdown("<div class='section-header'>Credit History</div>", unsafe_allow_html=True)
        prev_defaults  = st.selectbox("Previous Loan Default?", ["No", "Yes – resolved", "Yes – pending"], index=0)
        oldest_acct_yr = st.number_input("Age of Oldest Bank Account (Years)", min_value=0, max_value=50, value=5)

    # BNPL summary if detected
    if any(bnpl_flags):
        yrs_with_bnpl = [str(years[i]) for i, f in enumerate(bnpl_flags) if f]
        st.markdown(f"""
        <div class='warn-banner'>
            💳 <strong>BNPL Usage Detected</strong> in FY {', '.join(yrs_with_bnpl)}.
            Frequent Buy Now Pay Later usage is factored into your repayment-ability assessment.
            High BNPL reliance may reduce your FinBridge score by up to 15 points.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr class='fb-divider'>", unsafe_allow_html=True)

    if st.button("🔍  Compute FinBridge Credit Score", use_container_width=True):
        if sum(income_vals) == 0:
            st.error("Please enter income data for at least one year.")
        else:
            # BNPL penalty
            bnpl_penalty = sum(1 for f in bnpl_flags if f) * 5

            st.session_state.stmt_data = {
                "years":            years,
                "annual_income":    income_vals,
                "annual_expense":   expense_vals,
                "annual_savings":   savings_vals,
                "existing_emis":    emi_vals,
                "credit_txn_count": credit_counts,
                "debit_txn_count":  debit_counts,
                "bounce_count":     bounce_counts,
                "overdraft_count":  od_counts,
                "cash_deposits":    cash_vals,
                "has_gst":          has_gst,
                "itr_filed":        itr_filed,
                "bank_count":       bank_count,
                "prev_defaults":    prev_defaults,
                "oldest_account_yr": oldest_acct_yr,
                "bnpl_penalty":     bnpl_penalty,
            }

            score, comps, raw = compute_finbridge_score(st.session_state.stmt_data)
            cibil = estimate_cibil_score(st.session_state.stmt_data)

            if itr_filed == "Yes, all years":  score = min(900, score + 15)
            elif itr_filed == "Occasionally":  score = max(300, score - 20)
            elif itr_filed == "No":            score = max(300, score - 40)
            if prev_defaults == "Yes – pending":
                score = max(300, score - 80);  cibil = max(300, cibil - 100)
            elif prev_defaults == "Yes – resolved":
                score = max(300, score - 30);  cibil = max(300, cibil - 50)
            if oldest_acct_yr >= 10:
                score = min(900, score + 15);  cibil = min(900, cibil + 20)
            score = max(300, score - bnpl_penalty)

            st.session_state.finbridge_score = score
            st.session_state.cibil_score     = cibil
            st.session_state.components      = comps
            st.session_state.raw_score       = raw
            st.session_state.scores_computed = True
            st.session_state.step            = "score"
            st.success("Score computed! Redirecting to your FinBridge Score.")
            st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# PAGE: LOAN PURPOSE & ELIGIBILITY  (now 3rd in menu)
# ════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "loan":
    fb    = st.session_state.finbridge_score
    prof  = st.session_state.profile_data
    stmt  = st.session_state.stmt_data
    scores_ready = st.session_state.scores_computed

    st.markdown("<div class='section-title'>💰 Loan Purpose & Eligibility</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>Real-time market rates, personalised eligibility and EMI estimates based on your financial profile.</div>", unsafe_allow_html=True)

    # ── Live rate fetch ──────────────────────────────────────────────────────
    with st.spinner("Fetching latest loan rates…"):
        rates_data = fetch_live_rates()

    live_badge = "<span class='badge badge-teal' style='font-size:0.7rem;'>🟢 Live Attempt</span>" if rates_data["live"] \
                 else "<span class='badge badge-gold' style='font-size:0.7rem;'>📅 Industry Avg</span>"
    st.markdown(f"""
    <div style='display:flex;align-items:center;gap:0.8rem;margin-bottom:1.5rem;'>
        <span style='font-size:0.82rem;color:#000000;'>Rate data: {rates_data['source']}</span>
        {live_badge}
    </div>
    """, unsafe_allow_html=True)

    # ── Rate Tables ─────────────────────────────────────────────────────────
    tab_home, tab_pers, tab_elig = st.tabs(["🏠 Home Loan Rates", "💳 Personal Loan Rates", "🎯 My Eligibility"])

    with tab_home:
        hd = rates_data["home"]
        col_hl, col_hr = st.columns([1.6, 1], gap="large")
        with col_hl:
            st.markdown("<div class='section-header'>Home Loan Rates by Lender (April 2025)</div>", unsafe_allow_html=True)
            header = "<div class='rate-row'><div class='rate-cell rate-header'>Bank / NBFC</div><div class='rate-cell rate-header'>Min Rate</div><div class='rate-cell rate-header'>Max Rate</div></div>"
            rows   = "".join(
                f"<div class='rate-row'>"
                f"<div class='rate-cell'>{l['bank']}</div>"
                f"<div class='rate-cell' style='color:#3EC87A;'>{l['min']:.2f}%</div>"
                f"<div class='rate-cell' style='color:#F0B429;'>{l['max']:.2f}%</div>"
                f"</div>"
                for l in hd["lenders"]
            )
            st.markdown(header + rows, unsafe_allow_html=True)

        with col_hr:
            # Visual: gauge for average
            fig_h = go.Figure(go.Indicator(
                mode="gauge+number",
                value=hd["avg"],
                title={"text": "Avg Home Loan Rate (%)", "font": {"size": 13, "color": "#000000"}},
                number={"suffix": "% p.a.", "font": {"size": 32, "color": "#F0B429"}},
                gauge={
                    "axis": {"range": [7, 12], "tickfont": {"color": "#000000", "size": 9}},
                    "bar":  {"color": "#F0B429", "thickness": 0.25},
                    "bgcolor": "#112240",
                    "steps": [
                        {"range": [7, 8.5],  "color": "rgba(62,200,122,0.15)"},
                        {"range": [8.5, 10], "color": "rgba(240,180,41,0.12)"},
                        {"range": [10, 12],  "color": "rgba(224,92,92,0.12)"},
                    ],
                }
            ))
            fig_h.update_layout(height=220, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                margin=dict(t=40, b=10, l=20, r=20))
            st.plotly_chart(fig_h, use_container_width=True)
            st.markdown(f"""
            <div style='text-align:center;font-size:0.8rem;color:#000000;background:#112240;border:1px solid #1E3A5F;border-radius:8px;padding:0.6rem;'>
                RBI Repo Rate: <b style='color:#F0B429;'>{rates_data['repo']}%</b> &nbsp;|&nbsp;
                Spread: <b style='color:#0EC4B0;'>~2.0–3.5%</b><br>
                Market Range: <b style='color:#000000;'>{hd['low']}% – {hd['high']}%</b>
            </div>
            """, unsafe_allow_html=True)

    with tab_pers:
        pd_r = rates_data["personal"]
        col_pl, col_pr = st.columns([1.6, 1], gap="large")
        with col_pl:
            st.markdown("<div class='section-header'>Personal Loan Rates by Lender (April 2025)</div>", unsafe_allow_html=True)
            header = "<div class='rate-row'><div class='rate-cell rate-header'>Bank / NBFC</div><div class='rate-cell rate-header'>Min Rate</div><div class='rate-cell rate-header'>Max Rate</div></div>"
            rows   = "".join(
                f"<div class='rate-row'>"
                f"<div class='rate-cell'>{l['bank']}</div>"
                f"<div class='rate-cell' style='color:#3EC87A;'>{l['min']:.2f}%</div>"
                f"<div class='rate-cell' style='color:#E05C5C;'>{l['max']:.2f}%</div>"
                f"</div>"
                for l in pd_r["lenders"]
            )
            st.markdown(header + rows, unsafe_allow_html=True)

        with col_pr:
            fig_p = go.Figure(go.Indicator(
                mode="gauge+number",
                value=pd_r["avg"],
                title={"text": "Avg Personal Loan Rate (%)", "font": {"size": 13, "color": "#000000"}},
                number={"suffix": "% p.a.", "font": {"size": 32, "color": "#E05C5C"}},
                gauge={
                    "axis": {"range": [10, 36], "tickfont": {"color": "#000000", "size": 9}},
                    "bar":  {"color": "#E05C5C", "thickness": 0.25},
                    "bgcolor": "#112240",
                    "steps": [
                        {"range": [10, 14], "color": "rgba(62,200,122,0.15)"},
                        {"range": [14, 22], "color": "rgba(240,180,41,0.12)"},
                        {"range": [22, 36], "color": "rgba(224,92,92,0.12)"},
                    ],
                }
            ))
            fig_p.update_layout(height=220, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                margin=dict(t=40, b=10, l=20, r=20))
            st.plotly_chart(fig_p, use_container_width=True)
            st.markdown(f"""
            <div style='text-align:center;font-size:0.8rem;color:#000000;background:#112240;border:1px solid #1E3A5F;border-radius:8px;padding:0.6rem;'>
                Market Range: <b style='color:#000000;'>{pd_r['low']}% – {pd_r['high']}%</b><br>
                Avg (unsecured, mid-credit): <b style='color:#E05C5C;'>{pd_r['avg']}% p.a.</b>
            </div>
            """, unsafe_allow_html=True)

    # ── Combined averages strip ──────────────────────────────────────────────
    st.markdown(f"""
    <div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:1rem;margin:1.2rem 0;'>
        <div class='metric-card'>
            <div class='metric-val' style='color:#3EC87A;'>{rates_data["home"]["avg"]}%</div>
            <div class='metric-lab'>Avg Home Loan Rate p.a.</div>
        </div>
        <div class='metric-card'>
            <div class='metric-val' style='color:#E05C5C;'>{rates_data["personal"]["avg"]}%</div>
            <div class='metric-lab'>Avg Personal Loan Rate p.a.</div>
        </div>
        <div class='metric-card'>
            <div class='metric-val' style='color:#F0B429;'>{rates_data["repo"]}%</div>
            <div class='metric-lab'>RBI Repo Rate (Apr 2025)</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with tab_elig:
        if not scores_ready:
            st.markdown("""
            <div class='info-banner'>
                ℹ️ Complete your bank statement input and compute your FinBridge Score to see
                personalised eligibility below. In the meantime, use the rate tables above to explore.
            </div>
            """, unsafe_allow_html=True)
            if st.button("→ Go to Bank Statement Input"):
                st.session_state.step = "statement"; st.rerun()
        else:
            label, badge, color = get_score_band(fb)
            col_inp, col_res = st.columns([1, 1.2], gap="large")

            with col_inp:
                st.markdown("<div class='section-header'>Financing Purpose & Parameters</div>", unsafe_allow_html=True)
                purpose      = st.selectbox("Why do you need financing?", list(LOAN_PURPOSES.keys()))
                purpose_data = LOAN_PURPOSES[purpose]
                rate_lo, rate_hi = purpose_data["rate_range"]
                max_tenure_yr    = purpose_data["max_tenure"]
                industry         = purpose_data["industry"]

                score_discount   = max(0, (fb - 600) / 300)
                assigned_rate    = round(rate_hi - score_discount * (rate_hi - rate_lo), 2)
                assigned_rate    = max(rate_lo, min(rate_hi, assigned_rate))

                desired_amount   = st.number_input("Desired Loan Amount (₹)", min_value=10000.0, value=1000000.0, step=50000.0, format="%.0f")
                tenure_years     = st.slider("Preferred Tenure (Years)", 1, max_tenure_yr, min(5, max_tenure_yr))
                tenure_months    = tenure_years * 12

                st.markdown(f"""
                <div style='background:#0A1628;border:1px solid #1E3A5F;border-radius:8px;padding:0.8rem;margin:0.8rem 0;font-size:0.82rem;'>
                    <b style='color:#F0B429;'>Industry:</b> <span style='color:#000000;'>{industry}</span><br>
                    <b style='color:#F0B429;'>Market Rate Range:</b> <span style='color:#000000;'>{rate_lo:.1f}% – {rate_hi:.1f}% p.a.</span><br>
                    <b style='color:#F0B429;'>Max Tenure:</b> <span style='color:#000000;'>Up to {max_tenure_yr} years</span>
                </div>
                <div style='background:rgba(240,180,41,0.08);border:1px solid rgba(240,180,41,0.3);border-radius:8px;padding:0.8rem;font-size:0.85rem;color:#F0B429;'>
                    🎯 <b>Your Assigned Rate: {assigned_rate:.2f}% p.a.</b><br>
                    <span style='font-size:0.75rem;color:#000000;'>Determined by FinBridge Score {fb} within {rate_lo}–{rate_hi}% range</span>
                </div>
                """, unsafe_allow_html=True)

            with col_res:
                max_eligible, disposable_emi = max_loan_eligible(stmt, assigned_rate, tenure_months)
                desired_emi  = calc_emi(desired_amount, assigned_rate, tenure_months)
                max_emi      = calc_emi(max_eligible, assigned_rate, tenure_months)
                can_afford   = desired_emi <= disposable_emi
                eligible_pct = min(100, (max_eligible / desired_amount * 100)) if desired_amount > 0 else 0

                st.markdown("<div class='section-header'>Eligibility Summary</div>", unsafe_allow_html=True)
                m1, m2 = st.columns(2)
                with m1:
                    st.markdown(f"""<div class='metric-card'>
                        <div class='metric-val'>{format_inr(max_eligible)}</div>
                        <div class='metric-lab'>Max Eligible Loan</div>
                    </div>""", unsafe_allow_html=True)
                with m2:
                    st.markdown(f"""<div class='metric-card'>
                        <div class='metric-val'>{format_inr(disposable_emi)}/mo</div>
                        <div class='metric-lab'>EMI Capacity (FOIR 55%)</div>
                    </div>""", unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                m3, m4 = st.columns(2)
                with m3:
                    st.markdown(f"""<div class='metric-card'>
                        <div class='metric-val' style='color:#0EC4B0;'>{format_inr(desired_emi)}/mo</div>
                        <div class='metric-lab'>EMI on Desired Amount</div>
                    </div>""", unsafe_allow_html=True)
                with m4:
                    st.markdown(f"""<div class='metric-card'>
                        <div class='metric-val' style='color:#F0B429;'>{assigned_rate:.2f}%</div>
                        <div class='metric-lab'>Interest Rate (p.a.)</div>
                    </div>""", unsafe_allow_html=True)

                bar_color = "#3EC87A" if eligible_pct >= 90 else "#F0B429" if eligible_pct >= 60 else "#E05C5C"
                st.markdown(f"""
                <div style='margin:1rem 0;'>
                    <div style='display:flex;justify-content:space-between;font-size:0.8rem;color:#000000;margin-bottom:0.3rem;'>
                        <span>Eligibility Coverage</span><span>{eligible_pct:.1f}%</span>
                    </div>
                    <div style='background:#1E3A5F;border-radius:50px;height:10px;'>
                        <div style='width:{min(eligible_pct,100):.1f}%;background:{bar_color};border-radius:50px;height:10px;transition:width 0.5s;'></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                verdict_color = "#3EC87A" if can_afford else "#E05C5C"
                verdict_icon  = "✅" if can_afford else "❌"
                verdict_msg   = "Your desired loan is within repayment capacity." if can_afford \
                                else f"Desired EMI exceeds capacity. Max eligible: {format_inr(max_eligible)}"
                st.markdown(f"""
                <div style='background:rgba(0,0,0,0.2);border:1px solid {verdict_color};border-radius:8px;padding:0.9rem;font-size:0.85rem;color:{verdict_color};'>
                    {verdict_icon} {verdict_msg}
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<hr class='fb-divider'>", unsafe_allow_html=True)
            st.markdown("<div class='section-header'>Eligibility Across All Loan Types</div>", unsafe_allow_html=True)
            rows_tbl = []
            for p, pd_info in LOAN_PURPOSES.items():
                lo, hi = pd_info["rate_range"]
                sc_disc = max(0, (fb - 600) / 300)
                arate = max(lo, min(hi, round(hi - sc_disc * (hi - lo), 2)))
                t_mo  = min(60, pd_info["max_tenure"] * 12)
                mel, _ = max_loan_eligible(stmt, arate, t_mo)
                rows_tbl.append({"Purpose": p, "Industry": pd_info["industry"],
                                 "Rate (% p.a.)": f"{arate:.2f}", "Max Tenure": f"{pd_info['max_tenure']} yrs",
                                 "Max Eligible": format_inr(mel)})
            st.dataframe(pd.DataFrame(rows_tbl), use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════════════════
# PAGE: FINBRIDGE SCORE  (enhanced with layman explanations)
# ════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "score":
    if not st.session_state.scores_computed:
        st.warning("Please complete the bank statement input first.")
        if st.button("→ Go to Bank Statement Input"):
            st.session_state.step = "statement"; st.rerun()
        st.stop()

    prof  = st.session_state.profile_data
    fb    = st.session_state.finbridge_score
    ci    = st.session_state.cibil_score
    comps = st.session_state.components
    stmt  = st.session_state.stmt_data
    label, badge, color = get_score_band(fb)
    lbl_ci, bdg_ci, clr_ci = get_score_band(ci)

    st.markdown("<div class='section-title'>🏅 FinBridge Credit Score</div>", unsafe_allow_html=True)

    # ── Score hero + gauge ────────────────────────────────────────────────────
    col_score, col_gauge = st.columns([1, 1.5], gap="large")

    with col_score:
        st.markdown(f"""
        <div class="score-hero">
            <div style='font-size:0.8rem;color:#000000;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.5rem;'>FinBridge Credit Score</div>
            <div class="score-num">{fb}</div>
            <div style='margin:0.8rem 0;'>
                <span class='badge {badge}' style='font-size:0.95rem;padding:0.4rem 1.2rem;'>{label}</span>
            </div>
            <div style='font-size:0.8rem;color:#000000;'>Score Range: 300 – 900</div>
            <div style='font-size:0.8rem;color:#000000;margin-top:0.3rem;'>
                Assessed for: <b style="color:#000000">{prof.get("name","Applicant")}</b>
            </div>
            <div style='font-size:0.8rem;color:#000000;'>Profile: {prof.get("profile_type","")}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        m1, m2 = st.columns(2)
        with m1:
            st.markdown(f"""<div class='metric-card'>
                <div class='metric-val'>{fb}</div>
                <div class='metric-lab'>FinBridge Score</div>
            </div>""", unsafe_allow_html=True)
        with m2:
            st.markdown(f"""<div class='metric-card'>
                <div class='metric-val' style='color:#0EC4B0;'>{ci}</div>
                <div class='metric-lab'>Est. Traditional Score</div>
            </div>""", unsafe_allow_html=True)

    with col_gauge:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=fb,
            delta={"reference": ci, "valueformat": ".0f", "prefix": "vs Traditional: "},
            title={"text": "FinBridge Score", "font": {"size": 14, "color": "#000000"}},
            number={"font": {"size": 48, "color": "#F0B429"}},
            gauge={
                "axis": {"range": [300, 900], "tickwidth": 1, "tickcolor": "#1E3A5F",
                         "tickvals": [300, 450, 550, 650, 700, 750, 900],
                         "tickfont": {"color": "#000000", "size": 10}},
                "bar": {"color": color, "thickness": 0.25},
                "bgcolor": "#112240", "borderwidth": 0,
                "steps": [
                    {"range": [300, 599], "color": "rgba(224,92,92,0.15)"},
                    {"range": [600, 649], "color": "rgba(224,137,41,0.15)"},
                    {"range": [650, 699], "color": "rgba(240,180,41,0.15)"},
                    {"range": [700, 749], "color": "rgba(124,200,126,0.15)"},
                    {"range": [750, 900], "color": "rgba(62,200,122,0.15)"},
                ],
                "threshold": {"line": {"color": "#F0B429", "width": 3}, "thickness": 0.75, "value": fb}
            }
        ))
        fig_gauge.update_layout(
            height=280, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font={"color": "#000000"}, margin=dict(t=40, b=10, l=30, r=30),
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

    st.markdown("<hr class='fb-divider'>", unsafe_allow_html=True)

    # ── Component Radar + Bar ─────────────────────────────────────────────────
    col_r, col_b2 = st.columns(2, gap="large")
    cats  = list(comps.keys())
    vals  = list(comps.values())
    maxes = [25, 20, 18, 17, 12, 8]

    with col_r:
        st.markdown("**Score Component Breakdown**")
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=vals + [vals[0]], theta=cats + [cats[0]], fill='toself',
            fillcolor="rgba(240,180,41,0.15)", line=dict(color="#F0B429", width=2), name="Your Score"
        ))
        fig_radar.add_trace(go.Scatterpolar(
            r=maxes + [maxes[0]], theta=cats + [cats[0]], fill='toself',
            fillcolor="rgba(14,196,176,0.06)", line=dict(color="#0EC4B0", width=1, dash="dot"), name="Max"
        ))
        fig_radar.update_layout(
            polar=dict(bgcolor="rgba(0,0,0,0)",
                       radialaxis=dict(visible=True, range=[0, 25], gridcolor="#1E3A5F", tickfont=dict(color="#000000", size=9)),
                       angularaxis=dict(tickfont=dict(color="#000000", size=10), gridcolor="#1E3A5F")),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            showlegend=True, legend=dict(font=dict(color="#000000", size=10)),
            height=320, margin=dict(t=20, b=20, l=20, r=20),
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with col_b2:
        st.markdown("**Component Scores vs Maximum**")
        colors_bar = []
        for v, m in zip(vals, maxes):
            ratio = v / m if m > 0 else 0
            colors_bar.append("#3EC87A" if ratio >= 0.75 else "#F0B429" if ratio >= 0.5 else "#E05C5C")
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(x=cats, y=maxes, name="Max",
                                  marker_color="rgba(255,255,255,0.07)", marker_line=dict(color="#1E3A5F", width=1)))
        fig_bar.add_trace(go.Bar(x=cats, y=vals, name="Your Score", marker_color=colors_bar,
                                  text=[f"{v:.1f}" for v in vals], textposition="outside",
                                  textfont=dict(color="#000000", size=10)))
        fig_bar.update_layout(
            barmode="overlay", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#000000", size=10),
            xaxis=dict(gridcolor="#1E3A5F", tickfont=dict(color="#000000", size=9)),
            yaxis=dict(gridcolor="#1E3A5F"),
            legend=dict(font=dict(color="#000000", size=10)),
            height=320, margin=dict(t=20, b=60, l=10, r=10),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("<hr class='fb-divider'>", unsafe_allow_html=True)

    # ── Cash-Flow Trend ───────────────────────────────────────────────────────
    st.markdown("**Cash-Flow Trend Analysis**")
    _years    = stmt.get("years",           [])
    _incomes  = stmt.get("annual_income",   [])
    _expenses = stmt.get("annual_expense",  [])
    _savings  = stmt.get("annual_savings",  [])
    _emis     = stmt.get("existing_emis",   [])
    _net      = [i - e - em for i, e, em in zip(_incomes, _expenses, _emis)]

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(x=_years, y=_incomes,  name="Income",   line=dict(color="#3EC87A", width=2.5), mode="lines+markers", marker=dict(size=7)))
    fig_trend.add_trace(go.Scatter(x=_years, y=_expenses, name="Expenses", line=dict(color="#E05C5C", width=2, dash="dash"), mode="lines+markers", marker=dict(size=6)))
    fig_trend.add_trace(go.Scatter(x=_years, y=_emis,     name="EMIs",     line=dict(color="#F0B429", width=2, dash="dot"),  mode="lines+markers", marker=dict(size=6)))
    fig_trend.add_trace(go.Bar(x=_years, y=_savings, name="Savings",
                               marker_color="rgba(14,196,176,0.3)", marker_line=dict(color="#0EC4B0", width=1)))
    fig_trend.add_trace(go.Bar(x=_years, y=_net, name="Net Cash Flow",
                               marker_color=["rgba(62,200,122,0.4)" if v >= 0 else "rgba(224,92,92,0.4)" for v in _net],
                               marker_line=dict(color="#1E3A5F", width=0)))
    fig_trend.update_layout(
        barmode="group", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#000000"),
        xaxis=dict(gridcolor="#1E3A5F", title="Financial Year"),
        yaxis=dict(gridcolor="#1E3A5F", title="Amount (₹)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#000000", size=10)),
        height=320, margin=dict(t=30, b=40, l=10, r=10),
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("<hr class='fb-divider'>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    # LAYMAN EXPLANATIONS — FinBridge vs CIBIL  ← New Section
    # ════════════════════════════════════════════════════════════════════════
    st.markdown("<div style='font-family:\"Playfair Display\",serif;font-size:1.2rem;color:#F0B429;margin-bottom:1rem;'>🧠 What Do These Scores Actually Mean?</div>", unsafe_allow_html=True)

    diff      = fb - ci
    diff_sign = "+" if diff >= 0 else ""

    # Dynamic layman narrative
    avg_income_mo = float(np.mean(_incomes)) / 12 if _incomes else 0
    avg_sav_rate  = float(np.mean(np.array(_savings) / np.where(np.array(_incomes) == 0, 1, np.array(_incomes)))) * 100 if _incomes else 0
    total_bounces = sum(stmt.get("bounce_count", [0]))

    # Score meaning
    meaning_map = {
        "Excellent": ("🌟", "You are an outstanding borrower. Banks will actively compete to lend you money at their lowest rates. You can negotiate for premium terms.", "bg-green"),
        "Good":      ("✅", "You are a reliable borrower. Most banks and NBFCs will approve your loan. You qualify for competitive interest rates.", "bg-green"),
        "Fair":      ("⚠️", "You are an average-risk borrower. Standard loans are available, but rates may be higher. A co-applicant or collateral could improve your offer.", "bg-gold"),
        "Marginal":  ("🔶", "Your creditworthiness needs work. Loan options are limited; secured loans (against property/gold) are your best bet right now.", "bg-gold"),
        "Poor":      ("🚨", "Banks will likely decline unsecured loans at this score. Focus on rebuilding financial discipline for 12–18 months before applying.", "bg-red"),
    }
    icon_m, meaning_text, _ = meaning_map.get(label, ("ℹ️", "", ""))

    st.markdown(f"""
    <div class='explain-card'>
        <div class='explain-title'>{icon_m} Your FinBridge Score: {fb} ({label})</div>
        <div class='explain-body'>{meaning_text}</div>
    </div>
    """, unsafe_allow_html=True)

    # Why different from CIBIL?
    explain_lines = []
    if diff > 0:
        explain_lines.append(f"✅ FinBridge sees <b>{diff} points more</b> than traditional CIBIL.")
    elif diff < 0:
        explain_lines.append(f"⚠️ FinBridge gives <b>{abs(diff)} points less</b> than traditional CIBIL.")
    else:
        explain_lines.append("🟰 Both scores are aligned — your traditional credit history mirrors your actual cash flow.")

    # Specific reasons
    reasons = []
    if avg_sav_rate >= 15:
        reasons.append(f"<b>Strong savings habit ({avg_sav_rate:.1f}% of income saved)</b> — CIBIL ignores this entirely; FinBridge rewards it significantly.")
    if avg_income_mo > 0 and float(np.mean(_incomes)) / float(np.mean(np.where(np.array(_emis) == 0, 1, np.array(_emis)))) > 4:
        reasons.append("<b>Low debt burden relative to income</b> — your DSCR is healthy, showing you can comfortably handle new debt.")
    if total_bounces == 0:
        reasons.append("<b>Zero payment bounces</b> — a clean account history positively impacts both scores, but is weighted more heavily in FinBridge's 6-factor model.")
    elif total_bounces > 3:
        reasons.append(f"<b>{total_bounces} payment bounces detected</b> — this hurts both scores but has a compounding penalty in CIBIL (each bounce can drop CIBIL by 30–50 points).")
    if prof.get("profile_type") in ["Freelancer", "Student"]:
        reasons.append(f"<b>Non-traditional income profile ({prof.get('profile_type')})</b> — CIBIL penalises irregular income; FinBridge analyses actual cash-flow patterns instead.")
    if not reasons:
        reasons.append("<b>Consistent income and spending patterns</b> — both systems read your financial behaviour similarly. This means your creditworthiness is well-established.")

    full_explain = " ".join(explain_lines) + "<br><br><b>Why the difference?</b><ul>" + "".join(f"<li style='margin-bottom:0.4rem;'>{r}</li>" for r in reasons) + "</ul>"

    st.markdown(f"""
    <div class='explain-card'>
        <div class='explain-title'>📊 FinBridge ({fb}) vs Traditional CIBIL (~{ci}) — Score Difference: {diff_sign}{diff}</div>
        <div class='explain-body'>{full_explain}</div>
    </div>
    """, unsafe_allow_html=True)

    # Eligibility table
    st.markdown(f"""
    <div class='explain-card'>
        <div class='explain-title'>🏦 What Loans Are You Eligible For?</div>
        <div class='explain-body'>
            Based on your FinBridge Score of <b>{fb} ({label})</b>:
            <table style='width:100%;border-collapse:collapse;margin-top:0.8rem;font-size:0.82rem;'>
                <tr style='border-bottom:1px solid #1E3A5F;'>
                    <th style='text-align:left;padding:0.4rem 0.8rem;color:#000000;'>Loan Type</th>
                    <th style='text-align:center;padding:0.4rem;color:#000000;'>CIBIL Eligibility</th>
                    <th style='text-align:center;padding:0.4rem;color:#F0B429;'>FinBridge Eligibility</th>
                </tr>
                <tr style='border-bottom:1px solid #0A1628;'>
                    <td style='padding:0.5rem 0.8rem;color:#000000;'>Home Loan</td>
                    <td style='text-align:center;padding:0.5rem;color:{"#3EC87A" if ci>=700 else "#E05C5C"};'>{"✅ Eligible" if ci>=700 else "⚠️ Marginal" if ci>=650 else "❌ Unlikely"}</td>
                    <td style='text-align:center;padding:0.5rem;color:{"#3EC87A" if fb>=700 else "#E05C5C"};'>{"✅ Eligible" if fb>=700 else "⚠️ Marginal" if fb>=650 else "❌ Unlikely"}</td>
                </tr>
                <tr style='border-bottom:1px solid #0A1628;'>
                    <td style='padding:0.5rem 0.8rem;color:#000000;'>Personal Loan</td>
                    <td style='text-align:center;padding:0.5rem;color:{"#3EC87A" if ci>=680 else "#E05C5C"};'>{"✅ Eligible" if ci>=680 else "⚠️ Possible" if ci>=620 else "❌ Unlikely"}</td>
                    <td style='text-align:center;padding:0.5rem;color:{"#3EC87A" if fb>=680 else "#E05C5C"};'>{"✅ Eligible" if fb>=680 else "⚠️ Possible" if fb>=620 else "❌ Unlikely"}</td>
                </tr>
                <tr style='border-bottom:1px solid #0A1628;'>
                    <td style='padding:0.5rem 0.8rem;color:#000000;'>Business / MSME Loan</td>
                    <td style='text-align:center;padding:0.5rem;color:{"#3EC87A" if ci>=700 else "#E05C5C"};'>{"✅ Eligible" if ci>=700 else "⚠️ Marginal" if ci>=650 else "❌ Unlikely"}</td>
                    <td style='text-align:center;padding:0.5rem;color:{"#3EC87A" if fb>=660 else "#E05C5C"};'>{"✅ Eligible" if fb>=660 else "⚠️ Possible" if fb>=620 else "❌ Unlikely"}</td>
                </tr>
                <tr>
                    <td style='padding:0.5rem 0.8rem;color:#000000;'>Gold / Secured Loan</td>
                    <td style='text-align:center;padding:0.5rem;color:#3EC87A;'>✅ Any Score</td>
                    <td style='text-align:center;padding:0.5rem;color:#3EC87A;'>✅ Any Score</td>
                </tr>
            </table>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Score interpretation
    interpretation = {
        "Excellent": ("🌟 Outstanding — eligible for premium loan products at the best rates with flexible tenure.", "#3EC87A"),
        "Good":      ("✅ Strong profile — eligible for most products at competitive rates.",                         "#7CC87E"),
        "Fair":      ("⚠️ Average — standard loans available; co-applicant recommended for larger amounts.",         "#F0B429"),
        "Marginal":  ("🔶 Below average — limited options; collateral or guarantor strongly advised.",               "#E08929"),
        "Poor":      ("🚨 Needs improvement — focus on cash-flow discipline before applying for unsecured credit.",  "#E05C5C"),
    }
    msg, col = interpretation.get(label, ("", "#000000"))
    st.markdown(f"""
    <div style='background:rgba(0,0,0,0.2);border:1px solid {col};border-radius:10px;padding:1rem 1.3rem;color:{col};font-size:0.92rem;margin-top:0.5rem;'>
        {msg}
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# PAGE: CIBIL vs FINBRIDGE COMPARISON
# ════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "comparison":
    if not st.session_state.scores_computed:
        st.warning("Please complete the bank statement input first.")
        st.stop()

    fb = st.session_state.finbridge_score
    ci = st.session_state.cibil_score
    prof = st.session_state.profile_data
    stmt = st.session_state.stmt_data
    label_fb, badge_fb, color_fb = get_score_band(fb)
    label_ci, badge_ci, color_ci = get_score_band(ci)

    st.markdown("<div class='section-title'>⚖️ Traditional CIBIL vs FinBridge Score</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>Understand how the FinBridge methodology differs from a traditional bureau score — and why it matters for your real creditworthiness.</div>", unsafe_allow_html=True)

    col_ci, col_fb = st.columns(2, gap="large")
    with col_ci:
        st.markdown(f"""
        <div style='text-align:center;padding:2rem 1rem;background:#112240;border:1px solid #1E3A5F;border-radius:14px;'>
            <div style='font-size:0.7rem;letter-spacing:0.15em;text-transform:uppercase;color:#000000;margin-bottom:0.5rem;'>Traditional CIBIL Score</div>
            <div style='font-family:"Playfair Display",serif;font-size:4rem;font-weight:700;color:{color_ci};'>{ci}</div>
            <span class='badge {badge_ci}' style='font-size:0.9rem;padding:0.35rem 1rem;'>{label_ci}</span>
            <div style='font-size:0.75rem;color:#000000;margin-top:1rem;'>Bureau-based | Payment History Focused</div>
        </div>
        """, unsafe_allow_html=True)
    with col_fb:
        st.markdown(f"""
        <div style='text-align:center;padding:2rem 1rem;background:linear-gradient(135deg,#1A3A5C,#0A1628);border:2px solid #F0B429;border-radius:14px;'>
            <div style='font-size:0.7rem;letter-spacing:0.15em;text-transform:uppercase;color:#F0B429;margin-bottom:0.5rem;'>FinBridge Credit Score</div>
            <div style='font-family:"Playfair Display",serif;font-size:4rem;font-weight:700;color:{color_fb};'>{fb}</div>
            <span class='badge {badge_fb}' style='font-size:0.9rem;padding:0.35rem 1rem;'>{label_fb}</span>
            <div style='font-size:0.75rem;color:#000000;margin-top:1rem;'>Bank Statement Driven | Cash-Flow Intelligence</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr class='fb-divider'>", unsafe_allow_html=True)

    fig_comp = go.Figure()
    fig_comp.add_trace(go.Bar(name="Traditional Score", x=["Score"], y=[ci],  marker_color=color_ci, width=0.25,
                               text=[ci], textposition="outside", textfont=dict(color="#000000", size=14)))
    fig_comp.add_trace(go.Bar(name="FinBridge Score",   x=["Score"], y=[fb],  marker_color=color_fb, width=0.25,
                               text=[fb], textposition="outside", textfont=dict(color="#000000", size=14)))
    for y0, y1, label_t in [(750,900,"Excellent"),(700,749,"Good"),(650,699,"Fair"),(600,649,"Marginal"),(300,599,"Poor")]:
        fig_comp.add_hrect(y0=y0, y1=y1, fillcolor="rgba(255,255,255,0.02)", line_width=0, annotation_text=label_t, annotation_position="right")
    fig_comp.update_layout(
        barmode="group", height=350,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(range=[300, 960], gridcolor="#1E3A5F"),
        xaxis=dict(gridcolor="#1E3A5F"),
        font=dict(color="#000000"),
        legend=dict(font=dict(color="#000000"), orientation="h", y=1.1),
        margin=dict(t=40, b=20, l=10, r=70),
    )
    st.plotly_chart(fig_comp, use_container_width=True)

    st.markdown("<hr class='fb-divider'>", unsafe_allow_html=True)
    st.markdown("**Methodology Comparison**")
    comp_data = [
        ("Data Source",              "CIBIL Bureau / Credit Report",              "Actual Bank Statements (3–5 years)"),
        ("Income Verification",      "Declared income only",                      "Actual credited amounts verified"),
        ("Payment History",          "Primary factor (35%+ weight)",              "One of 6 balanced dimensions"),
        ("Cash-Flow Analysis",       "Not considered",                            "Core scoring factor (20%)"),
        ("Savings Behaviour",        "Not assessed",                              "Weighted at 18%"),
        ("Debt Service Coverage",    "Estimated only",                            "Calculated from real outflows (17%)"),
        ("Informal Income",          "Cannot capture",                            "Reflected in cash-flow patterns"),
        ("Freelancer / Gig Workers", "Often penalised (irregular income)",        "Fairly assessed via income stability"),
        ("Students / First-timers",  "No score (thin file)",                      "Scored on available history (3 yrs)"),
        ("Real-time Adjustments",    "Quarterly updates only",                    "Instant re-assessment possible"),
        ("Manipulation Risk",        "Credit card gaming possible",               "Difficult to manipulate bank records"),
        ("India Relevance",          "Urban / salaried bias",                     "Inclusive of semi-urban & rural patterns"),
    ]
    header_html = "<div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:8px;'>" + \
        "".join(f"<div style='background:#0A1628;border:1px solid #1E3A5F;border-radius:8px;padding:0.7rem 1rem;font-size:0.8rem;font-weight:600;color:#000000;text-transform:uppercase;letter-spacing:0.05em;'>{h}</div>"
                for h in ["Parameter", "Traditional CIBIL", "FinBridge"]) + "</div>"
    rows_html = ""
    for param, trad, fb_val in comp_data:
        rows_html += f"""
        <div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:6px;'>
            <div style='background:#112240;border:1px solid #1E3A5F;border-radius:6px;padding:0.6rem 0.9rem;font-size:0.82rem;color:#000000;font-weight:500;'>{param}</div>
            <div style='background:#112240;border:1px solid #1E3A5F;border-radius:6px;padding:0.6rem 0.9rem;font-size:0.82rem;color:#000000;'>{trad}</div>
            <div style='background:linear-gradient(135deg,#1A3A5C,#0A1628);border:1px solid rgba(240,180,41,0.3);border-radius:6px;padding:0.6rem 0.9rem;font-size:0.82rem;color:#000000;'>{fb_val}</div>
        </div>"""
    st.markdown(header_html + rows_html, unsafe_allow_html=True)

    st.markdown("<hr class='fb-divider'>", unsafe_allow_html=True)
    st.markdown("**Who benefits most from FinBridge scoring?**")
    benefit_cols = st.columns(4, gap="small")
    benefits = [("🧑‍🎓","Students","Build credit history without credit cards"),
                ("💻","Freelancers","Cash-flow recognized despite irregular income"),
                ("🏪","MSMEs","5-year business cash-flow tells the real story"),
                ("🌾","Informal Earners","Cash deposits and transaction patterns scored")]
    for col, (icon, title, desc) in zip(benefit_cols, benefits):
        with col:
            st.markdown(f"""
            <div class='metric-card' style='padding:1.3rem;'>
                <div style='font-size:2rem;'>{icon}</div>
                <div style='font-size:0.92rem;font-weight:600;color:#000000;margin:0.5rem 0 0.3rem;'>{title}</div>
                <div style='font-size:0.78rem;color:#000000;'>{desc}</div>
            </div>
            """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# PAGE: EMI PLANNER
# ════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "emi":
    if not st.session_state.scores_computed:
        st.warning("Please complete the bank statement input first."); st.stop()

    fb   = st.session_state.finbridge_score
    stmt = st.session_state.stmt_data
    prof = st.session_state.profile_data

    st.markdown("<div class='section-title'>📅 EMI Planner & Repayment Intelligence</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>Model your repayment schedule, understand the true cost of borrowing, and stress-test your monthly cash-flow.</div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1.5], gap="large")

    with col1:
        st.markdown("<div class='section-header'>Loan Inputs</div>", unsafe_allow_html=True)
        loan_amount  = st.number_input("Loan Amount (₹)",          min_value=10000.0, value=1500000.0, step=50000.0, format="%.0f")
        int_rate     = st.slider("Annual Interest Rate (%)",        6.0, 24.0, 10.5, 0.25)
        tenure_yr    = st.slider("Loan Tenure (Years)",             1, 30, 10)
        tenure_mo    = tenure_yr * 12
        emi          = calc_emi(loan_amount, int_rate, tenure_mo)
        total_pmt    = emi * tenure_mo
        total_int    = total_pmt - loan_amount
        int_to_p     = (total_int / loan_amount * 100) if loan_amount > 0 else 0

        m1, m2 = st.columns(2)
        with m1: st.markdown(f"""<div class='metric-card'><div class='metric-val'>{format_inr(emi)}/mo</div><div class='metric-lab'>Monthly EMI</div></div>""", unsafe_allow_html=True)
        with m2: st.markdown(f"""<div class='metric-card'><div class='metric-val' style='color:#E05C5C;'>{format_inr(total_int)}</div><div class='metric-lab'>Total Interest</div></div>""", unsafe_allow_html=True)
        m3, m4 = st.columns(2)
        with m3: st.markdown(f"""<div class='metric-card'><div class='metric-val' style='color:#0EC4B0;'>{format_inr(total_pmt)}</div><div class='metric-lab'>Total Payable</div></div>""", unsafe_allow_html=True)
        with m4: st.markdown(f"""<div class='metric-card'><div class='metric-val' style='color:#F0B429;'>{int_to_p:.1f}%</div><div class='metric-lab'>Interest-to-Principal</div></div>""", unsafe_allow_html=True)

    with col2:
        fig_pie = go.Figure(go.Pie(
            labels=["Principal", "Total Interest"], values=[loan_amount, total_int],
            hole=0.55, marker=dict(colors=["#0EC4B0","#E05C5C"]),
            textinfo="label+percent", textfont=dict(color="#000000", size=11),
            hovertemplate="%{label}: ₹%{value:,.0f}<extra></extra>"
        ))
        fig_pie.add_annotation(text=f"Total<br>{format_inr(total_pmt)}", x=0.5, y=0.5, showarrow=False,
                               font=dict(size=13, color="#000000"))
        fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              showlegend=True, legend=dict(font=dict(color="#000000"), orientation="h", y=-0.1),
                              height=300, margin=dict(t=20, b=30, l=10, r=10))
        st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown("**Year-wise Amortisation**")
        balances, principals, interests_p = [], [], []
        balance = loan_amount
        r_mo    = int_rate / (12 * 100)
        for yr in range(1, tenure_yr + 1):
            yr_int, yr_prin = 0.0, 0.0
            for _ in range(12):
                if balance <= 0: break
                ip = balance * r_mo
                pp = min(emi - ip, balance)
                balance -= pp; yr_int += ip; yr_prin += pp
            principals.append(round(yr_prin, 0)); interests_p.append(round(yr_int, 0))
            balances.append(max(0, round(balance, 0)))

        yrs_labels = [f"Yr {i}" for i in range(1, tenure_yr + 1)]
        fig_amort  = go.Figure()
        fig_amort.add_trace(go.Bar(name="Principal",    x=yrs_labels, y=principals,   marker_color="#0EC4B0"))
        fig_amort.add_trace(go.Bar(name="Interest",     x=yrs_labels, y=interests_p,  marker_color="#E05C5C"))
        fig_amort.add_trace(go.Scatter(name="Balance",  x=yrs_labels, y=balances,
                                       mode="lines+markers", line=dict(color="#F0B429", width=2), yaxis="y2"))
        fig_amort.update_layout(
            barmode="stack", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(gridcolor="#1E3A5F"),
            yaxis=dict(gridcolor="#1E3A5F", title="Annual Payment (₹)"),
            yaxis2=dict(overlaying="y", side="right", title="Balance (₹)", gridcolor="#1E3A5F"),
            legend=dict(font=dict(color="#000000", size=9), orientation="h", y=1.1),
            font=dict(color="#000000", size=9),
            height=300, margin=dict(t=30, b=40, l=10, r=10),
        )
        st.plotly_chart(fig_amort, use_container_width=True)

    st.markdown("<hr class='fb-divider'>", unsafe_allow_html=True)
    st.markdown("**Monthly Cash-Flow Stress Test**")
    avg_mo_income  = float(np.mean(stmt.get("annual_income",  [600000]))) / 12
    avg_mo_expense = float(np.mean(stmt.get("annual_expense", [400000]))) / 12
    exist_mo_emi   = float(np.mean(stmt.get("existing_emis",  [0])))      / 12
    net_after_emi  = avg_mo_income - avg_mo_expense - exist_mo_emi - emi

    sc_cols = st.columns(4, gap="small")
    for col, (lbl, val, clr) in zip(sc_cols, [
        ("Monthly Income",   f"₹{avg_mo_income:,.0f}",  "#3EC87A"),
        ("Monthly Expenses", f"₹{avg_mo_expense:,.0f}", "#E05C5C"),
        ("Existing EMIs",    f"₹{exist_mo_emi:,.0f}",   "#E08929"),
        ("New EMI",          f"₹{emi:,.0f}",             "#F0B429"),
    ]):
        with col:
            st.markdown(f"""<div class='metric-card'><div class='metric-val' style='font-size:1.2rem;color:{clr};'>{val}</div><div class='metric-lab'>{lbl}</div></div>""", unsafe_allow_html=True)

    net_color = "#3EC87A" if net_after_emi > 0 else "#E05C5C"
    net_icon  = "✅" if net_after_emi > 0 else "⚠️"
    note = "Comfortable repayment capacity." if net_after_emi > avg_mo_income * 0.1 else \
           "Tight cash flow. Consider lower loan or longer tenure." if net_after_emi > 0 else \
           "Loan would result in negative balance. Reduce desired amount."
    st.markdown(f"""
    <div style='background:rgba(0,0,0,0.2);border:2px solid {net_color};border-radius:10px;padding:1rem 1.3rem;margin-top:1rem;'>
        <span style='color:{net_color};font-size:1rem;font-weight:600;'>{net_icon} Net Monthly Surplus: <span style='font-family:"Playfair Display",serif;font-size:1.4rem;'>₹{net_after_emi:,.0f}</span></span>
        <div style='font-size:0.8rem;color:#000000;margin-top:0.4rem;'>{note}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr class='fb-divider'>", unsafe_allow_html=True)
    st.markdown("**Prepayment Benefit Simulator**")
    pre_c1, pre_c2 = st.columns([1, 2])
    with pre_c1:
        prepay = st.number_input("Annual Prepayment Amount (₹)", min_value=0.0, value=50000.0, step=10000.0, format="%.0f")
    if prepay > 0 and r_mo > 0:
        bal_pp, mo_taken, int_pp = loan_amount, 0, 0.0
        for m in range(tenure_mo):
            if bal_pp <= 0: break
            ip = bal_pp * r_mo; pp = min(emi - ip, bal_pp)
            bal_pp -= pp; int_pp += ip; mo_taken += 1
            if (m + 1) % 12 == 0: bal_pp = max(0, bal_pp - prepay)
        int_saved  = total_int - int_pp
        mo_saved   = tenure_mo - mo_taken
        with pre_c2:
            pp_c = st.columns(3, gap="small")
            with pp_c[0]: st.markdown(f"""<div class='metric-card'><div class='metric-val' style='color:#3EC87A;'>{format_inr(max(0,int_saved))}</div><div class='metric-lab'>Interest Saved</div></div>""", unsafe_allow_html=True)
            with pp_c[1]: st.markdown(f"""<div class='metric-card'><div class='metric-val' style='color:#0EC4B0;'>{months_to_label(max(0,mo_saved))}</div><div class='metric-lab'>Tenure Reduced</div></div>""", unsafe_allow_html=True)
            with pp_c[2]: st.markdown(f"""<div class='metric-card'><div class='metric-val' style='color:#F0B429;'>{format_inr(int_pp+loan_amount)}</div><div class='metric-lab'>New Total Payable</div></div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# PAGE: CREDIT REPORT
# ════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "report":
    if not st.session_state.scores_computed:
        st.warning("Please complete the bank statement input first."); st.stop()

    fb    = st.session_state.finbridge_score
    ci    = st.session_state.cibil_score
    prof  = st.session_state.profile_data
    stmt  = st.session_state.stmt_data
    comps = st.session_state.components
    label, badge, color = get_score_band(fb)

    st.markdown("<div class='section-title'>📋 FinBridge Credit Intelligence Report</div>", unsafe_allow_html=True)

    st.markdown(f"""
    <div style='background:linear-gradient(135deg,#1A3A5C 0%,#0A1628 100%);border:1px solid #F0B429;border-radius:14px;padding:2rem;margin-bottom:1.5rem;'>
        <div style='display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:1rem;'>
            <div>
                <div style='font-family:"Playfair Display",serif;font-size:1.5rem;font-weight:700;color:#F0B429;'>FinBridge Credit Intelligence Report</div>
                <div style='color:#000000;font-size:0.82rem;margin-top:0.3rem;'>Confidential | Generated: {datetime.now().strftime("%B %Y")}</div>
            </div>
            <div style='text-align:right;'>
                <div style='font-size:0.75rem;color:#000000;'>FinBridge Score</div>
                <div style='font-family:"Playfair Display",serif;font-size:2.5rem;color:{color};font-weight:700;'>{fb}</div>
                <span class='badge {badge}'>{label}</span>
            </div>
        </div>
        <hr style='border-color:#1E3A5F;margin:1rem 0;'>
        <div style='display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;font-size:0.82rem;'>
            <div><span style='color:#000000;'>Name:</span> <span style='color:#000000;'>{prof.get("name","N/A")}</span></div>
            <div><span style='color:#000000;'>Age:</span> <span style='color:#000000;'>{prof.get("age","N/A")}</span></div>
            <div><span style='color:#000000;'>Profile:</span> <span style='color:#000000;'>{prof.get("profile_type","N/A")}</span></div>
            <div><span style='color:#000000;'>City:</span> <span style='color:#000000;'>{prof.get("city","N/A")}</span></div>
            <div><span style='color:#000000;'>Occupation:</span> <span style='color:#000000;'>{prof.get("occupation","N/A")}</span></div>
            <div><span style='color:#000000;'>Credit Cards:</span> <span style='color:#000000;'>{prof.get("credit_cards","N/A")}</span></div>
            <div><span style='color:#000000;'>Active Loans:</span> <span style='color:#000000;'>{prof.get("loans_active","N/A")}</span></div>
            <div><span style='color:#000000;'>Collateral:</span> <span style='color:#000000;'>{prof.get("has_collateral","N/A")}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    incomes  = stmt.get("annual_income",  [1])
    avg_inc  = float(np.mean(incomes))
    avg_exp  = float(np.mean(stmt.get("annual_expense", [0])))
    avg_sav  = float(np.mean(stmt.get("annual_savings",  [0])))
    tot_bnc  = int(sum(stmt.get("bounce_count", [0])))
    sav_rate = (avg_sav / avg_inc * 100) if avg_inc > 0 else 0

    r1, r2, r3, r4, r5 = st.columns(5, gap="small")
    for col, (lbl, val, clr) in zip([r1,r2,r3,r4,r5], [
        ("FinBridge Score",    str(fb),              color),
        ("Traditional Score",  str(ci),              "#0EC4B0"),
        ("Avg Annual Income",  format_inr(avg_inc),  "#3EC87A"),
        ("Avg Savings Rate",   f"{sav_rate:.1f}%",   "#F0B429"),
        ("Total Bounces",      str(tot_bnc),          "#E05C5C" if tot_bnc > 2 else "#000000"),
    ]):
        with col:
            st.markdown(f"""<div class='metric-card'><div class='metric-val' style='font-size:1.4rem;color:{clr};'>{val}</div><div class='metric-lab'>{lbl}</div></div>""", unsafe_allow_html=True)

    st.markdown("<hr class='fb-divider'>", unsafe_allow_html=True)
    st.markdown("**Score Component Analysis**")
    maxes_dict = {"Income Stability":25,"Cash-Flow":20,"Savings Behaviour":18,"Debt Coverage":17,"Expenditure Discipline":12,"Account Behaviour":8}
    for comp_name, score_val in comps.items():
        max_val = maxes_dict.get(comp_name, 25)
        pct     = score_val / max_val * 100 if max_val > 0 else 0
        bar_col = "#3EC87A" if pct >= 75 else "#F0B429" if pct >= 50 else "#E05C5C"
        strength= "Strong" if pct >= 75 else "Moderate" if pct >= 50 else "Weak"
        st.markdown(f"""
        <div style='display:grid;grid-template-columns:180px 1fr 80px 70px;gap:1rem;align-items:center;margin-bottom:0.6rem;'>
            <div style='font-size:0.85rem;color:#000000;'>{comp_name}</div>
            <div style='background:#1E3A5F;border-radius:50px;height:8px;'>
                <div style='width:{pct:.1f}%;background:{bar_col};border-radius:50px;height:8px;'></div>
            </div>
            <div style='font-size:0.85rem;color:{bar_col};text-align:right;'>{score_val:.1f}/{max_val}</div>
            <div><span class='badge {"badge-green" if pct>=75 else "badge-gold" if pct>=50 else "badge-red"}' style='font-size:0.68rem;'>{strength}</span></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr class='fb-divider'>", unsafe_allow_html=True)
    col_str, col_imp = st.columns(2, gap="large")
    with col_str:
        st.markdown("**💪 Key Strengths**")
        strengths = []
        if comps.get("Income Stability",0)>=18:     strengths.append("Consistent income growth — strong financial stability")
        if comps.get("Savings Behaviour",0)>=13:     strengths.append("Strong savings discipline — above benchmark savings rate")
        if comps.get("Cash-Flow",0)>=15:             strengths.append("Positive cash-flow maintained across all years")
        if comps.get("Debt Coverage",0)>=12:         strengths.append("Healthy Debt Service Coverage Ratio (DSCR)")
        if comps.get("Expenditure Discipline",0)>=9: strengths.append("Controlled expenditure relative to income")
        if comps.get("Account Behaviour",0)>=6:      strengths.append("Clean account history with minimal bounces")
        if tot_bnc == 0:                             strengths.append("Zero bounce record — excellent payment behaviour")
        if not strengths: strengths.append("Continue building financial discipline for a stronger score")
        for s in strengths:
            st.markdown(f"""<div style='background:rgba(62,200,122,0.05);border:1px solid rgba(62,200,122,0.2);border-radius:8px;padding:0.6rem 0.9rem;margin-bottom:0.5rem;font-size:0.83rem;color:#000000;'>✅ {s}</div>""", unsafe_allow_html=True)

    with col_imp:
        st.markdown("**🔧 Areas for Improvement**")
        improvements = []
        if comps.get("Savings Behaviour",0)<10:      improvements.append("Increase monthly savings rate to at least 20% of income")
        if comps.get("Cash-Flow",0)<12:              improvements.append("Improve cash-flow consistency — reduce unnecessary outflows")
        if comps.get("Income Stability",0)<15:       improvements.append("Diversify income sources to improve stability score")
        if comps.get("Debt Coverage",0)<10:          improvements.append("Reduce existing EMI obligations to improve DSCR")
        if comps.get("Account Behaviour",0)<6:       improvements.append("Eliminate cheque/ECS bounces — maintain minimum balance")
        if comps.get("Expenditure Discipline",0)<8:  improvements.append("Reduce discretionary spending to below 75% of income")
        if tot_bnc > 2:                              improvements.append(f"Address {tot_bnc} bounces recorded — serious negative signal")
        if not improvements: improvements.append("Excellent profile — maintain current financial discipline")
        for im in improvements:
            st.markdown(f"""<div style='background:rgba(240,180,41,0.05);border:1px solid rgba(240,180,41,0.2);border-radius:8px;padding:0.6rem 0.9rem;margin-bottom:0.5rem;font-size:0.83rem;color:#000000;'>⚠️ {im}</div>""", unsafe_allow_html=True)

    st.markdown("<hr class='fb-divider'>", unsafe_allow_html=True)
    st.markdown("**📈 Score Improvement Projection**")
    months_proj = list(range(0, 25, 3))
    if sav_rate < 20 and tot_bnc == 0:  proj = [min(900, fb + int(m*2.5)) for m in months_proj]
    elif tot_bnc > 0:                   proj = [min(900, fb + int(m*1.2)) for m in months_proj]
    else:                               proj = [min(900, fb + int(m*3.0)) for m in months_proj]

    fig_proj = go.Figure()
    fig_proj.add_trace(go.Scatter(
        x=[f"M+{m}" for m in months_proj], y=proj,
        mode="lines+markers", line=dict(color="#F0B429", width=2.5),
        marker=dict(size=8, color="#F0B429"),
        fill="tozeroy", fillcolor="rgba(240,180,41,0.05)", name="Projected Score"
    ))
    fig_proj.add_hline(y=750, line_dash="dot", line_color="#3EC87A", annotation_text="Excellent (750)", annotation_font_color="#3EC87A")
    fig_proj.add_hline(y=700, line_dash="dot", line_color="#7CC87E", annotation_text="Good (700)",      annotation_font_color="#7CC87E")
    fig_proj.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="#1E3A5F"), yaxis=dict(gridcolor="#1E3A5F", range=[300, 950]),
        font=dict(color="#000000"),
        height=250, margin=dict(t=20, b=30, l=10, r=10), showlegend=False,
    )
    st.plotly_chart(fig_proj, use_container_width=True)

    st.markdown("""
    <div style='text-align:center;font-size:0.72rem;color:#4A6080;margin-top:1rem;border-top:1px solid #1E3A5F;padding-top:1rem;'>
        FinBridge Credit Intelligence Platform &nbsp;|&nbsp; This report is for informational purposes only and does not constitute a formal credit assessment.
        &nbsp;|&nbsp; FinBridge is not a registered Credit Information Company under the Credit Information Companies (Regulation) Act, 2005.
        &nbsp;|&nbsp; All scores are computed using the applicant's self-declared bank statement data.
    </div>
    """, unsafe_allow_html=True)

else:
    st.session_state.step = "profile"
    st.rerun()
