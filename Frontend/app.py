import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.graph_objs as go
import streamlit as st

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(ROOT)
BACKEND_PATH = os.path.join(PROJECT_ROOT, "backend")
MODELS_PATH = os.path.join(BACKEND_PATH, "models")
for p in [BACKEND_PATH, MODELS_PATH]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from models.recomendador import Recomendador
    from config import CLASES_RIEGO, PARCELAS, SUELO
except ImportError as e:
    st.error(f"Error de importacion: {e}")
    st.stop()

st.set_page_config(
    page_title="DRIP - Precision Irrigation",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_css() -> None:
    with open(os.path.join(ROOT, "css", "variables.css"), encoding="utf-8") as f:
        vars_css = f.read()
    with open(os.path.join(ROOT, "css", "main.css"), encoding="utf-8") as f:
        main_css = f.read()
    st.markdown(f"<style>{vars_css}\n{main_css}</style>", unsafe_allow_html=True)


inject_css()

C_SUCCESS = "#7B9B35"
C_WARNING = "#E8A838"
C_DANGER = "#D45B3A"
C_INFO = "#7C9CA8"
C_DARK = "#385E5E"
BG = "rgba(0,0,0,0)"
GRID = "rgba(56,94,94,0.12)"
TICK = "#6E7A7A"


def base_layout(height=260):
    return dict(
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        font=dict(family="Sora", color=TICK, size=11),
        margin=dict(l=8, r=8, t=36, b=8),
        height=height,
        showlegend=False,
    )


def ax(ticksuffix="", title_text="", rng=None, **kw):
    d = dict(gridcolor=GRID, tickcolor=TICK, linecolor=GRID, zeroline=False)
    if ticksuffix:
        d["ticksuffix"] = ticksuffix
    if title_text:
        d["title"] = dict(text=title_text, font=dict(size=10))
    if rng:
        d["range"] = rng
    d.update(kw)
    return d


def color_h(theta):
    if theta >= SUELO["theta_umbral"]:
        return C_SUCCESS
    if theta >= SUELO["theta_critico"]:
        return C_WARNING
    return C_DANGER


def cls_sensor(theta, valido):
    if not valido:
        return "warn"
    if theta >= SUELO["theta_umbral"]:
        return "ok"
    if theta >= SUELO["theta_critico"]:
        return "warn"
    return "crit"


def kpi_cls(theta):
    return "green" if theta >= SUELO["theta_umbral"] else "amber" if theta >= SUELO["theta_critico"] else "red"


def badge_dec(dec):
    if dec == CLASES_RIEGO[0]["nombre"]:
        return "ok", "Sin deficit"
    if dec == CLASES_RIEGO[1]["nombre"]:
        return "warn", "Planificar riego"
    return "crit", "Accion inmediata"


def hist_24h(theta, et0):
    kc = 0.85
    loss = (et0 * kc) / 24 / 10
    vals, t = [], theta
    for _ in range(25):
        vals.append(round(t, 4))
        t = min(SUELO["theta_fc"], t + loss + np.random.uniform(-0.002, 0.003))
    return list(reversed(vals))


def fig_linea_24h(theta, et0):
    vals = hist_24h(theta, et0)
    pcts = [round(v * 100, 1) for v in vals]
    horas = [f"{h:02d}:00" for h in range(25)]
    u = round(SUELO["theta_umbral"] * 100, 1)
    c = round(SUELO["theta_critico"] * 100, 1)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=horas,
            y=pcts,
            mode="lines",
            line=dict(color=C_DARK, width=2.4, shape="spline"),
            fill="tozeroy",
            fillcolor="rgba(157,197,218,0.25)",
        )
    )
    fig.add_hline(y=u, line=dict(color=C_WARNING, dash="dash", width=1.2))
    fig.add_hline(y=c, line=dict(color=C_DANGER, dash="dot", width=1.2))

    lay = base_layout(250)
    lay["title"] = dict(text="Comportamiento de humedad - 24h", font=dict(size=12, color=C_DARK))
    lay["xaxis"] = ax(tickvals=horas[::4], tickfont=dict(size=10))
    lay["yaxis"] = ax(ticksuffix="%", rng=[8, 52], tickfont=dict(size=10))
    fig.update_layout(**lay)
    return fig


def fig_barras_sensores(sensores):
    rows = []
    for sid, s in sorted(sensores.items()):
        if s["valido"]:
            lbl = sid.split("_")[-1] if "_" in sid else sid
            pct = round(s["theta_sensor"] * 100, 1)
            cl = cls_sensor(s["theta_sensor"], True)
            rows.append(dict(Sensor=lbl, Humedad=pct, cls=cl))
    if not rows:
        fig = go.Figure()
        lay = base_layout(260)
        lay["title"] = dict(text="Comparativo por sensor", font=dict(size=12, color=C_DARK))
        lay["xaxis"] = ax(visible=False)
        lay["yaxis"] = ax(visible=False)
        lay["annotations"] = [
            dict(
                text="Sin sensores validos para mostrar",
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=12, color=TICK),
            )
        ]
        fig.update_layout(**lay)
        return fig

    df = pd.DataFrame(rows)

    cmap = {"ok": C_SUCCESS, "warn": C_WARNING, "crit": C_DANGER}
    fig = go.Figure()
    for estado, col in cmap.items():
        sub = df[df["cls"] == estado]
        if sub.empty:
            continue
        fig.add_trace(
            go.Bar(
                x=sub["Sensor"],
                y=sub["Humedad"],
                marker=dict(color=col, opacity=0.9),
                text=[f"{v}%" for v in sub["Humedad"]],
                textposition="outside",
                textfont=dict(size=9, color=col),
            )
        )

    lay = base_layout(260)
    lay["title"] = dict(text="Comparativo por sensor", font=dict(size=12, color=C_DARK))
    lay["xaxis"] = ax(tickfont=dict(size=9))
    lay["yaxis"] = ax(ticksuffix="%", rng=[0, 56], tickfont=dict(size=10))
    fig.update_layout(**lay)
    return fig


def fig_dona(sensores):
    ok = warn = crit = 0
    for s in sensores.values():
        if not s["valido"]:
            warn += 1
            continue
        t = s["theta_sensor"]
        if t >= SUELO["theta_umbral"]:
            ok += 1
        elif t >= SUELO["theta_critico"]:
            warn += 1
        else:
            crit += 1

    fig = go.Figure(
        go.Pie(
            labels=["Optimo", "Atencion", "Critico"],
            values=[ok, warn, crit],
            hole=0.56,
            marker=dict(colors=[C_SUCCESS, C_WARNING, C_DANGER], line=dict(color="#F6F6F3", width=2)),
            textinfo="percent+label",
        )
    )
    lay = base_layout(250)
    lay["title"] = dict(text="Estado de sensores", font=dict(size=12, color=C_DARK))
    fig.update_layout(**lay)
    return fig


def fig_proyeccion(theta, et0):
    kc = 0.85
    loss = (et0 * kc) / 10
    dias = ["Hoy"] + [f"Dia {i}" for i in range(1, 8)]
    vals, t = [round(theta * 100, 1)], theta
    for _ in range(7):
        t = max(0.05, t - loss + np.random.uniform(-0.005, 0.005))
        vals.append(round(t * 100, 1))

    fig = go.Figure(
        go.Scatter(
            x=dias,
            y=vals,
            mode="lines+markers",
            line=dict(color=C_INFO, width=2.3, shape="spline"),
            marker=dict(color=[color_h(v / 100) for v in vals], size=10),
        )
    )
    fig.add_hline(y=SUELO["theta_umbral"] * 100, line=dict(color=C_WARNING, dash="dash", width=1.2))
    fig.add_hline(y=SUELO["theta_critico"] * 100, line=dict(color=C_DANGER, dash="dot", width=1.2))

    lay = base_layout(260)
    lay["title"] = dict(text="Proyeccion hidrica - 7 dias", font=dict(size=12, color=C_DARK))
    lay["xaxis"] = ax(tickfont=dict(size=10))
    lay["yaxis"] = ax(ticksuffix="%", rng=[0, 52], tickfont=dict(size=10))
    fig.update_layout(**lay)
    return fig


def fig_comparativa(todas):
    rows = []
    for d in todas.values():
        if d:
            rows.append(dict(Parcela=d["nombre"].split(" ")[0], Humedad=round(d["theta"] * 100, 1), Nombre=d["nombre"]))
    df = pd.DataFrame(rows).sort_values("Humedad")

    fig = go.Figure(
        go.Bar(
            x=df["Humedad"],
            y=df["Parcela"],
            orientation="h",
            marker=dict(color=[color_h(h / 100) for h in df["Humedad"]]),
            text=[f"{v}%" for v in df["Humedad"]],
            textposition="outside",
            customdata=df["Nombre"],
            hovertemplate="<b>%{customdata}</b><br>Humedad: %{x}%<extra></extra>",
        )
    )
    lay = base_layout(220)
    lay["title"] = dict(text="Comparativa horizontal de parcelas", font=dict(size=12, color=C_DARK))
    lay["xaxis"] = ax(ticksuffix="%", rng=[0, 55], tickfont=dict(size=10))
    lay["yaxis"] = ax(tickfont=dict(size=10))
    fig.update_layout(**lay)
    return fig


def fig_radar(todas):
    cats = ["Humedad", "Sensores OK", "Confianza", "Sin deficit"]
    colors = [C_SUCCESS, C_INFO, C_DARK, C_WARNING]
    fig = go.Figure()

    for i, d in enumerate([v for v in todas.values() if v]):
        n_ok = sum(1 for s in d["sensores"].values() if s["valido"] and s["theta_sensor"] >= SUELO["theta_umbral"])
        vals = [
            round(d["theta"] * 100 / 50 * 100),
            round(d["n_validos"] / 12 * 100),
            round(d["confianza"]),
            round(n_ok / max(d["n_validos"], 1) * 100),
        ]
        col = colors[i % len(colors)]
        fig.add_trace(
            go.Scatterpolar(
                r=vals + [vals[0]],
                theta=cats + [cats[0]],
                fill="toself",
                name=d["nombre"].split(" ")[0],
                line=dict(color=col, width=2),
                fillcolor=col,
                opacity=0.22,
            )
        )

    lay = base_layout(320)
    lay["showlegend"] = True
    lay["title"] = dict(text="Radar multidimensional", font=dict(size=12, color=C_DARK))
    lay["polar"] = dict(
        bgcolor=BG,
        radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=9, color=TICK), gridcolor=GRID, linecolor=GRID),
        angularaxis=dict(tickfont=dict(size=10, color=TICK), gridcolor=GRID),
    )
    fig.update_layout(**lay)
    return fig


def render_topbar(nombre, municipio):
    t = datetime.now().strftime("%Y-%m-%d %H:%M")
    st.markdown(
        f"""
    <div class="topbar">
      <span class="topbar-left">DRIP | {nombre} - {municipio}</span>
      <span class="topbar-right"><span class="dot"></span>Clima y telemetria activa | {t}</span>
    </div>""",
        unsafe_allow_html=True,
    )


def render_kpis(d):
    theta = d["theta"]
    bc, bt = badge_dec(d["decision"])
    dc = "green" if bc == "ok" else "amber" if bc == "warn" else "red"
    cc = "green" if d["confianza"] >= 80 else "amber"
    temp = d.get("temp_suelo_promedio")
    temp_txt = f"{temp:.1f}" if temp is not None else "-"

    st.markdown(
        f"""
    <div class="kpi-wrap">
      <div class="kpi">
        <div class="kpi-label">Humedad</div>
        <div class="kpi-val {kpi_cls(theta)}">{round(theta * 100, 1)}%</div>
        <div class="kpi-sub">Umbral {round(SUELO['theta_umbral'] * 100)}%</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Temperatura suelo</div>
        <div class="kpi-val blue">{temp_txt} C</div>
        <div class="kpi-sub">ET0 {d.get('et0', 5.2)} mm</div>
      </div>
      <div class="kpi">
        <div class="kpi-label">Decision IA</div>
        <div class="kpi-val {dc} mid">{d['decision']}</div>
        <span class="badge {bc}">{bt}</span>
      </div>
      <div class="kpi">
        <div class="kpi-label">Confianza IA</div>
        <div class="kpi-val {cc}">{round(d['confianza'])}%</div>
        <div class="kpi-sub">{d['n_validos']}/12 sensores validos</div>
      </div>
    </div>""",
        unsafe_allow_html=True,
    )


def render_clima_cards(d):
    temp = d.get("temp_suelo_promedio")
    temp_txt = f"{temp:.1f}" if temp is not None else "-"
    n_ok = sum(1 for s in d["sensores"].values() if s["valido"] and s["theta_sensor"] >= SUELO["theta_umbral"])

    st.markdown(
        f"""
    <div class="clima-grid">
      <div class="clima-card"><div class="cc-val">{temp_txt} C</div><div class="cc-label">Temp. suelo prom.</div></div>
      <div class="clima-card"><div class="cc-val">{d.get('et0', 5.2)} mm</div><div class="cc-label">ET0 diaria</div></div>
      <div class="clima-card"><div class="cc-val">{d['n_validos']}/12</div><div class="cc-label">Sensores activos</div></div>
      <div class="clima-card"><div class="cc-val">{n_ok}</div><div class="cc-label">Sensores optimos</div></div>
    </div>""",
        unsafe_allow_html=True,
    )


def render_sensores(sensores, modo_temp=False):
    nodes = []
    for sid, s in sorted(sensores.items()):
        cl = cls_sensor(s["theta_sensor"], s["valido"])
        lbl = sid.split("_")[-1] if "_" in sid else sid
        if modo_temp and s.get("temp_suelo"):
            val = f"{s['temp_suelo']:.1f} C"
            sub = "Caliente" if s["temp_suelo"] > 30 else "Normal"
        else:
            val = f"{round(s['theta_sensor'] * 100)}%"
            sub = {"ok": "Optimo", "warn": "Atencion", "crit": "Critico"}[cl]
        nodes.append(
            f"""
            <div class="snode {cl}">
              <div class="sn-id">{lbl}</div>
              <div class="sn-val">{val}</div>
              <div class="sn-sub">{sub}</div>
            </div>"""
        )
    st.markdown(f'<div class="sgrid">{"".join(nodes)}</div>', unsafe_allow_html=True)


def render_ranking(todas):
    items = sorted([(d["nombre"], d["theta"]) for d in todas.values() if d], key=lambda x: -x[1])
    html = ""
    for i, (nombre, theta) in enumerate(items, 1):
        pct = round(theta * 100, 1)
        col = color_h(theta)
        bw = round((theta / 0.45) * 100)
        html += f"""
        <div class="rank-item">
          <span class="rk-pos">#{i}</span>
          <span class="rk-name">{nombre}</span>
          <div class="rk-bwrap"><div class="rk-bar" style="width:{bw}%;background:{col}"></div></div>
          <span class="rk-pct" style="color:{col}">{pct}%</span>
        </div>"""
    st.markdown(html, unsafe_allow_html=True)


def infer_alertas(d):
    alertas = []
    now = datetime.now().strftime("%H:%M")
    for sid, s in d["sensores"].items():
        if not s["valido"]:
            alertas.append({"sev": "Advertencia", "msg": f"Sensor {sid} sin validacion", "hora": now})
            continue
        if s["theta_sensor"] < SUELO["theta_critico"]:
            alertas.append({"sev": "Critica", "msg": f"Humedad critica en {sid}", "hora": now})
        elif s["theta_sensor"] < SUELO["theta_umbral"]:
            alertas.append({"sev": "Advertencia", "msg": f"Humedad en atencion en {sid}", "hora": now})
    if d["confianza"] < 70:
        alertas.append({"sev": "Informacion", "msg": "Confianza IA por debajo de 70%", "hora": now})
    if not alertas:
        alertas.append({"sev": "Informacion", "msg": "Operacion estable, sin eventos urgentes", "hora": now})
    return alertas


def sidebar():
    with st.sidebar:
        st.markdown("## DRIP")
        st.caption("Monitoreo inteligente de riego")
        st.divider()
        pid = st.selectbox("Parcela activa", list(PARCELAS.keys()), format_func=lambda x: f"{x} - {PARCELAS[x]['nombre']}")
        modo = st.radio("Vista de sensores", ["Humedad", "Temperatura"], horizontal=True)
        if st.button("Actualizar datos", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    return pid, modo == "Temperatura"


@st.cache_resource(show_spinner=False)
def init_recomendador():
    return Recomendador()


@st.cache_data(ttl=300, show_spinner=False)
def get_datos(_rec, pid):
    return _rec.recomendar(pid)


@st.cache_data(ttl=300, show_spinner=False)
def get_todas(_rec):
    return {pid: get_datos(_rec, pid) for pid in PARCELAS}


def render_login():
    st.markdown("""
    <div class="login-card">
      <h2>Acceso DRIP</h2>
      <p>Centro operativo agrotech para decisiones rapidas de riego.</p>
    </div>
    """, unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        user = st.text_input("Usuario", placeholder="tecnico.campo")
        if st.button("Ingresar", use_container_width=True, type="primary"):
            if user.strip():
                st.session_state["logged_in"] = True
                st.session_state["user"] = user.strip()
                with st.spinner("Inicializando DRIP..."):
                    pass
                st.rerun()
            else:
                st.warning("Ingresa un usuario valido.")


def render_mobile_nav(active):
    names = ["Inicio", "Sensores", "IA", "Parcelas", "Alertas"]
    pills = []
    for n in names:
        cl = "mobile-pill active" if n == active else "mobile-pill"
        pills.append(f"<div class='{cl}'>{n}</div>")
    st.markdown(f"<div class='mobile-nav'>{''.join(pills)}</div>", unsafe_allow_html=True)


def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        render_login()
        return

    rec = init_recomendador()
    pid, usar_temp = sidebar()

    with st.spinner("Consultando sensores, clima e IA..."):
        d = get_datos(rec, pid)
        todas = get_todas(rec)

    if not d:
        st.error("No se pudieron cargar datos para la parcela seleccionada.")
        return

    alertas = infer_alertas(d)
    et0_ref = d.get("et0", 5.2)

    render_topbar(d["nombre"], d["municipio"])

    tabs = st.tabs(["Inicio", "Sensores", "IA / Recomendacion", "Parcelas", "Alertas"])

    with tabs[0]:
        render_kpis(d)
        st.markdown('<div class="sec-hdr">Contexto climatico</div>', unsafe_allow_html=True)
        render_clima_cards(d)
        st.markdown('<div class="sec-hdr">Tendencia 24h</div>', unsafe_allow_html=True)
        st.plotly_chart(fig_linea_24h(d["theta"], et0_ref), width="stretch")
        if st.button("Ver recomendacion", use_container_width=True):
            st.info(f"Decision actual: {d['decision']} | Lamina: {d['lamina_mm']} mm | Volumen: {d['volumen_m3']} m3")
        render_mobile_nav("Inicio")

    with tabs[1]:
        st.markdown('<div class="sec-hdr">Estado de nodos IoT</div>', unsafe_allow_html=True)
        render_sensores(d["sensores"], modo_temp=usar_temp)
        c1, c2 = st.columns([2, 1])
        with c1:
            st.plotly_chart(fig_barras_sensores(d["sensores"]), width="stretch")
        with c2:
            st.plotly_chart(fig_dona(d["sensores"]), width="stretch")
        render_mobile_nav("Sensores")

    with tabs[2]:
        st.markdown('<div class="sec-hdr">Decision y recomendacion IA</div>', unsafe_allow_html=True)
        render_kpis(d)
        c1, c2 = st.columns([1, 1])
        with c1:
            st.metric("Lamina sugerida (mm)", d["lamina_mm"])
            st.metric("Volumen estimado (m3)", d["volumen_m3"])
        with c2:
            st.metric("Estado IA", d["decision"])
            st.metric("Confianza", f"{round(d['confianza'])}%")
        st.markdown('<div class="sec-hdr">Explicacion IA</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="expbox">{d["explicacion"]}</div>', unsafe_allow_html=True)
        st.plotly_chart(fig_proyeccion(d["theta"], et0_ref), width="stretch")
        render_mobile_nav("IA")

    with tabs[3]:
        st.markdown('<div class="sec-hdr">Comparacion entre parcelas</div>', unsafe_allow_html=True)
        c1, c2 = st.columns([2, 1])
        with c1:
            st.plotly_chart(fig_comparativa(todas), width="stretch")
        with c2:
            st.markdown("**Ranking por humedad**")
            render_ranking(todas)
        st.plotly_chart(fig_radar(todas), width="stretch")
        render_mobile_nav("Parcelas")

    with tabs[4]:
        st.markdown('<div class="sec-hdr">Centro de alertas</div>', unsafe_allow_html=True)
        filtro = st.radio("Filtro", ["Todas", "Criticas", "Advertencias", "Informacion"], horizontal=True)
        sev_map = {"Criticas": "Critica", "Advertencias": "Advertencia", "Informacion": "Informacion"}
        items = alertas if filtro == "Todas" else [a for a in alertas if a["sev"] == sev_map[filtro]]
        for a in items:
            if a["sev"] == "Critica":
                st.error(f"[{a['hora']}] {a['msg']}")
            elif a["sev"] == "Advertencia":
                st.warning(f"[{a['hora']}] {a['msg']}")
            else:
                st.info(f"[{a['hora']}] {a['msg']}")
        render_mobile_nav("Alertas")


if __name__ == "__main__":
    main()
