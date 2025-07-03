# Placeholder for spam-detector handlers 
import re
from datetime import datetime
from uuid import UUID
from typing import List, Tuple, Optional
import httpx
import asyncio
import aioredis
from .models import SpamEvaluationResponse, Action

# Spam detection configuration
SPAM_KEYWORDS = [
    "free", "win", "winner", "prize", "cash", "urgent", "claim", "click", "buy now", "limited offer"
]
SPAM_PATTERNS = [
    re.compile(r"\\b(?:\d{10,})\\b"),  # long digit sequences
    re.compile(r"http[s]?://[\\w./-]+"),  # URLs
    re.compile(r"[A-Z]{5,}"),  # long uppercase words
]
BLOCK_THRESHOLD = 0.8
FLAG_THRESHOLD = 0.6

# Redis and rate limit config
REDIS_URL = "redis://localhost:6379/0"
REDIS_EXPIRE = 3600  # 1 hour
RATE_LIMIT = 10  # max 10 external calls per minute
RATE_LIMIT_KEY = "external_api_rate_limit"

redis = None

async def get_redis():
    global redis
    if redis is None:
        redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    return redis

async def check_external_spam_db(phone_number: str) -> Optional[float]:
    """
    Query an external spam database (Truecaller-style) for phone reputation.
    Returns a score (0.0 good, 1.0 bad) or None if unavailable.
    Caches results in Redis and rate limits external calls.
    """
    redis_conn = await get_redis()
    cache_key = f"spamdb:{phone_number}"
    cached = await redis_conn.get(cache_key)
    if cached is not None:
        return float(cached)
    # Rate limiting
    calls = await redis_conn.incr(RATE_LIMIT_KEY)
    if calls == 1:
        await redis_conn.expire(RATE_LIMIT_KEY, 60)
    if calls > RATE_LIMIT:
        return None  # Rate limit exceeded, fallback
    # External API call (placeholder URL)
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"https://public-spam-api.example.com/lookup?phone={phone_number}")
            if resp.status_code == 200:
                data = resp.json()
                score = float(data.get("spam_score", 0.0))  # 0.0-1.0
                await redis_conn.set(cache_key, score, ex=REDIS_EXPIRE)
                return score
    except Exception as e:
        # Log error (placeholder)
        pass
    return None  # Fallback if API fails

async def evaluate_spam(phone_number: str, message: str, timestamp: datetime, trace_id: UUID) -> SpamEvaluationResponse:
    # Run detection methods
    content_score, content_reasons = analyze_message_content(message)
    # Try external spam DB first
    external_score = await check_external_spam_db(phone_number)
    if external_score is not None:
        reputation_score = external_score
    else:
        reputation_score = await check_phone_reputation(phone_number)
    timing_score = check_timing_patterns(phone_number, timestamp)

    # Combine scores (weighted average)
    weights = [0.5, 0.3, 0.2]  # content, reputation, timing
    scores = [content_score, reputation_score, timing_score]
    score = sum(w * s for w, s in zip(weights, scores))

    # Determine action
    if score >= BLOCK_THRESHOLD:
        action = Action.BLOCK
    elif score >= FLAG_THRESHOLD:
        action = Action.FLAG
    else:
        action = Action.ALLOW

    # Collect reasons
    reasons = content_reasons
    if reputation_score > 0.5:
        reasons.append("Phone number has poor reputation.")
    if timing_score > 0.5:
        reasons.append("Suspicious timing pattern detected.")
    if external_score is not None:
        reasons.append("External spam DB checked.")
    else:
        reasons.append("External spam DB unavailable, used internal rules.")

    # Store evaluation result (placeholder)
    # TODO: Implement database storage

    return SpamEvaluationResponse(
        is_spam=score >= FLAG_THRESHOLD,
        score=score,
        reasons=reasons,
        action=action
    )

async def check_phone_reputation(phone_number: str) -> float:
    # Placeholder: Simulate reputation check (0.0 = good, 1.0 = bad)
    # TODO: Implement real reputation lookup
    if phone_number.endswith("9999"):
        return 0.9  # bad reputation
    return 0.1  # good reputation

def analyze_message_content(message: str) -> Tuple[float, List[str]]:
    reasons = []
    score = 0.0
    lower_msg = message.lower()
    for keyword in SPAM_KEYWORDS:
        if keyword in lower_msg:
            score += 0.2
            reasons.append(f"Keyword detected: '{keyword}'")
    for pattern in SPAM_PATTERNS:
        if pattern.search(message):
            score += 0.2
            reasons.append(f"Pattern matched: {pattern.pattern}")
    score = min(score, 1.0)
    return score, reasons

def check_timing_patterns(phone_number: str, timestamp: datetime) -> float:
    # Placeholder: Simulate timing pattern analysis
    # TODO: Implement real timing analysis
    if timestamp.hour < 6 or timestamp.hour > 22:
        return 0.7  # suspicious time
    return 0.1  # normal time 