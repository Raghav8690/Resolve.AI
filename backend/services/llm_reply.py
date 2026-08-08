import os
import json
from openai import OpenAI
from backend.config import OPENROUTER_MODEL, OPENROUTER_BASE_URL
from backend.models.schemas import OrderContext, Precedent

_client = None
_reply_cache = {}

def get_client():
    global _client
    if _client is None:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not set in environment")
        _client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key)
    return _client

def generate_reply(ticket_id: str, description: str, action: str, order: OrderContext, precedents: list[Precedent]) -> str:
    cache_key = f"{ticket_id}:{action}"
    if cache_key in _reply_cache:
        return _reply_cache[cache_key]
    
    prompt = f"""Write a customer support reply for a Zepto order issue.

Ticket: {description}
Order: {order.order_id}, Value: ₹{order.value_inr}, Status: {order.delivery_status}
Resolution: {action}

Write a concise, empathetic reply (2-3 sentences) that:
- Acknowledges the issue
- States the resolution clearly
- References the specific order
- Uses professional, helpful tone

Reply:"""
    
    try:
        client = get_client()
        response = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.3
        )
        reply = response.choices[0].message.content.strip()
    except Exception as e:
        reply = f"We've resolved your issue: {action} for order {order.order_id}. You'll receive confirmation shortly."
    
    _reply_cache[cache_key] = reply
    return reply
