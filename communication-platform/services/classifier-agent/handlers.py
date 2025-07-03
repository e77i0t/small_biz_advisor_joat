# Handlers for the Classifier Agent service 
from typing import List, Dict, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from communication_platform.shared.models import Message, ConversationCategory
from .models import ClassificationRequest, ClassificationResponse, AIClassificationResult, RuleBasedResult
from communication_platform.services.conversation_grouper.database import ConversationDB
from communication_platform.services.twilio_monitor.database import MessageDB
from communication_platform.shared.database import SessionLocal
import os
import openai
import asyncio
import json
import random

# Confidence thresholds
AI_CONFIDENCE_THRESHOLD = 0.7
RULE_CONFIDENCE_THRESHOLD = 0.5

# Keyword rules for fallback classification
CLASSIFICATION_RULES: Dict[ConversationCategory, List[str]] = {
    ConversationCategory.new_lead: ["interested", "quote", "estimate", "pricing", "new customer"],
    ConversationCategory.quote_request: ["quote", "estimate", "price", "cost"],
    ConversationCategory.status_update: ["status", "update", "progress", "check in"],
    ConversationCategory.reminder: ["reminder", "appointment", "schedule", "upcoming"],
    ConversationCategory.spam: ["unsubscribe", "spam", "stop", "remove"],
    ConversationCategory.support: ["help", "support", "issue", "problem", "fix"],
    ConversationCategory.other: []
}

async def classify_conversation(conversation_id: UUID, trace_id: UUID) -> ClassificationResponse:
    """
    Fetches conversation and messages, tries AI classification, falls back to rule-based, stores and returns result.
    """
    with SessionLocal() as db:
        # Fetch conversation and messages
        conversation = db.query(ConversationDB).filter(ConversationDB.conversation_id == conversation_id).first()
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        messages_orm = conversation.get_messages() if hasattr(conversation, 'get_messages') else []
        if not messages_orm:
            raise ValueError(f"No messages found for conversation {conversation_id}")
        # Convert ORM messages to Pydantic Message models
        messages = [
            Message(
                message_id=m.message_id,
                type=m.type,
                **{"from": m.from_phone, "to": m.to_phone},
                content=m.content,
                timestamp=m.timestamp.timestamp() if hasattr(m.timestamp, 'timestamp') else float(m.timestamp),
                customer_id=m.customer_id,
                conversation_id=m.conversation_id
            ) for m in messages_orm
        ]
        text = extract_conversation_text(messages)
        context = {"customer_id": conversation.customer_id}
        # Try AI classification
        ai_result = await classify_with_openai(text, context)
        if ai_result and ai_result.confidence >= AI_CONFIDENCE_THRESHOLD:
            # Store result
            conversation.category = ai_result.category.value if isinstance(ai_result.category, ConversationCategory) else str(ai_result.category)
            conversation.confidence = ai_result.confidence
            db.commit()
            return ClassificationResponse(
                conversation_id=conversation_id,
                category=ai_result.category if isinstance(ai_result.category, ConversationCategory) else ConversationCategory(ai_result.category),
                confidence=ai_result.confidence,
                reasoning=ai_result.reasoning
            )
        # Fallback to rule-based
        rule_result = classify_with_rules(text, context)
        if rule_result and rule_result.confidence >= RULE_CONFIDENCE_THRESHOLD:
            conversation.category = rule_result.category.value if isinstance(rule_result.category, ConversationCategory) else str(rule_result.category)
            conversation.confidence = rule_result.confidence
            db.commit()
            return ClassificationResponse(
                conversation_id=conversation_id,
                category=rule_result.category if isinstance(rule_result.category, ConversationCategory) else ConversationCategory(rule_result.category),
                confidence=rule_result.confidence,
                reasoning=rule_result.reasoning
            )
        # Default to 'other'
        conversation.category = ConversationCategory.other.value
        conversation.confidence = 0.0
        db.commit()
        return ClassificationResponse(
            conversation_id=conversation_id,
            category=ConversationCategory.other,
            confidence=0.0,
            reasoning="No confident classification could be made."
        )

async def classify_with_openai(text: str, context: dict = None) -> Optional[AIClassificationResult]:
    """
    Use OpenAI API to classify the conversation text, expecting a JSON response. Includes retry logic.
    """
    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        return None
    categories = [cat.value for cat in ConversationCategory]
    prompt = (
        "You are an expert conversation classifier. "
        "Classify the following conversation into one of these categories: "
        f"{categories}. "
        "Respond ONLY in valid JSON with the following fields: category, confidence, reasoning. "
        "Example: {\\"category\\": \\\"support\\\", \\\"confidence\\\": 0.92, \\\"reasoning\\\": \\\"The user asked for help.\\\"} "
        f"Conversation: {text}\nContext: {context or {}}"
    )
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "You are a classification assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=256,
                temperature=0.2
            )
            content = response["choices"][0]["message"]["content"]
            # Try to parse JSON from the response
            try:
                # Find the first and last curly braces to extract JSON
                start = content.find('{')
                end = content.rfind('}') + 1
                json_str = content[start:end]
                data = json.loads(json_str)
                category = data.get("category", "other").strip().lower()
                try:
                    category_enum = ConversationCategory(category)
                except Exception:
                    category_enum = ConversationCategory.other
                confidence = float(data.get("confidence", 0.0))
                reasoning = data.get("reasoning", "")
                model_used = "gpt-4-turbo"
                return AIClassificationResult(
                    category=category_enum,
                    confidence=confidence,
                    reasoning=reasoning,
                    model_used=model_used
                )
            except Exception as parse_err:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt + random.random())
                continue
        except openai.error.RateLimitError as rate_err:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt + random.random())
            continue
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt + random.random())
            continue
    return None

def classify_with_rules(text: str, context: dict) -> Optional[RuleBasedResult]:
    """
    Rule-based classification using keyword matching.
    """
    text_lower = text.lower()
    for category, keywords in CLASSIFICATION_RULES.items():
        for kw in keywords:
            if kw in text_lower:
                return RuleBasedResult(
                    category=category,
                    confidence=0.6,
                    reasoning=f"Matched keyword '{kw}' for category '{category}'."
                )
    return RuleBasedResult(
        category=ConversationCategory.other,
        confidence=0.3,
        reasoning="No keyword match found."
    )

def extract_conversation_text(messages: List[Message]) -> str:
    """
    Concatenate message contents for classification.
    """
    return "\n".join([msg.content for msg in messages if hasattr(msg, 'content')]) 