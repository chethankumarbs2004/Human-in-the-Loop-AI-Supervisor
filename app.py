# app.py
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_migrate import Migrate
from db import db, HelpRequest, KnowledgeBase, RequestStatus
from datetime import datetime, timedelta, timezone
import threading, time
import os

# Demo-friendly timeout (seconds). Set via env var if desired.
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "120"))  # default 2 minutes for demo

app = Flask(__name__, 
    template_folder='frontdesk-ai/templates')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///frontdesk.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)

with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return redirect(url_for("dashboard"))

@app.route("/dashboard")
def dashboard():
    pending = HelpRequest.query.filter_by(status=RequestStatus.Pending).order_by(HelpRequest.created_at.desc()).all()
    resolved = HelpRequest.query.filter(HelpRequest.status!=RequestStatus.Pending).order_by(HelpRequest.created_at.desc()).limit(50).all()
    learned = KnowledgeBase.query.order_by(KnowledgeBase.added_on.desc()).all()
    return render_template("dashboard.html", pending=pending, resolved=resolved, learned=learned, timeout_seconds=TIMEOUT_SECONDS)

@app.route("/respond/<request_id>", methods=["GET", "POST"])
def respond(request_id):
    req = HelpRequest.query.get_or_404(request_id)
    if request.method == "GET":
        return render_template("respond.html", req=req)
    # POST: supervisor submitted answer
    answer = request.form.get("answer", "").strip()
    if not answer:
        return "Answer required", 400

    # Update request
    req.supervisor_response = answer
    req.status = RequestStatus.Resolved
    req.resolved_at = datetime.now(timezone.utc)
    db.session.add(req)

    # Update knowledge base (if similar question not exists)
    # For simplicity, use exact match check
    existing = KnowledgeBase.query.filter_by(question=req.question).first()
    if existing:
        existing.answer = answer
    else:
        kb = KnowledgeBase(question=req.question, answer=answer)
        db.session.add(kb)

    db.session.commit()

    # AI follows up to caller (simulated)
    print(f"AI -> Caller ({req.caller_id}): Hi — my supervisor says: {answer} (request id: {req.id})")

    return redirect(url_for("dashboard"))

@app.route("/create-request", methods=["POST"])
def create_request():
    data = request.json or {}
    question = data.get("question")
    caller_id = data.get("caller_id")
    if not question:
        return {"error": "question required"}, 400
    req = HelpRequest(question=question, caller_id=caller_id)
    db.session.add(req)
    db.session.commit()
    print(f"Notify Supervisor: Hey, I need help answering: \"{question}\" (request id: {req.id})")
    return {"id": req.id, "status": req.status.value}, 201

@app.route("/simulate-call", methods=["POST"])
def simulate_call():
    """
    Endpoint to simulate a call (useful for demo).
    JSON: {"question": "Do you offer pedicures?", "caller_id": "caller-123"}
    """
    from agent import handle_incoming_call
    data = request.json or {}
    question = data.get("question")
    caller_id = data.get("caller_id")
    if not question:
        return {"error": "question required"}, 400
    outcome = handle_incoming_call(question, caller_id)
    return jsonify(outcome)

@app.route("/api/requests")
def api_requests():
    allr = HelpRequest.query.order_by(HelpRequest.created_at.desc()).limit(100).all()
    return jsonify([r.to_dict() for r in allr])

@app.route("/api/knowledge")
def api_knowledge():
    k = KnowledgeBase.query.order_by(KnowledgeBase.added_on.desc()).all()
    return jsonify([x.to_dict() for x in k])

# Background worker: mark stale pending requests as Unresolved after TIMEOUT_SECONDS
def background_timeout_worker(app, interval=10):
    with app.app_context():
        while True:
            cutoff = datetime.now(timezone.utc) - timedelta(seconds=TIMEOUT_SECONDS)
            stale = HelpRequest.query.filter(HelpRequest.status==RequestStatus.Pending, HelpRequest.created_at < cutoff).all()
            for r in stale:
                print(f"[Worker] Marking request {r.id} as Unresolved (created_at={r.created_at})")
                r.status = RequestStatus.Unresolved
                r.resolved_at = datetime.now(timezone.utc)
                db.session.add(r)
            if stale:
                db.session.commit()
            time.sleep(interval)

def start_background_worker():
    t = threading.Thread(target=background_timeout_worker, args=(app,), daemon=True)
    t.start()

if __name__ == "__main__":
    start_background_worker()
    app.run(debug=True, port=5000)