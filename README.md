# Human-in-the-Loop AI Supervisor

A Flask-based web application simulating a Human-in-the-Loop AI system for a frontdesk service. The AI agent handles incoming customer queries using a knowledge base and predefined business information. If the AI cannot answer, it escalates to a human supervisor via a web dashboard for resolution, learning from the supervisor's responses to improve future answers.

## Features

- **AI Agent**: Answers questions based on a knowledge base (stored in SQLite) and hardcoded business info (e.g., hours, services, location).
- **Supervisor Dashboard**: Web UI for supervisors to view pending requests, respond to escalated queries, and monitor resolved/unresolved requests.
- **Knowledge Learning**: Supervisor responses update the knowledge base for future AI use.
- **Timeout Handling**: Pending requests auto-marked as "Unresolved" after a configurable timeout (default 2 minutes).
- **Simulation Endpoint**: API to simulate incoming calls for demo purposes.
- **API Endpoints**: JSON APIs for requests and knowledge base data.

## Architecture

- **Backend**: Flask with SQLAlchemy for database management (SQLite).
- **Database Models**:
  - `HelpRequest`: Stores customer questions, status (Pending/Resolved/Unresolved), supervisor responses.
  - `KnowledgeBase`: Stores learned Q&A pairs.
- **AI Logic** (in `agent.py`):
  - Normalizes text for matching.
  - Checks knowledge base for exact matches.
  - Falls back to business info keywords (hours, services, location).
  - Escalates to supervisor if no match.
- **Supervisor Loop**:
  - AI escalates → Supervisor responds via dashboard → Response updates KB → AI learns.
- **Background Worker**: Threaded worker checks for stale pending requests and marks them unresolved.

## Setup

1. **Prerequisites**:
   - Python 3.7+
   - Git

2. **Clone or Download**:
   - Download the code or clone the repository.

3. **Install Dependencies**:
   ```
   pip install -r requirements.txt
   ```

4. **Run the Application**:
   ```
   python app.py
   ```
   - The app runs on `http://localhost:5000`.
   - Access the dashboard at `/dashboard`.

5. **Environment Variables** (optional):
   - `TIMEOUT_SECONDS`: Set timeout for pending requests (default 120 seconds).

## Usage

- **Dashboard**: View pending, resolved, and unresolved requests. Click "Respond" to answer.
- **Simulate Call**: Use the form on the dashboard to test the AI with sample questions.
- **API**:
  - `POST /create-request`: Create a new help request (JSON: `{"question": "...", "caller_id": "..."}`).
  - `POST /simulate-call`: Simulate a call (same JSON).
  - `GET /api/requests`: Get all requests (JSON).
  - `GET /api/knowledge`: Get knowledge base (JSON).

## Design Notes

- **AI Decision Flow**:
  1. Normalize question text.
  2. Search knowledge base for exact match.
  3. Check business info keywords.
  4. If no answer, create HelpRequest and notify supervisor.
- **Supervisor Interaction**: Web-based form for responses, auto-updates KB.
- **Learning**: Exact question match updates existing KB entry; new questions add to KB.
- **Timeout**: Background thread monitors pending requests; marks as Unresolved after timeout.
- **Demo-Friendly**: Short timeout, simulation endpoint for testing without real calls.
- **Security**: No authentication implemented; for demo purposes only.
- **Scalability**: Uses SQLite; for production, switch to PostgreSQL/MySQL.
