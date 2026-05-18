# =============================================================================
# DASHBOARD STREAMLIT - SISTEMA IA DE RIEGO SINALOA
# =============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from datetime import datetime
import sys, os

# =============================================================================
# PATHS
# =============================================================================

ROOT = os.path.dirname(os.path.abspath(__file__))
MODELS_PATH = os.path.join(ROOT, "models")
for p in [ROOT, MODELS_PATH]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    
    from models.recomendador import Recomendador
    from config import PARCELAS, SUELO, CLASES_RIEGO

except ImportError as e:
    st.error(f"❌ Error de importación: {e}")
    st.stop()

# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Sistema IA de Riego – Sinaloa",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# CSS
# =============================================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700&family=Space+Mono:wght@400;700&display=swap');

html, body, [class*="css"] { font-family: 'Sora', sans-serif; }
.stApp { background: #0b1a12; color: #dff0e8; }

[data-testid="stSidebar"] { background: #071009 !important; border-right: 1px solid rgba(80,200,130,0.15); }
[data-testid="stSidebar"] label, [data-testid="stSidebar"] p,
[data-testid="stSidebar"] span, [data-testid="stSidebar"] div { color: #90c8a8 !important; }

#MainMenu, footer, header { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }

h1,h2,h3,h4 { color: #50c882 !important; font-family: 'Sora', sans-serif !important; }

.stButton > button {
    background: #1a4d2e; color: #80e8a8;
    border: 1px solid #2d7a4f; border-radius: 8px;
    font-family: 'Sora', sans-serif; font-weight: 600;
    transition: all 0.2s;
}
.stButton > button:hover { background: #2d7a4f; color: #fff; }

/* ── KPI cards ── */
.kpi-wrap { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:24px; }
.kpi {
    background: linear-gradient(145deg,#0f2318,#152d1e);
    border: 1px solid rgba(80,200,130,0.18); border-radius:16px;
    padding:20px 18px; text-align:center; min-height:120px;
    display:flex; flex-direction:column; justify-content:center; align-items:center; gap:6px;
}
.kpi-label { font-size:10px; color:#5a8a6a; letter-spacing:.09em; text-transform:uppercase; font-weight:700; }
.kpi-val   { font-family:'Space Mono',monospace; font-size:30px; font-weight:700; line-height:1; }
.kpi-sub   { font-size:10px; color:#3d6b4f; }
.kpi-val.green { color:#50c882; }
.kpi-val.amber { color:#f9a84d; }
.kpi-val.red   { color:#f25c5c; }
.kpi-val.blue  { color:#5bc8f5; }
.kpi-val.mid   { font-size:16px; line-height:1.35; }

.badge { display:inline-block; padding:3px 12px; border-radius:20px; font-size:10px; font-weight:700; margin-top:2px; }
.badge.ok   { background:rgba(80,200,130,.18); color:#50c882; }
.badge.warn { background:rgba(249,168,77,.18);  color:#f9a84d; }
.badge.crit { background:rgba(242,92,92,.18);   color:#f25c5c; }

/* ── Topbar ── */
.topbar {
    background:linear-gradient(90deg,#071009,#0f2318);
    border:1px solid rgba(80,200,130,0.15); border-radius:14px;
    padding:13px 22px; display:flex; justify-content:space-between; align-items:center;
    margin-bottom:22px;
}
.topbar-left { font-family:'Space Mono',monospace; font-size:12px; color:#50c882; letter-spacing:.07em; }
.topbar-right { font-family:'Space Mono',monospace; font-size:11px; color:#3d6b4f; }
.dot { display:inline-block; width:7px; height:7px; border-radius:50%;
       background:#50c882; margin-right:6px; animation:blink 1.4s infinite; }
@keyframes blink{0%,100%{opacity:1}50%{opacity:.2}}

/* ── Sensor grid ── */
.sgrid { display:grid; grid-template-columns:repeat(6,1fr); gap:8px; }
.snode { border-radius:12px; padding:11px 6px; text-align:center; border:1px solid transparent; transition:transform .15s; }
.snode:hover { transform:scale(1.05); }
.snode.ok   { background:rgba(80,200,130,.1);  border-color:rgba(80,200,130,.3); }
.snode.warn { background:rgba(249,168,77,.1);  border-color:rgba(249,168,77,.3); }
.snode.crit { background:rgba(242,92,92,.1);   border-color:rgba(242,92,92,.3);  }
.sn-id  { font-size:9px; font-weight:700; letter-spacing:.05em; color:#3d6b4f; margin-bottom:3px; }
.sn-val { font-family:'Space Mono',monospace; font-size:15px; font-weight:700; }
.sn-val.ok   { color:#50c882; }
.sn-val.warn { color:#f9a84d; }
.sn-val.crit { color:#f25c5c; }
.sn-sub { font-size:9px; color:#3d6b4f; margin-top:2px; }

/* ── Section header ── */
.sec-hdr {
    font-size:13px; font-weight:700; color:#50c882; letter-spacing:.05em;
    text-transform:uppercase; border-left:3px solid #50c882;
    padding-left:10px; margin:22px 0 12px;
}

/* ── Explicación ── */
.expbox {
    background:#0f2318; border:1px solid rgba(80,200,130,.18);
    border-left:4px solid #50c882; border-radius:12px;
    padding:18px 20px; font-family:'Space Mono',monospace;
    font-size:11.5px; line-height:1.9; color:#90c8a8; white-space:pre-wrap;
}

/* ── Ranking ── */
.rank-item {
    display:flex; align-items:center; gap:10px;
    padding:9px 12px; background:#0f2318; border-radius:9px;
    border:1px solid rgba(80,200,130,.12); margin-bottom:6px;
}
.rk-pos  { font-family:'Space Mono',monospace; font-size:11px; color:#3d6b4f; width:20px; }
.rk-name { flex:1; font-size:12px; font-weight:600; color:#dff0e8; }
.rk-bwrap{ width:80px; height:5px; background:rgba(255,255,255,.07); border-radius:3px; overflow:hidden; }
.rk-bar  { height:100%; border-radius:3px; }
.rk-pct  { font-family:'Space Mono',monospace; font-size:11px; width:38px; text-align:right; }

/* ── Clima cards ── */
.clima-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:8px; margin-bottom:8px; }
.clima-card {
    background:#0f2318; border:1px solid rgba(80,200,130,.14);
    border-radius:11px; padding:12px 10px; text-align:center;
}
.cc-icon  { font-size:22px; margin-bottom:4px; }
.cc-val   { font-family:'Space Mono',monospace; font-size:18px; font-weight:700; color:#50c882; }
.cc-label { font-size:10px; color:#3d6b4f; margin-top:2px; }

.ftr { text-align:center; padding:14px; font-size:10px;
       color:#2d5a3e; font-family:'Space Mono',monospace;
       border-top:1px solid rgba(80,200,130,.1); margin-top:24px; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# COLORES Y HELPERS DE PLOTLY
# =============================================================================

C_GREEN  = "#50c882"
C_AMBER  = "#f9a84d"
C_RED    = "#f25c5c"
C_BLUE   = "#5bc8f5"
C_PURPLE = "#b388ff"
C_TEAL   = "#26c6da"

GRID  = "rgba(255,255,255,0.04)"
TICK  = "#3d6b4f"
BG    = "rgba(0,0,0,0)"


def base_layout(height=260):
    """Layout base de Plotly sin ejes (se añaden al llamar)."""
    return dict(
        paper_bgcolor=BG, plot_bgcolor=BG,
        font=dict(family="Sora", color=TICK, size=11),
        margin=dict(l=8, r=8, t=36, b=8),
        height=height,
        showlegend=False,
    )


def ax(ticksuffix="", title_text="", rng=None, **kw):
    """Devuelve un dict de eje sin duplicados."""
    d = dict(gridcolor=GRID, tickcolor=TICK,
             linecolor="rgba(255,255,255,0.05)", zeroline=False)
    if ticksuffix:
        d["ticksuffix"] = ticksuffix
    if title_text:
        d["title"] = dict(text=title_text, font=dict(size=10))
    if rng:
        d["range"] = rng
    d.update(kw)
    return d


def color_h(theta):
    if theta >= SUELO["theta_umbral"]:  return C_GREEN
    if theta >= SUELO["theta_critico"]: return C_AMBER
    return C_RED


def cls_sensor(theta, valido):
    if not valido:                       return "warn"
    if theta >= SUELO["theta_umbral"]:  return "ok"
    if theta >= SUELO["theta_critico"]: return "warn"
    return "crit"


def kpi_cls(theta):
    return ("green" if theta >= SUELO["theta_umbral"]
            else "amber" if theta >= SUELO["theta_critico"]
            else "red")


def badge_dec(dec):
    if dec == CLASES_RIEGO[0]["nombre"]: return "ok",   "✓ Sin déficit"
    if dec == CLASES_RIEGO[1]["nombre"]: return "warn", "⚠ Planificar"
    return "crit", "🔴 Acción ya"


def hist_24h(theta, et0):
    kc   = 0.85
    loss = (et0 * kc) / 24 / 10
    vals, t = [], theta
    for _ in range(25):
        vals.append(round(t, 4))
        t = min(SUELO["theta_fc"], t + loss + np.random.uniform(-0.002, 0.003))
    return list(reversed(vals))

# =============================================================================
# FIGURAS
# =============================================================================

def fig_gauge(theta):
    pct = round(theta * 100, 1)
    col = color_h(theta)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct,
        number=dict(suffix="%", font=dict(size=36, family="Space Mono", color=col)),
        gauge=dict(
            axis=dict(range=[0, 50], tickwidth=1, tickcolor=TICK, tickfont=dict(size=10)),
            bar=dict(color=col, thickness=0.25),
            bgcolor=BG, borderwidth=0,
            steps=[
                dict(range=[0,                         SUELO["theta_critico"]*100], color="rgba(242,92,92,0.10)"),
                dict(range=[SUELO["theta_critico"]*100, SUELO["theta_umbral"]*100], color="rgba(249,168,77,0.10)"),
                dict(range=[SUELO["theta_umbral"]*100,  50],                        color="rgba(80,200,130,0.10)"),
            ],
            threshold=dict(line=dict(color=col, width=3), thickness=0.8, value=pct),
        ),
    ))
    lay = base_layout(220)
    lay["margin"] = dict(l=20, r=20, t=10, b=10)
    fig.update_layout(**lay)
    return fig


def fig_linea_24h(theta, et0):
    vals  = hist_24h(theta, et0)
    pcts  = [round(v*100, 1) for v in vals]
    horas = [f"{h:02d}:00" for h in range(25)]
    u = round(SUELO["theta_umbral"]*100, 1)
    c = round(SUELO["theta_critico"]*100, 1)

    fig = go.Figure()
    fig.add_hrect(y0=0,  y1=c, fillcolor="rgba(242,92,92,0.06)", line_width=0)
    fig.add_hrect(y0=c,  y1=u, fillcolor="rgba(249,168,77,0.06)", line_width=0)
    fig.add_hrect(y0=u,  y1=50, fillcolor="rgba(80,200,130,0.06)", line_width=0)
    fig.add_trace(go.Scatter(
        x=horas, y=pcts, mode="lines",
        line=dict(color=C_GREEN, width=2.5, shape="spline"),
        fill="tozeroy", fillcolor="rgba(80,200,130,0.08)",
    ))
    fig.add_hline(y=u, line=dict(color=C_AMBER, dash="dash", width=1.5),
                  annotation_text=f"Umbral {u}%",
                  annotation_font_color=C_AMBER, annotation_font_size=10,
                  annotation_position="top right")
    fig.add_hline(y=c, line=dict(color=C_RED, dash="dot", width=1.5),
                  annotation_text=f"Crítico {c}%",
                  annotation_font_color=C_RED, annotation_font_size=10,
                  annotation_position="bottom right")

    lay = base_layout(250)
    lay["title"]  = dict(text="Humedad del suelo — últimas 24 h", font=dict(size=12, color=C_GREEN))
    lay["xaxis"]  = ax(tickvals=horas[::4], tickfont=dict(size=10))
    lay["yaxis"]  = ax(ticksuffix="%", rng=[8, 52], tickfont=dict(size=10))
    fig.update_layout(**lay)
    return fig


def fig_barras_sensores(sensores):
    rows = []
    for sid, s in sorted(sensores.items()):
        if s["valido"]:
            lbl = sid.split("_")[-1] if "_" in sid else sid
            pct = round(s["theta_sensor"]*100, 1)
            cl  = cls_sensor(s["theta_sensor"], True)
            rows.append(dict(Sensor=lbl, Humedad=pct, cls=cl))
    df = pd.DataFrame(rows, columns=["Sensor", "Humedad", "cls"])

    if df.empty:
        fig = go.Figure()
        lay = base_layout(270)
        lay["title"] = dict(text="Humedad por sensor", font=dict(size=12, color=C_GREEN))
        lay["xaxis"] = ax(visible=False)
        lay["yaxis"] = ax(visible=False)
        lay["annotations"] = [dict(
            text="Sin sensores validos para graficar",
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False, font=dict(size=11, color=TICK),
        )]
        fig.update_layout(**lay)
        return fig

    cmap = {"ok": C_GREEN, "warn": C_AMBER, "crit": C_RED}
    fig  = go.Figure()
    for estado, col in cmap.items():
        sub = df[df["cls"] == estado]
        if sub.empty: continue
        fig.add_trace(go.Bar(
            x=sub["Sensor"], y=sub["Humedad"],
            marker=dict(color=col, opacity=0.85, line=dict(width=0)),
            text=[f"{v}%" for v in sub["Humedad"]],
            textposition="outside", textfont=dict(size=9, color=col),
            name=estado,
        ))

    u = round(SUELO["theta_umbral"]*100, 1)
    c = round(SUELO["theta_critico"]*100, 1)
    fig.add_hline(y=u, line=dict(color=C_AMBER, dash="dash", width=1.2),
                  annotation_text=f"Umbral {u}%",
                  annotation_font_color=C_AMBER, annotation_font_size=9,
                  annotation_position="top left")
    fig.add_hline(y=c, line=dict(color=C_RED, dash="dot", width=1.2),
                  annotation_text=f"Crítico {c}%",
                  annotation_font_color=C_RED, annotation_font_size=9,
                  annotation_position="bottom left")

    lay = base_layout(270)
    lay["title"]   = dict(text="Humedad por sensor", font=dict(size=12, color=C_GREEN))
    lay["xaxis"]   = ax(tickfont=dict(size=9))
    lay["yaxis"]   = ax(ticksuffix="%", rng=[0, 56], tickfont=dict(size=10))
    lay["barmode"] = "group"
    lay["bargap"]  = 0.25
    fig.update_layout(**lay)
    return fig


def fig_dona(sensores):
    ok = warn = crit = 0
    for s in sensores.values():
        if not s["valido"]: warn += 1; continue
        t = s["theta_sensor"]
        if   t >= SUELO["theta_umbral"]:  ok   += 1
        elif t >= SUELO["theta_critico"]: warn += 1
        else:                              crit += 1

    fig = go.Figure(go.Pie(
        labels=["Óptimo", "Atención", "Crítico"],
        values=[ok, warn, crit],
        hole=0.58,
        marker=dict(colors=[C_GREEN, C_AMBER, C_RED],
                    line=dict(color="#0b1a12", width=3)),
        textinfo="percent+label",
        textfont=dict(size=11, color="#dff0e8"),
        pull=[0.04, 0, 0],
    ))
    lay = base_layout(250)
    lay["title"] = dict(text="Estado de sensores", font=dict(size=12, color=C_GREEN))
    lay["annotations"] = [dict(
        text=f"<b>{ok+warn+crit}</b><br><span style='font-size:10px'>sensores</span>",
        x=0.5, y=0.5, font_size=16, showarrow=False,
        font=dict(color="#dff0e8"),
    )]
    fig.update_layout(**lay)
    return fig


def fig_comparativa(todas):
    rows = []
    for pid, d in todas.items():
        if d:
            rows.append(dict(
                Parcela=d["nombre"].split(" ")[0],
                Humedad=round(d["theta"]*100, 1),
                Nombre=d["nombre"],
            ))
    df   = pd.DataFrame(rows).sort_values("Humedad")
    cols = [color_h(h/100) for h in df["Humedad"]]

    fig = go.Figure(go.Bar(
        x=df["Humedad"], y=df["Parcela"],
        orientation="h",
        marker=dict(color=cols, opacity=0.85, line=dict(width=0)),
        text=[f"{v}%" for v in df["Humedad"]],
        textposition="outside",
        textfont=dict(size=10, color="#dff0e8"),
        customdata=df["Nombre"],
        hovertemplate="<b>%{customdata}</b><br>Humedad: %{x}%<extra></extra>",
    ))
    u = round(SUELO["theta_umbral"]*100, 1)
    c = round(SUELO["theta_critico"]*100, 1)
    fig.add_vline(x=u, line=dict(color=C_AMBER, dash="dash", width=1.3),
                  annotation_text=f"Umbral {u}%",
                  annotation_font_color=C_AMBER, annotation_font_size=9)
    fig.add_vline(x=c, line=dict(color=C_RED, dash="dot", width=1.3),
                  annotation_text=f"Crítico {c}%",
                  annotation_font_color=C_RED, annotation_font_size=9)

    lay = base_layout(220)
    lay["title"] = dict(text="Comparativa global — humedad actual",
                        font=dict(size=12, color=C_GREEN))
    lay["xaxis"] = ax(ticksuffix="%", rng=[0, 55], tickfont=dict(size=10))
    lay["yaxis"] = ax(tickfont=dict(size=10))
    fig.update_layout(**lay)
    return fig


def fig_proyeccion(theta, et0):
    kc   = 0.85
    loss = (et0 * kc) / 10
    dias = ["Hoy"] + [f"Día {i}" for i in range(1, 8)]
    vals, t = [round(theta*100, 1)], theta
    for _ in range(7):
        t = max(0.05, t - loss + np.random.uniform(-0.005, 0.005))
        vals.append(round(t*100, 1))

    colores = [color_h(v/100) for v in vals]

    fig = go.Figure()
    fig.add_hrect(y0=0, y1=SUELO["theta_critico"]*100,
                  fillcolor="rgba(242,92,92,0.07)", line_width=0,
                  annotation_text="Zona crítica",
                  annotation_font_color=C_RED, annotation_font_size=9,
                  annotation_position="bottom left")
    fig.add_hrect(y0=SUELO["theta_umbral"]*100, y1=50,
                  fillcolor="rgba(80,200,130,0.07)", line_width=0,
                  annotation_text="Zona óptima",
                  annotation_font_color=C_GREEN, annotation_font_size=9,
                  annotation_position="top left")
    fig.add_trace(go.Scatter(
        x=dias, y=vals, mode="lines+markers",
        line=dict(color=C_BLUE, width=2, shape="spline"),
        marker=dict(color=colores, size=10,
                    line=dict(color="#0b1a12", width=2)),
        text=[f"{v}%" for v in vals],
        textposition="top center",
        textfont=dict(size=9, color="#dff0e8"),
        hovertemplate="%{x}: <b>%{y}%</b><extra></extra>",
    ))
    fig.add_hline(y=SUELO["theta_umbral"]*100,
                  line=dict(color=C_AMBER, dash="dash", width=1.2))
    fig.add_hline(y=SUELO["theta_critico"]*100,
                  line=dict(color=C_RED, dash="dot", width=1.2))

    lay = base_layout(270)
    lay["title"] = dict(text="Proyección hídrica — próximos 7 días",
                        font=dict(size=12, color=C_GREEN))
    lay["xaxis"] = ax(tickfont=dict(size=10))
    lay["yaxis"] = ax(ticksuffix="%", rng=[0, 52], tickfont=dict(size=10))
    fig.update_layout(**lay)
    return fig


def fig_scatter_temp(sensores):
    xs, ys, ids = [], [], []
    for sid, s in sensores.items():
        if s["valido"] and s.get("temp_suelo"):
            xs.append(s["temp_suelo"])
            ys.append(round(s["theta_sensor"]*100, 1))
            ids.append(sid.split("_")[-1] if "_" in sid else sid)
    if not xs:
        return None

    fig = go.Figure(go.Scatter(
        x=xs, y=ys, mode="markers+text",
        text=ids, textposition="top center",
        textfont=dict(size=9, color=TICK),
        marker=dict(
            color=ys,
            colorscale=[[0, C_RED], [0.5, C_AMBER], [1, C_GREEN]],
            size=12, opacity=0.85,
            line=dict(color="#0b1a12", width=1.5),
            showscale=True,
            colorbar=dict(
                title=dict(text="Humedad %", font=dict(size=10, color=TICK)),
                tickfont=dict(size=9, color=TICK),
                thickness=10, len=0.6,
            ),
        ),
        hovertemplate="<b>%{text}</b><br>Temp: %{x}°C<br>Humedad: %{y}%<extra></extra>",
    ))
    lay = base_layout(260)
    lay["title"] = dict(text="Temperatura vs. Humedad del suelo",
                        font=dict(size=12, color=C_GREEN))
    lay["xaxis"] = ax(title_text="Temperatura suelo (°C)", tickfont=dict(size=10))
    lay["yaxis"] = ax(ticksuffix="%", title_text="Humedad (%)", tickfont=dict(size=10))
    fig.update_layout(**lay)
    return fig


def fig_radar(todas):
    cats = ["Humedad", "Sensores OK", "Confianza", "Sin déficit"]
    pal  = [C_GREEN, C_BLUE, C_PURPLE, C_TEAL, C_AMBER]
    fig  = go.Figure()

    for i, (pid, d) in enumerate(todas.items()):
        if not d: continue
        n_ok = sum(1 for s in d["sensores"].values()
                   if s["valido"] and s["theta_sensor"] >= SUELO["theta_umbral"])
        vals = [
            round(d["theta"]*100 / 50 * 100),
            round(d["n_validos"] / 12 * 100),
            round(d["confianza"]),
            round(n_ok / max(d["n_validos"], 1) * 100),
        ]
        col = pal[i % len(pal)]
        fig.add_trace(go.Scatterpolar(
           r=vals + [vals[0]], theta=cats + [cats[0]],
    fill="toself",
    name=d["nombre"].split(" ")[0],
    line=dict(color=col, width=2),
    fillcolor=col,  # ✅ Sin el "+ 18"
    opacity=0.5,
        ))

    lay = base_layout(300)
    lay["showlegend"] = True
    lay["legend"]     = dict(bgcolor=BG, font=dict(size=10, color="#90c8a8"))
    lay["title"]      = dict(text="Comparativa multidimensional de parcelas",
                             font=dict(size=12, color=C_GREEN))
    lay["polar"] = dict(
        bgcolor=BG,
        radialaxis=dict(visible=True, range=[0, 100],
                        tickfont=dict(size=9, color=TICK),
                        gridcolor=GRID, linecolor=GRID),
        angularaxis=dict(tickfont=dict(size=10, color="#90c8a8"), gridcolor=GRID),
    )
    # quitar xaxis/yaxis que no aplican al polar
    lay.pop("xaxis", None)
    lay.pop("yaxis", None)
    fig.update_layout(**lay)
    return fig

# =============================================================================
# COMPONENTES HTML
# =============================================================================

def render_topbar(nombre, municipio):
    t = datetime.now().strftime("%H:%M:%S")
    st.markdown(f"""
    <div class="topbar">
      <span class="topbar-left">🌾 SISTEMA IA DE RIEGO · SINALOA MX &nbsp;|&nbsp; {nombre} · {municipio}</span>
      <span class="topbar-right"><span class="dot"></span>EN VIVO · {t}</span>
    </div>""", unsafe_allow_html=True)


def render_kpis(d):
    theta = d["theta"]
    kc    = kpi_cls(theta)
    bc, bt = badge_dec(d["decision"])
    dc    = "green" if bc=="ok" else "amber" if bc=="warn" else "red"
    cc    = "green" if d["confianza"] >= 80 else "amber"
    st.markdown(f"""
    <div class="kpi-wrap">
      <div class="kpi">
        <div class="kpi-label">💧 Humedad del suelo</div>
        <div class="kpi-val {kc}">{round(theta*100,1)}%</div>
        <div class="kpi-sub">Umbral {round(SUELO['theta_umbral']*100)}% · Crítico {round(SUELO['theta_critico']*100)}%</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">🎯 Decisión IA</div>
        <div class="kpi-val {dc} mid">{d['decision']}</div>
        <span class="badge {bc}">{bt}</span>
      </div>
      <div class="kpi">
        <div class="kpi-label">💦 Lámina de riego</div>
        <div class="kpi-val blue">{d['lamina_mm']} <span style="font-size:14px">mm</span></div>
        <div class="kpi-sub">Vol: {d['volumen_m3']} m³</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">✓ Confianza del sistema</div>
        <div class="kpi-val {cc}">{round(d['confianza'])}%</div>
        <div class="kpi-sub">{d['n_validos']}/12 sensores activos</div>
      </div>
    </div>""", unsafe_allow_html=True)


def render_clima_cards(d):
    temp_s = d.get("temp_suelo_promedio")
    temp_s_txt = f"{temp_s:.1f}" if temp_s else "—"
    et0    = d.get("et0", 5.2)
    n_ok   = sum(1 for s in d["sensores"].values()
                 if s["valido"] and s["theta_sensor"] >= SUELO["theta_umbral"])
    st.markdown(f"""
    <div class="clima-grid">
      <div class="clima-card">
        <div class="cc-icon">🌡️</div>
        <div class="cc-val">{temp_s_txt}°C</div>
        <div class="cc-label">Temp. suelo promedio</div>
      </div>
      <div class="clima-card">
        <div class="cc-icon">💧</div>
        <div class="cc-val">{et0} mm</div>
        <div class="cc-label">ET₀ del día</div>
      </div>
      <div class="clima-card">
        <div class="cc-icon">📡</div>
        <div class="cc-val">{d['n_validos']}/12</div>
        <div class="cc-label">Sensores activos</div>
      </div>
      <div class="clima-card">
        <div class="cc-icon">✅</div>
        <div class="cc-val">{n_ok}</div>
        <div class="cc-label">Sensores en óptimo</div>
      </div>
    </div>""", unsafe_allow_html=True)


def render_sensores(sensores, modo_temp=False):
    nodes = []
    for sid, s in sorted(sensores.items()):
        cl  = cls_sensor(s["theta_sensor"], s["valido"])
        lbl = sid.split("_")[-1] if "_" in sid else sid
        if modo_temp and s.get("temp_suelo"):
            val = f"{s['temp_suelo']:.1f}°C"
            sub = "Caliente" if s["temp_suelo"] > 30 else "Cálido" if s["temp_suelo"] > 25 else "Normal"
        else:
            val = f"{round(s['theta_sensor']*100)}%"
            sub = {"ok":"Óptimo","warn":"Atención","crit":"Crítico"}[cl]
        nodes.append(f"""
        <div class="snode {cl}">
          <div class="sn-id">{lbl}</div>
          <div class="sn-val {cl}">{val}</div>
          <div class="sn-sub">{sub}</div>
        </div>""")
    st.markdown(f'<div class="sgrid">{"".join(nodes)}</div>', unsafe_allow_html=True)


def render_ranking(todas):
    items = sorted(
        [(d["nombre"], d["theta"]) for d in todas.values() if d],
        key=lambda x: -x[1],
    )
    html = ""
    for i, (nombre, theta) in enumerate(items, 1):
        pct = round(theta*100, 1)
        col = color_h(theta)
        bw  = round((theta / 0.45)*100)
        html += f"""
        <div class="rank-item">
          <span class="rk-pos">#{i}</span>
          <span class="rk-name">{nombre}</span>
          <div class="rk-bwrap"><div class="rk-bar" style="width:{bw}%;background:{col}"></div></div>
          <span class="rk-pct" style="color:{col}">{pct}%</span>
        </div>"""
    st.markdown(html, unsafe_allow_html=True)

# =============================================================================
# SIDEBAR
# =============================================================================

def sidebar():
    with st.sidebar:
        st.markdown("## 🌾 Panel de Control")
        st.caption("Sistema IA · Sinaloa, México")
        st.divider()

        pid = st.selectbox(
            "Parcela activa",
            list(PARCELAS.keys()),
            format_func=lambda x: f"{x} · {PARCELAS[x]['nombre']}",
        )
        st.divider()

        modo = st.radio("Vista de sensores", ["💧 Humedad", "🌡️ Temperatura"])
        st.divider()

        if st.button("🔄 Actualizar datos", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        st.divider()
        st.caption("**Umbrales del suelo**")
        st.caption(f"🟢 Óptimo:    ≥ {SUELO['theta_umbral']:.0%}")
        st.caption(f"🟡 Atención:  ≥ {SUELO['theta_critico']:.0%}")
        st.caption(f"🔴 Crítico:   < {SUELO['theta_critico']:.0%}")
        st.caption(f"💧 Cap. campo: {SUELO['theta_fc']:.0%}")
        st.divider()
        st.caption("🤖 Random Forest + Isolation Forest\n📡 12 sensores/parcela\n⏱ Caché: 5 min")

    return pid, "Temperatura" in modo

# =============================================================================
# MAIN
# =============================================================================

@st.cache_resource(show_spinner=False)
def init_recomendador():
    try:
        return Recomendador()
    except Exception as e:
        st.error(f"❌ {e}")
        return None


@st.cache_data(ttl=300, show_spinner=False)
def get_datos(_rec, pid):
    try:
        return _rec.recomendar(pid)
    except Exception as e:
        st.error(f"Error {pid}: {e}")
        return None


@st.cache_data(ttl=300, show_spinner=False)
def get_todas(_rec):
    return {pid: get_datos(_rec, pid) for pid in PARCELAS}


def main():
    rec = init_recomendador()
    if not rec:
        st.stop()

    pid, usar_temp = sidebar()

    with st.spinner("Consultando sensores y modelos IA…"):
        d     = get_datos(rec, pid)
        todas = get_todas(rec)

    if not d:
        st.error("No se pudieron cargar los datos.")
        st.stop()

    et0_ref = d.get("et0", 5.2)

    # ── Topbar ──────────────────────────────────────────────────────────────
    render_topbar(d["nombre"], d["municipio"])

    # ── KPIs ─────────────────────────────────────────────────────────────────
    render_kpis(d)

    # ── Condiciones actuales ─────────────────────────────────────────────────
    st.markdown('<div class="sec-hdr">🌤 Condiciones actuales</div>', unsafe_allow_html=True)
    render_clima_cards(d)

    # ── Gauge + Línea 24h ────────────────────────────────────────────────────
    st.markdown('<div class="sec-hdr">💧 Humedad del suelo</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 2])
    with c1:
        st.plotly_chart(fig_gauge(d["theta"]), width="stretch")
    with c2:
        st.plotly_chart(fig_linea_24h(d["theta"], et0_ref), width="stretch")

    # ── Barras + Dona ────────────────────────────────────────────────────────
    st.markdown('<div class="sec-hdr">📊 Análisis de sensores</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([2, 1])
    with c1:
        st.plotly_chart(fig_barras_sensores(d["sensores"]), width="stretch")
    with c2:
        st.plotly_chart(fig_dona(d["sensores"]), width="stretch")

    # ── Grid de nodos ────────────────────────────────────────────────────────
    st.markdown('<div class="sec-hdr">📡 Red de sensores — nodo por nodo</div>', unsafe_allow_html=True)
    render_sensores(d["sensores"], modo_temp=usar_temp)
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Proyección + Scatter ─────────────────────────────────────────────────
    st.markdown('<div class="sec-hdr">📈 Proyección y correlaciones</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(fig_proyeccion(d["theta"], et0_ref), width="stretch")
    with c2:
        fig_sc = fig_scatter_temp(d["sensores"])
        if fig_sc:
            st.plotly_chart(fig_sc, width="stretch")
        else:
            st.info("ℹ️ Sin datos de temperatura en sensores para esta parcela.")

    # ── Comparativa + Ranking ────────────────────────────────────────────────
    st.markdown('<div class="sec-hdr">🌍 Vista global de parcelas</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([2, 1])
    with c1:
        st.plotly_chart(fig_comparativa(todas), width="stretch")
    with c2:
        st.markdown("**Ranking por humedad**")
        render_ranking(todas)

    # ── Radar ────────────────────────────────────────────────────────────────
    st.markdown('<div class="sec-hdr">🕸 Comparativa multidimensional</div>', unsafe_allow_html=True)
    st.plotly_chart(fig_radar(todas), width="stretch")

    # ── Explicación IA ───────────────────────────────────────────────────────
    st.markdown('<div class="sec-hdr">💡 Análisis completo del sistema IA</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="expbox">{d["explicacion"]}</div>', unsafe_allow_html=True)

    # ── Footer ───────────────────────────────────────────────────────────────
    st.markdown(
        f'<div class="ftr">🌾 Sistema IA de Riego Predictivo · Sinaloa, México &nbsp;|&nbsp; '
        f'🤖 Random Forest + Isolation Forest &nbsp;|&nbsp; '
        f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
