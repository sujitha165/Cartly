"""
Cartly Smart Retention Recommendation Engine
Generates actionable, rule-based retention strategies tailored to
customer churn risk, revenue at risk, and purchasing dynamics.
"""

from typing import Dict, Any, List
import pandas as pd


RETENTION_DISCLAIMER = (
    "NOTE: Recommendations are generated via rule-based heuristic segmentation. "
    "Expected churn reduction rates require empirical validation via controlled A/B testing "
    "before asserting causal effectiveness."
)


def generate_customer_recommendation(row: pd.Series) -> Dict[str, Any]:
    """Generate tailored recommendation and explicit business reason for a single customer."""
    cust_id = str(row.get("customer_id", row.get("CustomerID", "Unknown")))
    risk_level = str(row.get("risk_tier", "Medium"))
    value_tier = str(row.get("customer_value_tier", "Medium Value"))
    rev_at_risk = float(row.get("revenue_at_risk", 0.0))
    future_rev = float(row.get("estimated_future_revenue", 0.0))
    recency = int(row.get("recency_days", row.get("Recency", 30)))
    cancel_rate = float(row.get("cancellation_rate", 0.0))
    priority = str(row.get("priority", "Medium"))

    # Rule Matrix
    if risk_level == "High" and value_tier == "High Value":
        action = "VIP Concierge Retention Outreach & Exclusive Loyalty Incentive"
        reason = (
            f"Customer represents high financial risk (£{rev_at_risk:.2f} at risk of £{future_rev:.2f} projected). "
            f"Has been inactive for {recency} days. Requires immediate high-touch outreach from account manager "
            "with a bespoke 20% renewal discount."
        )
    elif risk_level == "High" and value_tier == "Medium Value":
        action = "Automated Re-Engagement Email Sequence with Dynamic Discount"
        reason = (
            f"Moderate value account with high churn likelihood (£{rev_at_risk:.2f} at risk). "
            f"Inactive for {recency} days. Deploy 3-step automated win-back series featuring past top-category items."
        )
    elif risk_level == "High" and value_tier == "Low Value":
        action = "Low-Cost Automated Win-Back Campaign & Free Shipping Voucher"
        reason = (
            f"Low historical spend but elevated churn probability. Deploy cost-effective push/email notification "
            "with a low-margin incentive (e.g. Free Shipping on next order)."
        )
    elif risk_level == "Medium" and value_tier == "High Value":
        action = "Proactive Account Check-in & VIP Previews"
        reason = (
            f"High-value client showing early signs of waning engagement (£{rev_at_risk:.2f} at risk). "
            "Send personalized product recommendations and early access to upcoming product drops."
        )
    elif risk_level == "Medium" and value_tier in ["Medium Value", "Low Value"]:
        action = "Category Re-engagement & Customer Feedback Survey"
        reason = (
            "Moderate engagement trend. Send brief customer satisfaction survey with a small £5 credit "
            "to gauge sentiment and stimulate repeat purchase."
        )
    elif risk_level == "Low" and value_tier == "High Value":
        action = "Loyalty Expansion & Exclusive Tier Recognition"
        reason = (
            "Healthy, loyal top-tier customer. Reward ongoing loyalty with surprise bonus reward points, "
            "referral bonuses, and invitations to beta test new offerings."
        )
    else:  # Low risk + Low/Medium value
        action = "Standard Lifecycle Engagement & Cross-Sell Recommendations"
        reason = (
            "Stable low-risk customer. Maintain regular marketing cadence, automated newsletter, and relevant "
            "cross-category product suggestions."
        )

    # Special condition: high return rate
    if cancel_rate >= 0.20:
        action += " + Post-Return Quality Survey"
        reason += f" Customer exhibits an elevated return/cancellation rate ({cancel_rate*100:.1f}%). Include post-return follow-up to resolve product dissatisfaction."

    return {
        "customer_id": cust_id,
        "risk_level": risk_level,
        "customer_value_tier": value_tier,
        "estimated_future_revenue": round(future_rev, 2),
        "estimated_revenue_at_risk": round(rev_at_risk, 2),
        "priority": priority,
        "recommended_action": action,
        "reason": reason
    }


def generate_all_recommendations(protected_df: pd.DataFrame) -> pd.DataFrame:
    """Generate recommendations for all customers in the dataset."""
    if protected_df.empty:
        return pd.DataFrame(columns=[
            "customer_id", "risk_level", "customer_value_tier",
            "estimated_future_revenue", "estimated_revenue_at_risk",
            "priority", "recommended_action", "reason"
        ])

    records = [generate_customer_recommendation(row) for _, row in protected_df.iterrows()]
    rec_df = pd.DataFrame(records)

    # Sort Critical first, then by revenue at risk descending
    priority_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    rec_df["priority_order"] = rec_df["priority"].map(priority_order).fillna(4)
    rec_df = rec_df.sort_values(["priority_order", "estimated_revenue_at_risk"], ascending=[True, False]).drop(columns=["priority_order"]).reset_index(drop=True)

    return rec_df
