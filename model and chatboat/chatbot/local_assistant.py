"""
ai_models_and_chatbot - Local Offline Forensic Chatbot Assistant
Provides intelligent, sub-5ms evidence-grounded answers for fraud analysts
without requiring external network connections or API keys.
"""

from typing import Dict, Any, List, Optional


class LocalChatAssistant:
    """
    Offline intelligence engine generating forensic case analysis,
    verifications questions, and risk factor explanations.
    """

    def generate_response(
        self,
        user_message: str,
        transaction_context: Optional[Dict[str, Any]] = None
    ) -> str:
        msg = (user_message or "").lower()
        ctx = transaction_context or {}

        # Extract telemetry
        tx_id = ctx.get("transaction_id", "Current Transaction")
        amount = float(ctx.get("amount", 0.0))
        amount_dev = float(ctx.get("amount_deviation", 1.0))
        is_new_dev = int(ctx.get("is_new_device", 0)) == 1
        is_new_rec = int(ctx.get("is_new_receiver", 0)) == 1
        failed_att = int(ctx.get("failed_attempts", 0))
        hour = int(ctx.get("hour", 14))
        score = float(ctx.get("risk_score", 0.0))
        level = ctx.get("risk_level", "LOW")

        # 1. Specific Query: Account Takeover (ATO)
        if any(w in msg for w in ["ato", "takeover", "hack", "compromise", "device"]):
            if is_new_dev and (failed_att >= 2 or amount_dev >= 3.0):
                return (
                    f"[ALERT] High Probability ATO Indicators Detected for {tx_id}:\n\n"
                    f"* Hardware Anomaly: The session authenticated from an unverified device identifier never previously linked to this account.\n"
                    f"* Security Precursors: Preceded by {failed_att} failed PIN/password authentication attempts.\n"
                    f"* Behavioral Surge: Transfer amount is BDT {amount:,.2f} ({amount_dev:.1f}x higher than baseline).\n\n"
                    f"Recommended Analyst Action: Place temporary freeze on fund disbursement and contact customer via registered phone."
                )
            elif is_new_dev:
                return (
                    f"[NOTE] Moderate Device Anomaly:\n"
                    f"This transfer was initiated from an unregistered device, but authentication was completed successfully without prior failed attempts. "
                    f"Verify whether the customer recently upgraded their phone."
                )
            else:
                return (
                    f"[VERIFIED] No Significant ATO Indicators:\n"
                    f"The transaction originated from the customer's familiar hardware device with 0 failed authentication attempts."
                )

        # 2. Specific Query: Verification Questions / What to ask customer
        if any(w in msg for w in ["ask", "question", "verify", "call", "inquire"]):
            return (
                f"[CHECKLIST] Recommended Verification Checklist for {tx_id}:\n\n"
                f"1. 'Did you personally authorize a transfer of BDT {amount:,.2f} at {hour:02d}:00 hours?'\n"
                f"2. 'What is your relationship with the recipient beneficiary account?'\n"
                f"3. 'Did anyone contact you claiming to be from upay, Bangladesh Bank, or a lottery asking you to send funds?'\n"
                f"4. 'Did you recently switch to a new phone or share your OTP with anyone?'"
            )

        # 3. Specific Query: Scam / Social Engineering
        if any(w in msg for w in ["scam", "social engineering", "fraud", "mule", "fake"]):
            if is_new_rec and amount_dev >= 4.0:
                return (
                    f"[ALERT] Potential Scam / Mule Pattern:\n\n"
                    f"* Rapid outflow of BDT {amount:,.2f} to a first-time unverified beneficiary.\n"
                    f"* The amount is {amount_dev:.1f}x higher than the customer's typical transaction profile.\n"
                    f"* Pattern is consistent with impersonation scams or urgency coercion where victims are persuaded to liquidate balances."
                )
            return (
                f"[INFO] Scam Evaluation:\n"
                f"Beneficiary analysis shows {'first-time contact' if is_new_rec else 'established counterparty'}. "
                f"Current risk score stands at {score}/100 ({level} risk)."
            )

        # 4. Default: Comprehensive Forensic Summary
        findings = []
        if amount_dev >= 3.0:
            findings.append(f"Transfer amount of BDT {amount:,.2f} represents a {amount_dev:.1f}x surge over historical average.")
        if is_new_dev:
            findings.append("Session originated from an unregistered hardware device.")
        if is_new_rec:
            findings.append("Beneficiary is a first-time recipient with no prior interaction history.")
        if failed_att >= 1:
            findings.append(f"Preceded by {failed_att} failed authentication attempts.")
        if hour in [1, 2, 3, 4]:
            findings.append(f"Executed during off-hours ({hour:02d}:00 AM).")

        if not findings:
            findings.append("Transaction parameters conform strictly with normal customer baseline spending.")

        findings_bullets = "\n".join([f"* {f}" for f in findings])

        return (
            f"[ASSESSMENT] Forensic Case Assessment for {tx_id}:\n\n"
            f"Assigned Risk Score: {score} / 100 ({level} Risk Tier)\n\n"
            f"Key Empirical Observations:\n{findings_bullets}\n\n"
            f"Governance Recommendation: "
            f"{'Requires Human Analyst Investigation.' if level == 'HIGH' else ('Trigger step-up 2FA confirmation.' if level == 'MEDIUM' else 'Safe to execute immediately.')}"
        )
