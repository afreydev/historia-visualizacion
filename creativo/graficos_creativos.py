"""
WirallesTEC – Gráficos creativos: "Rescatando a Bucaramanga"
Estética: diagnóstico forense de datos · fondo blanco · colores claros
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "graficos")
os.makedirs(OUT, exist_ok=True)

# ── PALETA ───────────────────────────────────────────────────────────────────
BG       = "#F8F9FA"   # gris muy claro — fondo principal
BG_CARD  = "#FFFFFF"   # blanco puro — fondo de gráfico
VERDE    = "#16A085"   # verde esmeralda — Pereira, actividad positiva
ROJO     = "#C0392B"   # rojo oscuro — Bucaramanga, peligro
AMBAR    = "#E67E22"   # naranja terracota — promedio, avisos
GRIS     = "#95A5A6"   # gris medio — otras sucursales, referencia
TEXTO    = "#1A1A2E"   # texto principal
AZUL     = "#2980B9"   # Bogotá

CIUDAD_COLORES = {
    "Bogotá D.C.":  AZUL,
    "Medellín":     "#8E44AD",
    "Cali":         "#27AE60",
    "Barranquilla": "#D35400",
    "Pasto":        "#626567",
    "Cartagena":    "#1A5276",
    "Pereira":      VERDE,
    "Bucaramanga":  ROJO,
}

def base_layout(fig, titulo=""):
    fig.update_layout(
        paper_bgcolor=BG, plot_bgcolor=BG_CARD,
        font=dict(family="'JetBrains Mono', 'Courier New', monospace", color=TEXTO, size=13),
        title=dict(text=titulo, font=dict(size=19, color=TEXTO), x=0.05, y=0.97),
        margin=dict(l=60, r=50, t=70, b=60),
    )
    fig.update_xaxes(gridcolor="#E8ECEF", zerolinecolor="#E8ECEF", tickfont=dict(color=GRIS))
    fig.update_yaxes(gridcolor="#E8ECEF", zerolinecolor="#E8ECEF", tickfont=dict(color=GRIS))
    return fig


def save_slide(fig, path):
    """Guarda un slide como HTML centrado con max-width."""
    chart_html = fig.to_html(full_html=False, include_plotlyjs=True)
    full = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    html, body {{ margin: 0; padding: 0; background: {BG}; }}
    .wrapper {{ max-width: 1100px; margin: 0 auto; padding: 20px 24px; }}
  </style>
</head>
<body>
  <div class="wrapper">
    {chart_html}
  </div>
</body>
</html>"""
    with open(path, "w") as f:
        f.write(full)


# ── CARGA DE DATOS ───────────────────────────────────────────────────────────
def cargar():
    suc  = pd.read_excel(f"{BASE}/base-de-datos.xlsx", sheet_name="Sucursales (Server)")
    vend = pd.read_excel(f"{BASE}/base-de-datos.xlsx", sheet_name="Vendedores")
    vend["activo"] = vend["FechaSalida"].astype(str).str.startswith("9999")

    t22 = pd.read_excel(f"{BASE}/tickets_2022.xlsx"); t22["year"] = 2022
    t23 = pd.read_excel(f"{BASE}/tickets_2023.xlsx"); t23["year"] = 2023
    t24 = pd.read_excel(f"{BASE}/tickets_2024.xlsx"); t24["year"] = 2024
    tk  = pd.concat([t22, t23, t24], ignore_index=True)
    tk  = tk[tk["Precio Total (USD)"] < 50_000].copy()
    tk["Sucursal ID"]  = tk["Sucursal ID"].astype("Int64")
    tk["Fecha Venta"]  = pd.to_datetime(tk["Fecha Venta"])
    tk["mes"]          = tk["Fecha Venta"].dt.to_period("M").dt.to_timestamp()
    return suc, vend, tk


suc, vend, tk = cargar()


# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 1 – ECG: la línea que se aplana
# ═══════════════════════════════════════════════════════════════════════════════
def slide1_ecg():
    todos = pd.DataFrame({"mes": pd.date_range("2022-01", "2024-12", freq="MS")})
    buca  = tk[tk["Sucursal ID"] == 7].groupby("mes")["Precio Total (USD)"].sum().reset_index()
    data  = todos.merge(buca, on="mes", how="left").fillna(0)
    data["Precio Total (USD)"] /= 1000

    fig = go.Figure()

    activo   = data[data["mes"] < "2024-01-01"]
    flatline = data[data["mes"] >= "2024-01-01"]

    fig.add_trace(go.Scatter(
        x=activo["mes"], y=activo["Precio Total (USD)"],
        mode="lines", fill="tozeroy",
        line=dict(color=VERDE, width=2.5),
        fillcolor="rgba(22,160,133,0.12)",
        name="Actividad",
        hovertemplate="%{x|%b %Y}: $%{y:.1f}k USD<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=flatline["mes"], y=flatline["Precio Total (USD)"],
        mode="lines", fill="tozeroy",
        line=dict(color=ROJO, width=3),
        fillcolor="rgba(192,57,43,0.08)",
        name="Flatline 2024",
        hovertemplate="%{x|%b %Y}: $%{y:.1f}k USD<extra></extra>",
    ))

    fig.add_vline(
        x=pd.Timestamp("2024-01-01").timestamp() * 1000,
        line=dict(dash="dash", color=ROJO, width=1.5),
    )

    fig.add_annotation(
        x="2024-06-01", y=0.5,
        text="FLATLINE<br>Enero 2024 →",
        font=dict(color=ROJO, size=15, family="'Courier New', monospace"),
        showarrow=False, xanchor="left",
    )
    fig.add_annotation(
        x="2023-02-01", y=4.8,
        text="$4,621 USD<br>pico máximo",
        font=dict(color=AMBAR, size=11),
        showarrow=True, arrowcolor=AMBAR, arrowhead=2, ax=0, ay=-35,
    )

    fig.add_annotation(
        x=0.97, y=0.95, xref="paper", yref="paper",
        text=f"<b>Ventas 2024</b><br><span style='font-size:24px; color:{ROJO}'>$0 USD</span>",
        font=dict(color=TEXTO, size=13),
        showarrow=False, align="right",
        bgcolor="rgba(192,57,43,0.08)", bordercolor=ROJO, borderwidth=1, borderpad=8,
    )

    fig.update_layout(
        xaxis=dict(title="", tickformat="%b %Y", showgrid=False),
        yaxis=dict(title="Ventas mensuales (miles USD)", showgrid=True),
        showlegend=False, height=420,
    )
    base_layout(fig, "Bucaramanga · Actividad comercial 2022–2024")
    save_slide(fig, f"{OUT}/slide1_ecg.html")
    print("✓ slide1_ecg.html")


# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 2 – Bump chart: el ranking que cuenta la historia
# ═══════════════════════════════════════════════════════════════════════════════
def slide2_bump():
    rankings = {
        "Bogotá D.C.":  [1, 1, 1],
        "Medellín":     [3, 2, 3],
        "Cali":         [2, 3, 5],
        "Barranquilla": [4, 4, 6],
        "Pasto":        [6, 6, 2],
        "Cartagena":    [5, 8, 7],
        "Pereira":      [8, 5, 4],
        "Bucaramanga":  [7, 7, None],
    }
    anios = [2022, 2023, 2024]

    fig = go.Figure()

    for ciudad, ranks in rankings.items():
        color = CIUDAD_COLORES.get(ciudad, GRIS)
        width = 3.5 if ciudad in ("Bucaramanga", "Pereira") else 1.5

        x_valid = [a for a, r in zip(anios, ranks) if r is not None]
        y_valid = [r for r in ranks if r is not None]

        fig.add_trace(go.Scatter(
            x=x_valid, y=y_valid,
            mode="lines+markers+text",
            name=ciudad,
            line=dict(color=color, width=width),
            marker=dict(size=12 if ciudad in ("Bucaramanga","Pereira") else 8,
                        color=color,
                        line=dict(width=2, color="#FFFFFF")),
            text=["" if i < len(x_valid)-1 else ciudad for i in range(len(x_valid))],
            textposition="middle right",
            textfont=dict(color=color, size=12 if ciudad in ("Bucaramanga","Pereira") else 10),
            hovertemplate=f"<b>{ciudad}</b><br>%{{x}}: Puesto %{{y}}<extra></extra>",
        ))

        if ciudad == "Bucaramanga":
            fig.add_annotation(
                x=2024, y=8.3,
                text="<b>⊘</b>",
                font=dict(color=ROJO, size=22),
                showarrow=False,
            )
            fig.add_annotation(
                x=2024, y=8.8,
                text="Bucaramanga<br>sin ventas",
                font=dict(color=ROJO, size=11),
                showarrow=False,
            )

    for ciudad, ranks in rankings.items():
        color = CIUDAD_COLORES.get(ciudad, GRIS)
        if ranks[0] is not None:
            fig.add_annotation(
                x=2021.85, y=ranks[0],
                text=ciudad.replace(" D.C.",""),
                font=dict(color=color, size=10),
                showarrow=False, xanchor="right",
            )

    fig.update_layout(
        xaxis=dict(tickvals=[2022, 2023, 2024], ticktext=["2022","2023","2024"],
                   range=[2021.7, 2024.8], showgrid=False, title=""),
        yaxis=dict(autorange="reversed", tickvals=list(range(1, 9)),
                   ticktext=[f"#{i}" for i in range(1, 9)],
                   title="Posición en ranking de ventas", showgrid=True),
        showlegend=False, height=480,
    )
    base_layout(fig, "Ranking de Sucursales por Ventas · 2022 → 2024")
    save_slide(fig, f"{OUT}/slide2_bump.html")
    print("✓ slide2_bump.html")


# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 3 – Timeline anotado: la escena del crimen
# ═══════════════════════════════════════════════════════════════════════════════
def slide3_timeline():
    todos = pd.DataFrame({"mes": pd.date_range("2022-01", "2024-12", freq="MS")})
    buca  = tk[tk["Sucursal ID"] == 7].groupby("mes")["Precio Total (USD)"].sum().reset_index()
    data  = todos.merge(buca, on="mes", how="left").fillna(0)
    data["ventas_k"] = data["Precio Total (USD)"] / 1000

    salidas = [
        ("2022-10-01", "Lourdes",  -0.4),
        ("2023-04-01", "Iván",     -0.4),
        ("2023-06-01", "Gustavo",  -0.4),
        ("2024-03-01", "Laura\n+ Camila", -0.4),
    ]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=data["mes"], y=data["ventas_k"],
        mode="lines", fill="tozeroy",
        line=dict(color=VERDE, width=2),
        fillcolor="rgba(22,160,133,0.15)",
        name="Ventas Bucaramanga",
        hovertemplate="%{x|%b %Y}: $%{y:.2f}k USD<extra></extra>",
    ))

    for i, (fecha, nombre, _) in enumerate(salidas):
        ts = pd.Timestamp(fecha).timestamp() * 1000
        es_doble = "Camila" in nombre
        color_ev = ROJO if es_doble else AMBAR

        fig.add_vline(x=ts, line=dict(color=color_ev, width=1.5, dash="dot"))

        y_icono = 5.0 - i * 0.6
        fig.add_annotation(
            x=fecha, y=y_icono,
            text=f"👤✕  <b>{nombre}</b>",
            font=dict(color=color_ev, size=11, family="'Courier New', monospace"),
            showarrow=False, xanchor="left", bgcolor="rgba(255,255,255,0.92)",
            bordercolor=color_ev, borderwidth=1, borderpad=4,
        )

    fig.add_vrect(
        x0="2024-01-01", x1="2024-12-31",
        fillcolor="rgba(192,57,43,0.06)",
        line=dict(color=ROJO, width=0),
        annotation_text="2024: CERO VENTAS",
        annotation_position="top left",
        annotation_font=dict(color=ROJO, size=12),
    )

    fig.add_annotation(
        x="2024-07-01", y=2.2,
        text="👤 Carlos  👤 Teresa<br><i>2 vendedores · $0 generados</i>",
        font=dict(color=ROJO, size=11),
        showarrow=False, bgcolor="rgba(192,57,43,0.08)",
        bordercolor=ROJO, borderwidth=1, borderpad=6,
    )

    fig.update_layout(
        xaxis=dict(title="", tickformat="%b %Y", showgrid=False),
        yaxis=dict(title="Ventas mensuales (miles USD)", showgrid=True),
        showlegend=False, height=450,
    )
    base_layout(fig, "Bucaramanga · Cada salida dejó una huella")
    save_slide(fig, f"{OUT}/slide3_timeline.html")
    print("✓ slide3_timeline.html")


# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 4A – Waffle chart: el peso real de Bucaramanga
# ═══════════════════════════════════════════════════════════════════════════════
def slide4a_waffle():
    pcts = {
        "Bogotá D.C.":  36,
        "Cali":         16,
        "Medellín":     15,
        "Pasto":         9,
        "Barranquilla":  8,
        "Pereira":       7,
        "Cartagena":     6,
        "Bucaramanga":   3,
    }
    cells, legend = [], []
    for ciudad, n in pcts.items():
        cells.extend([ciudad] * n)
        legend.append(ciudad)
    cells = cells[:100]

    grid = np.array(cells).reshape(10, 10)
    color_ids = {c: i for i, c in enumerate(legend)}
    z = np.vectorize(lambda c: color_ids[c])(grid)

    colorscale = []
    n = len(legend)
    for i, ciudad in enumerate(legend):
        colorscale.append([i / n,       CIUDAD_COLORES[ciudad]])
        colorscale.append([(i+1) / n,   CIUDAD_COLORES[ciudad]])

    text_grid = [["" for _ in range(10)] for _ in range(10)]
    for r in range(9, -1, -1):
        for c in range(10):
            if cells[r * 10 + c] == "Bucaramanga":
                text_grid[r][c] = "BUC"

    fig = go.Figure(go.Heatmap(
        z=z[::-1],
        colorscale=colorscale,
        showscale=False,
        text=text_grid[::-1],
        texttemplate="%{text}",
        textfont=dict(color="#FFFFFF", size=9, family="'Courier New', monospace"),
        xgap=3, ygap=3,
        hovertemplate="<b>%{customdata}</b><extra></extra>",
        customdata=grid[::-1],
    ))

    for i, (ciudad, n) in enumerate(pcts.items()):
        fig.add_annotation(
            x=10.5, y=9 - i,
            text=f"<span style='color:{CIUDAD_COLORES[ciudad]}'>■</span> {ciudad}: {n}%",
            font=dict(size=11, color=TEXTO),
            showarrow=False, xanchor="left",
        )

    fig.add_annotation(
        x=4.5, y=-1.2,
        text=f"<b style='color:{ROJO}'>3 de cada 100 dólares</b> son de Bucaramanga",
        font=dict(size=13, color=TEXTO),
        showarrow=False,
    )

    fig.update_layout(
        xaxis=dict(visible=False, range=[-0.5, 16]),
        yaxis=dict(visible=False, range=[-1.8, 10]),
        height=480, width=820,
    )
    base_layout(fig, "¿Cuánto pesa Bucaramanga en la empresa? · Total 2022–2024")
    save_slide(fig, f"{OUT}/slide4a_waffle.html")
    print("✓ slide4a_waffle.html")


# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 4B – Quadrant chart: el veredicto sobre Rafael y Ana
# ═══════════════════════════════════════════════════════════════════════════════
def slide4b_quadrant():
    vend_suc = vend.groupby("SucursalID").agg(
        activos=("activo","sum")
    ).reset_index()
    variedad = (tk.groupby("Sucursal ID")["Producto ID"].nunique()
                .reset_index().rename(columns={"Sucursal ID":"SucursalID","Producto ID":"n_prod"}))
    vsuc = (tk.groupby("Sucursal ID")["Precio Total (USD)"].sum()
            .reset_index().rename(columns={"Sucursal ID":"SucursalID","Precio Total (USD)":"ventas"}))
    df = vend_suc.merge(variedad, on="SucursalID").merge(vsuc, on="SucursalID")
    df = df.merge(suc[["SUCURSAL_ID","CIUDAD"]], left_on="SucursalID", right_on="SUCURSAL_ID")

    avg_x = df["activos"].mean()
    avg_y = df["n_prod"].mean()

    fig = go.Figure()

    fig.add_hline(y=avg_y, line=dict(color=GRIS, width=1, dash="dot"))
    fig.add_vline(x=avg_x, line=dict(color=GRIS, width=1, dash="dot"))

    for txt, x, y, xa, ya in [
        ("Portafolio fuerte,<br>equipo pequeño",  1.5, 195, "left",  "top"),
        ("El ideal:<br>Personas + Variedad",      11,  195, "right", "top"),
        ("<b>⚠ Sin personas<br>ni variedad</b>",  1.5,  45, "left",  "bottom"),
        ("Equipo fuerte,<br>portafolio por crecer", 11, 45, "right", "bottom"),
    ]:
        fig.add_annotation(
            x=x, y=y, text=txt,
            font=dict(color=GRIS, size=10, family="'Courier New', monospace"),
            showarrow=False, xanchor=xa, yanchor=ya,
            bgcolor="rgba(248,249,250,0.85)",
        )

    for _, row in df.iterrows():
        ciudad = row["CIUDAD"]
        color  = CIUDAD_COLORES.get(ciudad, GRIS)
        size   = max(18, min(55, row["ventas"] / 10000))
        bold   = ciudad in ("Bucaramanga", "Pereira", "Bogotá D.C.")

        fig.add_trace(go.Scatter(
            x=[row["activos"]], y=[row["n_prod"]],
            mode="markers+text",
            name=ciudad,
            text=[ciudad.replace(" D.C.","")],
            textposition="top center" if ciudad != "Bucaramanga" else "bottom center",
            textfont=dict(color=color, size=12 if bold else 10),
            marker=dict(size=size, color=color, opacity=0.85,
                        line=dict(width=2 if bold else 1, color="#FFFFFF")),
            showlegend=False,
            hovertemplate=(
                f"<b>{ciudad}</b><br>"
                f"Vendedores activos: {int(row['activos'])}<br>"
                f"Productos distintos: {int(row['n_prod'])}<br>"
                f"Ventas: ${row['ventas']:,.0f} USD<extra></extra>"
            ),
        ))

    fig.update_layout(
        xaxis=dict(title="Vendedores activos por sucursal  →  (visión de Ana)",
                   range=[0, 14.5], showgrid=False),
        yaxis=dict(title="Productos distintos vendidos  →  (visión de Rafael)",
                   range=[40, 230], showgrid=False),
        height=500,
    )
    base_layout(fig, "¿Qué impulsa las ventas? · Vendedores vs Variedad de Productos")
    save_slide(fig, f"{OUT}/slide4b_quadrant.html")
    print("✓ slide4b_quadrant.html")


# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 5 – Radar chart: radiografía de cinco dimensiones
# ═══════════════════════════════════════════════════════════════════════════════
def slide5_radar():
    vend_suc = vend.groupby("SucursalID").agg(
        activos=("activo","sum"),
        rotacion=("activo", lambda x: (~x).sum())
    ).reset_index()
    variedad = (tk.groupby("Sucursal ID")["Producto ID"].nunique()
                .reset_index().rename(columns={"Sucursal ID":"SucursalID","Producto ID":"n_prod"}))
    vsuc = (tk.groupby("Sucursal ID")["Precio Total (USD)"].sum()
            .reset_index().rename(columns={"Sucursal ID":"SucursalID","Precio Total (USD)":"ventas"}))
    ntick = (tk.groupby("Sucursal ID")["Ticket ID"].nunique()
             .reset_index().rename(columns={"Sucursal ID":"SucursalID","Ticket ID":"n_tickets"}))

    df = vend_suc.merge(variedad,"left","SucursalID").merge(vsuc,"left","SucursalID").merge(ntick,"left","SucursalID")
    df = df.merge(suc[["SUCURSAL_ID","CIUDAD"]], left_on="SucursalID", right_on="SUCURSAL_ID")

    df["retencion"] = df["activos"] / (df["activos"] + df["rotacion"])

    dims = ["activos","n_prod","ventas","n_tickets","retencion"]
    for d in dims:
        df[f"{d}_n"] = df[d] / df[d].max()

    cats = ["Vendedores<br>activos", "Variedad de<br>productos",
            "Ventas<br>totales", "Nº de<br>tickets", "Retención<br>de personal"]

    fig = go.Figure()

    capas = [
        ("Bogotá D.C.",  AZUL,   0.7,  True,  "toself"),
        ("Promedio",     AMBAR,  0.5,  True,  "toself"),
        ("Pereira",      VERDE,  0.7,  True,  "toself"),
        ("Bucaramanga",  ROJO,   0.8,  True,  "toself"),
    ]

    prom_vals = [df[f"{d}_n"].mean() for d in dims]
    prom_vals += [prom_vals[0]]

    for ciudad, color, opacity, fill, fillmode in capas:
        if ciudad == "Promedio":
            vals = prom_vals
        else:
            row = df[df["CIUDAD"] == ciudad].iloc[0]
            vals = [row[f"{d}_n"] for d in dims]
            vals += [vals[0]]

        ancho = 3 if ciudad in ("Bucaramanga","Pereira") else 1.5

        fig.add_trace(go.Scatterpolar(
            r=vals,
            theta=cats + [cats[0]],
            mode="lines+markers",
            name=ciudad,
            line=dict(color=color, width=ancho),
            marker=dict(size=6 if ancho > 2 else 4, color=color),
            fill=fillmode,
            fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:],16)},{opacity*0.35})",
            hovertemplate=f"<b>{ciudad}</b><br>%{{theta}}: %{{r:.0%}}<extra></extra>",
        ))

    fig.update_layout(
        polar=dict(
            bgcolor=BG_CARD,
            radialaxis=dict(visible=True, range=[0,1], tickvals=[0.25,0.5,0.75,1.0],
                            ticktext=["25%","50%","75%","100%"],
                            tickfont=dict(color=GRIS, size=9), gridcolor="#E8ECEF",
                            linecolor=GRIS),
            angularaxis=dict(tickfont=dict(color=TEXTO, size=11), gridcolor="#E8ECEF",
                             linecolor=GRIS),
        ),
        legend=dict(x=1.05, y=0.95, font=dict(color=TEXTO, size=11),
                    bgcolor="rgba(255,255,255,0)"),
        height=520,
    )
    base_layout(fig, "Diagnóstico Multidimensional · Bucaramanga vs la Empresa")
    fig.update_layout(paper_bgcolor=BG, plot_bgcolor=BG)
    save_slide(fig, f"{OUT}/slide5_radar.html")
    print("✓ slide5_radar.html")


# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 6 – Dumbbell chart: Pereira vs Bucaramanga
# ═══════════════════════════════════════════════════════════════════════════════
def slide6_dumbbell():
    vsay = (tk.groupby(["Sucursal ID","year"])["Precio Total (USD)"]
            .sum().reset_index()
            .merge(suc[["SUCURSAL_ID","CIUDAD"]], left_on="Sucursal ID", right_on="SUCURSAL_ID"))
    buca = vsay[vsay["CIUDAD"]=="Bucaramanga"].set_index("year")["Precio Total (USD)"]
    per  = vsay[vsay["CIUDAD"]=="Pereira"].set_index("year")["Precio Total (USD)"]

    anios = [2022, 2023, 2024]
    y_pos = [3, 2, 1]

    fig = go.Figure()

    for anio, y in zip(anios, y_pos):
        vb = buca.get(anio, 0) / 1000
        vp = per.get(anio, 0) / 1000

        fig.add_trace(go.Scatter(
            x=[vb, vp], y=[y, y],
            mode="lines",
            line=dict(color=GRIS, width=2.5),
            showlegend=False,
            hoverinfo="skip",
        ))

        fig.add_trace(go.Scatter(
            x=[vb], y=[y],
            mode="markers+text",
            marker=dict(size=18, color=ROJO, line=dict(width=2, color="#FFFFFF")),
            text=[f"${vb:.1f}k" if vb > 0 else "$0"],
            textposition="bottom center",
            textfont=dict(color=ROJO, size=12),
            name="Bucaramanga" if anio==2022 else None,
            showlegend=(anio==2022),
            hovertemplate=f"<b>Bucaramanga {anio}</b>: ${vb:.1f}k USD<extra></extra>",
        ))

        fig.add_trace(go.Scatter(
            x=[vp], y=[y],
            mode="markers+text",
            marker=dict(size=18, color=VERDE, line=dict(width=2, color="#FFFFFF")),
            text=[f"${vp:.1f}k"],
            textposition="bottom center",
            textfont=dict(color=VERDE, size=12),
            name="Pereira" if anio==2022 else None,
            showlegend=(anio==2022),
            hovertemplate=f"<b>Pereira {anio}</b>: ${vp:.1f}k USD<extra></extra>",
        ))

    for anio, y in zip(anios, y_pos):
        fig.add_annotation(x=-3, y=y, text=f"<b>{anio}</b>",
                           font=dict(color=TEXTO, size=14), showarrow=False, xanchor="right")

    fig.add_annotation(
        x=20, y=2.35,
        text="Pereira supera a Bucaramanga<br>por primera vez en 2023",
        font=dict(color=AMBAR, size=11),
        showarrow=True, arrowcolor=AMBAR, arrowhead=2,
        ax=60, ay=-20,
    )

    fig.add_annotation(
        x=26, y=0.7,
        text=f"<b style='color:{VERDE}'>Pereira: $52.6k</b> vs "
             f"<b style='color:{ROJO}'>Bucaramanga: $0</b><br>"
             f"Brecha: <b>$52,590 USD</b>",
        font=dict(color=TEXTO, size=12),
        showarrow=False, bgcolor="rgba(255,255,255,0.92)",
        bordercolor=AMBAR, borderwidth=1, borderpad=8,
    )

    fig.update_layout(
        xaxis=dict(title="Ventas anuales (miles USD)", showgrid=True, range=[-5, 70]),
        yaxis=dict(visible=False, range=[0.3, 3.7]),
        showlegend=True,
        legend=dict(x=0.75, y=0.98, font=dict(color=TEXTO, size=12),
                    bgcolor="rgba(255,255,255,0)"),
        height=380,
    )
    base_layout(fig, "Pereira vs Bucaramanga · La inversión que nadie esperaba")
    save_slide(fig, f"{OUT}/slide6_dumbbell.html")
    print("✓ slide6_dumbbell.html")


# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 7 – Plan de rescate: déficits reales + roadmap de 3 fases
# ═══════════════════════════════════════════════════════════════════════════════
def slide7_matrix():
    vend_suc  = vend.groupby("SucursalID").agg(activos=("activo","sum")).reset_index()
    variedad  = (tk.groupby("Sucursal ID")["Producto ID"].nunique()
                 .reset_index().rename(columns={"Sucursal ID":"SucursalID","Producto ID":"n_prod"}))

    buca_row  = vend_suc[vend_suc["SucursalID"]==7].iloc[0]
    buca_prod = int(variedad[variedad["SucursalID"]==7]["n_prod"].iloc[0])
    per_prod  = int(variedad[variedad["SucursalID"]==8]["n_prod"].iloc[0])
    per_23avg = tk[(tk["Sucursal ID"]==8) & (tk["year"]==2023)]["Precio Total (USD)"].sum() / 12

    sin_buca  = vend_suc[vend_suc["SucursalID"] != 7]
    avg_act   = round(sin_buca["activos"].mean())
    avg_prod  = int(variedad[variedad["SucursalID"] != 7]["n_prod"].mean().round())
    avg_mes   = tk[(tk["Sucursal ID"] != 7) & (tk["year"] == 2023)].groupby("Sucursal ID")["Precio Total (USD)"].sum().mean() / 12

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Déficits a cerrar", "Reapertura en 3 fases"),
        column_widths=[0.42, 0.58],
        horizontal_spacing=0.10,
    )

    # ══ PANEL A — Scorecard: Hoy → Meta Pereira → Promedio empresa ══════════
    fig.add_trace(go.Scatter(
        x=[0.5, 0.5, 0.5], y=[1, 2, 3],
        mode="markers", marker=dict(opacity=0),
        showlegend=False, hoverinfo="skip",
    ), row=1, col=1)

    kpis = [
        dict(label="Ventas / mes",
             actual="$0",
             meta_per=f"${per_23avg/1000:.1f}k",
             meta_avg=f"${avg_mes/1000:.1f}k",
             y=1),
        dict(label="Productos",
             actual=str(buca_prod),
             meta_per=str(per_prod),
             meta_avg=str(avg_prod),
             y=2),
        dict(label="Vendedores",
             actual=str(int(buca_row["activos"])),
             meta_per="6",
             meta_avg=str(avg_act),
             y=3),
    ]

    # Encabezados de columna (solo una vez, arriba del todo)
    for x, txt, color in [
        (0.08, "Hoy",     ROJO),
        (0.50, "Pereira", VERDE),
        (0.88, "Empresa", AMBAR),
    ]:
        fig.add_annotation(
            x=x, y=3.55,
            text=f"<i>{txt}</i>",
            font=dict(size=9, color=color), showarrow=False,
            xref="x", yref="y", align="center",
        )

    for k in kpis:
        fig.add_shape(
            type="line",
            x0=0.02, x1=0.98, y0=k["y"] - 0.46, y1=k["y"] - 0.46,
            line=dict(color="#E8ECEF", width=1),
            xref="x", yref="y",
        )
        fig.add_annotation(
            x=0.5, y=k["y"] + 0.30,
            text=f"<b>{k['label']}</b>",
            font=dict(size=10, color=GRIS), showarrow=False,
            xref="x", yref="y", align="center",
        )
        # Valor actual
        fig.add_annotation(
            x=0.08, y=k["y"],
            text=f"<b>{k['actual']}</b>",
            font=dict(size=18, color=ROJO), showarrow=False,
            xref="x", yref="y", align="center",
        )
        # Flecha 1
        fig.add_annotation(
            x=0.30, y=k["y"],
            text="→",
            font=dict(size=14, color=GRIS), showarrow=False,
            xref="x", yref="y", align="center",
        )
        # Meta Pereira
        fig.add_annotation(
            x=0.50, y=k["y"],
            text=f"<b>{k['meta_per']}</b>",
            font=dict(size=18, color=VERDE), showarrow=False,
            xref="x", yref="y", align="center",
        )
        # Flecha 2
        fig.add_annotation(
            x=0.70, y=k["y"],
            text="→",
            font=dict(size=14, color=GRIS), showarrow=False,
            xref="x", yref="y", align="center",
        )
        # Meta promedio empresa
        fig.add_annotation(
            x=0.88, y=k["y"],
            text=f"<b>{k['meta_avg']}</b>",
            font=dict(size=18, color=AMBAR), showarrow=False,
            xref="x", yref="y", align="center",
        )

    fig.update_xaxes(showticklabels=False, showgrid=False, range=[0, 1], row=1, col=1)
    fig.update_yaxes(showticklabels=False, showgrid=False, range=[0.4, 3.7], row=1, col=1)

    # ══ PANEL B — Gantt simplificado ══════════════════════════════════════
    fases = [
        dict(nombre="FASE 1", inicio=0, fin=2, color=ROJO,
             titulo="Estabilizar<br>el equipo", kpi="2 → 6 vendedores", y=3),
        dict(nombre="FASE 2", inicio=2, fin=5, color=AMBAR,
             titulo="Ampliar el portafolio",   kpi=f"72 → {per_prod} productos", y=2),
        dict(nombre="FASE 3", inicio=5, fin=8, color=VERDE,
             titulo="Reabierta",               kpi=f"Meta: ${per_23avg/1000:.1f}k USD/mes", y=1),
    ]

    for f in fases:
        mid = f["inicio"] + (f["fin"] - f["inicio"]) / 2

        fig.add_trace(go.Bar(
            x=[f["fin"] - f["inicio"]], y=[f["y"]], base=f["inicio"],
            orientation="h", width=0.65,
            marker=dict(color=f["color"], opacity=0.15,
                        line=dict(color=f["color"], width=2)),
            showlegend=False,
            hovertemplate=f"<b>{f['nombre']}</b> · {f['titulo']}<extra></extra>",
        ), row=1, col=2)

        # Nombre + título en dos líneas (evita overflow horizontal)
        fig.add_annotation(
            x=mid, y=f["y"] + 0.08,
            text=f"<b style='color:{f['color']}'>{f['nombre']}</b><br>"
                 f"<span style='font-size:10px'>{f['titulo']}</span>",
            font=dict(size=11, color=TEXTO), showarrow=False,
            xref="x2", yref="y2", align="center",
        )
        # KPI debajo
        fig.add_annotation(
            x=mid, y=f["y"] - 0.26,
            text=f"<b style='color:{f['color']}'>{f['kpi']}</b>",
            font=dict(size=10), showarrow=False,
            xref="x2", yref="y2",
        )

    fig.update_xaxes(
        tickvals=[0, 2, 5, 8],
        ticktext=["Hoy", "Mes 2", "Mes 5", "Mes 8"],
        tickfont=dict(color=GRIS, size=10),
        showgrid=True, range=[-0.3, 8.5], row=1, col=2,
    )
    fig.update_yaxes(
        tickvals=[1, 2, 3],
        ticktext=["Fase 3", "Fase 2", "Fase 1"],
        tickfont=dict(color=GRIS, size=11),
        showgrid=False, range=[0.4, 3.6], row=1, col=2,
    )

    fig.update_layout(barmode="overlay", height=460, showlegend=False)
    base_layout(fig, "Plan de Reapertura · Bucaramanga · El modelo ya existe")
    fig.update_layout(margin=dict(l=40, r=60, t=70, b=60))
    save_slide(fig, f"{OUT}/slide7_matrix.html")
    print("✓ slide7_matrix.html")


# ═══════════════════════════════════════════════════════════════════════════════
# INDEX HTML
# ═══════════════════════════════════════════════════════════════════════════════
def generar_index():
    slides = [
        ("slide1_ecg.html",       "La línea que se aplana"),
        ("slide2_bump.html",      "El ranking que cuenta la historia"),
        ("slide3_timeline.html",  "La escena del crimen"),
        ("slide4a_waffle.html",   "El peso real de Bucaramanga"),
        ("slide4b_quadrant.html", "El veredicto sobre Rafael y Ana"),
        ("slide5_radar.html",     "Radiografía de 5 dimensiones"),
        ("slide6_dumbbell.html",  "Pereira vs Bucaramanga"),
        ("slide7_matrix.html",    "El plan en 3 fases"),
    ]

    nav_items = "\n".join(
        f'''      <button class="slide-btn" onclick="load({i})" id="btn-{i}">
        <span class="num">{i+1:02d}</span>
        <span class="label">{label}</span>
      </button>'''
        for i, (_, label) in enumerate(slides)
    )

    slides_js = "[" + ", ".join(f'"{f}"' for f, _ in slides) + "]"

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>WirallesTEC · Rescatando a Bucaramanga</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: 'JetBrains Mono', 'Courier New', monospace;
      background: #F8F9FA;
      color: #1A1A2E;
      height: 100vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }}

    /* ── HEADER ── */
    .header {{
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 0 20px;
      height: 52px;
      background: #FFFFFF;
      border-bottom: 1px solid #E8ECEF;
      flex-shrink: 0;
    }}
    .header-tag {{
      color: #95A5A6;
      font-size: 10px;
      letter-spacing: 2px;
      text-transform: uppercase;
    }}
    .header-sep {{ color: #E8ECEF; }}
    .header-title {{
      font-size: 13px;
      font-weight: 700;
      color: #1A1A2E;
    }}
    .header-title span {{ color: #C0392B; }}
    .header-spacer {{ flex: 1; }}
    .nav-arrows {{ display: flex; gap: 6px; }}
    .nav-arrows button {{
      background: #F8F9FA;
      border: 1px solid #E8ECEF;
      border-radius: 4px;
      padding: 4px 10px;
      font-family: inherit;
      font-size: 13px;
      color: #95A5A6;
      cursor: pointer;
      transition: background 0.15s, color 0.15s;
    }}
    .nav-arrows button:hover {{ background: #E8ECEF; color: #1A1A2E; }}
    .slide-counter {{
      font-size: 11px;
      color: #95A5A6;
      min-width: 50px;
      text-align: center;
    }}

    /* ── LAYOUT ── */
    .layout {{
      display: flex;
      flex: 1;
      overflow: hidden;
    }}

    /* ── SIDEBAR ── */
    .sidebar {{
      width: 248px;
      flex-shrink: 0;
      background: #FFFFFF;
      border-right: 1px solid #E8ECEF;
      overflow-y: auto;
      padding: 12px 10px;
      display: flex;
      flex-direction: column;
      gap: 3px;
    }}
    .sidebar-label {{
      font-size: 10px;
      letter-spacing: 2px;
      color: #BDC3C7;
      text-transform: uppercase;
      padding: 2px 8px 10px;
    }}
    .slide-btn {{
      display: flex;
      align-items: center;
      gap: 10px;
      width: 100%;
      padding: 9px 10px;
      border: 1px solid transparent;
      border-radius: 6px;
      background: none;
      cursor: pointer;
      text-align: left;
      font-family: inherit;
      font-size: 12px;
      color: #1A1A2E;
      transition: background 0.12s, border-color 0.12s;
    }}
    .slide-btn:hover {{
      background: #F8F9FA;
      border-color: #E8ECEF;
    }}
    .slide-btn.active {{
      background: #F0FAF8;
      border-color: #16A085;
      color: #16A085;
    }}
    .slide-btn.active .num {{
      background: #16A085;
      color: #FFFFFF;
      border-color: #16A085;
    }}
    .num {{
      flex-shrink: 0;
      min-width: 26px;
      height: 22px;
      background: #F8F9FA;
      border: 1px solid #E8ECEF;
      border-radius: 4px;
      font-size: 10px;
      color: #95A5A6;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .label {{ line-height: 1.3; }}

    /* ── VIEWER ── */
    .viewer {{
      flex: 1;
      overflow: hidden;
      background: #F8F9FA;
    }}
    .viewer iframe {{
      width: 100%;
      height: 100%;
      border: none;
      display: block;
    }}
  </style>
</head>
<body>

  <header class="header">
    <span class="header-tag">WirallesTEC</span>
    <span class="header-sep">·</span>
    <span class="header-title">Rescatando a <span>Bucaramanga</span></span>
    <div class="header-spacer"></div>
    <div class="nav-arrows">
      <button onclick="loadPrev()" title="Slide anterior (←)">&#8592;</button>
      <span class="slide-counter" id="counter">1 / {len(slides)}</span>
      <button onclick="loadNext()" title="Slide siguiente (→)">&#8594;</button>
    </div>
  </header>

  <div class="layout">
    <nav class="sidebar">
      <div class="sidebar-label">Slides</div>
{nav_items}
    </nav>
    <div class="viewer">
      <iframe id="viewer-frame" src="{slides[0][0]}"></iframe>
    </div>
  </div>

  <script>
    const slides = {slides_js};
    let active = 0;

    function load(idx) {{
      if (idx < 0 || idx >= slides.length) return;
      active = idx;
      document.getElementById('viewer-frame').src = slides[idx];
      document.querySelectorAll('.slide-btn').forEach((b, i) => {{
        b.classList.toggle('active', i === idx);
      }});
      document.getElementById('counter').textContent = (idx + 1) + ' / ' + slides.length;
    }}

    function loadNext() {{ load(Math.min(active + 1, slides.length - 1)); }}
    function loadPrev() {{ load(Math.max(active - 1, 0)); }}

    document.addEventListener('keydown', e => {{
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') loadNext();
      if (e.key === 'ArrowLeft'  || e.key === 'ArrowUp')   loadPrev();
    }});

    // Marcar el primer slide como activo al cargar
    document.getElementById('btn-0').classList.add('active');
  </script>

</body>
</html>"""
    with open(f"{OUT}/index.html", "w") as f:
        f.write(html)
    print("✓ index.html")


# ── EJECUTAR TODO ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Generando gráficos creativos WirallesTEC...\n")
    slide1_ecg()
    slide2_bump()
    slide3_timeline()
    slide4a_waffle()
    slide4b_quadrant()
    slide5_radar()
    slide6_dumbbell()
    slide7_matrix()
    generar_index()
    print(f"\n✅ Listos en: {OUT}/")
    print("   Abre creativo/graficos/index.html en el navegador.")
