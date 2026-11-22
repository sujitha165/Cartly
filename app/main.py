"""
Cartly – Retail Intelligence & Revenue Protection System
Main Streamlit Application
Supports Dynamic Multi-Currency (INR ₹, GBP £, USD $) with Documented Exchange Rates.
"""
import plotly.express as px
import os
import sys
from typing import Dict, Any, Optional
import streamlit as st
import pandas as pd
import numpy as np

# Ensure root workspace is on python path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.data.loader import load_dataset, validate_columns
from src.data.cleaner import clean_retail_data, generate_data_health_report
from src.data.db import init_db, get_table_counts, reset_database
from src.data.repository import (
    sync_cleaned_data_to_db,
    sync_features_to_db,
    sync_predictions_to_db,
    sync_recommendations_to_db
)
from src.analytics.executive import (
    filter_transactions,
    calculate_executive_kpis,
    calculate_monthly_revenue_trends,
    calculate_top_selling_products,
    calculate_customer_purchasing_trends
)
from src.analytics.product_analytics import (
    get_product_summary,
    get_top_products,
    get_lowest_performing_products,
    get_product_monthly_trend
)
from src.analytics.rfm import (
    calculate_rfm_metrics,
    score_rfm,
    segment_customers,
    get_rfm_segment_summary,
    SEGMENT_DESCRIPTIONS
)
from src.features.churn_features import (
    build_churn_snapshot,
    generate_chronological_churn_data,
    FEATURE_COLUMNS
)
from src.models.churn_model import (
    train_and_compare_models,
    load_model_bundle,
    predict_customer_churn_probabilities,
    DEFAULT_MODEL_PATH
)
from src.business.revenue_protection import (
    calculate_revenue_at_risk,
    calculate_revenue_protection_summary
)
from src.business.recommendations import (
    generate_all_recommendations,
    RETENTION_DISCLAIMER
)
from app.styles import CUSTOM_CSS, render_banner, render_kpi, render_badge
from app.components import (
    create_revenue_trend_chart,
    create_top_products_chart,
    create_product_monthly_trend_chart,
    create_rfm_scatter_chart,
    create_rfm_treemap,
    create_churn_probability_histogram,
    create_revenue_at_risk_scatter,
    create_priority_donut_chart,
    create_confusion_matrix_heatmap,
    create_roc_and_pr_curves,
    create_feature_importance_chart
)

# Set page configuration
st.set_page_config(
    page_title="Cartly – Retail Intelligence & Revenue Protection",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject styling
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# --- Cached Data Loaders ---
@st.cache_data(show_spinner=False)
def load_and_clean_dataset(filepath: str, is_excel: bool = False, nrows: Optional[int] = None):
    ftype = "xlsx" if is_excel else "csv"
    df_raw, meta = load_dataset(filepath, file_type=ftype, nrows=nrows)
    if not meta["is_valid"]:
        return df_raw, pd.DataFrame(), meta, {}
    cleaned_df, report = clean_retail_data(df_raw, drop_missing_customers=True)
    return df_raw, cleaned_df, meta, report


def initialize_session_state():
    """Initialize core session variables."""
    if "active_data_source" not in st.session_state:
        st.session_state["active_data_source"] = "sample_50k"
    if "cleaned_df" not in st.session_state:
        st.session_state["cleaned_df"] = None
    if "raw_df" not in st.session_state:
        st.session_state["raw_df"] = None
    if "clean_report" not in st.session_state:
        st.session_state["clean_report"] = None
    if "model_bundle" not in st.session_state:
        st.session_state["model_bundle"] = load_model_bundle()
    if "predictions_df" not in st.session_state:
        st.session_state["predictions_df"] = None
    if "protected_df" not in st.session_state:
        st.session_state["protected_df"] = None
    if "recommendations_df" not in st.session_state:
        st.session_state["recommendations_df"] = None


initialize_session_state()

# Ensure default sample data is loaded if empty
if st.session_state["cleaned_df"] is None:
    sample_path = os.path.join(ROOT_DIR, "data", "sample_retail_50k.csv")
    if os.path.exists(sample_path):
        raw, cleaned, meta, rep = load_and_clean_dataset(sample_path)
        st.session_state["raw_df"] = raw
        st.session_state["cleaned_df"] = cleaned
        st.session_state["clean_report"] = rep


# --- SIDEBAR NAVIGATION & CONTROLS ---
with st.sidebar:
    st.markdown("""
        <div style="padding: 0.5rem 0 1rem 0;">
            <h2 style="margin:0; color:#1E293B; font-weight:800; display:flex; align-items:center; gap:8px;">
                🛒 Cartly
            </h2>
            <p style="margin:2px 0 0 0; font-size:0.78rem; color:#64748B; font-weight:500;">
                Turn Customer Insights into Revenue Protection
            </p>
        </div>
    """, unsafe_allow_html=True)

    menu = st.radio(
        "Navigation",
        [
            "1. Executive Dashboard",
            "2. Product Revenue Analysis",
            "3. Customer Analytics (RFM)",
            "4. Customer Churn Prediction",
            "5. Revenue Protection Engine",
            "6. Retention Recommendations",
            "7. Model Performance",
            "8. Data Management"
        ],
        index=0
    )

    st.markdown("---")
    st.markdown("#### 💱 Currency Settings")
    currency_options = [
        "Indian Rupee (INR - ₹)",
        "British Pound (GBP - £)",
        "US Dollar (USD - $)"
    ]
    selected_currency = st.selectbox(
        "Display Currency",
        currency_options,
        index=0  # Default to Indian Rupee (INR - ₹)
    )

    CURRENCY_CONFIG = {
        "Indian Rupee (INR - ₹)": {
            "symbol": "₹",
            "rate": 105.50,
            "code": "INR",
            "desc": "Documented Conversion: 1 GBP = ₹105.50 INR (Nov 2026 Rate)"
        },
        "British Pound (GBP - £)": {
            "symbol": "£",
            "rate": 1.00,
            "code": "GBP",
            "desc": "Original Dataset Currency (1 GBP = £1.00)"
        },
        "US Dollar (USD - $)": {
            "symbol": "$",
            "rate": 1.28,
            "code": "USD",
            "desc": "Documented Conversion: 1 GBP = $1.28 USD (Nov 2026 Rate)"
        }
    }
    curr_cfg = CURRENCY_CONFIG[selected_currency]
    curr_sym = curr_cfg["symbol"]
    curr_rate = curr_cfg["rate"]
    st.caption(f"ℹ️ {curr_cfg['desc']}")

    st.markdown("---")
    st.markdown("#### ⚙️ Data & Environment")

    dataset_choice = st.selectbox(
        "Active Dataset Source",
        ["Sample Dataset (50,000 Rows)", "Full Dataset (1,067,371 Rows)", "Custom Uploaded File"],
        index=0 if st.session_state["active_data_source"] == "sample_50k" else 1
    )

    if dataset_choice == "Sample Dataset (50,000 Rows)" and st.session_state["active_data_source"] != "sample_50k":
        sample_path = os.path.join(ROOT_DIR, "data", "sample_retail_50k.csv")
        with st.spinner("Loading high-speed sample dataset..."):
            raw, cleaned, meta, rep = load_and_clean_dataset(sample_path)
            st.session_state["raw_df"] = raw
            st.session_state["cleaned_df"] = cleaned
            st.session_state["clean_report"] = rep
            st.session_state["active_data_source"] = "sample_50k"
            st.session_state["predictions_df"] = None
            st.session_state["protected_df"] = None
            st.session_state["recommendations_df"] = None
        st.rerun()

    elif dataset_choice == "Full Dataset (1,067,371 Rows)" and st.session_state["active_data_source"] != "full":
        full_path = os.path.join(ROOT_DIR, "data", "online_retail_II.csv")
        if os.path.exists(full_path):
            with st.spinner("Loading full Kaggle Online Retail II dataset (1.07M rows)..."):
                raw, cleaned, meta, rep = load_and_clean_dataset(full_path)
                st.session_state["raw_df"] = raw
                st.session_state["cleaned_df"] = cleaned
                st.session_state["clean_report"] = rep
                st.session_state["active_data_source"] = "full"
                st.session_state["predictions_df"] = None
                st.session_state["protected_df"] = None
                st.session_state["recommendations_df"] = None
            st.rerun()
        else:
            st.warning("Full dataset file data/online_retail_II.csv not found.")

    # Global Date and Country Filters
    cleaned_df = st.session_state["cleaned_df"]
    filtered_df = cleaned_df

    if cleaned_df is not None and not cleaned_df.empty:
        min_date = cleaned_df["InvoiceDate"].min().date()
        max_date = cleaned_df["InvoiceDate"].max().date()

        st.markdown("##### 🔍 Global Filters")
        date_range = st.date_input(
            "Transaction Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )

        all_countries = ["All"] + sorted(cleaned_df["Country"].unique().tolist())
        selected_countries = st.multiselect("Filter by Country", all_countries, default=["All"])

        # Apply filtering
        start_dt = pd.to_datetime(date_range[0]) if len(date_range) > 0 else None
        end_dt = pd.to_datetime(date_range[1]) + pd.Timedelta(days=1) if len(date_range) > 1 else None
        country_filter = None if "All" in selected_countries or not selected_countries else selected_countries

        filtered_df = filter_transactions(cleaned_df, start_date=start_dt, end_date=end_dt, countries=country_filter)

    st.markdown("---")
    # Model Status badge in sidebar
    model_bundle = st.session_state["model_bundle"]
    if model_bundle:
        b_name = model_bundle.get("model_name", "Trained")
        f1_val = model_bundle.get("metrics", {}).get("f1_score", 0.0)
        st.success(f"🤖 **Model Active**: {b_name}\n\n**Test F1**: `{f1_val:.3f}`")
    else:
        st.info("ℹ️ Churn Model: Not Yet Trained")

    db_counts = get_table_counts()
    st.caption(f"💾 **SQLite Synced**: {db_counts.get('customers', 0):,} Customers | {db_counts.get('orders', 0):,} Orders")


# Helper function to format currency dynamically
def fmt_curr(val: float) -> str:
    """Format numeric values according to the currently active currency & rate."""
    converted = float(val) * curr_rate
    return f"{curr_sym}{converted:,.2f}"


# ==========================================
# MODULE 1: EXECUTIVE DASHBOARD
# ==========================================
if menu == "1. Executive Dashboard":
    st.markdown(render_banner("Executive Retail Performance Dashboard", f"Comprehensive overview of revenue, transaction volume, returns, and customer retention dynamics ({curr_sym})"), unsafe_allow_html=True)

    if filtered_df is None or filtered_df.empty:
        st.warning("No transaction data available for the selected filters. Please adjust date or country filters.")
    else:
        kpis = calculate_executive_kpis(filtered_df)

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.markdown(render_kpi(f"Net Revenue ({curr_sym})", fmt_curr(kpis['net_revenue']), f"Gross: {fmt_curr(kpis['gross_revenue'])}", "#10B981"), unsafe_allow_html=True)
        with col2:
            st.markdown(render_kpi(f"Return Volume ({curr_sym})", fmt_curr(kpis['return_amount']), f"Return Rate: {kpis['return_rate_pct']:.1f}%", "#EF4444"), unsafe_allow_html=True)
        with col3:
            st.markdown(render_kpi("Total Orders", f"{kpis['total_orders']:,}", f"Avg Items: {kpis['average_items_per_order']}", "#6366F1"), unsafe_allow_html=True)
        with col4:
            st.markdown(render_kpi("Active Customers", f"{kpis['total_customers']:,}", f"In Catalog: {kpis['total_products']:,} SKUs", "#3B82F6"), unsafe_allow_html=True)
        with col5:
            st.markdown(render_kpi(f"Average Order Value", fmt_curr(kpis['average_order_value']), "Net Revenue / Order", "#F59E0B"), unsafe_allow_html=True)

        st.markdown("###")

        # Monthly revenue trends & top products
        c_left, c_right = st.columns([1.6, 1.0])
        with c_left:
            monthly_trends = calculate_monthly_revenue_trends(filtered_df)
            trend_fig = create_revenue_trend_chart(monthly_trends, curr_symbol=curr_sym, curr_rate=curr_rate)
            st.plotly_chart(trend_fig, use_container_width=True)

        with c_right:
            top_products = calculate_top_selling_products(filtered_df, top_n=8)
            top_fig = create_top_products_chart(top_products, metric="NetRevenue", curr_symbol=curr_sym, curr_rate=curr_rate)
            st.plotly_chart(top_fig, use_container_width=True)

        # Customer Purchasing Trends
        c_trend1, c_trend2 = st.columns([1.2, 1.0])
        with c_trend1:
            cust_trends = calculate_customer_purchasing_trends(filtered_df)
            if not cust_trends.empty:
                cust_trends["AvgSpendConverted"] = cust_trends["AvgSpendPerCustomer"] * curr_rate
                fig_cust = px.bar(
                    cust_trends,
                    x="YearMonth",
                    y="TotalActive",
                    title="<b>Active Transacting Customers per Month</b>",
                    labels={"TotalActive": "Active Customer Count", "YearMonth": "Month"},
                    template="plotly_white",
                    color_discrete_sequence=["#6366F1"]
                )
                st.plotly_chart(fig_cust, use_container_width=True)
        with c_trend2:
            st.markdown("#### 📊 Key Performance Observations")
            st.markdown(f"""
            - **Active Currency**: `{selected_currency}` ({curr_cfg['desc']})
            - **Net Realization Rate**: `{100 - kpis['return_rate_pct']:.1f}%` of gross billings translated to realized net revenue.
            - **Average Customer Spend**: `{fmt_curr(kpis['net_revenue']/max(kpis['total_customers'],1))}` across `{kpis['total_customers']:,}` accounts.
            - **Catalog Breadth**: Sales distributed across `{kpis['total_products']:,}` distinct merchandise items.
            - **Financial Accuracy Note**: Returns & cancellations (`C`-invoices) are isolated and subtracted without double-counting.
            """)


# ==========================================
# MODULE 2: PRODUCT REVENUE ANALYSIS
# ==========================================
elif menu == "2. Product Revenue Analysis":
    st.markdown(render_banner("Product Revenue & Inventory Analytics", f"Granular performance, returns analysis, top sellers, and low-performing inventory ({curr_sym})"), unsafe_allow_html=True)

    if filtered_df is None or filtered_df.empty:
        st.warning("No data available.")
    else:
        prod_summary = get_product_summary(filtered_df)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(render_kpi("Catalog SKUs", f"{len(prod_summary):,}", "Active items sold", "#6366F1"), unsafe_allow_html=True)
        with col2:
            st.markdown(render_kpi("Units Dispatched", f"{int(prod_summary['QuantitySold'].sum()):,}", "Positive deliveries", "#10B981"), unsafe_allow_html=True)
        with col3:
            st.markdown(render_kpi("Units Returned", f"{int(prod_summary['QuantityReturned'].sum()):,}", "Offsetting returns", "#EF4444"), unsafe_allow_html=True)
        with col4:
            st.markdown(render_kpi(f"Top Product Revenue", fmt_curr(prod_summary['NetRevenue'].max()), prod_summary.iloc[0]['Description'][:25], "#F59E0B"), unsafe_allow_html=True)

        st.markdown("###")

        tab_top, tab_low, tab_trends = st.tabs(["🏆 Top 10 Products", "⚠️ Lowest-Performing Products", "📈 Monthly Product Trends"])

        with tab_top:
            top_metric = st.radio("Rank Top Products By:", ["NetRevenue", "QuantitySold"], horizontal=True)
            top_10 = get_top_products(filtered_df, top_n=10, metric=top_metric).copy()
            top_10["GrossRevenue"] = top_10["GrossRevenue"] * curr_rate
            top_10["ReturnsAmount"] = top_10["ReturnsAmount"] * curr_rate
            top_10["NetRevenue"] = top_10["NetRevenue"] * curr_rate

            col_t1, col_t2 = st.columns([1.2, 1.0])
            with col_t1:
                st.plotly_chart(create_top_products_chart(top_10, metric=top_metric, curr_symbol=curr_sym, curr_rate=1.0), use_container_width=True)
            with col_t2:
                st.dataframe(
                    top_10[["StockCode", "Description", "QuantitySold", "GrossRevenue", "ReturnsAmount", "NetRevenue"]].style.format({
                        "GrossRevenue": curr_sym + "{:,.2f}",
                        "ReturnsAmount": curr_sym + "{:,.2f}",
                        "NetRevenue": curr_sym + "{:,.2f}",
                        "QuantitySold": "{:,}"
                    }),
                    use_container_width=True,
                    height=380
                )

        with tab_low:
            st.markdown("Identify low-revenue or high-return SKUs requiring inventory review or clearance:")
            min_orders = st.slider("Filter: Minimum Orders Count", 1, 20, 2)
            lowest_prods = get_lowest_performing_products(filtered_df, bottom_n=15, min_orders=min_orders).copy()
            lowest_prods["ReturnsAmount"] = lowest_prods["ReturnsAmount"] * curr_rate
            lowest_prods["NetRevenue"] = lowest_prods["NetRevenue"] * curr_rate
            lowest_prods["AvgUnitPrice"] = lowest_prods["AvgUnitPrice"] * curr_rate

            st.dataframe(
                lowest_prods[["StockCode", "Description", "OrderCount", "QuantitySold", "ReturnsAmount", "NetRevenue", "AvgUnitPrice"]].style.format({
                    "ReturnsAmount": curr_sym + "{:,.2f}",
                    "NetRevenue": curr_sym + "{:,.2f}",
                    "AvgUnitPrice": curr_sym + "{:,.2f}",
                    "QuantitySold": "{:,}"
                }),
                use_container_width=True,
                height=380
            )

        with tab_trends:
            top_skus = prod_summary.head(10)["StockCode"].tolist()
            selected_skus = st.multiselect("Select Products for Monthly Trajectory:", top_skus, default=top_skus[:3])
            if selected_skus:
                prod_trends = get_product_monthly_trend(filtered_df, stock_codes=selected_skus)
                st.plotly_chart(create_product_monthly_trend_chart(prod_trends, curr_symbol=curr_sym, curr_rate=curr_rate), use_container_width=True)


# ==========================================
# MODULE 3: CUSTOMER ANALYTICS (RFM)
# ==========================================
elif menu == "3. Customer Analytics (RFM)":
    st.markdown(render_banner("Customer Purchasing Behaviour & RFM Segmentation", f"Transparent quintile-based Recency, Frequency, Monetary (RFM) behavioral clustering ({curr_sym})"), unsafe_allow_html=True)

    if filtered_df is None or filtered_df.empty:
        st.warning("No customer data available.")
    else:
        with st.expander("⚙️ Configure RFM Segmentation Parameters", expanded=False):
            rfm_bins = st.slider("Quantile Division Granularity (Binned 1 to N)", min_value=3, max_value=5, value=5)
            st.markdown("""
            **Scoring Rules:**
            - **Recency (R)**: Lower days since last purchase yields higher score (5 = most recent).
            - **Frequency (F)**: Higher unique orders yields higher score (5 = most frequent).
            - **Monetary (M)**: Higher net spend yields higher score (5 = highest lifetime value).
            """)

        with st.spinner("Computing customer RFM metrics..."):
            rfm_raw = calculate_rfm_metrics(filtered_df)
            scored_rfm = score_rfm(rfm_raw, q=rfm_bins)
            segmented_rfm = segment_customers(scored_rfm)
            seg_summary = get_rfm_segment_summary(segmented_rfm)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(render_kpi("Analyzed Accounts", f"{len(segmented_rfm):,}", "Identified customers", "#6366F1"), unsafe_allow_html=True)
        with col2:
            champ_cnt = int((segmented_rfm["Segment"] == "Champions").sum())
            st.markdown(render_kpi("Champions", f"{champ_cnt:,}", f"{(champ_cnt/max(len(segmented_rfm),1)*100):.1f}% of base", "#10B981"), unsafe_allow_html=True)
        with col3:
            at_risk_cnt = int((segmented_rfm["Segment"] == "At Risk").sum())
            st.markdown(render_kpi("At Risk Segment", f"{at_risk_cnt:,}", "Dormant high-spenders", "#EF4444"), unsafe_allow_html=True)
        with col4:
            loyal_cnt = int((segmented_rfm["Segment"] == "Loyal Customers").sum())
            st.markdown(render_kpi("Loyal Customers", f"{loyal_cnt:,}", "High repeat cadence", "#3B82F6"), unsafe_allow_html=True)

        st.markdown("###")

        c1, c2 = st.columns([1.3, 1.0])
        with c1:
            st.plotly_chart(create_rfm_scatter_chart(segmented_rfm, curr_symbol=curr_sym, curr_rate=curr_rate), use_container_width=True)
        with c2:
            st.plotly_chart(create_rfm_treemap(seg_summary, curr_symbol=curr_sym, curr_rate=curr_rate), use_container_width=True)

        st.markdown(f"#### 📋 Segment Distribution Summary Table ({curr_sym})")
        display_summary = seg_summary.copy()
        display_summary["TotalMonetary"] = display_summary["TotalMonetary"] * curr_rate
        display_summary["AvgMonetary"] = display_summary["AvgMonetary"] * curr_rate

        st.dataframe(
            display_summary.style.format({
                "CustomerCount": "{:,}",
                "CustomerSharePct": "{:.1f}%",
                "TotalMonetary": curr_sym + "{:,.2f}",
                "RevenueSharePct": "{:.1f}%",
                "AvgRecencyDays": "{:.1f} days",
                "AvgFrequency": "{:.1f} orders",
                "AvgMonetary": curr_sym + "{:,.2f}"
            }),
            use_container_width=True
        )

        with st.expander("🔍 Customer Profile Search & Individual RFM Lookup"):
            search_id = st.text_input("Enter Customer ID:", value="").strip()
            if search_id:
                cust_match = segmented_rfm[segmented_rfm["CustomerID"] == search_id]
                if not cust_match.empty:
                    c_row = cust_match.iloc[0]
                    st.success(f"Customer `{search_id}` found in segment **{c_row['Segment']}**!")
                    m1, m2, m3, m4, m5 = st.columns(5)
                    m1.metric("Recency", f"{c_row['Recency']} days", f"R Score: {c_row['R_Score']}")
                    m2.metric("Frequency", f"{c_row['Frequency']} orders", f"F Score: {c_row['F_Score']}")
                    m3.metric(f"Net Spend ({curr_sym})", fmt_curr(c_row['Monetary']), f"M Score: {c_row['M_Score']}")
                    m4.metric("RFM Code", f"{c_row['RFM_Score']}")
                    m5.metric("Country", f"{c_row['Country']}")
                    st.info(f"**Segment Context**: {c_row['SegmentDescription']}")
                else:
                    st.error(f"Customer ID `{search_id}` not found in the active dataset.")


# ==========================================
# MODULE 4: CUSTOMER CHURN PREDICTION
# ==========================================
elif menu == "4. Customer Churn Prediction":
    st.markdown(render_banner("Customer Churn Prediction Engine", "Predicting customer defection using rigorous historical snapshot methodology"), unsafe_allow_html=True)

    st.markdown("""
    <div class="cartly-disclaimer">
        <b>📐 Operational Churn Definition & Leakage Prevention Protocol:</b><br>
        A customer is labelled as <b>churned (1)</b> if they make <b>no purchase during the 90 days following the observation date</b>.<br>
        • <b>180-Day Historical Observation Window</b>: Features are extracted strictly from transactions occurring prior to the observation date.<br>
        • <b>90-Day Future Evaluation Window</b>: Target label is determined purely by future transactions.<br>
        • <b>Chronological Splitting</b>: Train and test sets are formed across chronological time periods to prevent any temporal data leakage.
    </div>
    """, unsafe_allow_html=True)

    cleaned_df = st.session_state["cleaned_df"]
    model_bundle = st.session_state["model_bundle"]

    col_btn1, col_btn2 = st.columns([1.2, 2.8])
    with col_btn1:
        retrain_clicked = st.button("🚀 Train / Retrain Churn Models", type="primary", use_container_width=True)

    if retrain_clicked:
        with st.spinner("Constructing chronological snapshots and training ML classifiers..."):
            train_df, test_df, split_meta = generate_chronological_churn_data(cleaned_df)
            if train_df.empty or test_df.empty:
                st.error("Dataset time span insufficient to build dual chronological snapshots.")
            else:
                train_res = train_and_compare_models(train_df, test_df, save_best_model=True)
                st.session_state["model_bundle"] = load_model_bundle()
                model_bundle = st.session_state["model_bundle"]
                st.success(f"Models trained successfully! Best performer: **{train_res['best_model_name']}** (F1: {train_res[train_res['best_model_name'].lower().replace(' ', '_')]['metrics']['f1_score']:.3f})")

    if model_bundle is None:
        st.info("ℹ️ No trained model currently found. Click the button above to train Logistic Regression and Random Forest models.")
    else:
        # Generate predictions for all active customers
        if st.session_state["predictions_df"] is None:
            with st.spinner("Scoring customer churn probabilities..."):
                max_dt = cleaned_df["InvoiceDate"].max()
                obs_dt = max_dt - pd.Timedelta(days=90)
                snapshot_df = build_churn_snapshot(cleaned_df, observation_date=obs_dt, history_days=180, future_days=90)
                if not snapshot_df.empty:
                    preds = predict_customer_churn_probabilities(model_bundle, snapshot_df)
                    st.session_state["predictions_df"] = preds

        pred_df = st.session_state["predictions_df"]

        if pred_df is not None and not pred_df.empty:
            c1, c2, c3, c4 = st.columns(4)
            high_risk = int((pred_df["risk_tier"] == "High").sum())
            med_risk = int((pred_df["risk_tier"] == "Medium").sum())
            low_risk = int((pred_df["risk_tier"] == "Low").sum())
            avg_prob = float(pred_df["churn_probability"].mean())

            with c1:
                st.markdown(render_kpi("High Risk Accounts", f"{high_risk:,}", "Probability >= 70%", "#EF4444"), unsafe_allow_html=True)
            with c2:
                st.markdown(render_kpi("Medium Risk Accounts", f"{med_risk:,}", "Probability 35% - 70%", "#F59E0B"), unsafe_allow_html=True)
            with c3:
                st.markdown(render_kpi("Low Risk Accounts", f"{low_risk:,}", "Probability < 35%", "#10B981"), unsafe_allow_html=True)
            with c4:
                st.markdown(render_kpi("Mean Churn Probability", f"{avg_prob*100:.1f}%", "Cohort average", "#6366F1"), unsafe_allow_html=True)

            st.markdown("###")
            st.plotly_chart(create_churn_probability_histogram(pred_df), use_container_width=True)

            # Individual customer search
            st.markdown("#### 🔎 Individual Customer Churn Risk Lookup")
            cust_search = st.text_input("Look up Customer ID for Churn Probability:", value="").strip()
            if cust_search:
                match = pred_df[pred_df["customer_id"] == cust_search]
                if not match.empty:
                    m = match.iloc[0]
                    tier_color = "#EF4444" if m["risk_tier"] == "High" else ("#F59E0B" if m["risk_tier"] == "Medium" else "#10B981")
                    st.markdown(f"""
                    <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-left:5px solid {tier_color}; border-radius:8px; padding:1.2rem; margin:1rem 0;">
                        <h4 style="margin:0; color:#1E293B;">Customer ID: <code>{cust_search}</code> | Risk Tier: <span style="color:{tier_color}; font-weight:700;">{m['risk_tier']}</span></h4>
                        <div style="display:flex; gap:24px; margin-top:12px; font-size:0.95rem;">
                            <div><b>Churn Probability:</b> {m['churn_probability']*100:.1f}%</div>
                            <div><b>Recency:</b> {m['recency_days']} days</div>
                            <div><b>Order Frequency:</b> {m['frequency_orders']}</div>
                            <div><b>Historical Spend ({curr_sym}):</b> {fmt_curr(m['monetary_spend'])}</div>
                            <div><b>Cancellation Rate:</b> {m['cancellation_rate']*100:.1f}%</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error(f"Customer `{cust_search}` was not active in the historical observation window.")


# ==========================================
# MODULE 5: SMART REVENUE PROTECTION ENGINE
# ==========================================
elif menu == "5. Revenue Protection Engine":
    st.markdown(render_banner("Smart Revenue Protection Engine", f"Cartly Signature Feature: Translating Churn Probabilities into Quantifiable Revenue at Risk ({curr_sym})"), unsafe_allow_html=True)

    st.markdown(f"""
    <div class="cartly-disclaimer">
        <b>💡 Revenue Protection Baseline Formula:</b><br>
        <code>Estimated Revenue at Risk = Churn Probability × Estimated Future Revenue</code><br>
        <i>Estimated Future Revenue</i> is computed from historical run-rate spend during the observation window.<br>
        <b>Active Currency:</b> <code>{selected_currency}</code> ({curr_cfg['desc']})<br>
        <b>Disclaimer:</b> This is an estimated exposure metric to prioritize retention interventions, not guaranteed lost revenue.
    </div>
    """, unsafe_allow_html=True)

    cleaned_df = st.session_state["cleaned_df"]
    model_bundle = st.session_state["model_bundle"]

    if model_bundle is None:
        st.warning("Please train the churn model in Module 4 before calculating Revenue at Risk.")
    else:
        # Build predictions and revenue protection
        if st.session_state["protected_df"] is None:
            if st.session_state["predictions_df"] is None:
                max_dt = cleaned_df["InvoiceDate"].max()
                obs_dt = max_dt - pd.Timedelta(days=90)
                snapshot_df = build_churn_snapshot(cleaned_df, observation_date=obs_dt, history_days=180, future_days=90)
                st.session_state["predictions_df"] = predict_customer_churn_probabilities(model_bundle, snapshot_df)

            st.session_state["protected_df"] = calculate_revenue_at_risk(st.session_state["predictions_df"])

        protected_df = st.session_state["protected_df"]
        summary = calculate_revenue_protection_summary(protected_df)

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.markdown(render_kpi(f"Revenue at Risk ({curr_sym})", fmt_curr(summary['total_revenue_at_risk']), f"{summary['pct_revenue_at_risk']:.1f}% of future spend", "#EF4444"), unsafe_allow_html=True)
        with col2:
            st.markdown(render_kpi(f"Projected Future Rev", fmt_curr(summary['total_future_revenue']), "90-day run rate", "#10B981"), unsafe_allow_html=True)
        with col3:
            st.markdown(render_kpi("Critical Attention", f"{summary['immediate_attention_customers']:,}", "High Risk + High Value", "#EF4444"), unsafe_allow_html=True)
        with col4:
            st.markdown(render_kpi("High-Risk Accounts", f"{summary['high_risk_customers']:,}", "Defection probability >= 70%", "#F59E0B"), unsafe_allow_html=True)
        with col5:
            st.markdown(render_kpi(f"Mean Exposure / Cust", fmt_curr(summary['avg_revenue_at_risk_per_customer']), "Average risk per account", "#6366F1"), unsafe_allow_html=True)

        st.markdown("###")

        c_mat, c_pie = st.columns([1.6, 1.0])
        with c_mat:
            st.plotly_chart(create_revenue_at_risk_scatter(protected_df, curr_symbol=curr_sym, curr_rate=curr_rate), use_container_width=True)
        with c_pie:
            st.plotly_chart(create_priority_donut_chart(protected_df), use_container_width=True)

        st.markdown(f"#### 🎯 High-Risk & High-Value Customer Protection Ranking ({curr_sym})")
        priority_filter = st.multiselect(
            "Filter Customer Exposure by Priority:",
            ["Critical", "High", "Medium", "Low"],
            default=["Critical", "High"]
        )

        filtered_exposure = protected_df[protected_df["priority"].isin(priority_filter)].copy() if priority_filter else protected_df.copy()
        filtered_exposure["DisplayFutureRev"] = filtered_exposure["estimated_future_revenue"] * curr_rate
        filtered_exposure["DisplayRisk"] = filtered_exposure["revenue_at_risk"] * curr_rate

        st.dataframe(
            filtered_exposure[[
                "risk_rank", "customer_id", "priority", "risk_tier", "customer_value_tier",
                "churn_probability", "DisplayFutureRev", "DisplayRisk", "recency_days", "frequency_orders"
            ]].rename(columns={
                "DisplayFutureRev": f"Estimated Future Rev ({curr_sym})",
                "DisplayRisk": f"Revenue at Risk ({curr_sym})"
            }).style.format({
                "churn_probability": "{:.1%}",
                f"Estimated Future Rev ({curr_sym})": curr_sym + "{:,.2f}",
                f"Revenue at Risk ({curr_sym})": curr_sym + "{:,.2f}"
            }),
            use_container_width=True,
            height=400
        )

        csv_data = filtered_exposure.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Export Revenue at Risk Table (CSV)", csv_data, "cartly_revenue_at_risk.csv", "text/csv")


# ==========================================
# MODULE 6: RETENTION RECOMMENDATIONS
# ==========================================
elif menu == "6. Retention Recommendations":
    st.markdown(render_banner("Smart Customer Retention Recommendations", f"Tailored, rule-based interventions to protect revenue and curb customer churn ({curr_sym})"), unsafe_allow_html=True)

    st.markdown(f"""
    <div class="cartly-disclaimer">
        <b>⚠️ Scientific Transparency Disclaimer:</b><br>
        {RETENTION_DISCLAIMER}<br>
        <b>Display Currency:</b> <code>{selected_currency}</code> ({curr_cfg['desc']})
    </div>
    """, unsafe_allow_html=True)

    protected_df = st.session_state["protected_df"]
    if protected_df is None:
        st.warning("Please visit Module 5 (Revenue Protection Engine) first to calculate revenue at risk.")
    else:
        if st.session_state["recommendations_df"] is None:
            with st.spinner("Generating customer retention recommendations..."):
                st.session_state["recommendations_df"] = generate_all_recommendations(protected_df)

        recs_df = st.session_state["recommendations_df"]

        col_f1, col_f2 = st.columns([1, 1])
        with col_f1:
            p_selected = st.selectbox("Filter Recommendations by Priority:", ["All", "Critical", "High", "Medium", "Low"], index=0)
        with col_f2:
            r_search = st.text_input("Filter by Customer ID:", value="").strip()

        display_recs = recs_df
        if p_selected != "All":
            display_recs = display_recs[display_recs["priority"] == p_selected]
        if r_search:
            display_recs = display_recs[display_recs["customer_id"] == r_search]

        st.caption(f"Displaying **{len(display_recs):,}** recommended actions:")

        for _, rec in display_recs.head(15).iterrows():
            card_class = rec["priority"].lower()
            badge = render_badge(rec["priority"], rec["priority"])
            risk_badge = render_badge(f"Risk: {rec['risk_level']}", rec['risk_level'])
            converted_risk = fmt_curr(rec['estimated_revenue_at_risk'])

            st.markdown(f"""
            <div class="recommendation-card {card_class}">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div style="font-weight:700; font-size:1.05rem; color:#0F172A;">
                        Customer <code>{rec['customer_id']}</code> &nbsp; {badge} &nbsp; {risk_badge}
                    </div>
                    <div style="font-weight:700; color:#EF4444; font-size:1.05rem;">
                        {converted_risk} at risk
                    </div>
                </div>
                <div style="margin-top:8px; font-weight:600; color:#4338CA; font-size:0.95rem;">
                    🎯 Recommended Action: {rec['recommended_action']}
                </div>
                <div style="margin-top:6px; color:#475569; font-size:0.875rem; line-height:1.4;">
                    <b>Reasoning:</b> {rec['reason']}
                </div>
            </div>
            """, unsafe_allow_html=True)

        if len(display_recs) > 15:
            st.info(f"Showing top 15 of {len(display_recs):,} recommendations. Export full table below.")

        csv_recs = display_recs.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Export Retention Action Plan (CSV)", csv_recs, "cartly_retention_recommendations.csv", "text/csv")


# ==========================================
# MODULE 7: MODEL PERFORMANCE
# ==========================================
elif menu == "7. Model Performance":
    st.markdown(render_banner("Machine Learning Model Performance & Evaluation", "Side-by-side benchmark of Logistic Regression and Random Forest classifiers"), unsafe_allow_html=True)

    model_bundle = st.session_state["model_bundle"]
    if model_bundle is None or "full_comparison" not in model_bundle:
        st.info("No comparative model training run recorded yet. Please go to Module 4 and train the models.")
    else:
        comp = model_bundle["full_comparison"]
        lr_metrics = comp["logistic_regression"]["metrics"]
        rf_metrics = comp["random_forest"]["metrics"]

        st.markdown(f"**Best Performing Model**: `{comp['best_model_name']}` (Selected based on balanced F1-Score & ROC-AUC)")
        st.markdown(f"**Dataset Split Details**: `{comp['train_samples']:,}` Train Snapshot Instances | `{comp['test_samples']:,}` Chronological Test Snapshot Instances")

        st.markdown("###")

        # Side-by-side metric comparison table
        metrics_table = pd.DataFrame({
            "Metric": ["Accuracy", "Precision", "Recall", "F1-Score", "ROC-AUC", "PR-AUC"],
            "Logistic Regression": [
                f"{lr_metrics['accuracy']:.4f}",
                f"{lr_metrics['precision']:.4f}",
                f"{lr_metrics['recall']:.4f}",
                f"{lr_metrics['f1_score']:.4f}",
                f"{lr_metrics['roc_auc']:.4f}",
                f"{lr_metrics['pr_auc']:.4f}"
            ],
            "Random Forest Classifier": [
                f"{rf_metrics['accuracy']:.4f}",
                f"{rf_metrics['precision']:.4f}",
                f"{rf_metrics['recall']:.4f}",
                f"{rf_metrics['f1_score']:.4f}",
                f"{rf_metrics['roc_auc']:.4f}",
                f"{rf_metrics['pr_auc']:.4f}"
            ]
        })
        st.dataframe(metrics_table, use_container_width=True)

        st.markdown("###")

        # Confusion Matrices
        c_cm1, c_cm2 = st.columns(2)
        with c_cm1:
            st.plotly_chart(create_confusion_matrix_heatmap(lr_metrics["confusion_matrix"], "Logistic Regression"), use_container_width=True)
        with c_cm2:
            st.plotly_chart(create_confusion_matrix_heatmap(rf_metrics["confusion_matrix"], "Random Forest"), use_container_width=True)

        # ROC and PR Curves
        roc_f, pr_f = create_roc_and_pr_curves(lr_metrics, rf_metrics)
        c_curve1, c_curve2 = st.columns(2)
        with c_curve1:
            st.plotly_chart(roc_f, use_container_width=True)
        with c_curve2:
            st.plotly_chart(pr_f, use_container_width=True)

        # Feature Importance
        st.markdown("###")
        c_imp1, c_imp2 = st.columns(2)
        with c_imp1:
            st.plotly_chart(create_feature_importance_chart(comp["logistic_regression"]["feature_importance"], "Logistic Regression (|Weights|)"), use_container_width=True)
        with c_imp2:
            st.plotly_chart(create_feature_importance_chart(comp["random_forest"]["feature_importance"], "Random Forest (Gini Importance)"), use_container_width=True)


# ==========================================
# MODULE 8: DATA MANAGEMENT
# ==========================================
elif menu == "8. Data Management":
    st.markdown(render_banner("Data Management, Ingestion & SQLite Storage", "Upload datasets, run data health diagnostics, inspect cleaning steps, and manage SQLite persistence"), unsafe_allow_html=True)

    tab_upload, tab_health, tab_db = st.tabs(["📁 Dataset Ingestion", "🩺 Data Quality Health Check", "💾 SQLite Database Management"])

    with tab_upload:
        st.markdown("#### Upload Retail Dataset (CSV or Excel)")
        uploaded_file = st.file_uploader("Upload CSV or XLSX file:", type=["csv", "xlsx", "xls"])

        if uploaded_file is not None:
            file_ext = uploaded_file.name.split(".")[-1].lower()
            with st.spinner("Parsing and validating uploaded dataset..."):
                u_raw, u_meta = load_dataset(uploaded_file, file_type=file_ext)

                if not u_meta["is_valid"]:
                    st.error(u_meta["error_message"])
                else:
                    st.success(f"File validated successfully! Found {len(u_raw):,} records with all canonical columns.")
                    st.session_state["raw_df"] = u_raw
                    st.session_state["active_data_source"] = "uploaded"

                    with st.spinner("Cleaning uploaded data..."):
                        u_cleaned, u_rep = clean_retail_data(u_raw, drop_missing_customers=True)
                        st.session_state["cleaned_df"] = u_cleaned
                        st.session_state["clean_report"] = u_rep
                        st.session_state["predictions_df"] = None
                        st.session_state["protected_df"] = None
                        st.session_state["recommendations_df"] = None
                    st.rerun()

        st.markdown("---")
        st.markdown("#### Raw Data Preview")
        if st.session_state["raw_df"] is not None:
            st.dataframe(st.session_state["raw_df"].head(100), use_container_width=True, height=300)
        else:
            st.info("No raw data loaded.")

    with tab_health:
        st.markdown("#### Data Quality & Cleaning Diagnostics")
        raw_df = st.session_state["raw_df"]
        rep = st.session_state["clean_report"]

        if raw_df is not None and rep is not None:
            h = generate_data_health_report(raw_df)

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Raw Records", f"{h['total_records']:,}")
            with col2:
                st.metric("Duplicate Rows", f"{h['duplicate_records']:,}", f"-{rep['duplicate_rows_removed']:,} removed")
            with col3:
                st.metric("Missing Customer IDs", f"{h['missing_counts'].get('Customer ID', 0):,}", f"{h['missing_percentages'].get('Customer ID', 0):.1f}%")
            with col4:
                st.metric("Cancellations Detected", f"{h['cancellations_count']:,}", f"{(h['cancellations_count']/max(h['total_records'],1)*100):.1f}%")

            st.markdown("###")
            st.markdown("##### Missing Values by Column:")
            missing_df = pd.DataFrame({
                "Column": list(h["missing_counts"].keys()),
                "Missing Count": list(h["missing_counts"].values()),
                "Missing Percentage": [f"{p:.2f}%" for p in h["missing_percentages"].values()]
            })
            st.dataframe(missing_df, use_container_width=True)

            st.markdown(f"##### Financial Cleaning Reconciliation ({curr_sym}):")
            st.markdown(f"""
            - **Gross Sales Realized**: `{fmt_curr(rep['gross_sales_gbp'])}`
            - **Returns & Offset Cancellations**: `{fmt_curr(rep['returns_amount_gbp'])}`
            - **Realized Net Revenue**: `{fmt_curr(rep['net_revenue_gbp'])}`
            - **Cleaned Records Preserved**: `{rep['final_rows']:,}` transactions across `{rep['unique_customers']:,}` customers
            """)

    with tab_db:
        st.markdown("#### SQLite Database Relational Store (`database/cartly.db`)")
        counts = get_table_counts()

        c_t1, c_t2, c_t3, c_t4 = st.columns(4)
        c_t1.metric("Customers Table", f"{counts.get('customers', 0):,}")
        c_t2.metric("Products Table", f"{counts.get('products', 0):,}")
        c_t3.metric("Orders Table", f"{counts.get('orders', 0):,}")
        c_t4.metric("Order Items Table", f"{counts.get('order_items', 0):,}")

        c_s1, c_s2 = st.columns(2)
        with c_s1:
            if st.button("🔄 Sync Active Cleaned Data to SQLite", use_container_width=True):
                with st.spinner("Ingesting to SQLite tables..."):
                    sync_cleaned_data_to_db(st.session_state["cleaned_df"])
                    if st.session_state["predictions_df"] is not None:
                        sync_predictions_to_db(st.session_state["predictions_df"])
                    if st.session_state["recommendations_df"] is not None:
                        sync_recommendations_to_db(st.session_state["recommendations_df"])
                    st.success("Synchronized successfully to SQLite database!")
                    st.rerun()

        with c_s2:
            if st.button("🗑️ Reset SQLite Database", use_container_width=True):
                reset_database()
                st.warning("SQLite database tables dropped and recreated clean.")
                st.rerun()
