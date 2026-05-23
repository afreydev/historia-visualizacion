"""
WirallesTEC – Gráficos creativos: "La sucursal que perdió el pulso"
Estética: diagnóstico forense de datos · fondo negro · neon verde/rojo
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
BG       = "#0D0D0D"
BG_CARD  = "#141420"
NEON     = "#00FF9F"   # verde neón — Pereira, positivo
ROJO     = "#E63946"   # rojo — Bucaramanga, peligro
AMBAR    = "#F4A261"   # ámbar — promedio, avisos
GRIS     = "#4A4A6A"   # gris azulado — otras sucursales
BLANCO   = "#F0F0F0"
AZUL     = "#457B9D"   # Bogotá

CIUDAD_COLORES = {
    "Bogotá D.C.":  AZUL,
    "Medellín":     "#A8DADC",
    "Cali":         "#7EC8E3",
    "Barranquilla": "#5B8DB8",
    "Pasto":        "#9DB4C0",
    "Cartagena":    "#8FB3C9",
    "Pereira":      NEON,
    "Bucaramanga":  ROJO,
}

def base_layout(fig, titulo=""):
    fig.update_layout(
        paper_bgcolor=BG, plot_bgcolor=BG_CARD,
        font=dict(family="'JetBrains Mono', 'Courier New', monospace", color=BLANCO, size=13),
        title=dict(text=titulo, font=dict(size=19, color=BLANCO), x=0.05, y=0.97),
        margin=dict(l=60, r=50, t=70, b=60),
    )
    fig.update_xaxes(gridcolor="#1E1E2E", zerolinecolor="#1E1E2E", tickfont=dict(color=GRIS))
    fig.update_yaxes(gridcolor="#1E1E2E", zerolinecolor="#1E1E2E", tickfont=dict(color=GRIS))
    return fig


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
    # Ventas mensuales Bucaramanga con todos los meses (0 donde no hubo ventas)
    todos = pd.DataFrame({"mes": pd.date_range("2022-01", "2024-12", freq="MS")})
    buca  = tk[tk["Sucursal ID"] == 7].groupby("mes")["Precio Total (USD)"].sum().reset_index()
    data  = todos.merge(buca, on="mes", how="left").fillna(0)
    data["Precio Total (USD)"] /= 1000  # en miles

    fig = go.Figure()

    # Área de fondo bajo la curva — verde cuando hay actividad, rojo en flatline
    activo   = data[data["mes"] < "2024-01-01"]
    flatline = data[data["mes"] >= "2024-01-01"]

    fig.add_trace(go.Scatter(
        x=activo["mes"], y=activo["Precio Total (USD)"],
        mode="lines", fill="tozeroy",
        line=dict(color=NEON, width=2.5),
        fillcolor="rgba(0,255,159,0.10)",
        name="Actividad",
        hovertemplate="%{x|%b %Y}: $%{y:.1f}k USD<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=flatline["mes"], y=flatline["Precio Total (USD)"],
        mode="lines", fill="tozeroy",
        line=dict(color=ROJO, width=3),
        fillcolor="rgba(230,57,70,0.08)",
        name="Flatline 2024",
        hovertemplate="%{x|%b %Y}: $%{y:.1f}k USD<extra></extra>",
    ))

    # Línea vertical: inicio 2024
    fig.add_vline(
        x=pd.Timestamp("2024-01-01").timestamp() * 1000,
        line=dict(dash="dash", color=ROJO, width=1.5),
    )

    # Anotaciones clave
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

    # KPI en esquina superior derecha
    fig.add_annotation(
        x=0.97, y=0.95, xref="paper", yref="paper",
        text="<b>Ventas 2024</b><br><span style='font-size:24px; color:#E63946'>$0 USD</span>",
        font=dict(color=BLANCO, size=13),
        showarrow=False, align="right",
        bgcolor="rgba(230,57,70,0.15)", bordercolor=ROJO, borderwidth=1, borderpad=8,
    )

    fig.update_layout(
        xaxis=dict(title="", tickformat="%b %Y", showgrid=False),
        yaxis=dict(title="Ventas mensuales (miles USD)", showgrid=True),
        showlegend=False, height=420,
    )
    base_layout(fig, "Bucaramanga · Actividad comercial 2022–2024")
    fig.write_html(f"{OUT}/slide1_ecg.html")
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
        dash  = "solid"

        # Trazar la línea solo entre puntos válidos
        x_valid = [a for a, r in zip(anios, ranks) if r is not None]
        y_valid = [r for r in ranks if r is not None]

        fig.add_trace(go.Scatter(
            x=x_valid, y=y_valid,
            mode="lines+markers+text",
            name=ciudad,
            line=dict(color=color, width=width, dash=dash),
            marker=dict(size=12 if ciudad in ("Bucaramanga","Pereira") else 8,
                        color=color,
                        line=dict(width=2, color=BG)),
            text=["" if i < len(x_valid)-1 else ciudad for i in range(len(x_valid))],
            textposition="middle right",
            textfont=dict(color=color, size=12 if ciudad in ("Bucaramanga","Pereira") else 10),
            hovertemplate=f"<b>{ciudad}</b><br>%{{x}}: Puesto %{{y}}<extra></extra>",
        ))

        # Símbolo ⊘ para Bucaramanga en 2024
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

    # Etiquetas del lado izquierdo
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
    fig.write_html(f"{OUT}/slide2_bump.html")
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

    # Área de ventas
    fig.add_trace(go.Scatter(
        x=data["mes"], y=data["ventas_k"],
        mode="lines", fill="tozeroy",
        line=dict(color=NEON, width=2),
        fillcolor="rgba(0,255,159,0.12)",
        name="Ventas Bucaramanga",
        hovertemplate="%{x|%b %Y}: $%{y:.2f}k USD<extra></extra>",
    ))

    # Líneas y anotaciones de salidas
    for i, (fecha, nombre, _) in enumerate(salidas):
        ts = pd.Timestamp(fecha).timestamp() * 1000
        es_doble = "Camila" in nombre
        color_ev = "#FF6B6B" if es_doble else AMBAR

        fig.add_vline(x=ts, line=dict(color=color_ev, width=1.5, dash="dot"))

        # Ícono persona sobre la línea
        y_icono = 5.0 - i * 0.6
        fig.add_annotation(
            x=fecha, y=y_icono,
            text=f"👤✕  <b>{nombre}</b>",
            font=dict(color=color_ev, size=11, family="'Courier New', monospace"),
            showarrow=False, xanchor="left", bgcolor="rgba(20,20,32,0.85)",
            bordercolor=color_ev, borderwidth=1, borderpad=4,
        )

    # Zona flatline 2024
    fig.add_vrect(
        x0="2024-01-01", x1="2024-12-31",
        fillcolor="rgba(230,57,70,0.06)",
        line=dict(color=ROJO, width=0),
        annotation_text="2024: CERO VENTAS",
        annotation_position="top left",
        annotation_font=dict(color=ROJO, size=12),
    )

    # Dos vendedores restantes
    fig.add_annotation(
        x="2024-07-01", y=2.2,
        text="👤 Carlos  👤 Teresa<br><i>2 vendedores · $0 generados</i>",
        font=dict(color=ROJO, size=11),
        showarrow=False, bgcolor="rgba(230,57,70,0.12)",
        bordercolor=ROJO, borderwidth=1, borderpad=6,
    )

    fig.update_layout(
        xaxis=dict(title="", tickformat="%b %Y", showgrid=False),
        yaxis=dict(title="Ventas mensuales (miles USD)", showgrid=True),
        showlegend=False, height=450,
    )
    base_layout(fig, "Bucaramanga · Cada salida dejó una huella")
    fig.write_html(f"{OUT}/slide3_timeline.html")
    print("✓ slide3_timeline.html")


# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 4A – Waffle chart: el peso real de Bucaramanga
# ═══════════════════════════════════════════════════════════════════════════════
def slide4a_waffle():
    # Participación redondeada a 100 celdas
    pcts = {
        "Bogotá D.C.":  36,
        "Cali":         16,
        "Medellín":     15,
        "Pasto":         9,
        "Barranquilla":  8,
        "Pereira":       7,
        "Cartagena":     6,
        "Bucaramanga":   3,  # ligeramente redondeado a 3 para llegar a 100
    }
    # Construir matriz 10×10
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

    # Texto por celda
    text_grid = [["" for _ in range(10)] for _ in range(10)]
    # Marcar las celdas de Bucaramanga con "BUC"
    buca_idx = list(pcts.keys()).index("Bucaramanga")
    count = 0
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
        textfont=dict(color=BG, size=9, family="'Courier New', monospace"),
        xgap=3, ygap=3,
        hovertemplate="<b>%{customdata}</b><extra></extra>",
        customdata=grid[::-1],
    ))

    # Leyenda manual
    for i, (ciudad, n) in enumerate(pcts.items()):
        fig.add_annotation(
            x=10.5, y=9 - i,
            text=f"<span style='color:{CIUDAD_COLORES[ciudad]}'>■</span> {ciudad}: {n}%",
            font=dict(size=11, color=BLANCO),
            showarrow=False, xanchor="left",
        )

    # Anotación grande para Bucaramanga
    fig.add_annotation(
        x=4.5, y=-1.2,
        text="<b style='color:#E63946'>3 de cada 100 dólares</b> son de Bucaramanga",
        font=dict(size=13, color=BLANCO),
        showarrow=False,
    )

    fig.update_layout(
        xaxis=dict(visible=False, range=[-0.5, 16]),
        yaxis=dict(visible=False, range=[-1.8, 10]),
        height=480, width=820,
    )
    base_layout(fig, "¿Cuánto pesa Bucaramanga en la empresa? · Total 2022–2024")
    fig.write_html(f"{OUT}/slide4a_waffle.html")
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

    # Líneas divisorias de cuadrantes
    fig.add_hline(y=avg_y, line=dict(color=GRIS, width=1, dash="dot"))
    fig.add_vline(x=avg_x, line=dict(color=GRIS, width=1, dash="dot"))

    # Etiquetas de cuadrantes
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
            bgcolor="rgba(20,20,32,0.7)",
        )

    # Puntos por sucursal
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
                        line=dict(width=2 if bold else 1, color=BG)),
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
    fig.write_html(f"{OUT}/slide4b_quadrant.html")
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

    # Retención = inverso de rotación normalizado
    df["retencion"] = df["activos"] / (df["activos"] + df["rotacion"])

    dims = ["activos","n_prod","ventas","n_tickets","retencion"]
    for d in dims:
        df[f"{d}_n"] = df[d] / df[d].max()

    cats = ["Vendedores<br>activos", "Variedad de<br>productos",
            "Ventas<br>totales", "Nº de<br>tickets", "Retención<br>de personal"]

    fig = go.Figure()

    capas = [
        ("Bogotá D.C.",  AZUL,   0.5,  True,  "toself"),
        ("Promedio",     AMBAR,  0.3,  True,  "toself"),
        ("Pereira",      NEON,   0.5,  True,  "toself"),
        ("Bucaramanga",  ROJO,   0.6,  True,  "toself"),
    ]

    # Calcular promedio empresa
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
            fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:],16)},{opacity*0.25})",
            hovertemplate=f"<b>{ciudad}</b><br>%{{theta}}: %{{r:.2f}}<extra></extra>",
        ))

    fig.update_layout(
        polar=dict(
            bgcolor=BG_CARD,
            radialaxis=dict(visible=True, range=[0,1], tickvals=[0.25,0.5,0.75,1.0],
                            tickfont=dict(color=GRIS, size=9), gridcolor="#1E1E2E",
                            linecolor=GRIS),
            angularaxis=dict(tickfont=dict(color=BLANCO, size=11), gridcolor="#1E1E2E",
                             linecolor=GRIS),
        ),
        legend=dict(x=1.05, y=0.95, font=dict(color=BLANCO, size=11),
                    bgcolor="rgba(0,0,0,0)"),
        height=520,
    )
    base_layout(fig, "Diagnóstico Multidimensional · Bucaramanga vs la Empresa")
    fig.update_layout(paper_bgcolor=BG, plot_bgcolor=BG)
    fig.write_html(f"{OUT}/slide5_radar.html")
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

        # Línea conectora
        fig.add_trace(go.Scatter(
            x=[vb, vp], y=[y, y],
            mode="lines",
            line=dict(color=GRIS, width=2.5),
            showlegend=False,
            hoverinfo="skip",
        ))

        # Punto Bucaramanga
        fig.add_trace(go.Scatter(
            x=[vb], y=[y],
            mode="markers+text",
            marker=dict(size=18, color=ROJO, line=dict(width=2, color=BG)),
            text=[f"${vb:.1f}k" if vb > 0 else "$0"],
            textposition="bottom center",
            textfont=dict(color=ROJO, size=12),
            name="Bucaramanga" if anio==2022 else None,
            showlegend=(anio==2022),
            hovertemplate=f"<b>Bucaramanga {anio}</b>: ${vb:.1f}k USD<extra></extra>",
        ))

        # Punto Pereira
        fig.add_trace(go.Scatter(
            x=[vp], y=[y],
            mode="markers+text",
            marker=dict(size=18, color=NEON, line=dict(width=2, color=BG)),
            text=[f"${vp:.1f}k"],
            textposition="bottom center",
            textfont=dict(color=NEON, size=12),
            name="Pereira" if anio==2022 else None,
            showlegend=(anio==2022),
            hovertemplate=f"<b>Pereira {anio}</b>: ${vp:.1f}k USD<extra></extra>",
        ))

        # Flecha de dirección
        direccion_buca = "↑" if anio > 2022 and buca.get(anio,0) > buca.get(anio-1,0) else "↓"
        direccion_per  = "↑" if anio > 2022 and per.get(anio,0) > per.get(anio-1,0) else "↑"

    # Etiquetas de año
    for anio, y in zip(anios, y_pos):
        fig.add_annotation(x=-3, y=y, text=f"<b>{anio}</b>",
                           font=dict(color=BLANCO, size=14), showarrow=False, xanchor="right")

    # Anotación del cruce 2023
    fig.add_annotation(
        x=20, y=2.35,
        text="Pereira supera a Bucaramanga<br>por primera vez en 2023",
        font=dict(color=AMBAR, size=11),
        showarrow=True, arrowcolor=AMBAR, arrowhead=2,
        ax=60, ay=-20,
    )

    # Brecha 2024
    fig.add_annotation(
        x=26, y=0.7,
        text=f"<b style='color:{NEON}'>Pereira: $52.6k</b> vs "
             f"<b style='color:{ROJO}'>Bucaramanga: $0</b><br>"
             f"Brecha: <b>$52,590 USD</b>",
        font=dict(color=BLANCO, size=12),
        showarrow=False, bgcolor="rgba(20,20,32,0.9)",
        bordercolor=AMBAR, borderwidth=1, borderpad=8,
    )

    fig.update_layout(
        xaxis=dict(title="Ventas anuales (miles USD)", showgrid=True, range=[-5, 70]),
        yaxis=dict(visible=False, range=[0.3, 3.7]),
        showlegend=True,
        legend=dict(x=0.75, y=0.98, font=dict(color=BLANCO, size=12),
                    bgcolor="rgba(0,0,0,0)"),
        height=380,
    )
    base_layout(fig, "Pereira vs Bucaramanga · La inversión que nadie esperaba")
    fig.write_html(f"{OUT}/slide6_dumbbell.html")
    print("✓ slide6_dumbbell.html")


# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 7 – Plan de rescate: déficits reales + roadmap de 3 fases
# ═══════════════════════════════════════════════════════════════════════════════
def slide7_matrix():
    # ── Datos reales para el bullet chart ─────────────────────────────────
    vend_suc  = vend.groupby("SucursalID").agg(activos=("activo","sum")).reset_index()
    variedad  = (tk.groupby("Sucursal ID")["Producto ID"].nunique()
                 .reset_index().rename(columns={"Sucursal ID":"SucursalID","Producto ID":"n_prod"}))
    vsuc_mes  = (tk.groupby("Sucursal ID")["Precio Total (USD)"].sum() / 36
                 ).reset_index().rename(columns={"Sucursal ID":"SucursalID","Precio Total (USD)":"v_mes"})

    buca_row  = vend_suc[vend_suc["SucursalID"]==7].iloc[0]
    buca_prod = int(variedad[variedad["SucursalID"]==7]["n_prod"].iloc[0])
    buca_vmes = float(vsuc_mes[vsuc_mes["SucursalID"]==7]["v_mes"].iloc[0])

    # Referencias desde los datos
    per_prod  = int(variedad[variedad["SucursalID"]==8]["n_prod"].iloc[0])       # 133
    per_23avg = tk[(tk["Sucursal ID"]==8) & (tk["year"]==2023)]["Precio Total (USD)"].sum() / 12  # $2,135
    emp_vend  = float(vend_suc[vend_suc["SucursalID"]!=7]["activos"].mean())     # 5.9
    emp_prod  = float(variedad[variedad["SucursalID"]!=7]["n_prod"].mean())      # 145
    bog_vend  = int(vend_suc[vend_suc["SucursalID"]==1]["activos"].iloc[0])      # 12
    bog_prod  = int(variedad[variedad["SucursalID"]==1]["n_prod"].iloc[0])       # 205
    bog_vmes  = float(vsuc_mes[vsuc_mes["SucursalID"]==1]["v_mes"].iloc[0])      # 12,485

    # ── Figura con dos paneles ─────────────────────────────────────────────
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Los tres déficits de Bucaramanga", "El plan de rescate · 3 fases"),
        column_widths=[0.42, 0.58],
    )

    # ══ PANEL A — Bullet / gap chart ══════════════════════════════════════
    metricas = [
        dict(
            label="Vendedores<br>activos",
            actual=int(buca_row["activos"]),  # 2
            meta=6,                            # meta Fase 1
            empresa=emp_vend,                  # 5.9
            maximo=bog_vend,                   # 12
            unidad="",
            y=3,
        ),
        dict(
            label="Productos<br>distintos vendidos",
            actual=buca_prod,                  # 72
            meta=per_prod,                     # 133 (nivel Pereira)
            empresa=emp_prod,                  # 145
            maximo=bog_prod,                   # 205
            unidad="",
            y=2,
        ),
        dict(
            label="Ventas promedio<br>mensuales (USD)",
            actual=0,                          # $0 en 2024
            meta=round(per_23avg),             # $2,135 (Pereira 2023)
            empresa=round(bog_vmes * 0.35),    # aprox promedio empresa excl. Bogotá
            maximo=round(bog_vmes),            # $12,485 Bogotá
            unidad="$",
            y=1,
        ),
    ]

    for m in metricas:
        norm = lambda v: v / m["maximo"]  # normalizar sobre máximo

        # Barra de fondo: rango completo (0 → máximo)
        fig.add_trace(go.Bar(
            x=[1.0], y=[m["y"]],
            orientation="h",
            marker=dict(color=GRIS, opacity=0.15),
            showlegend=False, hoverinfo="skip",
            width=0.35,
        ), row=1, col=1)

        # Barra promedio empresa
        fig.add_trace(go.Bar(
            x=[norm(m["empresa"])], y=[m["y"]],
            orientation="h",
            marker=dict(color=GRIS, opacity=0.4),
            showlegend=False,
            width=0.35,
            hovertemplate=f"Promedio empresa: {m['unidad']}{m['empresa']:,.0f}<extra></extra>",
        ), row=1, col=1)

        # Punto actual — Bucaramanga (rojo)
        fig.add_trace(go.Scatter(
            x=[norm(m["actual"]) if m["actual"] > 0 else 0.012],
            y=[m["y"]],
            mode="markers",
            marker=dict(size=16, color=ROJO, symbol="diamond",
                        line=dict(width=2, color=BLANCO)),
            showlegend=False,
            hovertemplate=f"Bucaramanga hoy: {m['unidad']}{m['actual']:,}<extra></extra>",
        ), row=1, col=1)

        # Punto meta — objetivo del plan (verde)
        fig.add_trace(go.Scatter(
            x=[norm(m["meta"])], y=[m["y"]],
            mode="markers",
            marker=dict(size=16, color=NEON, symbol="circle",
                        line=dict(width=2, color=BLANCO)),
            showlegend=False,
            hovertemplate=f"Meta del plan: {m['unidad']}{m['meta']:,}<extra></extra>",
        ), row=1, col=1)

        # Flecha del gap: de actual a meta
        fig.add_annotation(
            x=norm(m["meta"]), y=m["y"] + 0.28,
            ax=norm(m["actual"]) if m["actual"] > 0 else 0.012,
            ay=m["y"] + 0.28,
            xref="x", yref="y", axref="x", ayref="y",
            showarrow=True, arrowhead=2, arrowwidth=2,
            arrowcolor=AMBAR, text="",
        )

        # Labels: actual y meta
        fig.add_annotation(
            x=norm(m["actual"]) if m["actual"] > 0 else 0.012,
            y=m["y"] - 0.27,
            text=f"<b style='color:{ROJO}'>HOY: {m['unidad']}{m['actual']:,}</b>",
            font=dict(size=10), showarrow=False, xref="x", yref="y",
        )
        fig.add_annotation(
            x=norm(m["meta"]), y=m["y"] - 0.27,
            text=f"<b style='color:{NEON}'>META: {m['unidad']}{m['meta']:,}</b>",
            font=dict(size=10), showarrow=False, xref="x", yref="y",
        )

    # Leyenda manual panel A
    for sym, color, txt in [("diamond", ROJO, "Bucaramanga hoy"),
                              ("circle",  NEON, "Meta del plan"),
                              ("square",  GRIS, "Promedio empresa")]:
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode="markers",
            marker=dict(size=10, color=color, symbol=sym),
            name=txt, showlegend=True,
        ), row=1, col=1)

    fig.update_xaxes(showticklabels=False, showgrid=False, range=[0, 1.08], row=1, col=1)
    fig.update_yaxes(
        tickvals=[1, 2, 3],
        ticktext=["Ventas/mes", "Productos<br>distintos", "Vendedores<br>activos"],
        tickfont=dict(color=BLANCO, size=11),
        showgrid=False, row=1, col=1,
    )

    # ══ PANEL B — Gantt de 3 fases ════════════════════════════════════════
    fases = [
        dict(
            nombre="FASE 1", inicio=0, fin=2, color=ROJO,
            titulo="Estabilizar el equipo",
            acciones=["Contratar 4 vendedores", "Bonos de retención", "Capacitación intensiva"],
            kpi=f"2 → 6 vendedores activos",
            y=3,
        ),
        dict(
            nombre="FASE 2", inicio=2, fin=5, color=AMBAR,
            titulo="Ampliar el portafolio",
            acciones=["Top 5 categorías de Bogotá/Cali", "Campañas promocionales", "KPI semanal de tickets"],
            kpi=f"72 → {per_prod} productos distintos",
            y=2,
        ),
        dict(
            nombre="FASE 3", inicio=5, fin=8, color=NEON,
            titulo="Escalar y replicar",
            acciones=["Benchmark mensual vs Pereira", "Replicar modelo en Cartagena", "Revisión trimestral de viabilidad"],
            kpi=f"Meta: ${per_23avg/1000:.1f}k USD/mes",
            y=1,
        ),
    ]

    for f in fases:
        # Barra de la fase
        fig.add_trace(go.Bar(
            x=[f["fin"] - f["inicio"]],
            y=[f["y"]],
            base=f["inicio"],
            orientation="h",
            marker=dict(color=f["color"], opacity=0.25,
                        line=dict(color=f["color"], width=2)),
            showlegend=False,
            width=0.55,
            hovertemplate=f"<b>{f['nombre']}</b><br>Mes {f['inicio']+1} – {f['fin']}<br>{f['titulo']}<extra></extra>",
        ), row=1, col=2)

        # Nombre de fase y título
        fig.add_annotation(
            x=f["inicio"] + (f["fin"] - f["inicio"]) / 2,
            y=f["y"] + 0.38,
            text=f"<b style='color:{f['color']}'>{f['nombre']}</b>  ·  {f['titulo']}",
            font=dict(size=11, color=BLANCO), showarrow=False,
            xref="x2", yref="y2",
        )

        # Acciones dentro de la barra
        texto_acc = "<br>".join(f"• {a}" for a in f["acciones"])
        fig.add_annotation(
            x=f["inicio"] + (f["fin"] - f["inicio"]) / 2,
            y=f["y"],
            text=texto_acc,
            font=dict(size=9.5, color=BLANCO), showarrow=False,
            xref="x2", yref="y2",
            align="left",
        )

        # KPI bajo la barra
        fig.add_annotation(
            x=f["inicio"] + (f["fin"] - f["inicio"]) / 2,
            y=f["y"] - 0.38,
            text=f"<b style='color:{f['color']}'>▶ {f['kpi']}</b>",
            font=dict(size=10), showarrow=False,
            xref="x2", yref="y2",
        )

    # Etiquetas de meses en eje X
    fig.update_xaxes(
        tickvals=list(range(9)),
        ticktext=[f"Mes {i}" if i > 0 else "Hoy" for i in range(9)],
        tickfont=dict(color=GRIS, size=10),
        showgrid=True, range=[-0.3, 8.5],
        row=1, col=2,
    )
    fig.update_yaxes(
        tickvals=[1, 2, 3],
        ticktext=["Fase 3", "Fase 2", "Fase 1"],
        tickfont=dict(color=GRIS, size=11),
        showgrid=False, range=[0.4, 3.9],
        row=1, col=2,
    )

    fig.update_layout(
        barmode="overlay",
        height=490,
        legend=dict(x=0.01, y=0.01, font=dict(color=BLANCO, size=10),
                    bgcolor="rgba(20,20,32,0.8)", bordercolor=GRIS, borderwidth=1),
    )
    base_layout(fig, "Plan de Rescate · Bucaramanga · Basado en datos reales")
    fig.write_html(f"{OUT}/slide7_matrix.html")
    print("✓ slide7_matrix.html")


# ═══════════════════════════════════════════════════════════════════════════════
# INDEX HTML
# ═══════════════════════════════════════════════════════════════════════════════
def generar_index():
    slides = [
        ("slide1_ecg.html",       "Slide 1 — ECG: La línea que se aplana"),
        ("slide2_bump.html",      "Slide 2 — Bump chart: El ranking que cuenta la historia"),
        ("slide3_timeline.html",  "Slide 3 — Timeline anotado: La escena del crimen"),
        ("slide4a_waffle.html",   "Slide 4A — Waffle: El peso real de Bucaramanga"),
        ("slide4b_quadrant.html", "Slide 4B — Quadrant: El veredicto sobre Rafael y Ana"),
        ("slide5_radar.html",     "Slide 5 — Radar: Radiografía de 5 dimensiones"),
        ("slide6_dumbbell.html",  "Slide 6 — Dumbbell: Pereira vs Bucaramanga"),
        ("slide7_matrix.html",    "Slide 7 — Matriz + Proyección: La decisión es hoy"),
    ]
    items = "\n".join(
        f'<li><a href="{f}" target="_blank">'
        f'<span class="num">{i+1:02d}</span>{label}</a></li>'
        for i, (f, label) in enumerate(slides)
    )
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>WirallesTEC · La sucursal que perdió el pulso</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'JetBrains Mono', 'Courier New', monospace;
      background: #0D0D0D; color: #F0F0F0;
      display: flex; flex-direction: column; align-items: center;
      padding: 60px 20px; min-height: 100vh;
    }}
    .tag {{ color: #4A4A6A; font-size: 12px; letter-spacing: 3px; margin-bottom: 10px; }}
    h1 {{ color: #00FF9F; font-size: 26px; margin-bottom: 6px; text-align: center; }}
    .sub {{ color: #4A4A6A; font-size: 13px; margin-bottom: 50px; }}
    .ecg {{ color: #E63946; font-size: 36px; margin-bottom: 16px; letter-spacing: -2px; }}
    ul {{ list-style: none; width: 100%; max-width: 580px; }}
    li {{ margin: 10px 0; }}
    a {{
      display: flex; align-items: center; gap: 14px;
      padding: 14px 20px; background: #141420;
      border: 1px solid #1E1E2E; border-radius: 6px;
      color: #F0F0F0; text-decoration: none; font-size: 13px;
      transition: border-color 0.2s, background 0.2s;
    }}
    a:hover {{ border-color: #00FF9F; background: #1A1A30; color: #00FF9F; }}
    .num {{
      background: #1E1E2E; color: #4A4A6A;
      padding: 3px 8px; border-radius: 4px;
      font-size: 11px; min-width: 28px; text-align: center;
    }}
  </style>
</head>
<body>
  <div class="tag">TALLER FINAL · VISUALIZACIÓN · MAYO 2026</div>
  <div class="ecg">_/&#8254;\\_/&#8254;\\____</div>
  <h1>La sucursal que perdió el pulso</h1>
  <p class="sub">WirallesTEC · Diagnóstico forense de datos · 7 minutos</p>
  <ul>{items}</ul>
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
