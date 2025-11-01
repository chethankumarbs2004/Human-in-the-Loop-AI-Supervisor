# agent.py
"""
Simple AI agent simulation.
- Uses an in-memory business_info dict + knowledge base in DB to answer questions.
- If unable to answer, creates a HelpRequest via Flask endpoint (/create-request) or DB direct.
"""

from db import KnowledgeBase, HelpRequest, db, RequestStatus
from datetime import datetime
import re

# Basic business info (the "prompted" info)
BUSINESS_INFO = {
    "name": "Cozy Salon",
    "hours": "10:00 AM - 6:00 PM",
    "services": "Haircuts, Styling, Coloring, Manicure",
    "location": "123 Main Street"
}

def normalize_text(s: str):
    return re.sub(r'\s+', ' ', s.strip().lower())

def try_answer(question: str):
    qn_norm = normalize_text(question)
    # 1) Check knowledge base (DB)
    kb = KnowledgeBase.query.all()
    for k in kb:
        if normalize_text(k.question) == qn_norm:
            return k.answer, "kb"

    # 2) Simple business info match
    if "hour" in qn_norm or "open" in qn_norm:
        return f"We are open {BUSINESS_INFO['hours']}.", "info"
    if "service" in qn_norm or "pedicure" in qn_norm or "manicure" in qn_norm:
        # if "manicure" is in services, answer yes
        if "manicure" in BUSINESS_INFO["services"].lower():
            return f"Yes — we offer {BUSINESS_INFO['services']}.", "info"
    if "where" in qn_norm or "location" in qn_norm or "address" in qn_norm:
        return f"Our location is {BUSINESS_INFO['location']}.", "info"

    # else unknown
    return None, None

def handle_incoming_call(question: str, caller_id: str = None):
    """
    Called to simulate an incoming call text question.
    Returns a dict with outcome and any created help_request id.
    """
    answer, source = try_answer(question)
    if answer:
        # simulate speaking back
        print(f"AI -> Caller ({caller_id}): {answer}  [source: {source}]")
        return {"status": "answered", "answer": answer, "source": source}

    # Create help request in DB
    req = HelpRequest(question=question, caller_id=caller_id)
    db.session.add(req)
    db.session.commit()

    # Simulate texting the supervisor (console log / webhook)
    print(f"AI -> Caller ({caller_id}): Let me check with my supervisor and get back to you.")
    print(f"Notify Supervisor: Hey, I need help answering: \"{question}\" (request id: {req.id})")

    return {"status": "escalated", "request_id": req.id}
