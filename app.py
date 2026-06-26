
"""
GeoCS 360 — Mailchimp-style Customer Success Platform
Versão corrigida:
- navegação funcional por session_state
- botão de voltar para login visível no topo e na sidebar
- cliente abre ticket e acompanha seus tickets
- admin lê, responde e atualiza status
- design claro inspirado em Mailchimp
"""

from __future__ import annotations

import math
from datetime import datetime
from html import escape
from textwrap import dedent
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

from src.classifier import classify_ticket
from src.db import (
    authenticate_user,
    execute,
    get_client_by_id,
    get_client_by_name,
    get_clients,
    get_tickets_for_user,
    init_db,
    insert_ticket,
    save_ticket_response,
    seed_clients_if_empty,
    seed_demo_tickets,
    seed_users_if_empty,
)


st.set_page_config(
    page_title="GeoCS 360",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

:root {
    --bg: #f6f7f2;
    --surface: #ffffff;
    --surface-2: #f9faf7;
    --surface-3: #f1f4ee;
    --ink: #111827;
    --muted: #667085;
    --dim: #98a2b3;
    --border: #d9e0d3;
    --border-soft: #edf0e8;
    --yellow: #ffcc00;
    --teal: #007c89;
    --teal-soft: #dff6f4;
    --blue: #2563eb;
    --blue-soft: #eaf1ff;
    --green: #10b981;
    --green-soft: #e9fbf3;
    --red: #ef4444;
    --red-soft: #feecec;
    --orange: #f97316;
    --orange-soft: #fff3e8;
    --purple: #7c3aed;
    --purple-soft: #f1ecff;
    --shadow: 0 12px 28px rgba(17, 24, 39, 0.06);
}

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

.stApp { background: var(--bg) !important; }

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at 85% 8%, rgba(255, 204, 0, 0.22), transparent 24%),
        linear-gradient(180deg, #fffdf4 0%, var(--bg) 42%, #f8faf5 100%) !important;
}

[data-testid="stHeader"] { display: none !important; }
#MainMenu, footer { visibility: hidden !important; }

.block-container {
    padding-top: 1.1rem !important;
    padding-bottom: 3rem !important;
    max-width: 1480px !important;
}

[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
    box-shadow: 8px 0 24px rgba(17, 24, 39, 0.03);
}

[data-testid="stSidebar"] .stRadio > label { display: none !important; }
[data-testid="stSidebar"] .stRadio > div { display: flex; flex-direction: column; gap: 4px; }
[data-testid="stSidebar"] .stRadio label {
    border-radius: 9px !important;
    padding: 10px 12px !important;
    color: #344054 !important;
    font-weight: 700 !important;
    border: 1px solid transparent !important;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: #fff8d6 !important;
    border-color: #f5e5a3 !important;
}
[data-testid="stSidebar"] .stRadio div[data-baseweb="radio"] > div:first-child {
    display: none !important;
}

.stTextInput input,
.stTextArea textarea,
[data-baseweb="select"] > div,
.stMultiSelect [data-baseweb="select"] > div {
    background: var(--surface) !important;
    border: 1px solid #cfd8c7 !important;
    border-radius: 10px !important;
    color: var(--ink) !important;
    box-shadow: none !important;
}

.stTextInput input:focus,
.stTextArea textarea:focus {
    border-color: var(--teal) !important;
    box-shadow: 0 0 0 3px rgba(0, 124, 137, 0.10) !important;
}

label, .stMarkdown p { color: #344054 !important; }
.stCaption, small { color: var(--muted) !important; }

.stButton > button {
    border-radius: 10px !important;
    font-weight: 800 !important;
    border: 1px solid #111827 !important;
    background: var(--yellow) !important;
    color: #111827 !important;
    box-shadow: none !important;
    min-height: 42px !important;
}

.stButton > button:hover {
    background: #f2bf00 !important;
    border-color: #111827 !important;
    transform: translateY(-1px);
}

.stAlert {
    border-radius: 12px !important;
    border: 1px solid var(--border) !important;
    background: var(--surface) !important;
}

.topbar {
    background: rgba(255, 255, 255, 0.94);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 14px 18px;
    margin-bottom: 18px;
    box-shadow: var(--shadow);
}

.searchbox {
    border: 1px solid var(--border);
    background: var(--surface);
    border-radius: 12px;
    padding: 10px 14px;
    color: var(--muted);
    font-size: .92rem;
}

.avatar {
    width: 42px;
    height: 42px;
    border-radius: 999px;
    background: #fff0b3;
    color: #111827;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: 900;
    border: 1px solid #f4d76b;
}

.page-title {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 16px;
    margin: 8px 0 18px;
}

.page-title h1 {
    color: var(--ink);
    font-size: 1.75rem;
    font-weight: 900;
    letter-spacing: -0.04em;
    margin: 0;
}

.page-title p {
    color: var(--muted);
    font-size: .94rem;
    margin: 6px 0 0;
}

.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 18px;
    box-shadow: var(--shadow);
}

.card-pad { padding: 18px; }

.metric-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 18px;
    min-height: 128px;
    box-shadow: 0 8px 20px rgba(17, 24, 39, 0.04);
    position: relative;
    overflow: hidden;
}

.metric-icon {
    position: absolute;
    right: 18px;
    top: 22px;
    width: 44px;
    height: 44px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.15rem;
}

.icon-blue { background: var(--blue-soft); color: var(--blue); }
.icon-green { background: var(--green-soft); color: var(--green); }
.icon-red { background: var(--red-soft); color: var(--red); }
.icon-orange { background: var(--orange-soft); color: var(--orange); }
.icon-purple { background: var(--purple-soft); color: var(--purple); }

.metric-label {
    color: #344054;
    font-size: .78rem;
    font-weight: 700;
    margin-bottom: 8px;
}

.metric-value {
    color: var(--ink);
    font-size: 2rem;
    line-height: 1;
    font-weight: 900;
    letter-spacing: -0.045em;
}

.metric-delta {
    margin-top: 10px;
    color: var(--teal);
    font-size: .78rem;
    font-weight: 800;
}

.filterbar {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 10px 12px;
    margin: 16px 0;
    box-shadow: 0 6px 14px rgba(17, 24, 39, 0.03);
}

.badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 5px 9px;
    border-radius: 999px;
    font-size: .72rem;
    font-weight: 900;
    white-space: nowrap;
}

.badge-critical { background: var(--red-soft); color: #b42318; }
.badge-high { background: var(--orange-soft); color: #c2410c; }
.badge-medium { background: #fff8d6; color: #8a5b00; }
.badge-low { background: var(--green-soft); color: #047857; }
.badge-status { background: var(--blue-soft); color: var(--blue); }
.badge-neutral { background: #eef2f6; color: #475467; }
.badge-yellow { background: #fff3b0; color: #111827; }

.ticket-row {
    background: var(--surface);
    border-top: 1px solid var(--border-soft);
    padding: 15px 16px;
}

.ticket-row-active {
    background: #f1f6ff;
    border-left: 4px solid var(--blue);
}

.ticket-title {
    color: var(--ink);
    font-size: .92rem;
    font-weight: 900;
    margin-bottom: 4px;
}

.ticket-sub {
    color: var(--muted);
    font-size: .78rem;
}

.ticket-time {
    color: var(--muted);
    font-size: .72rem;
    font-weight: 700;
}

.panel-title {
    color: var(--ink);
    font-size: 1rem;
    font-weight: 900;
    margin: 0;
}

.section-label {
    color: #475467;
    font-size: .72rem;
    font-weight: 900;
    letter-spacing: .06em;
    text-transform: uppercase;
    margin-bottom: 8px;
}

.detail-title {
    color: var(--ink);
    font-size: 1.25rem;
    font-weight: 900;
    letter-spacing: -0.03em;
    margin: 8px 0 4px;
}

.detail-sub {
    color: var(--muted);
    font-size: .82rem;
    margin-bottom: 16px;
}

.info-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 12px;
    margin: 14px 0;
}

.info-item {
    border-right: 1px solid var(--border-soft);
    padding-right: 10px;
}

.info-label {
    color: var(--muted);
    font-size: .72rem;
    margin-bottom: 4px;
}

.info-value {
    color: var(--ink);
    font-size: .82rem;
    font-weight: 900;
}

.message-box {
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px;
    color: #344054;
    font-size: .86rem;
    line-height: 1.55;
}

.response-box {
    background: #f0fbf9;
    border: 1px solid #bfe7e2;
    border-radius: 12px;
    padding: 14px;
    color: #234e52;
    font-size: .86rem;
    line-height: 1.55;
}

.side-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 16px;
    box-shadow: 0 6px 16px rgba(17, 24, 39, 0.04);
    margin-bottom: 12px;
}

.timeline {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.timeline-item {
    display: flex;
    gap: 10px;
    align-items: flex-start;
    color: #344054;
    font-size: .84rem;
}

.timeline-dot {
    margin-top: 4px;
    width: 9px;
    height: 9px;
    background: var(--teal);
    border-radius: 999px;
    box-shadow: 0 0 0 4px rgba(0, 124, 137, 0.10);
    flex-shrink: 0;
}

.client-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 18px;
    box-shadow: 0 8px 20px rgba(17, 24, 39, 0.04);
    height: 100%;
}

.health-track {
    width: 100%;
    height: 8px;
    background: #eef2e8;
    border-radius: 999px;
    overflow: hidden;
    margin-top: 8px;
}

.health-fill {
    height: 8px;
    border-radius: 999px;
}

.help-card {
    background: #fff8d6;
    border: 1px solid #f5df80;
    border-radius: 16px;
    padding: 16px;
}

.empty-state {
    border: 1px dashed var(--border);
    border-radius: 16px;
    padding: 46px;
    text-align: center;
    color: var(--muted);
    background: var(--surface-2);
}

.login-card {
    max-width: 980px;
    margin: 6vh auto;
    display: grid;
    grid-template-columns: 1.05fr .95fr;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 26px;
    overflow: hidden;
    box-shadow: 0 24px 60px rgba(17, 24, 39, 0.10);
}

.login-brand {
    background:
        radial-gradient(circle at 16% 16%, rgba(255,204,0,.8), transparent 24%),
        linear-gradient(135deg, #fff8d6, #f5f8ed);
    padding: 42px;
    border-right: 1px solid var(--border);
}

.login-form { padding: 42px; }

.step-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 15px 0;
    color: #344054;
    font-weight: 800;
}

.step-dot {
    width: 22px;
    height: 22px;
    border-radius: 999px;
    border: 2px solid var(--teal);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--teal);
    font-size: .7rem;
}

@media (max-width: 1100px) {
    .info-grid { grid-template-columns: repeat(2, 1fr); }
    .login-card { grid-template-columns: 1fr; }
    .login-brand { border-right: none; border-bottom: 1px solid var(--border); }
}
</style>
""",
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# BOOTSTRAP
# -----------------------------------------------------------------------------
init_db()
seed_clients_if_empty()
seed_users_if_empty()
seed_demo_tickets()


# -----------------------------------------------------------------------------
# SESSION STATE
# -----------------------------------------------------------------------------
DEFAULT_STATE = {
    "user": None,
    "selected_ticket": None,
    "last_classification": None,
    "app_page": None,
    "nav_history": [],
    "overview_status_filter": "Todos",
}
for k, v in DEFAULT_STATE.items():
    if k not in st.session_state:
        st.session_state[k] = v


# -----------------------------------------------------------------------------
# HELPERS
# -----------------------------------------------------------------------------
def html(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return escape(str(value))


def safe_value(row: Any, key: str, default: str = "") -> str:
    try:
        value = row.get(key, default)
    except Exception:
        return default
    if value is None:
        return default
    try:
        if pd.isna(value):
            return default
    except Exception:
        pass
    return str(value)


def initials(name: str) -> str:
    parts = [p for p in str(name).split() if p]
    if not parts:
        return "U"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def role_label(role: str) -> str:
    return {"admin": "Administrador", "client": "Cliente", "viewer": "Leitura"}.get(role, role.title())


def priority_badge(priority: str) -> str:
    cls = {
        "Crítica": "badge-critical",
        "Alta": "badge-high",
        "Média": "badge-medium",
        "Baixa": "badge-low",
    }.get(str(priority), "badge-neutral")
    return f"<span class='badge {cls}'>{html(priority)}</span>"


def status_badge(status: str) -> str:
    cls = {
        "Aberto": "badge-status",
        "Em análise": "badge-yellow",
        "Aguardando cliente": "badge-medium",
        "Resolvido": "badge-low",
        "Escalado": "badge-high",
    }.get(str(status), "badge-neutral")
    return f"<span class='badge {cls}'>{html(status)}</span>"


def metric_card(label: str, value: str, icon: str, color: str, delta: str = "") -> str:
    delta_html = f"<div class='metric-delta'>{html(delta)}</div>" if delta else ""
    return f"""
    <div class="metric-card">
        <div class="metric-label">{html(label)}</div>
        <div class="metric-value">{html(value)}</div>
        {delta_html}
        <div class="metric-icon icon-{html(color)}">{html(icon)}</div>
    </div>
    """


def set_page(target: str) -> None:
    """Navigate without changing a Streamlit widget key after instantiation."""
    current = st.session_state.get("app_page")
    if current and current != target:
        st.session_state.setdefault("nav_history", []).append(current)
    st.session_state["app_page"] = target
    st.rerun()


def go_back() -> None:
    """Return to previous app page using our own navigation history."""
    history = st.session_state.get("nav_history", [])
    if history:
        st.session_state["app_page"] = history.pop()
    else:
        # Safe default by profile when there is no previous page.
        role_name = st.session_state.get("user", {}).get("role", "viewer")
        st.session_state["app_page"] = "🏠  Portal do Cliente" if role_name == "client" else "🏠  Visão Geral"
    st.rerun()


def logout() -> None:
    """Return to login. Do not mutate any active widget key."""
    st.session_state["user"] = None
    st.session_state["selected_ticket"] = None
    st.session_state["last_classification"] = None
    st.session_state["app_page"] = None
    st.session_state["nav_history"] = []
    st.session_state["overview_status_filter"] = "Todos"
    st.rerun()


def page_header(title: str, subtitle: str, action_label: str | None = None, action_target: str | None = None) -> None:
    c1, c2 = st.columns([0.78, 0.22])
    with c1:
        st.markdown(
            f"""
            <div class="page-title">
                <div>
                    <h1>{html(title)}</h1>
                    <p>{html(subtitle)}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        if action_label and action_target:
            st.write("")
            if st.button(action_label, type="primary", use_container_width=True, key=f"header_{action_target}"):
                set_page(action_target)


def render_timeline(items: list[tuple[str, str]]) -> None:
    """Render timeline with native Streamlit components to avoid raw HTML leaks."""
    with st.container(border=True):
        for idx, (time_label, text) in enumerate(items):
            dot_col, content_col = st.columns([0.06, 0.94])
            with dot_col:
                st.markdown("<div class='timeline-dot'></div>", unsafe_allow_html=True)
            with content_col:
                st.markdown(f"**{html(time_label)}**  ")
                st.caption(str(text))
            if idx < len(items) - 1:
                st.divider()


def health_color(score: int) -> str:
    if score >= 85:
        return "var(--green)"
    if score >= 65:
        return "var(--orange)"
    return "var(--red)"


def generate_insights(tickets_df: pd.DataFrame, clients_df: pd.DataFrame) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    if not tickets_df.empty:
        critical_open = tickets_df[(tickets_df["priority"] == "Crítica") & (tickets_df["status"] != "Resolvido")]
        if not critical_open.empty:
            c = critical_open.iloc[0]
            out.append({"icon": "🚨", "title": f"{c['client_name']} requer atenção", "text": f"Ticket crítico aberto com SLA de {c['sla_hours']}h.", "color": "var(--red)"})

        top_product = tickets_df["product"].value_counts().index[0]
        out.append({"icon": "📌", "title": "Padrão de demanda", "text": f"{top_product} concentra o maior volume de solicitações.", "color": "var(--teal)"})

        waiting = int((tickets_df["status"] == "Aguardando cliente").sum())
        if waiting:
            out.append({"icon": "💬", "title": "Follow-up pendente", "text": f"{waiting} ticket(s) aguardam retorno do cliente.", "color": "var(--orange)"})

    if not clients_df.empty and "health_score" in clients_df.columns:
        low = clients_df.sort_values("health_score").iloc[0]
        if int(low["health_score"]) < 75:
            out.append({"icon": "📉", "title": "Health em atenção", "text": f"{low['client_name']} está com Health Score {low['health_score']}%.", "color": "var(--orange)"})

    return out[:4] or [{"icon": "✅", "title": "Operação saudável", "text": "Nenhum alerta relevante no momento.", "color": "var(--green)"}]


# -----------------------------------------------------------------------------
# FORECAST HELPERS — demanda por fila e vertical
# -----------------------------------------------------------------------------
def normalize_vertical(sector: str) -> str:
    """Agrupa setores dos clientes em verticais de negócio mais executivas."""
    s = str(sector or "").lower()

    if "telecom" in s:
        return "Telecom"
    if "varejo" in s:
        return "Varejo"
    if "energia" in s or "elétr" in s or "eletric" in s:
        return "Energia"
    if "públic" in s or "prefeitura" in s or "governo" in s:
        return "Prefeituras / Setor Público"
    if "óleo" in s or "oleo" in s or "gás" in s or "gas" in s or "campo" in s or "agroneg" in s:
        return "Óleo e Gás / Campo"
    if "sustentabilidade" in s or "cadeia" in s or "produtiva" in s:
        return "Sustentabilidade / Cadeia Produtiva"
    return "Outros"


def build_forecast_dataset(tickets_df: pd.DataFrame, clients_df: pd.DataFrame) -> pd.DataFrame:
    """Enriquece tickets com vertical, risco e health score do cliente."""
    if tickets_df.empty or clients_df.empty:
        return pd.DataFrame()

    df = tickets_df.copy()
    cl = clients_df.copy()

    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")

    keep_cols = [
        "client_name",
        "sector",
        "criticality",
        "health_score",
        "churn_risk",
    ]
    cl = cl[[c for c in keep_cols if c in cl.columns]].copy()
    cl["vertical"] = cl["sector"].apply(normalize_vertical)

    df = df.merge(cl, on="client_name", how="left")
    df["vertical"] = df["vertical"].fillna("Outros")
    df["responsible_team"] = df["responsible_team"].fillna("Customer Success Support")
    df["status"] = df["status"].fillna("Aberto")
    df["priority"] = df["priority"].fillna("Média")
    df["health_score"] = pd.to_numeric(df.get("health_score", 80), errors="coerce").fillna(80)

    return df


def forecast_by_dimension(
    tickets_df: pd.DataFrame,
    clients_df: pd.DataFrame,
    dimension: str,
    horizon_days: int = 7,
) -> pd.DataFrame:
    """Previsão operacional explicável para próximos dias.

    Fórmula do MVP:
    - média diária recente ponderada: 65% últimos 7 dias + 35% últimos 30 dias;
    - ajuste por backlog aberto;
    - ajuste por clientes críticos, churn alto e health score baixo;
    - fallback para bases pequenas.
    """
    df = build_forecast_dataset(tickets_df, clients_df)

    if df.empty or dimension not in df.columns:
        return pd.DataFrame(columns=[dimension, "historical_30d", "recent_7d", "open_backlog", "forecast_7d", "risk_level"])

    max_date = df["created_at"].max()
    if pd.isna(max_date):
        max_date = pd.Timestamp.now()

    start_30 = max_date - pd.Timedelta(days=30)
    start_7 = max_date - pd.Timedelta(days=7)

    df_30 = df[df["created_at"] >= start_30].copy()
    df_7 = df[df["created_at"] >= start_7].copy()

    rows: list[dict[str, Any]] = []

    for value in sorted(df[dimension].dropna().unique()):
        base_all = df[df[dimension] == value]
        base_30 = df_30[df_30[dimension] == value]
        base_7 = df_7[df_7[dimension] == value]

        historical_30d = len(base_30)
        recent_7d = len(base_7)
        avg_30 = historical_30d / 30
        avg_7 = recent_7d / 7
        weighted_daily_avg = (avg_7 * 0.65) + (avg_30 * 0.35)

        open_backlog = int((base_all["status"] != "Resolvido").sum())
        critical_open = int(((base_all["priority"] == "Crítica") & (base_all["status"] != "Resolvido")).sum())
        high_risk_clients = int(base_all[base_all.get("churn_risk", "") == "Alto"]["client_name"].nunique()) if "churn_risk" in base_all.columns else 0
        low_health_clients = int(base_all[base_all["health_score"] < 75]["client_name"].nunique()) if "health_score" in base_all.columns else 0
        critical_clients = int(base_all[base_all.get("criticality", "") == "Crítica"]["client_name"].nunique()) if "criticality" in base_all.columns else 0

        risk_factor = 1.0
        risk_factor += min(open_backlog * 0.04, 0.35)
        risk_factor += min(critical_open * 0.08, 0.24)
        risk_factor += high_risk_clients * 0.12
        risk_factor += low_health_clients * 0.10
        risk_factor += critical_clients * 0.08

        forecast = math.ceil(weighted_daily_avg * horizon_days * risk_factor)

        # fallback para MVP com poucos dados e seed demonstrativo
        if forecast == 0 and len(base_all) > 0:
            forecast = max(1, math.ceil(len(base_all) * 0.45))

        if forecast >= 8:
            risk_level = "Alta demanda"
        elif forecast >= 4:
            risk_level = "Atenção"
        else:
            risk_level = "Estável"

        rows.append(
            {
                dimension: value,
                "historical_30d": historical_30d,
                "recent_7d": recent_7d,
                "open_backlog": open_backlog,
                "forecast_7d": forecast,
                "risk_level": risk_level,
            }
        )

    out = pd.DataFrame(rows)
    return out.sort_values(["forecast_7d", "open_backlog"], ascending=[False, False]).reset_index(drop=True)


def render_forecast_summary(queue_fc: pd.DataFrame, vertical_fc: pd.DataFrame) -> None:
    total_fc = int(queue_fc["forecast_7d"].sum()) if not queue_fc.empty else 0
    top_queue = queue_fc.iloc[0]["responsible_team"] if not queue_fc.empty else "—"
    top_vertical = vertical_fc.iloc[0]["vertical"] if not vertical_fc.empty else "—"
    overloaded = int((queue_fc["risk_level"] == "Alta demanda").sum()) if not queue_fc.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(metric_card("Forecast 7 dias", str(total_fc), "🔮", "blue", "Chamados previstos"), unsafe_allow_html=True)
    with c2:
        st.markdown(metric_card("Fila mais pressionada", str(top_queue), "🎯", "orange", "Maior previsão"), unsafe_allow_html=True)
    with c3:
        st.markdown(metric_card("Vertical líder", str(top_vertical), "🏢", "purple", "Maior demanda"), unsafe_allow_html=True)
    with c4:
        st.markdown(metric_card("Filas em alerta", str(overloaded), "⚠️", "red", "Alta demanda"), unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# LOGIN
# -----------------------------------------------------------------------------
def login_screen() -> None:
    st.markdown(
        """
        <div class="login-card">
            <div class="login-brand">
                <div style="font-size:2rem;">⚡</div>
                <h1 style="margin:10px 0 8px;color:#111827;font-size:2.1rem;letter-spacing:-.06em;">GeoCS 360</h1>
                <p style="color:#344054;font-size:1rem;line-height:1.6;margin:0;">
                    Portal de Customer Success para abrir tickets, acompanhar SLA,
                    responder clientes e priorizar chamados críticos com contexto de negócio.
                </p>
                <div style="margin-top:26px;border-top:1px solid #eadb8a;padding-top:22px;">
                    <div class="step-row"><span class="step-dot">✓</span> Conta criada</div>
                    <div class="step-row"><span class="step-dot">2</span> Abra um ticket</div>
                    <div class="step-row"><span class="step-dot">3</span> Acompanhe o SLA</div>
                    <div class="step-row"><span class="step-dot">4</span> Responda ou resolva</div>
                </div>
            </div>
            <div class="login-form">
                <div style="font-size:.78rem;color:#007c89;text-transform:uppercase;letter-spacing:.08em;font-weight:900;">Acesso seguro</div>
                <h2 style="margin:8px 0 6px;color:#111827;letter-spacing:-.04em;">Entrar no portal</h2>
                <p style="margin:0 0 22px;color:#667085;font-size:.9rem;">Use um dos usuários demo para navegar por perfis diferentes.</p>
        """,
        unsafe_allow_html=True,
    )

    email = st.text_input("E-mail", value="admin@geocs.com")
    password = st.text_input("Senha", value="admin123", type="password")

    if st.button("Entrar", type="primary", use_container_width=True):
        user = authenticate_user(email, password)
        if user:
            st.session_state["user"] = user
            st.session_state["selected_ticket"] = None
            st.session_state["last_classification"] = None
            st.session_state["app_page"] = None
            st.session_state["nav_history"] = []
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")

    st.markdown(
        """
            <div class="help-card" style="margin-top:18px;">
                <div style="font-weight:900;color:#111827;margin-bottom:8px;">Usuários demo</div>
                <div style="color:#344054;font-size:.82rem;line-height:1.7;">
                    <strong>Admin:</strong> admin@geocs.com / admin123<br>
                    <strong>Vivo:</strong> vivo@cliente.com / vivo123<br>
                    <strong>Starbucks:</strong> starbucks@cliente.com / starbucks123<br>
                    <strong>Recife:</strong> recife@cliente.com / recife123<br>
                    <strong>Viewer:</strong> viewer@geocs.com / viewer123
                </div>
            </div>
        </div>
    </div>
        """,
        unsafe_allow_html=True,
    )


if not st.session_state["user"]:
    login_screen()
    st.stop()


user = st.session_state["user"]
role = user.get("role", "viewer")


# -----------------------------------------------------------------------------
# MENU
# -----------------------------------------------------------------------------
if role == "admin":
    menu_options = ["🏠  Visão Geral", "🎫  Tickets", "➕  Novo Ticket", "💬  Respostas", "👥  Clientes", "📊  Analytics"]
elif role == "client":
    menu_options = ["🏠  Portal do Cliente", "➕  Abrir Ticket", "🎫  Meus Tickets"]
else:
    menu_options = ["🏠  Visão Geral", "🎫  Tickets", "👥  Clientes"]

if st.session_state.get("app_page") not in menu_options:
    st.session_state["app_page"] = menu_options[0]

with st.sidebar:
    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:10px;margin:8px 0 18px;">
            <div style="font-size:1.8rem;">⚡</div>
            <div>
                <div style="font-weight:900;color:#111827;font-size:1.1rem;letter-spacing:-.04em;">GeoCS 360</div>
                <div style="color:#667085;font-size:.75rem;">Customer Success</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    current_index = menu_options.index(st.session_state["app_page"])
    page_choice = st.radio(
        "Navegação",
        menu_options,
        index=current_index,
        label_visibility="collapsed",
    )

    if page_choice != st.session_state["app_page"]:
        st.session_state.setdefault("nav_history", []).append(st.session_state["app_page"])
        st.session_state["app_page"] = page_choice
        st.rerun()

    page = st.session_state["app_page"]

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="side-card" style="box-shadow:none;">
            <div style="display:flex;align-items:center;gap:10px;">
                <span class="avatar" style="width:36px;height:36px;">{html(initials(user.get('name','Usuário')))}</span>
                <div>
                    <div style="font-weight:900;color:#111827;font-size:.86rem;">{html(user.get('name','Usuário'))}</div>
                    <div style="color:#667085;font-size:.74rem;">{html(role_label(role))}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("↩️ Voltar para login", use_container_width=True, key="logout_sidebar"):
        logout()

    st.markdown(
        """
        <div style="margin-top:28px;color:#667085;font-size:.75rem;">
            <strong style="color:#111827;">GeoCS 360</strong> v1.3<br>
            Portal de tickets e atendimento
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# DATA
# -----------------------------------------------------------------------------
all_clients = get_clients()
tickets = get_tickets_for_user(user)

if role == "client":
    client_profile = get_client_by_id(user["client_id"])
    clients = pd.DataFrame([client_profile])
else:
    client_profile = None
    clients = all_clients

insights = generate_insights(tickets, clients)


# -----------------------------------------------------------------------------
# TOPBAR
# -----------------------------------------------------------------------------
top1, top2, top3, top4 = st.columns([0.23, 0.45, 0.18, 0.14])
with top1:
    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:12px;padding-top:4px;">
            <div style="font-size:1.65rem;">⚡</div>
            <div>
                <div style="font-size:1.05rem;font-weight:900;color:#111827;letter-spacing:-.03em;">GeoCS 360</div>
                <div style="font-size:.75rem;color:#667085;">Customer Success</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with top2:
    st.markdown("<div class='searchbox'>🔎 &nbsp; Buscar tickets, clientes, produtos... <span style='float:right;color:#98A2B3;font-weight:700;'>Ctrl + K</span></div>", unsafe_allow_html=True)
with top3:
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;justify-content:flex-end;gap:10px;padding-top:1px;">
            <span style="color:#344054;font-weight:700;">Ajuda</span>
            <span style="font-size:1.2rem;">🔔</span>
            <span class="avatar">{html(initials(user.get('name','Usuário')))}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
with top4:
    back_col, exit_col = st.columns([0.36, 0.64])
    with back_col:
        if st.button("←", use_container_width=True, key="back_top", help="Voltar para a tela anterior"):
            go_back()
    with exit_col:
        if st.button("Sair", use_container_width=True, key="logout_top"):
            logout()

st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# TICKET DETAIL — polished UX, no giant markdown blocks
# -----------------------------------------------------------------------------
def render_html_block(markup: str) -> None:
    """Render HTML safely after dedenting.

    This avoids Streamlit/Markdown interpreting indented HTML as a code block.
    """
    st.markdown(dedent(markup).strip(), unsafe_allow_html=True)


def render_info_tile(label: str, value: Any, accent: str | None = None) -> None:
    color = accent or "#111827"
    render_html_block(
        f"""
        <div class="message-box" style="height:100%;">
            <div class="info-label">{html(label)}</div>
            <strong style="color:{color};">{html(value)}</strong>
        </div>
        """
    )


def render_text_section(label: str, value: Any, tone: str = "default") -> None:
    bg = "#f0fbf9" if tone == "success" else "var(--surface-2)"
    border = "#bfe7e2" if tone == "success" else "var(--border)"
    render_html_block(
        f"""
        <div style="margin-top:14px;">
            <div class="section-label">{html(label)}</div>
            <div class="message-box" style="background:{bg};border-color:{border};">
                {html(value)}
            </div>
        </div>
        """
    )


def render_ticket_header(row: pd.Series) -> None:
    status = safe_value(row, "status", "Aberto")
    render_html_block(
        f"""
        <div class="card card-pad" style="border-top:5px solid #ffcc00;margin-bottom:14px;">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:18px;">
                <div>
                    <div style="margin-bottom:10px;">
                        {priority_badge(safe_value(row, "priority"))}
                        <span style="margin-left:8px;">{status_badge(status)}</span>
                    </div>
                    <div class="detail-title">{html(row["client_name"])} · {html(row["category"])}</div>
                    <div class="detail-sub">Ticket #{html(row["ticket_id"])} · criado em {html(str(row.get("created_at", ""))[:16])}</div>
                </div>
                <div style="text-align:right;color:#667085;font-size:.82rem;min-width:150px;">
                    Produto<br>
                    <strong style="color:#111827;font-size:.92rem;">{html(row["product"])}</strong>
                </div>
            </div>
        </div>
        """
    )


def render_ticket_summary_grid(row: pd.Series) -> None:
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        render_info_tile("Cliente", row["client_name"])
    with c2:
        render_info_tile("Solicitante", row["requester"])
    with c3:
        render_info_tile("Produto", row["product"])
    with c4:
        render_info_tile("Categoria", row["category"])
    with c5:
        render_info_tile("SLA", f"{row['sla_hours']}h", "#b42318")


def render_ticket_timeline(row: pd.Series) -> None:
    created = str(row.get("created_at", ""))[:16] or "Abertura"
    status = safe_value(row, "status", "Aberto")
    responded_at = safe_value(row, "responded_at", "")[:16]
    items = [
        (created, "Ticket recebido pelo portal"),
        (created, f"Classificação automática: {safe_value(row, 'priority')} · {safe_value(row, 'category')}"),
        (created, f"SLA definido: {safe_value(row, 'sla_hours')}h"),
        (created, f"Equipe sugerida: {safe_value(row, 'responsible_team')}"),
    ]
    if responded_at:
        items.append((responded_at, f"Resposta oficial enviada · Status: {status}"))
    else:
        items.append(("Pendente", f"Aguardando tratativa do CS · Status: {status}"))
    render_timeline(items)


def render_admin_response_form(row: pd.Series) -> None:
    current_response = safe_value(row, "admin_response", "")
    render_html_block(
        """
        <div class="card card-pad" style="margin-top:14px;">
            <div class="panel-title">Responder cliente</div>
            <p style="color:#667085;font-size:.86rem;margin:6px 0 14px;">
                Escreva a resposta oficial e atualize o status do chamado.
            </p>
        </div>
        """
    )

    response_text = st.text_area(
        "Resposta ao cliente",
        value=current_response or safe_value(row, "suggested_response", ""),
        height=170,
        placeholder="Digite sua resposta para o cliente...",
        key=f"admin_response_{row['ticket_id']}",
    )

    c1, c2 = st.columns([0.68, 0.32])
    with c1:
        new_status = st.selectbox(
            "Alterar status",
            ["Em análise", "Aguardando cliente", "Resolvido", "Escalado", "Aberto"],
            key=f"status_{row['ticket_id']}",
        )
    with c2:
        st.write("")
        if st.button("📨 Enviar resposta", type="primary", use_container_width=True, key=f"send_{row['ticket_id']}"):
            if not response_text.strip():
                st.warning("Digite uma resposta antes de enviar.")
            else:
                save_ticket_response(
                    ticket_id=str(row["ticket_id"]),
                    response=response_text.strip(),
                    responder_name=user.get("name", "CS Admin"),
                    new_status=new_status,
                )
                st.success("Resposta enviada e status atualizado.")
                st.rerun()


def render_ticket_detail(row: pd.Series, allow_response: bool) -> None:
    """Render ticket detail with Streamlit components + small safe HTML blocks.

    The previous version used one large indented HTML block, which Markdown could
    interpret as a code block. This version is intentionally componentized.
    """
    current_response = safe_value(row, "admin_response", "")
    responded_by = safe_value(row, "responded_by", "")
    responded_at = safe_value(row, "responded_at", "")[:16]

    render_ticket_header(row)
    render_ticket_summary_grid(row)

    tab_details, tab_timeline, tab_response, tab_system = st.tabs(
        ["Detalhes", "Timeline", "Resposta", "Classificação"]
    )

    with tab_details:
        render_text_section("Mensagem do cliente", row["original_message"])
        render_text_section("Resumo executivo", row["summary"])
        render_text_section("Impacto no negócio", row["business_impact"])
        render_text_section("Próxima ação recomendada", row["next_action"])

    with tab_timeline:
        render_html_block(
            """
            <div class="card card-pad" style="margin-top:10px;">
                <div class="panel-title">Linha do tempo do atendimento</div>
            </div>
            """
        )
        render_ticket_timeline(row)

    with tab_response:
        if current_response:
            render_html_block(
                f"""
                <div class="response-box" style="margin-top:10px;">
                    <div style="font-size:.73rem;color:#007c89;font-weight:900;text-transform:uppercase;letter-spacing:.06em;margin-bottom:8px;">
                        Resposta oficial {('por ' + html(responded_by)) if responded_by else ''} {('· ' + html(responded_at)) if responded_at else ''}
                    </div>
                    {html(current_response)}
                </div>
                """
            )
        elif role == "client":
            st.info("Seu ticket foi aberto. O time de Customer Success ainda não enviou uma resposta oficial.")
        else:
            st.info("Este ticket ainda não possui resposta oficial enviada ao cliente.")

        if allow_response:
            render_admin_response_form(row)

    with tab_system:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_info_tile("Prioridade", safe_value(row, "priority"), "#b42318" if safe_value(row, "priority") == "Crítica" else None)
        with c2:
            render_info_tile("Sentimento", safe_value(row, "sentiment"))
        with c3:
            render_info_tile("Objetivo", safe_value(row, "business_objective"))
        with c4:
            render_info_tile("Região", safe_value(row, "region_detected", "Não identificada"))

        render_text_section("Resposta sugerida pelo sistema", safe_value(row, "suggested_response"))


# -----------------------------------------------------------------------------
# PAGE: OVERVIEW / CLIENT PORTAL
# -----------------------------------------------------------------------------
if page in ("🏠  Visão Geral", "🏠  Portal do Cliente"):
    if role == "client":
        page_header("Portal do Cliente", f"Acompanhe seus tickets, status, respostas e SLA · {client_profile['client_name']}")
        cta1, cta2 = st.columns([0.24, 0.24])
        with cta1:
            if st.button("➕ Abrir novo ticket", type="primary", use_container_width=True):
                set_page("➕  Abrir Ticket")
        with cta2:
            if st.button("🎫 Ver meus tickets", use_container_width=True):
                set_page("🎫  Meus Tickets")
    else:
        page_header("Visão Geral", "Acompanhe os principais indicadores de atendimento", "＋ Novo Ticket", "➕  Novo Ticket")

    total = len(tickets)
    critical = int((tickets["priority"] == "Crítica").sum()) if not tickets.empty else 0
    avg_sla = f"{tickets['sla_hours'].mean():.1f}h" if not tickets.empty else "—"
    avg_health = f"{int(clients['health_score'].mean())}%" if not clients.empty else "—"
    high_risk = int((clients["churn_risk"] == "Alto").sum()) if not clients.empty and "churn_risk" in clients.columns else 0

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.markdown(metric_card("Total de Tickets", str(total), "📄", "blue", "+12% vs ontem"), unsafe_allow_html=True)
    with m2:
        st.markdown(metric_card("Tickets Críticos", str(critical), "⚠️", "red", "+5% vs ontem"), unsafe_allow_html=True)
    with m3:
        st.markdown(metric_card("SLA Médio", avg_sla, "🕒", "green", "-8% vs ontem"), unsafe_allow_html=True)
    with m4:
        st.markdown(metric_card("Health Score Médio", avg_health, "💜", "purple", "+3% vs ontem"), unsafe_allow_html=True)
    with m5:
        st.markdown(metric_card("Clientes em Risco", str(high_risk), "👥", "orange", "-2% vs ontem"), unsafe_allow_html=True)

    # Clickable operational filters.
    # These filters let the presenter/user immediately inspect which tickets are
    # inside each status bucket shown in the summary bar.
    status_filter_map = {
        "Todos": None,
        "Abertos": ["Aberto"],
        "Em andamento": ["Em análise", "Escalado"],
        "Aguardando cliente": ["Aguardando cliente"],
        "Resolvidos": ["Resolvido"],
    }

    status_counts = {
        "Todos": total,
        "Abertos": int((tickets["status"] == "Aberto").sum()) if not tickets.empty else 0,
        "Em andamento": int(tickets["status"].isin(["Em análise", "Escalado"]).sum()) if not tickets.empty else 0,
        "Aguardando cliente": int((tickets["status"] == "Aguardando cliente").sum()) if not tickets.empty else 0,
        "Resolvidos": int((tickets["status"] == "Resolvido").sum()) if not tickets.empty else 0,
    }

    current_status_filter = st.session_state.get("overview_status_filter", "Todos")
    if current_status_filter not in status_filter_map:
        current_status_filter = "Todos"
        st.session_state["overview_status_filter"] = "Todos"

    st.markdown("<div class='filterbar'>", unsafe_allow_html=True)
    filter_cols = st.columns(5)
    for col, label in zip(filter_cols, status_filter_map.keys()):
        with col:
            selected = current_status_filter == label
            btn_label = f"{label}  {status_counts[label]}"
            if st.button(
                btn_label,
                key=f"overview_status_{label}",
                use_container_width=True,
                type="primary" if selected else "secondary",
            ):
                st.session_state["overview_status_filter"] = label
                st.session_state["selected_ticket"] = None
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    overview_tickets = tickets.copy()
    selected_statuses = status_filter_map.get(current_status_filter)
    if selected_statuses and not overview_tickets.empty:
        overview_tickets = overview_tickets[overview_tickets["status"].isin(selected_statuses)].copy()

    st.caption(f"Filtro ativo: {current_status_filter} · {len(overview_tickets)} ticket(s) encontrados")

    col_left, col_mid, col_right = st.columns([0.33, 0.42, 0.25], gap="medium")

    with col_left:
        st.markdown("<div class='card' style='overflow:hidden;'>", unsafe_allow_html=True)
        st.markdown("<div class='card-pad'><div class='panel-title'>Tickets Recentes</div></div>", unsafe_allow_html=True)

        if overview_tickets.empty:
            st.markdown("<div class='empty-state'>Nenhum ticket encontrado para este filtro.</div>", unsafe_allow_html=True)
        else:
            if (
                st.session_state["selected_ticket"] is None
                or st.session_state["selected_ticket"] not in overview_tickets["ticket_id"].astype(str).tolist()
            ):
                st.session_state["selected_ticket"] = overview_tickets.iloc[0]["ticket_id"]

            for _, row in overview_tickets.head(10).iterrows():
                active = st.session_state["selected_ticket"] == row["ticket_id"]
                active_class = " ticket-row-active" if active else ""
                st.markdown(
                    f"""
                    <div class="ticket-row{active_class}">
                        <div style="display:flex;justify-content:space-between;gap:8px;">
                            <div>
                                <div class="ticket-title">{html(row["client_name"])} - {html(row["category"])}</div>
                                <div class="ticket-sub">#{html(row["ticket_id"])} · {html(row["requester"])}</div>
                            </div>
                            <div class="ticket-time">{html(str(row.get("created_at", ""))[:16])}</div>
                        </div>
                        <div style="margin-top:10px;">{priority_badge(row["priority"])} {status_badge(row.get("status", "Aberto"))}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("Abrir", key=f"open_recent_{row['ticket_id']}", use_container_width=True):
                    st.session_state["selected_ticket"] = row["ticket_id"]
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    selected_id = st.session_state["selected_ticket"]
    selected_df = overview_tickets[overview_tickets["ticket_id"] == selected_id] if selected_id and not overview_tickets.empty else pd.DataFrame()

    with col_mid:
        if selected_df.empty:
            st.markdown("<div class='empty-state'>Selecione um ticket para ver os detalhes.</div>", unsafe_allow_html=True)
        else:
            render_ticket_detail(selected_df.iloc[0], allow_response=False)

    with col_right:
        if role == "admin" and not selected_df.empty:
            r = selected_df.iloc[0]
            st.markdown("<div class='side-card'>", unsafe_allow_html=True)
            st.markdown("<div class='panel-title'>Responder cliente</div>", unsafe_allow_html=True)
            response_text = st.text_area(
                "Resposta",
                value=safe_value(r, "admin_response", "") or safe_value(r, "suggested_response", ""),
                height=140,
                placeholder="Digite sua resposta para o cliente...",
                key=f"quick_response_{r['ticket_id']}",
            )
            new_status = st.selectbox(
                "Alterar status",
                ["Em análise", "Aguardando cliente", "Resolvido", "Escalado", "Aberto"],
                key=f"quick_status_{r['ticket_id']}",
            )
            if st.button("📨 Enviar resposta", type="primary", use_container_width=True, key=f"quick_send_{r['ticket_id']}"):
                if not response_text.strip():
                    st.warning("Digite uma resposta antes de enviar.")
                else:
                    save_ticket_response(
                        ticket_id=str(r["ticket_id"]),
                        response=response_text.strip(),
                        responder_name=user.get("name", "CS Admin"),
                        new_status=new_status,
                    )
                    st.success("Resposta enviada.")
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='side-card'>", unsafe_allow_html=True)
        st.markdown("<div class='panel-title'>Insights</div>", unsafe_allow_html=True)
        for item in insights:
            st.markdown(
                f"""
                <div style="display:flex;gap:10px;margin-top:14px;">
                    <div style="font-size:1.15rem;">{html(item["icon"])}</div>
                    <div>
                        <div style="font-weight:900;color:{item["color"]};font-size:.84rem;">{html(item["title"])}</div>
                        <div style="color:#667085;font-size:.78rem;line-height:1.45;">{html(item["text"])}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# PAGE: NEW TICKET
# -----------------------------------------------------------------------------
elif page in ("➕  Novo Ticket", "➕  Abrir Ticket"):
    page_header(
        "Abrir Ticket" if role == "client" else "Novo Ticket",
        "Descreva o problema e a plataforma classificará prioridade, produto, SLA e equipe responsável",
    )

    examples = {
        "Vivo — Telecom / Rede": "Após a atualização do portal, o mapa de cobertura da região de Campinas deixou de exibir torres LTE e 5G. A equipe de planejamento não consegue validar a expansão prevista para esta semana.",
        "Starbucks — Expansão de Lojas": "Estamos avaliando novos pontos de loja no Sudeste, mas o dashboard com dados de mobilidade urbana e potencial de consumo não atualiza desde ontem. A análise de expansão está parada.",
        "BP — Campo": "As equipes de campo não conseguem sincronizar os pontos coletados no Field Maps desde ontem. Isso está atrasando a logística agrícola e gerando retrabalho.",
        "Eletrobras Chesf — Ativos": "Após a atualização do portal, nossa equipe não consegue visualizar ativos da rede elétrica no ArcGIS Enterprise. Precisamos disso para operação e manutenção.",
        "Prefeitura do Recife — COP": "O mapa de monitoramento das ocorrências do Centro de Operações deixou de atualizar em tempo real e está impactando a resposta a eventos críticos.",
        "Natura — Sustentabilidade": "O dashboard de rastreabilidade da cadeia sustentável não atualizou os dados desta semana e precisamos validar indicadores para uma reunião executiva.",
    }

    col_form, col_result = st.columns([0.45, 0.55], gap="large")

    with col_form:
        st.markdown("<div class='card card-pad'>", unsafe_allow_html=True)
        if role == "client":
            selected_client = client_profile["client_name"]
            st.markdown("<div class='section-label'>Cliente</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='message-box' style='font-weight:900;color:#111827;'>{html(selected_client)}</div>", unsafe_allow_html=True)
            requester = st.text_input("Solicitante", value=user.get("name", "Cliente"))
            available_examples = ["Mensagem livre"]
        else:
            selected_client = st.selectbox("Cliente", clients["client_name"].tolist())
            requester = st.text_input("Solicitante", value="Analista do Cliente")
            available_examples = ["Mensagem livre"] + list(examples.keys())

        selected_example = st.selectbox("Carregar exemplo", available_examples)
        default_message = "" if selected_example == "Mensagem livre" else examples[selected_example]
        message = st.text_area("Mensagem recebida", value=default_message, height=180, placeholder="Descreva o problema relatado pelo cliente...")

        submitted = st.button("⚡ Analisar e criar ticket", type="primary", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_result:
        if submitted:
            if not message.strip():
                st.warning("Digite uma mensagem para analisar.")
            else:
                with st.spinner("Classificando chamado..."):
                    client_row = get_client_by_name(selected_client)
                    classification = classify_ticket(message, client_row)
                    ticket_id = insert_ticket(client_row, requester, message, classification)
                    st.session_state["last_classification"] = {
                        "ticket_id": ticket_id,
                        "client": selected_client,
                        "classification": classification,
                    }
                    st.session_state["selected_ticket"] = ticket_id

        lc = st.session_state["last_classification"]
        if lc:
            c = lc["classification"]
            tid = lc["ticket_id"]
            now = datetime.now().strftime("%H:%M")
            # Success card: render with dedent helper to avoid Markdown treating
            # indented HTML as a code block.
            render_html_block(
                f"""
                <div class="card card-pad" style="border-top:4px solid var(--green);">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            <div style="font-size:.8rem;color:#007c89;font-weight:900;text-transform:uppercase;letter-spacing:.06em;">Ticket criado</div>
                            <div style="font-size:1.3rem;font-weight:900;color:#111827;margin-top:4px;">#{html(tid)}</div>
                        </div>
                        <div style="font-size:2rem;">✅</div>
                    </div>
                </div>
                """
            )

            s1, s2, s3 = st.columns(3)
            with s1:
                render_info_tile("Produto", c["product"])
            with s2:
                render_info_tile("Prioridade", c["priority"], "#b42318" if c["priority"] == "Crítica" else None)
            with s3:
                render_info_tile("SLA", f"{c['sla_hours']}h", "#b42318")

            render_text_section("Impacto identificado", c["business_impact"])
            render_text_section("Próxima ação", c["next_action"])

            st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown("#### Timeline")
                render_timeline(
                    [
                        (now, "Chamado recebido"),
                        (now, "Classificação por regras concluída"),
                        (now, f"SLA definido: {c['sla_hours']}h"),
                        (now, f"Equipe atribuída: {c['responsible_team']}"),
                        (now, f"Ticket #{tid} criado no sistema"),
                    ]
                )

            st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
            if st.button("🎫 Abrir ticket criado", use_container_width=True):
                set_page("🎫  Meus Tickets" if role == "client" else "🎫  Tickets")
        else:
            render_html_block(
                """
                <div class="empty-state">
                    <div style="font-size:2rem;margin-bottom:10px;">⚡</div>
                    <strong>Classifique um chamado para ver o resultado aqui</strong><br>
                    Produto · Prioridade · SLA · Timeline
                </div>
                """
            )


# -----------------------------------------------------------------------------
# PAGE: TICKETS
# -----------------------------------------------------------------------------
elif page in ("🎫  Tickets", "🎫  Meus Tickets"):
    page_header(
        "Meus Tickets" if role == "client" else "Tickets",
        "Acompanhe status, SLA, resposta oficial e detalhes de cada solicitação" if role == "client" else "Painel operacional para leitura, resposta e tratativa dos chamados",
        "＋ Novo Ticket" if role == "admin" else None,
        "➕  Novo Ticket" if role == "admin" else None,
    )

    if tickets.empty:
        st.markdown("<div class='empty-state'>Nenhum ticket encontrado.</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='filterbar'>", unsafe_allow_html=True)
        if role == "client":
            f1, f2 = st.columns(2)
            f_client = []
            with f1:
                f_priority = st.multiselect("Prioridade", ["Crítica", "Alta", "Média", "Baixa"])
            with f2:
                f_status = st.multiselect("Status", sorted(tickets["status"].unique()))
        else:
            f1, f2, f3 = st.columns(3)
            with f1:
                f_client = st.multiselect("Cliente", sorted(tickets["client_name"].unique()))
            with f2:
                f_priority = st.multiselect("Prioridade", ["Crítica", "Alta", "Média", "Baixa"])
            with f3:
                f_status = st.multiselect("Status", sorted(tickets["status"].unique()))
        st.markdown("</div>", unsafe_allow_html=True)

        df = tickets.copy()
        if f_client:
            df = df[df["client_name"].isin(f_client)]
        if f_priority:
            df = df[df["priority"].isin(f_priority)]
        if f_status:
            df = df[df["status"].isin(f_status)]

        col_list, col_detail = st.columns([0.34, 0.66], gap="medium")

        with col_list:
            st.markdown("<div class='card' style='overflow:hidden;'>", unsafe_allow_html=True)
            st.markdown("<div class='card-pad'><div class='panel-title'>Lista de tickets</div></div>", unsafe_allow_html=True)
            for _, row in df.iterrows():
                active = st.session_state["selected_ticket"] == row["ticket_id"]
                active_class = " ticket-row-active" if active else ""
                st.markdown(
                    f"""
                    <div class="ticket-row{active_class}">
                        <div style="display:flex;justify-content:space-between;gap:8px;">
                            <div>
                                <div class="ticket-title">{html(row["client_name"])} - {html(row["category"])}</div>
                                <div class="ticket-sub">#{html(row["ticket_id"])} · {html(row["product"])}</div>
                            </div>
                            <div class="ticket-time">{html(str(row.get("created_at", ""))[:16])}</div>
                        </div>
                        <div style="margin-top:10px;">{priority_badge(row["priority"])} {status_badge(row.get("status", "Aberto"))}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("Abrir ticket", key=f"open_ticket_{row['ticket_id']}", use_container_width=True):
                    st.session_state["selected_ticket"] = row["ticket_id"]
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        with col_detail:
            selected_id = st.session_state["selected_ticket"]
            if selected_id:
                selected = df[df["ticket_id"] == selected_id]
                if selected.empty:
                    selected = tickets[tickets["ticket_id"] == selected_id]
                if not selected.empty:
                    render_ticket_detail(selected.iloc[0], allow_response=(role == "admin"))
                else:
                    st.markdown("<div class='empty-state'>Ticket não encontrado nos filtros atuais.</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='empty-state'>Selecione um ticket para ler os detalhes.</div>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# PAGE: RESPONSES
# -----------------------------------------------------------------------------
elif page == "💬  Respostas":
    page_header("Respostas", "Fila rápida para responder clientes e atualizar status dos chamados")

    pending = tickets[tickets["status"] != "Resolvido"].copy() if not tickets.empty else pd.DataFrame()
    if pending.empty:
        st.markdown("<div class='empty-state'>Nenhuma resposta pendente.</div>", unsafe_allow_html=True)
    else:
        selected_id = st.selectbox(
            "Selecionar ticket",
            pending["ticket_id"].tolist(),
            format_func=lambda x: f"#{x} · {pending[pending['ticket_id'] == x].iloc[0]['client_name']} · {pending[pending['ticket_id'] == x].iloc[0]['category']}",
        )
        selected = pending[pending["ticket_id"] == selected_id].iloc[0]
        render_ticket_detail(selected, allow_response=True)


# -----------------------------------------------------------------------------
# PAGE: CLIENTS
# -----------------------------------------------------------------------------
elif page == "👥  Clientes":
    page_header("Clientes", "Base de clientes e contexto de negócio usado na priorização")

    if clients.empty:
        st.markdown("<div class='empty-state'>Sem clientes cadastrados.</div>", unsafe_allow_html=True)
    else:
        grid = st.columns(3)
        for idx, (_, c) in enumerate(clients.iterrows()):
            with grid[idx % 3]:
                score = int(c["health_score"])
                fill = health_color(score)
                ct = tickets[tickets["client_name"] == c["client_name"]] if not tickets.empty else pd.DataFrame()
                open_count = int((ct["status"] != "Resolvido").sum()) if not ct.empty else 0
                critical_count = int((ct["priority"] == "Crítica").sum()) if not ct.empty else 0
                st.markdown(
                    f"""
                    <div class="client-card">
                        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px;">
                            <div>
                                <div style="font-weight:900;color:#111827;font-size:1.05rem;">{html(c["client_name"])}</div>
                                <div style="color:#667085;font-size:.8rem;margin-top:2px;">{html(c["sector"])}</div>
                            </div>
                            {status_badge(c["churn_risk"])}
                        </div>
                        <div style="margin-top:16px;">
                            <div style="display:flex;justify-content:space-between;color:#344054;font-size:.82rem;">
                                <span>Health Score</span><strong>{score}%</strong>
                            </div>
                            <div class="health-track"><div class="health-fill" style="width:{score}%;background:{fill};"></div></div>
                        </div>
                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:16px;">
                            <div class="message-box"><div class="info-label">Abertos</div><strong>{open_count}</strong></div>
                            <div class="message-box"><div class="info-label">Críticos</div><strong>{critical_count}</strong></div>
                        </div>
                        <div style="margin-top:14px;color:#667085;font-size:.82rem;line-height:1.55;">{html(c["business_context"])}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# -----------------------------------------------------------------------------
# PAGE: ANALYTICS
# -----------------------------------------------------------------------------
elif page == "📊  Analytics":
    page_header("Analytics", "Indicadores executivos da operação de Customer Success")

    if tickets.empty:
        st.markdown("<div class='empty-state'>Sem dados para análise.</div>", unsafe_allow_html=True)
    else:
        c1, c2 = st.columns(2, gap="medium")
        with c1:
            fig = px.histogram(
                tickets,
                x="priority",
                title="Tickets por prioridade",
                category_orders={"priority": ["Crítica", "Alta", "Média", "Baixa"]},
                color="priority",
                color_discrete_map={"Crítica": "#ef4444", "Alta": "#f97316", "Média": "#facc15", "Baixa": "#10b981"},
            )
            fig.update_layout(paper_bgcolor="white", plot_bgcolor="white", font_color="#344054", margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig = px.histogram(tickets, x="product", title="Tickets por produto", color_discrete_sequence=["#007c89"])
            fig.update_layout(paper_bgcolor="white", plot_bgcolor="white", font_color="#344054", margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig, use_container_width=True)

        c3, c4 = st.columns(2, gap="medium")
        with c3:
            fig = px.histogram(
                tickets,
                x="client_name",
                color="priority",
                title="Tickets por cliente",
                color_discrete_map={"Crítica": "#ef4444", "Alta": "#f97316", "Média": "#facc15", "Baixa": "#10b981"},
            )
            fig.update_layout(paper_bgcolor="white", plot_bgcolor="white", font_color="#344054", margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig, use_container_width=True)
        with c4:
            fig = px.scatter_mapbox(
                clients,
                lat="latitude",
                lon="longitude",
                hover_name="client_name",
                hover_data=["sector", "health_score", "churn_risk"],
                color="churn_risk",
                size="health_score",
                zoom=3.2,
                height=420,
                color_discrete_map={"Baixo": "#10b981", "Médio": "#f97316", "Alto": "#ef4444"},
            )
            fig.update_layout(mapbox_style="open-street-map", paper_bgcolor="white", margin=dict(l=0, r=0, t=35, b=0), title="Mapa de clientes")
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.markdown("## Previsão de abertura de chamados")
        st.caption(
            "Estimativa operacional para os próximos 7 dias, calculada por média recente, histórico de 30 dias, backlog, criticidade, Health Score e risco do cliente."
        )

        forecast_queue = forecast_by_dimension(tickets, clients, "responsible_team", horizon_days=7)
        forecast_vertical = forecast_by_dimension(tickets, clients, "vertical", horizon_days=7)

        render_forecast_summary(forecast_queue, forecast_vertical)

        fq_col, fv_col = st.columns(2, gap="medium")

        risk_colors = {
            "Alta demanda": "#ef4444",
            "Atenção": "#f97316",
            "Estável": "#10b981",
        }

        with fq_col:
            st.markdown("### Por fila de atendimento")
            if forecast_queue.empty:
                st.info("Sem dados suficientes para previsão por fila.")
            else:
                fig_queue = px.bar(
                    forecast_queue.sort_values("forecast_7d", ascending=True),
                    x="forecast_7d",
                    y="responsible_team",
                    orientation="h",
                    color="risk_level",
                    text="forecast_7d",
                    title="Chamados previstos por fila — próximos 7 dias",
                    color_discrete_map=risk_colors,
                )
                fig_queue.update_layout(
                    paper_bgcolor="white",
                    plot_bgcolor="white",
                    font_color="#344054",
                    margin=dict(l=20, r=20, t=50, b=20),
                    xaxis_title="Chamados previstos",
                    yaxis_title="Fila",
                    legend_title="Risco",
                )
                st.plotly_chart(fig_queue, use_container_width=True)
                st.dataframe(forecast_queue, use_container_width=True, hide_index=True)

        with fv_col:
            st.markdown("### Por vertical de atuação")
            if forecast_vertical.empty:
                st.info("Sem dados suficientes para previsão por vertical.")
            else:
                fig_vertical = px.bar(
                    forecast_vertical.sort_values("forecast_7d", ascending=True),
                    x="forecast_7d",
                    y="vertical",
                    orientation="h",
                    color="risk_level",
                    text="forecast_7d",
                    title="Chamados previstos por vertical — próximos 7 dias",
                    color_discrete_map=risk_colors,
                )
                fig_vertical.update_layout(
                    paper_bgcolor="white",
                    plot_bgcolor="white",
                    font_color="#344054",
                    margin=dict(l=20, r=20, t=50, b=20),
                    xaxis_title="Chamados previstos",
                    yaxis_title="Vertical",
                    legend_title="Risco",
                )
                st.plotly_chart(fig_vertical, use_container_width=True)
                st.dataframe(forecast_vertical, use_container_width=True, hide_index=True)

        render_text_section(
            "Como interpretar a previsão",
            "Esta previsão é uma camada operacional explicável: ela não tenta substituir um modelo estatístico avançado, mas ajuda o time de CS a antecipar filas e verticais com tendência de maior demanda nos próximos dias. Em uma versão com mais histórico, essa camada poderia evoluir para modelos de séries temporais ou machine learning.",
            tone="success",
        )
