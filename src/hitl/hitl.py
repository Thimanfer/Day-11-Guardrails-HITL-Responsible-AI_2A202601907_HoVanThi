"""
Lab 11 — Part 4: Human-in-the-Loop Design
  TODO 11: Confidence Router
  TODO 12: Design 3 HITL decision points
"""
from dataclasses import dataclass


# ============================================================
# TODO 11: Implement ConfidenceRouter
#
# Route agent responses based on confidence scores:
#   - HIGH (>= 0.9): Auto-send to user
#   - MEDIUM (0.7 - 0.9): Queue for human review
#   - LOW (< 0.7): Escalate to human immediately
#
# Special case: if the action is HIGH_RISK (e.g., money transfer,
# account deletion), ALWAYS escalate regardless of confidence.
#
# Implement the route() method.
# ============================================================

HIGH_RISK_ACTIONS = [
    "transfer_money",
    "close_account",
    "change_password",
    "delete_data",
    "update_personal_info",
]


@dataclass
class RoutingDecision:
    """Result of the confidence router."""
    action: str          # "auto_send", "queue_review", "escalate"
    confidence: float
    reason: str
    priority: str        # "low", "normal", "high"
    requires_human: bool


class ConfidenceRouter:
    """Route agent responses based on confidence and risk level.

    Thresholds:
        HIGH:   confidence >= 0.9 -> auto-send
        MEDIUM: 0.7 <= confidence < 0.9 -> queue for review
        LOW:    confidence < 0.7 -> escalate to human

    High-risk actions always escalate regardless of confidence.
    """

    HIGH_THRESHOLD = 0.9
    MEDIUM_THRESHOLD = 0.7

    def route(self, response: str, confidence: float,
              action_type: str = "general") -> RoutingDecision:
        """Route a response based on confidence score and action type.

        Args:
            response: The agent's response text
            confidence: Confidence score between 0.0 and 1.0
            action_type: Type of action (e.g., "general", "transfer_money")

        Returns:
            RoutingDecision with routing action and metadata
        """
        # 1. High-risk actions always escalate regardless of confidence
        if action_type in HIGH_RISK_ACTIONS:
            return RoutingDecision(
                action="escalate",
                confidence=confidence,
                reason=f"High-risk action: {action_type}",
                priority="high",
                requires_human=True,
            )

        # 2. Confidence thresholds
        if confidence >= self.HIGH_THRESHOLD:
            return RoutingDecision(
                action="auto_send",
                confidence=confidence,
                reason="High confidence",
                priority="low",
                requires_human=False,
            )
        elif confidence >= self.MEDIUM_THRESHOLD:
            return RoutingDecision(
                action="queue_review",
                confidence=confidence,
                reason="Medium confidence — needs review",
                priority="normal",
                requires_human=True,
            )
        else:
            return RoutingDecision(
                action="escalate",
                confidence=confidence,
                reason="Low confidence — escalating",
                priority="high",
                requires_human=True,
            )


hitl_decision_points = [
    {
        "id": 1,
        "name": "High-Value Money Transfer Approval",
        "trigger": "User requests external money transfer exceeding 50,000,000 VND or initiating high-risk transfer action.",
        "hitl_model": "human-in-the-loop",
        "context_needed": "Sender account ID, recipient bank & account number, transaction amount, user biometric/OTP verification status, risk score, and payload diff.",
        "example": "Customer requests transferring 100,000,000 VND to a newly added external beneficiary account.",
        "approval_path": "Human reviewer inspects transaction details via banking portal -> Approve (dispatches API call with approval_id) / Reject (cancels transfer & notifies user) / Timeout (after 15 minutes, auto-reject for security).",
        "audit_fields": "request_id, correlation_id, user_id, action_type, destination, amount, reviewer_id, decision (APPROVED/REJECTED/TIMEOUT), timestamp_utc.",
    },
    {
        "id": 2,
        "name": "Account Closure & Sensitive Credential Reset",
        "trigger": "User requests closing savings/checking account or changing registered phone/email/password.",
        "hitl_model": "human-in-the-loop",
        "context_needed": "Customer identity verification records (CCCD scan), account balance status, outstanding loans, recent login IP/device fingerprint, and security question logs.",
        "example": "Customer initiates account closure request for an active account with a remaining balance of 25,000,000 VND.",
        "approval_path": "Support agent verifies customer identity via video/phone call -> Approve (queues account closing procedure) / Reject (retains account and alerts user) / Timeout (holds request in pending state for 24h).",
        "audit_fields": "request_id, correlation_id, user_id, action_type, identity_verification_score, reviewer_id, reviewer_notes, decision, timestamp_utc.",
    },
    {
        "id": 3,
        "name": "Medium Confidence AI Financial Advice / Loan Eligibility Review",
        "trigger": "AI confidence score falls between 0.70 and 0.89 for complex loan consultation or customized interest rate quotes.",
        "hitl_model": "human-on-the-loop",
        "context_needed": "Original customer inquiry, LLM generated response, confidence metrics, customer credit score category, and relevant bank policy guidelines.",
        "example": "Customer asks for loan eligibility and custom interest rate deduction based on collateral worth 2,000,000,000 VND.",
        "approval_path": "Bank officer reviews queued response in background -> Approve (sends AI answer) / Modify (edits proposal before sending) / Reject (substitutes standard advisor template).",
        "audit_fields": "request_id, correlation_id, confidence_score, ai_draft_response, final_sent_response, reviewer_id, review_latency_ms, timestamp_utc.",
    },
]


# ============================================================
# Quick tests
# ============================================================

def test_confidence_router():
    """Test ConfidenceRouter with sample scenarios."""
    router = ConfidenceRouter()

    test_cases = [
        ("Balance inquiry", 0.95, "general"),
        ("Interest rate question", 0.82, "general"),
        ("Ambiguous request", 0.55, "general"),
        ("Transfer $50,000", 0.98, "transfer_money"),
        ("Close my account", 0.91, "close_account"),
    ]

    print("Testing ConfidenceRouter:")
    print("=" * 80)
    print(f"{'Scenario':<25} {'Conf':<6} {'Action Type':<18} {'Decision':<15} {'Priority':<10} {'Human?'}")
    print("-" * 80)

    for scenario, conf, action_type in test_cases:
        decision = router.route(scenario, conf, action_type)
        print(
            f"{scenario:<25} {conf:<6.2f} {action_type:<18} "
            f"{decision.action:<15} {decision.priority:<10} "
            f"{'Yes' if decision.requires_human else 'No'}"
        )

    print("=" * 80)


def test_hitl_points():
    """Display HITL decision points."""
    print("\nHITL Decision Points:")
    print("=" * 60)
    for point in hitl_decision_points:
        print(f"\n  Decision Point #{point['id']}: {point['name']}")
        print(f"    Trigger:  {point['trigger']}")
        print(f"    Model:    {point['hitl_model']}")
        print(f"    Context:  {point['context_needed']}")
        print(f"    Example:  {point['example']}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_confidence_router()
    test_hitl_points()
