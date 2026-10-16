from __future__ import annotations
"""
Email drafting tool. Rule/template-based (no ML needed) â€” picks a
template based on keywords in the request, then fills it in.
"""

TEMPLATES = {
    "followup": (
        "Subject: Following Up: {topic}\n\n"
        "Dear {name},\n\n"
        "I hope this email finds you well.\n\n"
        "I am writing to follow up on our previous correspondence regarding {topic}. "
        "Could you please provide a brief update on the current status at your earliest convenience?\n\n"
        "If you need any additional information from my end, please do not hesitate to ask.\n\n"
        "Thank you for your time and assistance.\n\n"
        "Best regards,\n{sender}"
    ),
    "apology": (
        "Subject: Update regarding {topic} - Apologies for the Delay\n\n"
        "Dear {name},\n\n"
        "I hope you are having a productive week.\n\n"
        "Please accept my sincere apologies for the delay in getting back to you regarding {topic}. {reason} "
        "We are actively working on it and I will ensure this is resolved by {deadline}.\n\n"
        "Thank you for your patience and understanding.\n\n"
        "Best regards,\n{sender}"
    ),
    "reminder": (
        "Subject: Gentle Reminder: Action Required on {topic}\n\n"
        "Dear {name},\n\n"
        "I hope you are doing well.\n\n"
        "This is a gentle reminder regarding {topic}. Please let me know if there are any blockers or if you need further clarification to proceed.\n\n"
        "Looking forward to hearing from you soon.\n\n"
        "Best regards,\n{sender}"
    ),
    "thankyou": (
        "Subject: Thank You - {topic}\n\n"
        "Dear {name},\n\n"
        "I am writing to express my sincere gratitude for your time and insights today. "
        "I greatly appreciated our discussion on {topic}, and I look forward to our continued collaboration.\n\n"
        "Please feel free to reach out if you have any further questions.\n\n"
        "Best regards,\n{sender}"
    ),
    "greeting": (
        "Subject: Hello from {sender}\n\n"
        "Dear {name},\n\n"
        "I hope this email finds you well. I am reaching out to say hello and connect regarding {topic}.\n\n"
        "Please let me know a convenient time for us to speak further.\n\n"
        "Best regards,\n{sender}"
    ),
    "response_to_thanks": (
        "Subject: Re: Thank You\n\n"
        "Dear {name},\n\n"
        "You are very welcome! It was my pleasure to assist with {topic}. "
        "Please do not hesitate to reach out if anything else comes up.\n\n"
        "Best regards,\n{sender}"
    ),
    "generic": (
        "Subject: Regarding {topic}\n\n"
        "Dear {name},\n\n"
        "I hope you are doing well.\n\n"
        "{body}\n\n"
        "Please let me know if you need any further information.\n\n"
        "Best regards,\n{sender}"
    ),
    "leave": (
        "Subject: Leave Request - {topic}\n\n"
        "Dear {name},\n\n"
        "I am writing to formally request a leave of absence for {topic}.\n\n"
        "{body}\n\n"
        "I will ensure all my pending tasks are handed over appropriately before my departure. "
        "Please let me know if you need any further information or have any concerns.\n\n"
        "Thank you for your understanding.\n\n"
        "Best regards,\n{sender}"
    ),
}

_KEYWORD_MAP = {
    "follow up": "followup", "followed up": "followup", "haven't responded": "followup",
    "apolog": "apology", "delay": "apology", "sorry": "apology",
    "remind": "reminder",
    "thank you": "thankyou", "thanks": "thankyou",
    "hello": "greeting", "hi ": "greeting", "greeting": "greeting",
    "welcome": "response_to_thanks", "no problem": "response_to_thanks", "my pleasure": "response_to_thanks",
    "leave": "leave", "vacation": "leave", "sick": "leave", "absence": "leave"
}


def _pick_template(text: str) -> str:
    lowered = text.lower()
    for keyword, template_key in _KEYWORD_MAP.items():
        if keyword in lowered:
            return template_key
    return "generic"


import re

def _parse_input(text: str) -> dict:
    recipient = "there"
    topic = text[:60]
    
    to_match = re.search(r"\bto\s+([A-Z][a-zA-Z\s\(\)]+)(?:\b|$)", text, re.IGNORECASE)
    if to_match:
        recipient = to_match.group(1).strip()
        
    clean_text = re.sub(r"^(draft|write|compose|send)\s+(a|an|the)?\s*", "", text, flags=re.IGNORECASE)
    clean_text = re.sub(r"(email|message|letter)\s*", "", clean_text, flags=re.IGNORECASE)
    clean_text = re.sub(r"\bto\s+[A-Z][a-zA-Z\s\(\)]+(?:\b|$)", "", clean_text, flags=re.IGNORECASE).strip()
    
    if clean_text:
        topic = clean_text[:60]
        
    return {"recipient": recipient, "topic": topic, "clean_text": clean_text}

def run(input_text: str, context: dict) -> dict:
    template_key = _pick_template(input_text)
    template = TEMPLATES[template_key]
    
    parsed = _parse_input(input_text)
    
    body_text = context.get("summary")
    if not body_text:
        body_text = parsed["clean_text"]

    draft = template.format(
        name=context.get("recipient_name", parsed["recipient"]),
        sender=context.get("sender_name", "the team"),
        topic=context.get("topic", parsed["topic"]),
        reason=context.get("reason", "We ran into an unexpected delay."),
        deadline=context.get("deadline", "end of this week"),
        body=body_text,
    )

    return {
        "result": f"Here is a drafted '{template_key}' email based on your request:\n\n{draft}",
        "template_used": template_key,
        "status": "success",
    }
