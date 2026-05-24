import streamlit as st
import joblib
import re
import json
import csv
import io
import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date
from langdetect import detect
import plotly.graph_objects as go


# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="💸Pesa Salama",
    page_icon="🛡️",
    layout="centered",
    initial_sidebar_state="expanded",
)

# =============================================================================
# PERSISTENT STORAGE
# =============================================================================

STORAGE_FILE = "pesa_salama_history.json"
SETTINGS_FILE = "pesa_salama_settings.json"

def load_persistent_history():
    if os.path.exists(STORAGE_FILE):
        try:
            with open(STORAGE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_persistent_history(history):
    try:
        with open(STORAGE_FILE, "w") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        st.warning(f"⚠️ Could not save history: {e}")

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=2)
    except Exception:
        pass

# =============================================================================
# SESSION STATE
# =============================================================================

if "history" not in st.session_state:
    st.session_state.history = load_persistent_history()
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "settings" not in st.session_state:
    st.session_state.settings = load_settings()

# =============================================================================
# CUSTOM CSS
# =============================================================================

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
.stApp { background: linear-gradient(135deg, #081c15 0%, #0a2518 50%, #081c15 100%); }
.hero-section {
    background: linear-gradient(135deg, rgba(0,166,81,0.95), rgba(0,122,61,0.92));
    border-radius: 24px; padding: 38px 30px; margin-bottom: 28px;
    text-align: center; box-shadow: 0 8px 32px rgba(0,166,81,0.28);
    border: 1px solid rgba(255,255,255,0.08);
}
.logo-circle {
    width: 95px; height: 95px; border-radius: 50%;
    background: rgba(255,255,255,0.15);
    display: flex; align-items: center; justify-content: center;
    margin: auto auto 18px auto; font-size: 2.7rem; backdrop-filter: blur(8px);
}
.hero-title { color: white; font-size: 2.5rem; font-weight: 800; margin-bottom: 10px; }
.hero-subtitle { color: #e5fff0; font-size: 1rem; line-height: 1.7; max-width: 620px; margin: auto; }
.feature-badges { margin-top: 20px; }
.badge {
    display: inline-block; background: rgba(255,255,255,0.14); color: white;
    padding: 8px 15px; border-radius: 999px; margin: 5px;
    font-size: 0.82rem; font-weight: 500; border: 1px solid rgba(255,255,255,0.12);
}
.result-card {
    border-radius: 18px; padding: 20px 24px; margin: 14px 0; display: block;
    box-shadow: 0 6px 20px rgba(0,0,0,0.18); transition: all 0.3s ease; backdrop-filter: blur(8px);
}
.result-card:hover { transform: translateY(-2px); }
.card-positive { background: linear-gradient(90deg, rgba(13,59,34,0.95), rgba(20,90,50,0.95)); border-left: 6px solid #2ecc71; color: #dfffea; }
.card-negative { background: linear-gradient(90deg, rgba(59,13,13,0.95), rgba(90,20,20,0.95)); border-left: 6px solid #e74c3c; color: #ffe0e0; }
.card-neutral { background: linear-gradient(90deg, rgba(26,42,59,0.95), rgba(30,58,82,0.95)); border-left: 6px solid #3498db; color: #dcefff; }
.card-info { background: linear-gradient(90deg, rgba(28,28,48,0.95), rgba(40,40,70,0.95)); border-left: 6px solid #9b59b6; color: #f0e5ff; }
.card-urgent { background: linear-gradient(90deg, rgba(90,20,0,0.97), rgba(120,30,0,0.97)); border-left: 6px solid #ff4500; color: #fff0e0; border: 2px solid #ff4500; }
.card-label { font-size: 0.76rem; text-transform: uppercase; letter-spacing: 1.3px; opacity: 0.76; font-weight: 600; margin-bottom: 4px; }
.card-value { font-size: 1.3rem; font-weight: 700; }
.conf-bar-wrap { background: rgba(255,255,255,0.12); border-radius: 999px; height: 10px; margin-top: 12px; overflow: hidden; }
.conf-bar-fill { height: 100%; border-radius: 999px; }
.summary-bar {
    background: rgba(0,166,81,0.12); border-radius: 12px; padding: 12px 18px;
    margin-bottom: 16px; border: 1px solid rgba(0,166,81,0.2);
    color: #c8f0d8; font-size: 0.9rem; display: flex; gap: 18px; flex-wrap: wrap; align-items: center;
}
.history-row {
    background: rgba(255,255,255,0.04); border-radius: 12px; padding: 12px 16px;
    margin-bottom: 8px; border: 1px solid rgba(255,255,255,0.07); color: #c8f0d8; font-size: 0.88rem;
}
.stTextArea textarea {
    background-color: rgba(11,43,24,0.95) !important; color: #e8fff1 !important;
    border: 1.5px solid #00a651 !important; border-radius: 14px !important;
    font-size: 1rem !important; padding: 16px !important;
}
.stButton > button {
    background: linear-gradient(90deg, #00a651, #007a3d); color: white;
    font-weight: 700; font-size: 1rem; border: none; border-radius: 14px;
    padding: 14px 36px; width: 100%; box-shadow: 0 5px 18px rgba(0,166,81,0.35); transition: all 0.3s ease;
}
.stButton > button:hover { transform: translateY(-2px); opacity: 0.94; }
.footer { text-align: center; color: #76a58a; font-size: 0.82rem; margin-top: 42px; padding-bottom: 10px; }
.section-box {
    background: rgba(0,166,81,0.07); border-radius: 14px; padding: 16px 18px;
    border: 1px solid rgba(0,166,81,0.18); margin-bottom: 14px; color: #c8f0d8; font-size: 0.88rem;
}
</style>""", unsafe_allow_html=True)

# =============================================================================
# LOAD MODEL
# =============================================================================

@st.cache_resource(show_spinner=False)
def load_model():
    saved = joblib.load("04.advancedxgboostmodelfinal.pkl")
    return saved["tfidf"], saved["model"]

try:
    vectorizer, model = load_model()
except FileNotFoundError as e:
    st.error(f"⚠️ Model file not found: {e}\n\nEnsure 04.advancedxgboostmodelfinal.pkl is in the same folder as app.py")
    st.stop()

# =============================================================================
# CONSTANTS
# =============================================================================

CLASS_MAP = {0: "negative", 1: "neutral", 2: "positive"}
SENTIMENT_DISPLAY = {
    "negative": ("❌ Negative", "card-negative", "#e74c3c"),
    "neutral":  ("⚖️ Neutral",  "card-neutral",  "#3498db"),
    "positive": ("✅ Positive", "card-positive", "#00a651"),
}
URGENT_CATEGORIES = ["💸 Transaction Issues", "📱 App Issues"]
SWAHILI_SHENG_WORDS = [
    "niko","poa","sasa","msee","manze","mbogi",
    "sana","vizuri","hapana","asante","tatizo",
    "huduma","mbaya","mbovu","hii","ni",
]

# =============================================================================
# HELPERS
# =============================================================================

def handle_negations(text: str):
    text = text.lower()
    patterns = {
        r"\bnot good\b":"negative", r"\bnot working\b":"negative",
        r"\bnot helpful\b":"negative", r"\bhakuna network\b":"negative",
        r"\bhaifanyi vizuri\b":"negative", r"\bsi nzuri\b":"negative",
        r"\bmbaya\b":"negative", r"\bmbovu\b":"negative",
    }
    for pat, rep in patterns.items():
        text = re.sub(pat, rep, text)
    text = re.sub(r"\b(not|no|never)\s+(\w+)", r"\1_\2", text)
    return text

def is_swahili_sheng(text: str):
    return any(w in text.lower() for w in SWAHILI_SHENG_WORDS)

def detect_language(text: str, lang_mode: str = "Auto-detect"):
    t = text.lower()
    sheng   = ["niko","poa","sasa","msee","manze","mbogi"]
    swahili = ["sana","vizuri","hapana","asante","tatizo","huduma","mbaya","mbovu"]
    if lang_mode == "English only":
        return "English"
    if lang_mode == "Swahili / Sheng only":
        return "Sheng" if any(w in t for w in sheng) else "Swahili"
    if any(w in t for w in sheng):   return "Sheng"
    if any(w in t for w in swahili): return "Swahili"
    try:
        lang = detect(text)
        return "Swahili" if lang == "sw" else "English"
    except Exception:
        return "🌐 Unknown"

def detect_complaint_category(text: str):
    t = text.lower()
    cats = {
        "📶 Network Issues":     ["network","signal","internet","slow","connection"],
        "💸 Transaction Issues": ["payment","transaction","mpesa","withdraw","transfer","money","failed"],
        "🎧 Customer Service":   ["support","customer care","agent","response"],
        "📱 App Issues":         ["app","crash","bug","login","update","freeze","error"],
    }
    for cat, kws in cats.items():
        if any(k in t for k in kws):
            return cat
    return "📋 General Feedback"

def predict_sentiment(text: str, lang_mode: str = "Auto-detect"):
    if lang_mode == "Swahili / Sheng only" and not is_swahili_sheng(text):
        st.warning("⚠️ Language mode is Swahili/Sheng only but text appears to be English. Results may be less accurate.")
    if lang_mode == "English only" and is_swahili_sheng(text):
        st.warning("⚠️ Language mode is English only but text appears to contain Swahili/Sheng. Results may be less accurate.")
    processed   = handle_negations(text)
    transformed = vectorizer.transform([processed])
    raw_pred    = int(model.predict(transformed)[0])
    probs       = model.predict_proba(transformed)[0]
    confidence  = round(float(max(probs)) * 100, 1)
    sentiment   = CLASS_MAP.get(raw_pred, "neutral")
    return sentiment, confidence, probs

def export_history_csv(history):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["date","time","review","sentiment","confidence","category","language","feedback","source"])
    writer.writeheader()
    for row in history:
        writer.writerow({
            "date":       row.get("date",""),
            "time":       row.get("time",""),
            "review":     row.get("review",""),
            "sentiment":  row.get("sentiment",""),
            "confidence": row.get("confidence",""),
            "category":   row.get("category",""),
            "language":   row.get("language",""),
            "feedback":   row.get("feedback",""),
            "source":     row.get("source","manual"),
        })
    return output.getvalue()

def filter_by_date(history, date_filter):
    today_str = date.today().strftime("%Y-%m-%d")
    if date_filter == "Today":
        return [h for h in history if h.get("date","") == today_str]
    if date_filter == "This Week":
        from datetime import timedelta
        week = [(date.today() - __import__('datetime').timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
        return [h for h in history if h.get("date","") in week]
    if date_filter == "This Month":
        prefix = date.today().strftime("%Y-%m")
        return [h for h in history if h.get("date","").startswith(prefix)]
    return history

# =============================================================================
# ALERTS
# =============================================================================

def send_email_alert(subject: str, body: str, settings: dict):
    try:
        msg = MIMEMultipart()
        msg["From"]    = settings["email_sender"]
        msg["To"]      = settings["email_recipient"]
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(settings["email_sender"], settings["email_password"])
            server.sendmail(settings["email_sender"], settings["email_recipient"], msg.as_string())
        return True, "Email sent successfully"
    except Exception as e:
        return False, str(e)

def send_slack_alert(message: str, webhook_url: str):
    try:
        resp = requests.post(webhook_url, json={"text": message}, timeout=10)
        if resp.status_code == 200:
            return True, "Slack message sent"
        return False, f"Slack error: {resp.status_code}"
    except Exception as e:
        return False, str(e)

def fire_alerts(entry: dict, settings: dict, reason: str = "urgent"):
    """Fire email and/or Slack alerts based on saved settings."""
    if not settings:
        return

    sentiment  = entry.get("sentiment","").capitalize()
    category   = entry.get("category","")
    confidence = entry.get("confidence","")
    review     = entry.get("review","")[:200]
    timestamp  = f'{entry.get("date","")} {entry.get("time","")}'

    # --- Email ---
    if settings.get("email_enabled") and settings.get("email_sender") and settings.get("email_password") and settings.get("email_recipient"):
        subject = f"🚨 Pesa Salama Alert — {reason.upper()} — {sentiment}"
        body = f"""
        <div style="font-family:Arial,sans-serif;padding:20px;background:#f9f9f9;border-radius:10px;">
          <h2 style="color:#c0392b;">⚠️ Pesa Salama Alert</h2>
          <p><b>Reason:</b> {reason}</p>
          <p><b>Sentiment:</b> {sentiment}</p>
          <p><b>Category:</b> {category}</p>
          <p><b>Confidence:</b> {confidence}%</p>
          <p><b>Time:</b> {timestamp}</p>
          <hr/>
          <p><b>Review:</b><br/><i>"{review}"</i></p>
        </div>
        """
        ok, msg = send_email_alert(subject, body, settings)
        if not ok:
            st.sidebar.warning(f"Email alert failed: {msg}")

    # --- Slack ---
    if settings.get("slack_enabled") and settings.get("slack_webhook"):
        message = (
            f"🚨 *Pesa Salama Alert — {reason.upper()}*\n"
            f"*Sentiment:* {sentiment} | *Category:* {category} | *Confidence:* {confidence}%\n"
            f"*Time:* {timestamp}\n"
            f"*Review:* _{review}_"
        )
        ok, msg = send_slack_alert(message, settings["slack_webhook"])
        if not ok:
            st.sidebar.warning(f"Slack alert failed: {msg}")

def check_and_alert(entry: dict, settings: dict, confidence_threshold: int, neg_pct_threshold: int):
    """Decide whether to fire an alert for a single entry."""
    if not settings:
        return
    is_urgent    = entry["sentiment"] == "negative" and entry["category"] in URGENT_CATEGORIES
    is_uncertain = entry["confidence"] < confidence_threshold

    if settings.get("alert_on_urgent") and is_urgent:
        fire_alerts(entry, settings, reason="Urgent Negative Review")

    if settings.get("alert_on_uncertain") and is_uncertain:
        fire_alerts(entry, settings, reason=f"Low Confidence ({entry['confidence']}%)")

def check_batch_neg_pct(results: list, settings: dict, neg_pct_threshold: int):
    """Fire a summary alert if negative % in batch exceeds threshold."""
    if not settings or not settings.get("alert_on_neg_pct"):
        return
    total = len(results)
    if total == 0:
        return
    neg_pct = round(sum(1 for r in results if r["sentiment"] == "negative") / total * 100, 1)
    if neg_pct >= neg_pct_threshold:
        summary_entry = {
            "date":       date.today().strftime("%Y-%m-%d"),
            "time":       datetime.now().strftime("%H:%M:%S"),
            "review":     f"BATCH SUMMARY — {total} reviews, {neg_pct}% negative",
            "sentiment":  "negative",
            "category":   "📋 Batch Summary",
            "confidence": neg_pct,
        }
        fire_alerts(summary_entry, settings, reason=f"Batch Negative % Exceeded ({neg_pct}% ≥ {neg_pct_threshold}%)")


# =============================================================================
# CHARTS
# =============================================================================

def make_sentiment_pie(history):
    counts = {"positive":0,"neutral":0,"negative":0}
    for h in history:
        counts[h["sentiment"]] = counts.get(h["sentiment"],0)+1
    fig = go.Figure(go.Pie(
        labels=["Positive","Neutral","Negative"],
        values=[counts["positive"],counts["neutral"],counts["negative"]],
        marker=dict(colors=["#00a651","#3498db","#e74c3c"],line=dict(color="#0a2518",width=2)),
        hole=0.45, textinfo="label+percent", textfont=dict(color="white",size=13),
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white",family="Poppins"),margin=dict(t=20,b=20,l=20,r=20),showlegend=False,height=280)
    return fig

def make_category_bar(history):
    cat_counts = {}
    for h in history:
        cat_counts[h["category"]] = cat_counts.get(h["category"],0)+1
    cats,vals = list(cat_counts.keys()),list(cat_counts.values())
    fig = go.Figure(go.Bar(x=vals,y=cats,orientation="h",
        marker=dict(color="#00a651",line=dict(color="#007a3d",width=1)),
        text=vals,textposition="outside",textfont=dict(color="white")))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white",family="Poppins"),
        xaxis=dict(showgrid=False,zeroline=False,visible=False),
        yaxis=dict(showgrid=False,tickfont=dict(size=12)),
        margin=dict(t=10,b=10,l=10,r=40),height=max(180,len(cats)*52))
    return fig

def make_confidence_histogram(history):
    colors = ["#e74c3c" if h["sentiment"]=="negative" else "#00a651" if h["sentiment"]=="positive" else "#3498db" for h in history]
    fig = go.Figure(go.Bar(
        x=list(range(1,len(history)+1)),y=[h["confidence"] for h in history],
        marker=dict(color=colors),hovertext=[h["review"][:60] for h in history]))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white",family="Poppins"),
        xaxis=dict(title="Review #",showgrid=False,color="white"),
        yaxis=dict(title="Confidence %",range=[0,100],showgrid=True,gridcolor="rgba(255,255,255,0.08)",color="white"),
        margin=dict(t=10,b=40,l=50,r=10),height=240)
    return fig

def make_daily_trend(history):
    day_counts = {}
    for h in history:
        d = h.get("date","Unknown")
        day_counts[d] = day_counts.get(d,0)+1
    days = sorted(day_counts.keys())
    vals = [day_counts[d] for d in days]
    fig = go.Figure(go.Bar(x=days,y=vals,
        marker=dict(color="#00a651",line=dict(color="#007a3d",width=1)),
        text=vals,textposition="outside",textfont=dict(color="white")))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white",family="Poppins"),
        xaxis=dict(showgrid=False,color="white",tickangle=-30),
        yaxis=dict(showgrid=True,gridcolor="rgba(255,255,255,0.08)",color="white",title="Reviews"),
        margin=dict(t=10,b=60,l=50,r=10),height=240)
    return fig

# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.markdown("## 💸 Pesa Salama")
    st.markdown("---")

    # --- Model Info ---
    st.markdown("### 🧠 Model Info")
    st.markdown(
        '<div style="background:rgba(0,166,81,0.1);border-radius:10px;padding:12px;font-size:0.85rem;color:#b8f0cd;">'
        '🤖 <b>Model:</b> XGBoost<br>📐 <b>Vectorizer:</b> TF-IDF<br>'
        '🌍 <b>Languages:</b> English, Swahili, Sheng<br>'
        '🏷️ <b>Classes:</b> Positive · Neutral · Negative<br>'
        '📦 <b>Version:</b> v2.0</div>', unsafe_allow_html=True)
    st.markdown("---")

    # --- Settings ---
    st.markdown("### ⚙️ Settings")
    confidence_threshold = st.slider(
        "Flag as uncertain below (%)", 40, 90, 65, 5,
        help="Results below this confidence are flagged for manual review. Higher = stricter.")
    neg_pct_threshold = st.slider(
        "Alert when negative % exceeds (%)", 10, 90, 40, 5,
        help="Fire an alert when a batch has more than this % of negative reviews.")
    lang_mode = st.selectbox("Language mode",
        ["Auto-detect","English only","Swahili / Sheng only"],
        help="Controls how language is detected for each review.")
    st.markdown("---")

    st.markdown("---")

    # --- Batch CSV Upload ---
    st.markdown("### 📂 Batch CSV Upload")
    st.caption("Upload a CSV with a column named `review`")
    batch_file = st.file_uploader("Upload CSV", type=["csv"], label_visibility="collapsed")
    if batch_file:
        try:
            content = batch_file.read().decode("utf-8")
            reader  = csv.DictReader(io.StringIO(content))
            rows    = list(reader)
            if not rows or "review" not in rows[0]:
                st.error("CSV must have a column named `review`")
            else:
                st.success(f"✅ {len(rows)} reviews loaded")
                if st.button("▶ Run Batch Analysis"):
                    results  = []
                    progress = st.progress(0)
                    for i, row in enumerate(rows):
                        text  = row["review"]
                        s_key, conf, _ = predict_sentiment(text, lang_mode)
                        cat  = detect_complaint_category(text)
                        lang = detect_language(text, lang_mode)
                        entry = {
                            "date":date.today().strftime("%Y-%m-%d"),
                            "time":datetime.now().strftime("%H:%M:%S"),
                            "review":text,"sentiment":s_key,
                            "confidence":conf,"category":cat,
                            "language":lang,"feedback":"","source":"CSV Upload",
                        }
                        results.append(entry)
                        check_and_alert(entry, st.session_state.settings, confidence_threshold, neg_pct_threshold)
                        progress.progress((i+1)/len(rows))
                    check_batch_neg_pct(results, st.session_state.settings, neg_pct_threshold)
                    st.session_state.history = results + st.session_state.history
                    save_persistent_history(st.session_state.history)
                    st.success(f"🎉 {len(results)} reviews analysed and saved")
        except Exception as ex:
            st.error(f"Error reading CSV: {ex}")

    st.markdown("---")

    # --- Alert Settings ---
    st.markdown("### 🔔 Alert Settings")
    with st.expander("Configure Email & Slack Alerts", expanded=False):
        saved = st.session_state.settings

        st.markdown("**📧 Email Alerts (Gmail)**")
        email_enabled   = st.checkbox("Enable email alerts", value=saved.get("email_enabled", False))
        email_sender    = st.text_input("Your Gmail address", value=saved.get("email_sender",""), placeholder="you@gmail.com")
        email_password  = st.text_input("Gmail App Password", value=saved.get("email_password",""), type="password",
            help="Use a Gmail App Password, not your regular password. Create one at myaccount.google.com/apppasswords")
        email_recipient = st.text_input("Send alerts to", value=saved.get("email_recipient",""), placeholder="team@company.com")

        st.markdown("**💬 Slack Alerts**")
        slack_enabled = st.checkbox("Enable Slack alerts", value=saved.get("slack_enabled", False))
        slack_webhook = st.text_input("Slack Webhook URL", value=saved.get("slack_webhook",""), type="password",
            help="Create a webhook at api.slack.com/apps → Incoming Webhooks")

        st.markdown("**⚡ When to alert**")
        alert_on_urgent    = st.checkbox("Every urgent negative review", value=saved.get("alert_on_urgent", True))
        alert_on_uncertain = st.checkbox("Low confidence results", value=saved.get("alert_on_uncertain", False))
        alert_on_neg_pct   = st.checkbox("Batch negative % exceeded", value=saved.get("alert_on_neg_pct", True))

        if st.button("💾 Save Alert Settings"):
            new_settings = {
                "email_enabled":   email_enabled,
                "email_sender":    email_sender,
                "email_password":  email_password,
                "email_recipient": email_recipient,
                "slack_enabled":   slack_enabled,
                "slack_webhook":   slack_webhook,
                "alert_on_urgent":    alert_on_urgent,
                "alert_on_uncertain": alert_on_uncertain,
                "alert_on_neg_pct":   alert_on_neg_pct,
            }
            st.session_state.settings = new_settings
            save_settings(new_settings)
            st.success("✅ Settings saved")

        if st.button("🧪 Send Test Alert"):
            test_entry = {
                "date":date.today().strftime("%Y-%m-%d"),
                "time":datetime.now().strftime("%H:%M:%S"),
                "review":"This is a test alert from Pesa Salama AI.",
                "sentiment":"negative","category":"📱 App Issues","confidence":91.0,
            }
            fire_alerts(test_entry, st.session_state.settings, reason="Test Alert")
            st.success("Test alert fired — check your email/Slack.")

    st.markdown("---")

    # --- Storage & Export ---
    st.markdown("### 💾 Storage & Export")
    total_saved = len(st.session_state.history)
    st.markdown(
        f'<div style="background:rgba(0,166,81,0.1);border-radius:10px;padding:10px;font-size:0.84rem;color:#b8f0cd;">'
        f'📁 <b>{total_saved}</b> reviews saved permanently<br>'
        f'<span style="opacity:0.7;font-size:0.78rem;">Stored in pesa_salama_history.json</span>'
        f'</div>', unsafe_allow_html=True)
    st.markdown("")
    if st.session_state.history:
        csv_data = export_history_csv(st.session_state.history)
        st.download_button(
            label="⬇️ Download All Results CSV",
            data=csv_data,
            file_name=f"pesa_salama_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )
        if st.button("🗑️ Clear All History"):
            st.session_state.history = []
            st.session_state.last_result = None
            save_persistent_history([])
            st.rerun()
    else:
        st.caption("No results yet.")

# =============================================================================
# HERO
# =============================================================================

st.markdown(
    '<div class="hero-section">'
    '<div class="logo-circle">🛡️</div>'
    '<div class="hero-title">Pesa Salama</div>'
    '<div class="hero-subtitle">Multilingual sentiment intelligence for mobile money customer reviews, complaints, and service feedback analysis.</div>'
    '<div class="feature-badges">'
    '<span class="badge">🌍 Multilingual</span>'
    '<span class="badge">💸 Fintech Analytics</span>'
    '<span class="badge">🔔 Smart Alerts</span>'
    '</div></div>',
    unsafe_allow_html=True
)

# =============================================================================
# SINGLE REVIEW INPUT
# =============================================================================

review = st.text_area(
    "✍️ Enter a customer review",
    placeholder="e.g. This app is not working and keeps crashing / Hii app ni mbaya sana",
    height=150,
)
analyze_btn = st.button("🔍 Analyze Review")

# =============================================================================
# SINGLE REVIEW RESULT
# =============================================================================

if analyze_btn:
    if not review.strip():
        st.warning("⚠️ Please enter a review.")
    else:
        with st.spinner("Analysing..."):
            sentiment_key, confidence, probabilities = predict_sentiment(review, lang_mode)
            category = detect_complaint_category(review)
            language = detect_language(review, lang_mode)

        label, card_class, bar_color = SENTIMENT_DISPLAY[sentiment_key]
        is_urgent    = sentiment_key == "negative" and category in URGENT_CATEGORIES
        is_uncertain = confidence < confidence_threshold

        new_entry = {
            "date":date.today().strftime("%Y-%m-%d"),
            "time":datetime.now().strftime("%H:%M:%S"),
            "review":review,"sentiment":sentiment_key,
            "confidence":confidence,"category":category,
            "language":language,"feedback":"","source":"manual",
        }
        st.session_state.history.insert(0, new_entry)
        save_persistent_history(st.session_state.history)
        st.session_state.last_result = 0
        check_and_alert(new_entry, st.session_state.settings, confidence_threshold, neg_pct_threshold)

        st.markdown("---")
        st.markdown("## 📊 Analysis Results")

        if is_urgent:
            st.markdown('<div class="result-card card-urgent"><div class="card-label">⚠️ Urgent Flag</div><div class="card-value">Negative sentiment on a critical issue — needs immediate attention</div></div>', unsafe_allow_html=True)
        if is_uncertain:
            st.info(f"🤔 Low confidence ({confidence}%) — below your threshold of {confidence_threshold}%. Consider reviewing manually.")

        st.markdown(f'<div class="result-card {card_class}"><div class="card-label">Predicted Sentiment</div><div class="card-value">{label}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="result-card card-info"><div class="card-label">Confidence Score</div><div class="card-value">{confidence}%</div><div class="conf-bar-wrap"><div class="conf-bar-fill" style="width:{confidence}%;background:{bar_color};"></div></div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="result-card card-info"><div class="card-label">Complaint Category</div><div class="card-value">{category}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="result-card card-info"><div class="card-label">Detected Language</div><div class="card-value">{language}</div></div>', unsafe_allow_html=True)

        st.markdown("### 📈 Class Probability Breakdown")
        cols = st.columns(3)
        for i, (class_int, class_name) in enumerate(CLASS_MAP.items()):
            disp_label, _, _ = SENTIMENT_DISPLAY[class_name]
            with cols[i]:
                st.metric(label=disp_label, value=f"{round(float(probabilities[class_int])*100,1)}%")

        result_json = json.dumps({
            "date":new_entry["date"],"review":review,"sentiment":sentiment_key,
            "confidence":confidence,"category":category,"language":language,"urgent":is_urgent,
        }, indent=2)
        st.download_button("⬇️ Export This Result (JSON)", data=result_json,
            file_name="pesa_salama_result.json", mime="application/json")

# =============================================================================
# FEEDBACK
# =============================================================================

if st.session_state.last_result is not None and st.session_state.history:
    idx = st.session_state.last_result
    current_feedback = st.session_state.history[idx].get("feedback","")
    st.markdown("### 💬 Was this prediction correct?")
    if current_feedback:
        icons = {"correct":"👍","incorrect":"👎","unsure":"🤷"}
        msgs  = {"correct":"Marked as correct!","incorrect":"Marked as incorrect.","unsure":"Marked as unsure."}
        st.success(f"{icons[current_feedback]} {msgs[current_feedback]}")
    else:
        fb1,fb2,fb3 = st.columns(3)
        with fb1:
            if st.button("👍 Yes, correct"):
                st.session_state.history[idx]["feedback"] = "correct"
                save_persistent_history(st.session_state.history); st.rerun()
        with fb2:
            if st.button("👎 No, wrong"):
                st.session_state.history[idx]["feedback"] = "incorrect"
                save_persistent_history(st.session_state.history); st.rerun()
        with fb3:
            if st.button("🤷 Not sure"):
                st.session_state.history[idx]["feedback"] = "unsure"
                save_persistent_history(st.session_state.history); st.rerun()

# =============================================================================
# HISTORY + DATE FILTER + CHARTS
# =============================================================================

if st.session_state.history:
    st.markdown("---")
    st.markdown("## 🕓 History & Insights")

    fc1, fc2 = st.columns([1,3])
    with fc1:
        date_filter = st.selectbox("📅 Show", ["Today","This Week","This Month","All Time"], index=3)
    with fc2:
        use_custom = st.checkbox("Use custom date range")

    if use_custom:
        cr1,cr2 = st.columns(2)
        with cr1: start_date = st.date_input("From", value=date.today())
        with cr2: end_date   = st.date_input("To",   value=date.today())
        filtered = [h for h in st.session_state.history
                    if start_date.strftime("%Y-%m-%d") <= h.get("date","") <= end_date.strftime("%Y-%m-%d")]
        filter_label = f"{start_date} → {end_date}"
    else:
        filtered = filter_by_date(st.session_state.history, date_filter)
        filter_label = date_filter

    # Source filter
    all_sources = list(set(h.get("source","manual") for h in st.session_state.history))
    if len(all_sources) > 1:
        source_filter = st.multiselect("Filter by source", options=all_sources, default=all_sources)
        filtered = [h for h in filtered if h.get("source","manual") in source_filter]

    if not filtered:
        st.info(f"No reviews found for: {filter_label}")
    else:
        total    = len(filtered)
        pos      = sum(1 for h in filtered if h["sentiment"]=="positive")
        neg      = sum(1 for h in filtered if h["sentiment"]=="negative")
        neu      = sum(1 for h in filtered if h["sentiment"]=="neutral")
        urgent_c = sum(1 for h in filtered if h["sentiment"]=="negative" and h["category"] in URGENT_CATEGORIES)
        avg_conf = round(sum(h["confidence"] for h in filtered)/total, 1)

        st.markdown(
            f'<div class="summary-bar">'
            f'<span>📅 <b>{filter_label}</b></span>'
            f'<span>📋 <b>{total}</b> reviews</span>'
            f'<span>✅ <b>{pos}</b> positive</span>'
            f'<span>⚖️ <b>{neu}</b> neutral</span>'
            f'<span>❌ <b>{neg}</b> negative</span>'
            f'<span>⚠️ <b>{urgent_c}</b> urgent</span>'
            f'<span>📊 Avg confidence: <b>{avg_conf}%</b></span>'
            f'</div>', unsafe_allow_html=True)

        c1,c2 = st.columns(2)
        with c1:
            st.markdown("**Sentiment Breakdown**")
            st.plotly_chart(make_sentiment_pie(filtered), use_container_width=True, config={"displayModeBar":False})
        with c2:
            st.markdown("**Issues by Category**")
            st.plotly_chart(make_category_bar(filtered), use_container_width=True, config={"displayModeBar":False})

        st.markdown("**Confidence per Review**")
        st.plotly_chart(make_confidence_histogram(list(reversed(filtered))), use_container_width=True, config={"displayModeBar":False})

        if date_filter in ["This Week","This Month","All Time"] or use_custom:
            st.markdown("**Reviews per Day**")
            st.plotly_chart(make_daily_trend(filtered), use_container_width=True, config={"displayModeBar":False})

        st.markdown("**Recent Reviews**")
        s_icons = {"positive":"✅","negative":"❌","neutral":"⚖️"}
        for entry in filtered[:10]:
            icon    = s_icons.get(entry["sentiment"],"❓")
            preview = entry["review"][:75]+"..." if len(entry["review"])>75 else entry["review"]
            fb      = f' · Feedback: <b>{entry["feedback"]}</b>' if entry.get("feedback") else ""
            src     = f' · <span style="opacity:0.5;">{entry.get("source","manual")}</span>'
            st.markdown(
                f'<div class="history-row">'
                f'<span style="opacity:0.5;font-size:0.75rem;">{entry.get("date","")} {entry.get("time","")}</span>&nbsp;&nbsp;'
                f'{icon} <b>{entry["sentiment"].capitalize()}</b> &nbsp;·&nbsp;'
                f'{entry["confidence"]}% &nbsp;·&nbsp; {entry["category"]} &nbsp;·&nbsp; {entry["language"]}{fb}{src}<br>'
                f'<span style="opacity:0.7;">{preview}</span>'
                f'</div>', unsafe_allow_html=True)

        if total > 10:
            st.caption(f"Showing latest 10 of {total}. Download the full CSV from the sidebar.")

# =============================================================================
# FOOTER
# =============================================================================

st.markdown('<div class="footer">Pesa Salama &nbsp;•&nbsp; Powered by XGBoost + TF-IDF &nbsp;•&nbsp; Built with Streamlit &nbsp;•&nbsp; v2.0</div>', unsafe_allow_html=True)
