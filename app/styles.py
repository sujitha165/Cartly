"""
Cartly Custom Styling and CSS Themes
Modern, professional retail intelligence styling for Streamlit.
"""

CUSTOM_CSS = """
<style>
/* Main typography and container styling */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Header branding banner */
.cartly-banner {
    background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
    padding: 1.5rem 2rem;
    border-radius: 12px;
    color: #FFFFFF;
    margin-bottom: 1.5rem;
    border-left: 5px solid #6366F1;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}
.cartly-banner h1 {
    font-size: 1.85rem;
    font-weight: 700;
    margin: 0;
    color: #FFFFFF;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.cartly-banner p {
    font-size: 0.95rem;
    color: #94A3B8;
    margin: 0.3rem 0 0 0;
}

/* KPI Card styling */
.kpi-container {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 1.2rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.kpi-container:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 14px rgba(0, 0, 0, 0.06);
}
.kpi-title {
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #64748B;
    margin-bottom: 0.3rem;
}
.kpi-value {
    font-size: 1.75rem;
    font-weight: 700;
    color: #0F172A;
    margin-bottom: 0.2rem;
}
.kpi-subtext {
    font-size: 0.8rem;
    color: #64748B;
}

/* Status Badges */
.badge-critical {
    background-color: #FEE2E2;
    color: #DC2626;
    padding: 0.2rem 0.6rem;
    border-radius: 9999px;
    font-weight: 600;
    font-size: 0.75rem;
    display: inline-block;
}
.badge-high {
    background-color: #FFEDD5;
    color: #EA580C;
    padding: 0.2rem 0.6rem;
    border-radius: 9999px;
    font-weight: 600;
    font-size: 0.75rem;
    display: inline-block;
}
.badge-medium {
    background-color: #FEF3C7;
    color: #D97706;
    padding: 0.2rem 0.6rem;
    border-radius: 9999px;
    font-weight: 600;
    font-size: 0.75rem;
    display: inline-block;
}
.badge-low {
    background-color: #DCFCE7;
    color: #16A34A;
    padding: 0.2rem 0.6rem;
    border-radius: 9999px;
    font-weight: 600;
    font-size: 0.75rem;
    display: inline-block;
}

/* Action Recommendation Card */
.recommendation-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 1.25rem;
    margin-bottom: 1rem;
    border-left: 4px solid #6366F1;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
}
.recommendation-card.critical {
    border-left-color: #EF4444;
}
.recommendation-card.high {
    border-left-color: #F97316;
}
.recommendation-card.medium {
    border-left-color: #FBBF24;
}
.recommendation-card.low {
    border-left-color: #10B981;
}

/* Disclaimer Callout Box */
.cartly-disclaimer {
    background-color: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-left: 4px solid #64748B;
    border-radius: 6px;
    padding: 0.85rem 1.15rem;
    font-size: 0.825rem;
    color: #475569;
    margin: 1rem 0;
}

/* Table aesthetic */
.dataframe {
    font-size: 0.85rem !important;
}
</style>
"""


def render_banner(title: str, subtitle: str) -> str:
    """Return HTML banner for section headers."""
    return f"""
    <div class="cartly-banner">
        <h1>{title}</h1>
        <p>{subtitle}</p>
    </div>
    """


def render_kpi(label: str, value: str, subtext: str = "", border_color: str = "#6366F1") -> str:
    """Return HTML for an executive KPI metric card."""
    return f"""
    <div class="kpi-container" style="border-top: 3px solid {border_color};">
        <div class="kpi-title">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-subtext">{subtext}</div>
    </div>
    """


def render_badge(text: str, level: str = "medium") -> str:
    """Return HTML for a status badge."""
    lvl = level.lower()
    return f'<span class="badge-{lvl}">{text}</span>'
