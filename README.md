# Pesa-Salama-Classifier
## Real-time Financial Complaint Monitor and Distress Index for Kenya’s Mobile Money Ecosystem

> An end-to-end NLP pipeline that collects, cleans, and classifies customer reviews from Kenya's top fintech apps, combining classical machine learning with a multilingual transformer (AfriBERTa) to power a real-time financial complaint monitoring system.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Dataset](#dataset)
3. [Project Structure](#project-structure)
4. [Pipeline Walkthrough](#pipeline-walkthrough)
5. [Modelling Results](#modelling-results)
6. [Tech Stack](#tech-stack)
7. [Setup & Installation](#setup--installation)
8. [Usage](#usage)
9. [Key Findings](#key-findings)
10. [Limitations & Future Work](#limitations--future-work)

---

## Project Overview

Kenya's mobile money and digital banking ecosystem processes millions of user transactions daily. Buried in Google Play Store reviews lies a rich, real-time signal of customer frustration — failed transactions, fraud complaints, hidden charges, and broken UX — written in English, Swahili, and Sheng.

This project builds an automated pipeline to:

- Scrape raw, multilingual reviews from six major Kenyan fintech apps
- Preprocess and clean code-switched (English/Swahili/Sheng) text
- Classify reviews by **sentiment** (positive / neutral / negative)
- Detect **complaint categories** (fraud, failed transaction, hidden charges, customer support)
- Explain model predictions using **SHAP**
- Fine-tune **AfriBERTa**, a pretrained African-language transformer, for advanced classification

The end goal is a deployable monitoring system that flags emerging complaint trends in real time.

---

## Dataset

| Property | Detail |
|---|---|
| **Source** | Google Play Store — Kenya country store (`country='ke'`) |
| **Collection method** | `google-play-scraper` Python library (no API key required) |
| **Raw records** | ~53,500 reviews |
| **Date range** | 2023 – April 2026 |
| **Languages** | English, Swahili, Sheng (code-switched) |

### Apps Scraped

| App | Play Store ID | Category |
|---|---|---|
| M-PESA | `com.safaricom.mpesa.lifestyle` | Core mobile money |
| MySafaricom | `com.safaricom.mysafaricom` | Account management |
| KCB Mobile | `com.kcb.mobilebanking.android.mbp` | Traditional bank |
| Equity Mobile | `ke.co.equitygroup.equitymobile` | Traditional bank |
| Tala | `com.inventureaccess.safarirahisi` | Digital micro-lending |
| Branch | `com.branch_international.branch.branch_demo_android` | Digital micro-lending |

### Key Columns (cleaned dataset)

| Column | Description |
|---|---|
| `content` | Original review text |
| `score` | Star rating (1–5) |
| `sentiment` / `sentiment_label` | Positive / Neutral / Negative |
| `complaint_label` | Complaint category (keyword-classified) |
| `fraud_indicator` | Boolean flag for fraud-related language |
| `cleaned_text` | Normalised, emoji-decoded text |
| `processed_text` | Fully preprocessed text ready for TF-IDF |
| `final_language` | Detected language (en / sw / mixed) |
| `app_name` | Source application |

---

> **Convention:** `MASTER_RAW_kenya_fintech.csv` is the permanent, untouched source of truth. All transformations are applied to copies in the preprocessing notebook.