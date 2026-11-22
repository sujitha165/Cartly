"""
Cartly Plotly Component and Visualization Module
Interactive, responsive charts for retail intelligence and churn analytics.
Supports dynamic multi-currency display (INR ₹, GBP £, USD $).
"""

from typing import List, Dict, Any, Optional, Tuple
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

# Corporate palette
PRIMARY_COLOR = "#6366F1"    # Indigo
ACCENT_GREEN = "#10B981"     # Emerald
ACCENT_RED = "#EF4444"       # Rose
ACCENT_AMBER = "#F59E0B"     # Amber
DARK_SLATE = "#1E293B"       # Slate
BG_LIGHT = "#F8FAFC"


def create_revenue_trend_chart(
    monthly_df: pd.DataFrame,
    curr_symbol: str = "₹",
    curr_rate: float = 1.0
) -> go.Figure:
    """Monthly Revenue Trajectory: Gross Sales, Returns, and Net Revenue in selected currency."""
    if monthly_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No transaction data available", showarrow=False)
        return fig

    df = monthly_df.copy()
    df["GrossSalesConverted"] = df["GrossSales"] * curr_rate
    df["ReturnsConverted"] = df["Returns"] * curr_rate
    df["NetRevenueConverted"] = df["NetRevenue"] * curr_rate

    fig = go.Figure()

    # Gross Sales Bar
    fig.add_trace(go.Bar(
        x=df["YearMonth"],
        y=df["GrossSalesConverted"],
        name=f"Gross Sales ({curr_symbol})",
        marker_color="#94A3B8",
        opacity=0.75,
        hovertemplate="<b>%{x}</b><br>Gross: " + curr_symbol + "%{y:,.2f}<extra></extra>"
    ))

    # Returns Bar
    fig.add_trace(go.Bar(
        x=df["YearMonth"],
        y=df["ReturnsConverted"],
        name=f"Returns ({curr_symbol})",
        marker_color=ACCENT_RED,
        opacity=0.85,
        hovertemplate="<b>%{x}</b><br>Returns: " + curr_symbol + "%{y:,.2f}<extra></extra>"
    ))

    # Net Revenue Line
    fig.add_trace(go.Scatter(
        x=df["YearMonth"],
        y=df["NetRevenueConverted"],
        name=f"Net Revenue ({curr_symbol})",
        mode="lines+markers",
        line=dict(color=PRIMARY_COLOR, width=3),
        marker=dict(size=7, color=PRIMARY_COLOR),
        hovertemplate="<b>%{x}</b><br>Net Revenue: " + curr_symbol + "%{y:,.2f}<extra></extra>"
    ))

    fig.update_layout(
        title=f"<b>Monthly Revenue Performance & Returns Trajectory ({curr_symbol})</b>",
        xaxis_title="Billing Month",
        yaxis_title=f"Amount ({curr_symbol})",
        barmode="group",
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40)
    )
    return fig


def create_top_products_chart(
    top_df: pd.DataFrame,
    metric: str = "NetRevenue",
    curr_symbol: str = "₹",
    curr_rate: float = 1.0
) -> go.Figure:
    """Horizontal bar chart for top products."""
    if top_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No product data available", showarrow=False)
        return fig

    sorted_df = top_df.copy().sort_values(metric, ascending=True)

    if metric == "NetRevenue":
        sorted_df["DisplayMetric"] = sorted_df[metric] * curr_rate
        hover_str = "<b>%{y}</b><br>Net Revenue: " + curr_symbol + "%{x:,.2f}<extra></extra>"
        x_label = f"Net Revenue ({curr_symbol})"
    else:
        sorted_df["DisplayMetric"] = sorted_df[metric]
        hover_str = "<b>%{y}</b><br>Quantity: %{x:,}<extra></extra>"
        x_label = "Quantity Sold"

    fig = go.Figure(go.Bar(
        x=sorted_df["DisplayMetric"],
        y=sorted_df["Description"].str.slice(0, 32),
        orientation="h",
        marker=dict(
            color=sorted_df["DisplayMetric"],
            colorscale="Viridis",
            showscale=False
        ),
        hovertemplate=hover_str
    ))

    fig.update_layout(
        title=f"<b>Top Products by {metric} ({curr_symbol})</b>" if metric == "NetRevenue" else f"<b>Top Products by {metric}</b>",
        xaxis_title=x_label,
        yaxis_title="Product Description",
        template="plotly_white",
        margin=dict(l=20, r=20, t=50, b=30),
        height=400
    )
    return fig


def create_product_monthly_trend_chart(
    monthly_prod_df: pd.DataFrame,
    curr_symbol: str = "₹",
    curr_rate: float = 1.0
) -> go.Figure:
    """Line chart for top products over time."""
    if monthly_prod_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No monthly trend data", showarrow=False)
        return fig

    df = monthly_prod_df.copy()
    df["RevenueConverted"] = df["MonthlyRevenue"] * curr_rate

    fig = px.line(
        df,
        x="YearMonth",
        y="RevenueConverted",
        color="Description",
        title=f"<b>Product Revenue Trends Over Time ({curr_symbol})</b>",
        labels={"RevenueConverted": f"Monthly Revenue ({curr_symbol})", "YearMonth": "Month"},
        template="plotly_white",
        markers=True
    )
    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
        margin=dict(l=40, r=40, t=50, b=60)
    )
    return fig


def create_rfm_scatter_chart(
    rfm_df: pd.DataFrame,
    curr_symbol: str = "₹",
    curr_rate: float = 1.0
) -> go.Figure:
    """Scatter plot of Recency vs Frequency with size = Monetary."""
    if rfm_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No customer RFM data available", showarrow=False)
        return fig

    sample = rfm_df.sample(min(1200, len(rfm_df)), random_state=42) if len(rfm_df) > 1200 else rfm_df.copy()
    sample["MonetaryConverted"] = sample["Monetary"] * curr_rate

    color_map = {
        "Champions": "#10B981",
        "Loyal Customers": "#6366F1",
        "Potential Loyalists": "#3B82F6",
        "Promising / Recent": "#06B6D4",
        "Needs Attention": "#F59E0B",
        "At Risk": "#EF4444",
        "Hibernating": "#94A3B8"
    }

    fig = px.scatter(
        sample,
        x="Recency",
        y="Frequency",
        size="MonetaryConverted",
        color="Segment",
        hover_name="CustomerID",
        hover_data={"Recency": True, "Frequency": True, "MonetaryConverted": ":.2f", "Segment": True},
        color_discrete_map=color_map,
        title=f"<b>Customer RFM Distribution (Spend in {curr_symbol})</b>",
        labels={
            "Recency": "Recency (Days Since Last Order)",
            "Frequency": "Order Frequency (Transactions)",
            "MonetaryConverted": f"Net Spend ({curr_symbol})"
        },
        template="plotly_white",
        size_max=35
    )
    fig.update_layout(margin=dict(l=40, r=40, t=50, b=40))
    return fig


def create_rfm_treemap(
    summary_df: pd.DataFrame,
    curr_symbol: str = "₹",
    curr_rate: float = 1.0
) -> go.Figure:
    """Treemap of customer segments by Customer Count and Total Revenue."""
    if summary_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No segment summary available", showarrow=False)
        return fig

    df = summary_df.copy()
    df["TotalSpendConverted"] = df["TotalMonetary"] * curr_rate
    df["AvgSpendConverted"] = df["AvgMonetary"] * curr_rate

    fig = px.treemap(
        df,
        path=["Segment"],
        values="TotalSpendConverted",
        color="AvgRecencyDays",
        color_continuous_scale="RdYlGn_r",
        title=f"<b>Customer Segments: Revenue Share & Average Recency ({curr_symbol})</b>",
        hover_data={"CustomerCount": True, "RevenueSharePct": True, "AvgSpendConverted": ":.2f"}
    )
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20))
    return fig


def create_churn_probability_histogram(pred_df: pd.DataFrame) -> go.Figure:
    """Distribution of predicted churn probabilities with risk band callouts."""
    if pred_df.empty or "churn_probability" not in pred_df.columns:
        fig = go.Figure()
        fig.add_annotation(text="No predictions available", showarrow=False)
        return fig

    fig = px.histogram(
        pred_df,
        x="churn_probability",
        color="risk_tier",
        nbins=30,
        color_discrete_map={"High": ACCENT_RED, "Medium": ACCENT_AMBER, "Low": ACCENT_GREEN},
        title="<b>Predicted Customer Churn Probability Distribution</b>",
        labels={"churn_probability": "Predicted Churn Probability", "count": "Customer Count"},
        template="plotly_white",
        opacity=0.8
    )

    fig.add_vline(x=0.5, line_width=2, line_dash="dash", line_color="#334155", annotation_text="Threshold (0.50)")
    fig.add_vline(x=0.7, line_width=1.5, line_dash="dot", line_color=ACCENT_RED, annotation_text="High Risk (0.70)")
    fig.update_layout(margin=dict(l=40, r=40, t=50, b=40))
    return fig


def create_revenue_at_risk_scatter(
    protected_df: pd.DataFrame,
    curr_symbol: str = "₹",
    curr_rate: float = 1.0
) -> go.Figure:
    """Signature Chart: Estimated Future Revenue (Y) vs Churn Probability (X)."""
    if protected_df.empty or "revenue_at_risk" not in protected_df.columns:
        fig = go.Figure()
        fig.add_annotation(text="No revenue protection data", showarrow=False)
        return fig

    sample = protected_df.sample(min(1000, len(protected_df)), random_state=42) if len(protected_df) > 1000 else protected_df.copy()
    sample["FutureRevConverted"] = sample["estimated_future_revenue"] * curr_rate
    sample["RiskConverted"] = sample["revenue_at_risk"] * curr_rate

    color_map = {
        "Critical": ACCENT_RED,
        "High": "#EA580C",
        "Medium": ACCENT_AMBER,
        "Low": ACCENT_GREEN
    }

    fig = px.scatter(
        sample,
        x="churn_probability",
        y="FutureRevConverted",
        size="RiskConverted",
        color="priority",
        hover_name="customer_id",
        hover_data={
            "churn_probability": ":.3f",
            "FutureRevConverted": ":.2f",
            "RiskConverted": ":.2f",
            "priority": True,
            "customer_value_tier": True
        },
        color_discrete_map=color_map,
        title=f"<b>Smart Revenue Protection Matrix (Future Revenue vs Churn Probability in {curr_symbol})</b>",
        labels={
            "churn_probability": "Churn Probability",
            "FutureRevConverted": f"Estimated Future Revenue ({curr_symbol})"
        },
        template="plotly_white",
        size_max=32
    )

    med_rev = float(sample["FutureRevConverted"].median())
    fig.add_hline(y=med_rev, line_dash="dash", line_color="#CBD5E1", annotation_text=f"Median ({curr_symbol})")
    fig.add_vline(x=0.5, line_dash="dash", line_color="#CBD5E1", annotation_text="Risk Cutoff (50%)")

    fig.update_layout(margin=dict(l=40, r=40, t=50, b=40))
    return fig


def create_priority_donut_chart(protected_df: pd.DataFrame) -> go.Figure:
    """Customer allocation across Action Priorities."""
    if protected_df.empty or "priority" not in protected_df.columns:
        fig = go.Figure()
        return fig

    counts = protected_df["priority"].value_counts().reset_index()
    counts.columns = ["Priority", "Count"]

    color_map = {
        "Critical": ACCENT_RED,
        "High": "#EA580C",
        "Medium": ACCENT_AMBER,
        "Low": ACCENT_GREEN
    }

    fig = px.pie(
        counts,
        names="Priority",
        values="Count",
        color="Priority",
        color_discrete_map=color_map,
        hole=0.5,
        title="<b>Customers by Retention Priority</b>"
    )
    fig.update_traces(textinfo="percent+label")
    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=320)
    return fig


def create_confusion_matrix_heatmap(cm: List[List[int]], model_name: str) -> go.Figure:
    """Confusion matrix heatmap with actual counts."""
    labels = ["Retained (0)", "Churned (1)"]
    z = np.array(cm)

    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=labels,
        y=labels,
        colorscale="Blues",
        text=z,
        texttemplate="<b>%{text}</b>",
        textfont={"size": 16},
        hoverongaps=False
    ))

    fig.update_layout(
        title=f"<b>Confusion Matrix – {model_name}</b>",
        xaxis_title="Predicted Label",
        yaxis_title="True Label",
        template="plotly_white",
        margin=dict(l=50, r=50, t=50, b=40),
        height=350
    )
    return fig


def create_roc_and_pr_curves(
    lr_eval: Dict[str, Any],
    rf_eval: Dict[str, Any]
) -> Tuple[go.Figure, go.Figure]:
    """Generate ROC and Precision-Recall Curves comparing both models."""
    roc_fig = go.Figure()

    if "fpr" in lr_eval:
        roc_fig.add_trace(go.Scatter(
            x=lr_eval["fpr"],
            y=lr_eval["tpr"],
            mode="lines",
            name=f"Logistic Regression (AUC = {lr_eval.get('roc_auc', 0.5):.3f})",
            line=dict(color=PRIMARY_COLOR, width=2.5)
        ))

    if "fpr" in rf_eval:
        roc_fig.add_trace(go.Scatter(
            x=rf_eval["fpr"],
            y=rf_eval["tpr"],
            mode="lines",
            name=f"Random Forest (AUC = {rf_eval.get('roc_auc', 0.5):.3f})",
            line=dict(color=ACCENT_GREEN, width=2.5)
        ))

    roc_fig.add_trace(go.Scatter(
        x=[0, 1], y=[0, 1],
        mode="lines",
        line=dict(color="#94A3B8", dash="dash"),
        name="Random Chance (0.50)"
    ))

    roc_fig.update_layout(
        title="<b>Receiver Operating Characteristic (ROC) Curve</b>",
        xaxis_title="False Positive Rate",
        yaxis_title="True Positive Rate (Recall)",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40),
        height=380
    )

    pr_fig = go.Figure()

    if "precision_pts" in lr_eval:
        pr_fig.add_trace(go.Scatter(
            x=lr_eval["recall_pts"],
            y=lr_eval["precision_pts"],
            mode="lines",
            name=f"Logistic Regression (PR-AUC = {lr_eval.get('pr_auc', 0.0):.3f})",
            line=dict(color=PRIMARY_COLOR, width=2.5)
        ))

    if "precision_pts" in rf_eval:
        pr_fig.add_trace(go.Scatter(
            x=rf_eval["recall_pts"],
            y=rf_eval["precision_pts"],
            mode="lines",
            name=f"Random Forest (PR-AUC = {rf_eval.get('pr_auc', 0.0):.3f})",
            line=dict(color=ACCENT_GREEN, width=2.5)
        ))

    pr_fig.update_layout(
        title="<b>Precision-Recall (PR) Curve</b>",
        xaxis_title="Recall",
        yaxis_title="Precision",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40),
        height=380
    )

    return roc_fig, pr_fig


def create_feature_importance_chart(importance_list: List[Dict[str, Any]], model_name: str) -> go.Figure:
    """Horizontal bar chart for top feature importances."""
    if not importance_list:
        fig = go.Figure()
        return fig

    df = pd.DataFrame(importance_list).sort_values("importance", ascending=True)

    fig = go.Figure(go.Bar(
        x=df["importance"],
        y=df["feature"],
        orientation="h",
        marker=dict(color=PRIMARY_COLOR)
    ))

    fig.update_layout(
        title=f"<b>Feature Importance – {model_name}</b>",
        xaxis_title="Relative Importance Weight",
        yaxis_title="Model Feature",
        template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40),
        height=380
    )
    return fig
