# AI Study Room Scheduling Agent

> Multi-Agent Intelligent System for University Study Room Resource Scheduling

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Overview

The **AI Study Room Scheduling Agent** is a multi-agent intelligent system designed to solve common problems in university study room reservation systems: low resource utilization, poor user experience during peak hours, seat hogging, and high administrative overhead.

Unlike traditional booking systems that only provide simple time-slot reservations, this system uses a collaborative multi-agent architecture to intelligently analyze user behavior, predict no-show probability, dynamically allocate resources, detect anomalies, and execute tasks autonomously.

### Core Pain Points Addressed

- **Seat Hogging**: Detects malicious occupancy and frequent cancellations
- **Low Utilization**: Dynamic allocation based on predictive analytics
- **Peak Hour Strife**: Priority-based allocation with behavior scoring
- **Admin Overhead**: Automated anomaly detection and restriction enforcement
- **No-Shows**: Predictive risk modeling reduces wasted seats

## Architecture

```
                     +--------------------+
                     |      User          |
                     |     Request        |
                     +--------+-----------+
                              |
                              v
              +---------------+---------------+
              |                               |
     +--------v--------+           +----------v----------+
     |   User Behavior  |           |    Anomaly          |
     |  Analysis Agent  |           |  Detection Agent     |
     |                  |           |                     |
     | - Parse request  |           | - Monitor patterns  |
     | - Analyze history|           | - Detect anomalies  |
     | - Predict risk   |           | - Auto-blacklist    |
     | - Set priority   |           | - Trigger alerts    |
     +--------+---------+           +----------+----------+
              |                                |
              |        +-----------------------+
              |        |
     +--------v--------v---+
     |   Resource          |
     |   Scheduling Agent  |
     |                     |
     | - Score available   |
     |   seats             |
     | - Multi-factor      |
     |   allocation        |
     | - Load balancing    |
     +--------+------------+
              |
              v
     +--------+------------+
     |   Task Execution    |
     |   Agent             |
     |                     |
     | - Call booking API  |
     | - Send notification |
     | - Process release   |
     | - Log execution     |
     +---------------------+
              |
              v
     +---------------------+
     |     Result &        |
     |     Feedback        |
     +---------------------+
```

### Multi-Agent Workflow

1. **User Request** enters the system via natural language
2. **User Behavior Analysis Agent** parses intent, analyzes history, and predicts no-show probability
3. **Anomaly Detection Agent** monitors for suspicious patterns in parallel
4. **Resource Scheduling Agent** scores and selects the optimal seat allocation
5. **Task Execution Agent** executes reservation via API and sends notifications
6. **Result & Feedback** completes the closed-loop cycle

## Agents

| Agent | Role | Key Capabilities |
|-------|------|------------------|
| **User Behavior Analysis Agent** | Behavior modeling & risk prediction | No-show prediction, priority scoring, intent parsing |
| **Resource Scheduling Agent** | Dynamic seat allocation | Multi-factor scoring, load balancing, utilization optimization |
| **Anomaly Detection Agent** | Security & abuse prevention | Pattern detection, auto-blacklisting, risk scoring |
| **Task Execution Agent** | API integration & execution | Reservation API calls, notifications, release processing |

## Demo

### Quick Start

```bash
# Clone the repository
git clone https://github.com/your-username/ai-studyroom-agent.git
cd ai-studyroom-agent

# Run the demo
python main.py
```

### Sample Output

```
  +====================================================+
  |     AI Study Room Scheduling Agent                 |
  |     Multi-Agent Intelligent Resource Scheduler      |
  +====================================================+

  [System] Initializing Multi-Agent System...

  [Orchestrator] Agent registered: User Behavior Analysis Agent
  [Orchestrator] Agent registered: Resource Scheduling Agent
  [Orchestrator] Agent registered: Anomaly Detection Agent
  [Orchestrator] Agent registered: Task Execution Agent

  +--- User Request ------------------------------------
  |  [User] 我想预约明天下午3点图书馆A区的座位
  +---------------------------------------------------

  [behavior_agent] Parsed request: reserve | User: STU2024056
  [behavior_agent] No-show risk prediction: 27.0%
  [behavior_agent] Assigned priority: 0.61
  [scheduler_agent] Processing allocation | Risk: 27.0% | Priority: 0.61
  [scheduler_agent] Allocated seat: A-11 (Area A) | Score: 0.95
  [executor_agent] [API] Reservation confirmed: RSV-20260502-3146
  [executor_agent] [API] Notification sent: reservation confirmed

  >> Final Result:
     Status: [SUCCESS]
     Reservation ID: RSV-20260502-3146
     Seat: A-11
     Execution time: 449ms

  Phase 2: System Status

  Resource Status:
     Total Seats: 30
     Occupied: 2
     Available: 28
     Utilization: 6.7%

  Execution Status:
     Total Executions: 2
     Success Rate: 100.0%
```

### Demo Scenarios

The demo includes these test scenarios:

1. **Normal Reservation Flow**: Users reserve seats with different preferences
2. **Multi-language Support**: Chinese and English requests
3. **Cancellation Handling**: Cancel existing reservations
4. **Anomalous Behavior Detection**: Rapid-fire reservation attempts
5. **Resource Status Reporting**: Live utilization statistics

## Project Structure

```
ai-studyroom-agent/
├── main.py                        # Entry point and demo runner
├── requirements.txt               # Dependencies
├── README.md                      # This file
├── agents/
│   ├── user_behavior_agent.py     # User behavior analysis & risk prediction
│   ├── resource_scheduler.py      # Dynamic seat allocation
│   ├── anomaly_detector.py        # Abuse detection & prevention
│   └── task_executor.py           # API integration & execution
├── core/
│   ├── agent_base.py              # Abstract base agent class
│   ├── message.py                 # Inter-agent message protocol
│   └── orchestrator.py            # Multi-agent coordinator
├── models/
│   ├── user.py                    # User & behavior models
│   ├── seat.py                    # Seat & resource models
│   └── reservation.py             # Reservation models
├── utils/
│   └── helpers.py                 # Utility functions
└── data/                          # Sample data directory
```

## Tech Stack

- **Language**: Python 3.8+
- **Architecture**: Multi-Agent System (MAS)
- **Pattern**: Message-based inter-agent communication
- **Design**: Orchestrator-coordinated pipeline processing

Future integrations (prepared for):
- **LLM Integration**: Claude / GPT for advanced NLP parsing
- **RAG**: Vector-based context retrieval
- **Web API**: FastAPI for production deployment

## Core Algorithm: Seat Scoring

The Resource Scheduling Agent uses multi-factor scoring:

```
score = 0.5 (base)
  + 0.1  (has power)
  + 0.05 (window seat)
  + 0.1  (quiet zone)
  + 0.15 (low utilization area bonus)
  - 0.1  (high utilization penalty)
  - 0.1  (excessive daily usage penalty)
```

High-risk users are deliberately assigned lower-quality seats as a soft penalty (simulated RL approach).

## License

MIT
