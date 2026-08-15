#!/usr/bin/env python3
"""
AI Study Room Scheduling Agent
Multi-agent system for intelligent study room reservation and resource scheduling.
"""

import time
from datetime import datetime

from core.orchestrator import Orchestrator
from agents.user_behavior_agent import UserBehaviorAgent
from agents.resource_scheduler import ResourceSchedulerAgent
from agents.anomaly_detector import AnomalyDetectorAgent
from agents.task_executor import TaskExecutorAgent

# Sample user requests for demo
DEMO_REQUESTS = [
    "[User] 我想预约明天下午3点图书馆A区的座位",
    "[User] 预约明天下午安静学习区的座位",
    "[User] cancel my reservation for today",
    "[User] I need a window seat in area B for 2 hours",
    "[User] 释放座位，我要离开了",
    "[User] 预订讨论区的座位，我们小组有4个人",
]

# One user (STU2024099) firing requests in rapid succession — the
# anomaly detector aggregates activity per user to catch this pattern.
ANOMALOUS_REQUESTS = [
    "[User STU2024099] 预约座位",
    "[User STU2024099] 预约座位B区",
    "[User STU2024099] 再预约一个C区的",
    "[User STU2024099] 取消刚才的再预约A区",
    "[User STU2024099] 再试一次预约",
]


def print_banner():
    banner = r"""
  +====================================================+
  |     AI Study Room Scheduling Agent                 |
  |     Multi-Agent Intelligent Resource Scheduler      |
  +====================================================+
    """
    print(banner.lstrip('\n'))


def print_separator():
    print("\n  " + "-" * 50 + "\n")


def simulate_user_request(orchestrator: Orchestrator, request: str, delay: float = 0.3):
    """Simulate a user request and show the full agent pipeline."""
    print("\n  +--- User Request " + "-" * 32)
    print(f"  |  {request}")
    print("  +" + "-" * 44)

    responses = orchestrator.run_cycle(request)
    time.sleep(delay)

    for resp in responses:
        sender = orchestrator.get_agent(resp.sender)
        sender_name = sender.name if sender else resp.sender

        if resp.msg_type.value == "execution_result":
            print(f"\n  >> Final Result [{sender_name}]:")
            content = resp.content
            if content.get("status") == "success":
                if content.get("action") == "reserve":
                    r = content.get("reservation", {})
                    print(f"     Status: [SUCCESS]")
                    print(f"     Reservation ID: {r.get('reservation_id', 'N/A')}")
                    print(f"     Seat: {content.get('seat_id', 'N/A')}")
                    print(f"     Execution time: {content.get('execution_time_ms', 'N/A')}ms")
                elif content.get("action") in ("release", "cancel"):
                    print(f"     Status: [SUCCESS] {content.get('action').upper()} completed")
            else:
                print(f"     Status: [FAILED] - {content.get('reason', 'Unknown')}")

        elif resp.msg_type.value == "anomaly_alert":
            print(f"\n  [!] Anomaly Alert [{sender_name}]:")
            for anomaly in resp.content.get("anomalies", []):
                print(f"     - Type: {anomaly.get('type', 'unknown')}")
                print(f"       Severity: {anomaly.get('severity', 0):.2f}")
                print(f"       Detail: {anomaly.get('detail', '')}")
            if resp.content.get("is_blacklisted"):
                print(f"     -> User BLACKLISTED")
        elif resp.msg_type.value == "feedback":
            if "error" in resp.content:
                print(f"\n  [!] System Feedback: {resp.content.get('error')}")
                if resp.content.get("suggestion"):
                    print(f"     Suggestion: {resp.content.get('suggestion')}")

    time.sleep(delay)
    print_separator()


def run_full_demo():
    """Run the complete system demonstration."""
    print_banner()

    # Initialize orchestrator and agents
    print("  [System] Initializing Multi-Agent System...\n")
    time.sleep(0.5)

    orchestrator = Orchestrator()
    orchestrator.register_agent(UserBehaviorAgent())
    orchestrator.register_agent(ResourceSchedulerAgent())
    orchestrator.register_agent(AnomalyDetectorAgent())
    orchestrator.register_agent(TaskExecutorAgent())

    print(f"\n  [System] All agents initialized. Ready to process requests.\n")
    print(f"  [System] Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_separator()

    # ============================================================
    # Phase 1: Normal Reservation Flow
    # ============================================================
    print("  Phase 1: Normal Reservation Flow")
    print("  ==========================================\n")

    for req in DEMO_REQUESTS[:3]:
        simulate_user_request(orchestrator, req, delay=0.2)

    # ============================================================
    # Phase 2: Show stats after normal flow
    # ============================================================
    scheduler = orchestrator.get_agent("scheduler_agent")
    executor = orchestrator.get_agent("executor_agent")

    print("  Phase 2: System Status After Normal Operations")
    print("  ==========================================\n")
    if scheduler:
        stats = scheduler.get_stats()
        print(f"  Resource Status:")
        print(f"     Total Seats: {stats['total_seats']}")
        print(f"     Occupied: {stats['occupied']}")
        print(f"     Available: {stats['available']}")
        print(f"     Utilization: {stats['utilization']:.1f}%")
    if executor:
        estats = executor.get_stats()
        print(f"\n  Execution Status:")
        print(f"     Total Executions: {estats['total_executions']}")
        print(f"     Success Rate: {estats['success_rate']}")
        print(f"     Failures: {estats['failures']}")

    print_separator()

    # ============================================================
    # Phase 3: Anomalous Behavior Detection
    # ============================================================
    print("  Phase 3: Anomalous Behavior Detection")
    print("  ==========================================\n")

    for req in ANOMALOUS_REQUESTS:
        simulate_user_request(orchestrator, req, delay=0.1)

    # ============================================================
    # Phase 4: Final Report
    # ============================================================
    print("  Phase 4: Final System Report")
    print("  ==========================================\n")

    anomaly_agent = orchestrator.get_agent("anomaly_agent")
    if anomaly_agent:
        report = anomaly_agent.get_report()
        print(f"  Anomaly Detection Report:")
        print(f"     Total Anomalies Detected: {report['total_anomalies']}")
        print(f"     Blacklisted Users: {report['blacklisted_users']}")
        print(f"     Active Monitoring: {report['active_monitoring']} users")

    if scheduler:
        final_stats = scheduler.get_stats()
        print(f"\n  Final Resource Utilization: {final_stats['utilization']:.1f}%")

    print(f"\n  [System] Demo Complete. Total cycles: {orchestrator.step_count}")
    print(f"  [System] Thank you for using AI Study Room Scheduling Agent!\n")


if __name__ == "__main__":
    run_full_demo()
