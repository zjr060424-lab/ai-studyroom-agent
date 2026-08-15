# AI Study Room Scheduling Agent

> 易坐 (EasySeat) — a multi-agent intelligent system for university study room resource scheduling

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Overview

The **AI Study Room Scheduling Agent** is a multi-agent system designed to address common problems in university study room reservation systems: low resource utilization, poor user experience during peak hours, seat hogging, and high administrative overhead.

Instead of a monolithic booking script, the system decomposes the workflow into four cooperating agents coordinated by a central orchestrator over a typed message protocol. Each request flows through behavior analysis, anomaly monitoring, resource scheduling, and task execution — a closed loop from natural-language request to confirmed reservation.

### Core Pain Points Addressed

- **Seat Hogging**: one-active-seat-per-user conflict guard; duplicate reservations are rejected
- **Abuse Patterns**: rapid-fire and excessive-reservation detection with per-user activity tracking
- **Low Utilization**: multi-factor seat scoring with area-level load balancing
- **No-Shows**: heuristic no-show risk scoring drives priority and seat-quality decisions
- **Admin Overhead**: automated anomaly reports and recommended restriction actions

## Architecture

```
                  +--------------------+
                  |    User Request    |
                  |  (CLI / REST API)  |
                  +---------+----------+
                            |
                            v
                 +----------+-----------+
                 |     Orchestrator     |
                 |  (message routing,   |
                 |   pipeline control)  |
                 +----------+-----------+
                            |
        ------- message pipeline (typed protocol) -------
            |                                   |
   +--------v---------+                +--------+--------+
   |  User Behavior   |   observes     |    Anomaly      |
   |  Analysis Agent  | -------------> | Detection Agent |
   |                  |    traffic     |                 |
   | - Parse request  |                | - Track per-user|
   | - Profile user   |                |   activity      |
   | - Predict no-show|                | - Detect abuse  |
   | - Set priority   |                |   patterns      |
   +--------+---------+                | - Raise alerts  |
            |                          +--------+--------+
            v                                   |
   +--------+---------+                         |
   |    Resource      |   observes decisions    |
   | Scheduling Agent | <-----------------------+
   |                  |
   | - Conflict guard |
   | - Score seats    |
   | - Load balancing |
   +--------+---------+
            |
            v
   +--------+---------+
   |  Task Execution  |
   |      Agent       |
   |                  |
   | - Booking API    |
   | - Notifications  |
   | - Execution log  |
   +--------+---------+
            |
            v
   +--------+---------+
   | Result & Feedback|
   +------------------+
```

### Multi-Agent Workflow

1. A **user request** enters the system as natural language (CLI demo) or a REST call (web API)
2. The **User Behavior Analysis Agent** parses intent, builds a user profile, and predicts no-show risk
3. The **Anomaly Detection Agent** passively observes pipeline messages and flags abuse patterns
4. The **Resource Scheduling Agent** rejects conflicting requests, then scores and allocates the best seat
5. The **Task Execution Agent** executes the reservation through a (simulated) booking API and sends notifications
6. Results and alerts flow back to the caller, closing the loop

## Agents

| Agent | Role | Key Capabilities |
|-------|------|------------------|
| **User Behavior Analysis Agent** | Behavior modeling & risk prediction | Intent/area/time parsing, no-show risk scoring, dynamic priority |
| **Resource Scheduling Agent** | Seat allocation & conflict handling | Duplicate-reservation guard, multi-factor scoring, load balancing |
| **Anomaly Detection Agent** | Abuse monitoring | Per-user activity tracking, rapid-fire & excessive-booking detection, restriction recommendations |
| **Task Execution Agent** | Execution & feedback | Simulated booking API calls, notifications, execution statistics |

## Quick Start

Requires Python 3.8+. The CLI demo uses only the standard library; the web server needs FastAPI and Uvicorn.

```bash
# Clone the repository
git clone https://github.com/zjr060424-lab/ai-studyroom-agent.git
cd ai-studyroom-agent

# 1) Run the CLI demo (no dependencies needed)
python main.py

# 2) Run the web dashboard + REST API
pip install -r requirements.txt
python server.py
# then open http://127.0.0.1:8000
```

### Sample Output (CLI demo)

```
  +--- User Request --------------------------------
  |  [User] 我想预约明天下午3点图书馆A区的座位
  +--------------------------------------------
  [behavior_agent] [INFO] Parsed request: reserve | User: STU2024013
  [behavior_agent] [INFO] No-show risk prediction: 48.0%
  [behavior_agent] [INFO] Assigned priority: 0.57
  [scheduler_agent] [INFO] Processing allocation for STU2024013 | Risk: 48.0% | Priority: 0.57
  [scheduler_agent] [INFO] Allocated seat: A-27 (Area A) | Score: 0.90
  [executor_agent] [INFO] [API] [OK] Reservation confirmed: RSV-20260815-9149

  >> Final Result [Task Execution Agent]:
     Status: [SUCCESS]
     Reservation ID: RSV-20260815-9149
     Seat: A-27

  ...

  [scheduler_agent] [WARNING] Rejected: STU2024099 already holds seat A-20

  [!] System Feedback: duplicate_reservation
     Suggestion: Release or cancel your current seat before reserving a new one.

  [anomaly_agent] [INFO] [ALERT] Anomaly detected: rapid_fire_reservations for STU2024099 | Score: 0.75
```

The full transcript of a demo run is available at [docs/demo_output.txt](docs/demo_output.txt).

### Demo Scenarios

1. **Normal reservation flow** — bilingual (Chinese / English) natural-language requests
2. **Cancellation handling** — cancelling frees the held seat
3. **Conflict handling** — a user who already holds a seat cannot book a second one
4. **Anomalous behavior detection** — rapid-fire booking attempts trigger alerts
5. **Live statistics** — utilization, execution success rate, anomaly report

## Web API

`server.py` exposes the same pipeline through a FastAPI service with a vanilla-JS dashboard (seat map, reservation form, activity log) served at `/`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/status` | System overview: seats, executions, anomalies |
| GET | `/api/seats` | All seats with live status |
| GET | `/api/areas` | Per-area utilization summary |
| POST | `/api/reserve` | Run a reservation through the agent pipeline |
| POST | `/api/cancel` | Cancel a user's reservation (frees the seat) |
| POST | `/api/release` | Release a user's seat |
| GET | `/api/history` | Execution / allocation / anomaly history |

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/reserve \
  -H "Content-Type: application/json" \
  -d '{"user_id": "STU2024001", "request_text": "I want a quiet window seat", "preferred_area": "A", "duration_minutes": 120}'
```

The response contains the execution result, the behavior analysis (no-show risk, priority), and a per-agent message log of the pipeline run.

## Project Structure

```
ai-studyroom-agent/
├── main.py                        # CLI demo entry point
├── server.py                      # FastAPI web server + REST API
├── requirements.txt               # Web server dependencies
├── agents/
│   ├── user_behavior_agent.py     # Request parsing, no-show risk, priority
│   ├── resource_scheduler.py      # Conflict guard, seat scoring, allocation
│   ├── anomaly_detector.py        # Per-user activity monitoring & alerts
│   └── task_executor.py           # Simulated booking API execution
├── core/
│   ├── agent_base.py              # Abstract base agent (queue, memory, tick)
│   ├── message.py                 # Typed inter-agent message protocol
│   └── orchestrator.py            # Registration, routing, pipeline cycles
├── models/
│   ├── user.py                    # User & behavior dataclasses
│   ├── seat.py                    # Seat state machine (occupy / release)
│   └── reservation.py             # Reservation lifecycle model
├── static/
│   └── index.html                 # Single-page dashboard (vanilla JS)
└── docs/
    └── demo_output.txt            # Full CLI demo transcript
```

## Tech Stack

- **Language**: Python 3.8+ (multi-agent core is standard-library only)
- **Web**: FastAPI + Uvicorn + Pydantic; vanilla HTML/CSS/JS dashboard
- **Architecture**: orchestrator-coordinated multi-agent pipeline with a typed message protocol (dataclass + enum)
- **State**: in-memory seat/reservation state (single-process demo; no database)

Honest scope notes: the no-show prediction is a heuristic scoring model over simulated user histories (not a trained ML model), and the booking API / notifications are simulated. Planned future work: LLM-based request parsing (Claude API), persistent storage, and real check-in data.

## Core Algorithm: Seat Scoring

The Resource Scheduling Agent scores every available seat with multiple factors:

```
score = 0.5 (base)
  + 0.10  has power outlet
  + 0.05  window seat
  + 0.10  quiet zone
  + 0.15  low-utilization area bonus (load balancing)
  - 0.10  high-utilization area penalty
  - 0.10  excessive daily usage penalty
  ± 0.10 × (seat quality − 0.5)
```

Users with a high predicted no-show risk are deliberately assigned lower-scoring seats as a soft penalty, keeping premium seats for reliable users.

## License

[MIT](LICENSE) © 2026 Junrui Zhou

---

中文说明：本项目「易坐」是一个多智能体自习室座位调度系统的演示实现——四个 Agent（行为分析 / 资源调度 / 异常检测 / 任务执行）通过消息协议协作，完成从自然语言请求到座位分配的闭环，并提供 FastAPI Web 控制台。
