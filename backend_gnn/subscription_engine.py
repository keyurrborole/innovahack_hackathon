"""
Subscription Leak Detection Engine
====================================
Pure Python + numpy — no heavy ML dependencies required.

Given a list of transactions (date, description, amount), this engine:
1. Clusters transactions by merchant/description similarity
2. Detects recurring payment intervals (monthly, yearly, weekly)
3. Flags silent price increases (same merchant, increasing amount)
4. Identifies unused subscriptions (large gaps in transaction history)
5. Computes a "Leak Score" (0-100) per subscription
6. Recommends an action plan (cancel / downgrade / renegotiate)
"""
from __future__ import annotations
import re
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Any

import numpy as np

logger = logging.getLogger("subscription-engine")

# ── Constants ────────────────────────────────────────────────────────────────
RECURRENCE_WINDOWS = {
    "weekly":    (5,  10),    # 7d ± tolerance (days)
    "monthly":   (25, 35),
    "quarterly": (80, 100),
    "yearly":    (350, 380),
}

CANCEL_THRESHOLD   = 70   # leak score above this → CANCEL
DOWNGRADE_THRESHOLD = 45  # leak score above this → DOWNGRADE
RENEGOTIATE_THRESHOLD = 25  # above this → RENEGOTIATE

SUBSCRIPTION_KEYWORDS = [
    "netflix","spotify","amazon","prime","apple","google","microsoft",
    "adobe","slack","zoom","dropbox","hulu","disney","youtube","linkedin",
    "github","notion","figma","canva","grammarly","mcafee","norton",
    "avast","bitdefender","lastpass","1password","dashlane","expressvpn",
    "nordvpn","surfshark","chatgpt","openai","midjourney","claude",
    "subscription","renewal","auto-debit","standing order","emi",
    "insurance","loan","membership","annual fee","monthly fee",
    "bill","recharge","dth","broadband","wifi","gas","electricity",
    "water","postpaid","prepaid","paytm","phonepe","gpay","upi",
]

# ── Parsing utilities ─────────────────────────────────────────────────────────

def _normalize_merchant(desc: str) -> str:
    """Strip noise from a transaction description to get merchant name."""
    desc = desc.upper()
    # Remove transaction IDs, UPI refs, timestamps
    desc = re.sub(r'\b(UPI|NEFT|IMPS|RTGS|REF|TXN|ID|#)\s*[\w\-]+', '', desc)
    desc = re.sub(r'\b\d{6,}\b', '', desc)       # long numeric IDs
    desc = re.sub(r'[^A-Z0-9 ]', ' ', desc)
    desc = re.sub(r'\s+', ' ', desc).strip()
    # Take first 3 meaningful words
    words = [w for w in desc.split() if len(w) > 2]
    return ' '.join(words[:3]) if words else desc[:20]


def _merchant_similarity(a: str, b: str) -> float:
    """Jaccard similarity on character 3-grams."""
    def ngrams(s, n=3):
        s = s.lower().replace(' ', '')
        return set(s[i:i+n] for i in range(len(s)-n+1))
    sa, sb = ngrams(a), ngrams(b)
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _parse_date(val: str) -> datetime | None:
    formats = [
        "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y",
        "%Y-%m-%dT%H:%M:%S", "%d %b %Y", "%d %B %Y",
        "%b %d, %Y", "%d/%m/%y", "%d-%b-%Y", "%d %b, %Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(val.strip(), fmt)
        except ValueError:
            continue
    return None


def _parse_amount(val: str | float | int) -> float | None:
    if isinstance(val, (int, float)):
        return abs(float(val))
    val = str(val).replace(',', '').replace('₹', '').replace('$', '').replace('INR', '').strip()
    val = re.sub(r'[^\d.]', '', val)
    try:
        return abs(float(val)) if val else None
    except ValueError:
        return None


# ── Column detection ─────────────────────────────────────────────────────────

def _detect_columns(headers: list[str]) -> dict:
    """Auto-detect which column is date / amount / description."""
    mapping = {}
    date_kw    = ['date', 'time', 'timestamp', 'txn date', 'transaction date', 'value date', 'posting']
    amount_kw  = ['amount', 'debit', 'credit', 'value', 'sum', 'rs', 'inr', 'price', 'charge']
    desc_kw    = ['description', 'narration', 'particulars', 'merchant', 'payee', 'details',
                  'remarks', 'reference', 'mode', 'upi', 'transaction', 'name', 'memo']

    h_lower = [h.lower().strip() for h in headers]

    def best(keywords):
        for kw in keywords:
            for i, h in enumerate(h_lower):
                if kw in h:
                    return headers[i]
        return None

    mapping['date']   = best(date_kw)
    mapping['amount'] = best(amount_kw)
    mapping['desc']   = best(desc_kw)
    return mapping


# ── SMS parser ───────────────────────────────────────────────────────────────

def parse_sms_text(text: str) -> list[dict]:
    """Extract transactions from raw SMS/notification text."""
    transactions = []
    # Pattern: debited / charged / payment of / Rs. <amount> to/for <merchant>
    patterns = [
        r'(?:debited|charged|paid|payment of)[^\d]*(?:Rs\.?|INR|₹)?\s*([\d,]+(?:\.\d{1,2})?)\s*(?:to|for|at|via|towards)?\s*([A-Za-z][^\n\r\.]{3,40})',
        r'(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d{1,2})?)\s*(?:debited|deducted|charged|paid)\s*(?:to|for|at|via|towards)?\s*([A-Za-z][^\n\r\.]{3,40})',
        r'(?:auto.?debit|standing.?order|subscription)[^\d]*(?:Rs\.?|INR|₹)?\s*([\d,]+(?:\.\d{1,2})?)[^\n\r]*?([A-Za-z][^\n\r\.]{3,30})',
    ]
    date_pattern = r'(\d{1,2}[-/]\w{2,9}[-/]\d{2,4}|\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})'

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        for pat in patterns:
            m = re.search(pat, line, re.IGNORECASE)
            if m:
                amount = _parse_amount(m.group(1))
                merchant = m.group(2).strip()[:40]
                date_m = re.search(date_pattern, line)
                date = _parse_date(date_m.group(1)) if date_m else datetime.today()
                if amount and amount > 0:
                    transactions.append({
                        'date': date or datetime.today(),
                        'description': merchant,
                        'amount': amount,
                        'source': 'sms',
                    })
                break
    return transactions


# ── Core detection ───────────────────────────────────────────────────────────

def _group_by_merchant(transactions: list[dict]) -> dict[str, list[dict]]:
    """Group transactions into merchant clusters using similarity."""
    clusters: dict[str, list[dict]] = {}
    keys: list[str] = []

    for txn in transactions:
        merchant = _normalize_merchant(txn.get('description', ''))
        txn['_merchant'] = merchant

        # Find best matching existing cluster
        best_key, best_sim = None, 0.0
        for k in keys:
            sim = _merchant_similarity(merchant, k)
            if sim > best_sim:
                best_sim, best_key = sim, k

        if best_sim >= 0.4:
            clusters[best_key].append(txn)
        else:
            clusters[merchant] = [txn]
            keys.append(merchant)

    return clusters


def _detect_recurrence(dates: list[datetime]) -> tuple[str | None, float]:
    """Return (interval_name, confidence) for a sorted list of dates."""
    if len(dates) < 2:
        return None, 0.0

    dates = sorted(dates)
    gaps = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
    if not gaps:
        return None, 0.0

    avg_gap = float(np.mean(gaps))
    std_gap = float(np.std(gaps)) if len(gaps) > 1 else 0.0

    # Coefficient of variation — low means consistent
    cv = std_gap / avg_gap if avg_gap > 0 else 1.0

    best_name, best_score = None, 0.0
    for name, (lo, hi) in RECURRENCE_WINDOWS.items():
        if lo <= avg_gap <= hi:
            score = max(0.0, 1.0 - cv)   # more consistent → higher score
            if score > best_score:
                best_name, best_score = name, score

    return best_name, round(best_score, 2)


def _price_increase_flags(amounts: list[float], dates: list[datetime]) -> dict:
    """Detect silent price increases over time."""
    if len(amounts) < 3:
        return {"detected": False}

    paired = sorted(zip(dates, amounts))
    amounts_sorted = [a for _, a in paired]

    # Linear regression slope
    x = np.arange(len(amounts_sorted), dtype=float)
    y = np.array(amounts_sorted, dtype=float)
    if len(x) > 1:
        slope = float(np.polyfit(x, y, 1)[0])
    else:
        slope = 0.0

    first_avg = float(np.mean(y[:max(1, len(y)//3)]))
    last_avg  = float(np.mean(y[-(max(1, len(y)//3)):]))
    pct_change = ((last_avg - first_avg) / first_avg * 100) if first_avg > 0 else 0.0

    return {
        "detected":   slope > 0 and pct_change > 5,
        "slope":      round(slope, 2),
        "pct_change": round(pct_change, 1),
        "first_avg":  round(first_avg, 2),
        "last_avg":   round(last_avg, 2),
    }


def _usage_gap_days(dates: list[datetime]) -> int:
    """Days since last transaction for this merchant."""
    if not dates:
        return 0
    return (datetime.today() - max(dates)).days


def _compute_leak_score(
    recurrence_confidence: float,
    interval: str | None,
    price_increase: dict,
    usage_gap_days: int,
    avg_amount: float,
    txn_count: int,
) -> int:
    """
    Leak Score 0–100:
    - Higher = more likely a wasteful/problematic subscription
    Components:
      30pts  recurrence confidence (is it definitely recurring?)
      20pts  price increase detected
      30pts  usage gap (haven't used it recently)
      20pts  amount × frequency weight
    """
    score = 0

    # Recurrence certainty
    score += int(recurrence_confidence * 30)

    # Price increase
    if price_increase.get("detected"):
        pct = price_increase.get("pct_change", 0)
        score += min(20, int(pct / 2))

    # Usage gap
    if usage_gap_days > 180:
        score += 30
    elif usage_gap_days > 90:
        score += 20
    elif usage_gap_days > 30:
        score += 10

    # Amount/frequency weight
    monthly_cost = avg_amount
    if interval == "yearly":
        monthly_cost = avg_amount / 12
    elif interval == "quarterly":
        monthly_cost = avg_amount / 3
    elif interval == "weekly":
        monthly_cost = avg_amount * 4.3

    if monthly_cost > 2000:
        score += 20
    elif monthly_cost > 500:
        score += 12
    elif monthly_cost > 100:
        score += 6

    return min(100, score)


def _recommend_action(leak_score: int, price_increase: dict, usage_gap_days: int) -> dict:
    if leak_score >= CANCEL_THRESHOLD:
        action = "cancel"
        reason = "High cost with low usage"
        if usage_gap_days > 90:
            reason = f"Not used in {usage_gap_days} days — cancel immediately"
        if price_increase.get("detected"):
            reason += f". Silent price increase of {price_increase.get('pct_change',0):.0f}%"
    elif leak_score >= DOWNGRADE_THRESHOLD:
        action = "downgrade"
        reason = "Usage doesn't justify current plan — consider a lower tier"
        if price_increase.get("detected"):
            reason += f". Price crept up {price_increase.get('pct_change',0):.0f}%"
    elif leak_score >= RENEGOTIATE_THRESHOLD:
        action = "renegotiate"
        reason = "Call provider — loyalty discounts or better plans likely available"
    else:
        action = "keep"
        reason = "Active subscription at stable price"

    savings_estimate = 0.0
    return {"action": action, "reason": reason, "savings_estimate": savings_estimate}


# ── Public API ────────────────────────────────────────────────────────────────

def analyse_transactions(transactions: list[dict]) -> dict:
    """
    Main entry point.

    Args:
        transactions: list of dicts with keys: date (datetime), description (str), amount (float)

    Returns:
        dict with subscriptions, summary, leak_score
    """
    if not transactions:
        return {"subscriptions": [], "summary": {}, "overall_leak_score": 0}

    groups = _group_by_merchant(transactions)
    subscriptions = []
    total_monthly_spend = 0.0

    for merchant_key, txns in groups.items():
        if len(txns) < 2:
            continue  # need at least 2 occurrences to call it recurring

        dates   = [t['date'] for t in txns if isinstance(t.get('date'), datetime)]
        amounts = [t['amount'] for t in txns if isinstance(t.get('amount'), (int, float))]

        if not dates or not amounts:
            continue

        interval, confidence = _detect_recurrence(dates)
        if interval is None and confidence == 0.0:
            continue  # not recurring

        avg_amount   = float(np.mean(amounts))
        price_info   = _price_increase_flags(amounts, dates)
        gap_days     = _usage_gap_days(dates)
        leak_score   = _compute_leak_score(confidence, interval, price_info, gap_days, avg_amount, len(txns))
        action       = _recommend_action(leak_score, price_info, gap_days)

        # Monthly cost normalisation
        monthly = avg_amount
        if interval == "yearly":    monthly = avg_amount / 12
        elif interval == "quarterly": monthly = avg_amount / 3
        elif interval == "weekly":  monthly = avg_amount * 4.33

        total_monthly_spend += monthly

        # Potential savings
        if action["action"] in ("cancel", "downgrade"):
            action["savings_estimate"] = round(monthly, 2)

        # Is it a known subscription keyword?
        desc_lower = merchant_key.lower()
        is_known_sub = any(kw in desc_lower for kw in SUBSCRIPTION_KEYWORDS)

        subscriptions.append({
            "merchant":          merchant_key.title(),
            "interval":          interval,
            "recurrence_confidence": confidence,
            "avg_amount":        round(avg_amount, 2),
            "monthly_cost":      round(monthly, 2),
            "total_paid":        round(sum(amounts), 2),
            "transaction_count": len(txns),
            "last_seen":         max(dates).strftime("%Y-%m-%d"),
            "first_seen":        min(dates).strftime("%Y-%m-%d"),
            "days_since_last":   gap_days,
            "price_increase":    price_info,
            "leak_score":        leak_score,
            "action":            action,
            "is_known_subscription": is_known_sub,
            "sample_transactions": [
                {"date": t["date"].strftime("%Y-%m-%d"), "amount": t["amount"],
                 "description": t.get("description", "")}
                for t in sorted(txns, key=lambda x: x["date"], reverse=True)[:5]
            ],
        })

    # Sort by leak score descending
    subscriptions.sort(key=lambda x: x["leak_score"], reverse=True)

    # Overall leak score = weighted avg
    overall = 0
    if subscriptions:
        scores  = [s["leak_score"] for s in subscriptions]
        weights = [s["monthly_cost"] for s in subscriptions]
        if sum(weights) > 0:
            overall = int(np.average(scores, weights=weights))
        else:
            overall = int(np.mean(scores))

    potential_savings = sum(
        s["action"]["savings_estimate"] for s in subscriptions
        if s["action"]["action"] in ("cancel", "downgrade")
    )

    return {
        "subscriptions": subscriptions,
        "summary": {
            "total_subscriptions":   len(subscriptions),
            "total_monthly_spend":   round(total_monthly_spend, 2),
            "potential_monthly_savings": round(potential_savings, 2),
            "cancel_count":          sum(1 for s in subscriptions if s["action"]["action"] == "cancel"),
            "downgrade_count":       sum(1 for s in subscriptions if s["action"]["action"] == "downgrade"),
            "renegotiate_count":     sum(1 for s in subscriptions if s["action"]["action"] == "renegotiate"),
            "price_increase_count":  sum(1 for s in subscriptions if s["price_increase"]["detected"]),
        },
        "overall_leak_score": overall,
    }
