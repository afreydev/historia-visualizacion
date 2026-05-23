"""
WirallesTEC – Generador de gráficos para la presentación
Genera los 7 gráficos del plan.md como archivos HTML interactivos.
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import folium
from folium import plugins
import os

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "..")   # los .xlsx viven un nivel arriba
OUT  = os.path.join(BASE, "graficos")
os.makedirs(OUT, exist_ok=True)

# ── PALETA ──────────────────────────────────────────────────────────────────
C_ROJO      = "#E63946"
C_VERDE     = "#2DC653"
C_AMARILLO  = "#F4A261"
C_GRIS      = "#9E9E9E"
C_AZUL      = "#457B9D"
C_FONDO     = "#1A1A2E"
C_TEXTO     = "#F0F0F0"
C_TARJETA   = "#16213E"

ANIO_COLORES = {"2022": C_AZUL, "2023": C_AMARILLO, "2024": C_ROJO}

def estilo_base(fig, titulo=""):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=C_FONDO,
        plot_bgcolor=C_TARJETA,
        font=dict(family="Inter, Arial", color=C_TEXTO, size=13),
        title=dict(text=titulo, font=dict(size=20, color=C_TEXTO), x=0.05),
        margin=dict(l=60, r=40, t=70, b=60),
    )
    return fig


# ── CARGA Y LIMPIEZA DE DATOS ────────────────────────────────────────────────
def cargar_datos():
    suc  = pd.read_excel(f"{DATA}/base-de-datos.xlsx", sheet_name="Sucursales (Server)")
    vend = pd.read_excel(f"{DATA}/base-de-datos.xlsx", sheet_name="Vendedores")
    prod = pd.read_excel(f"{DATA}/base-de-datos.xlsx", sheet_name="Productos")
    cats = pd.read_excel(f"{DATA}/base-de-datos.xlsx", sheet_name="Categorías de productos")

    t22 = pd.read_excel(f"{DATA}/tickets_2022.xlsx"); t22["year"] = 2022
    t23 = pd.read_excel(f"{DATA}/tickets_2023.xlsx"); t23["year"] = 2023
    t24 = pd.read_excel(f"{DATA}/tickets_2024.xlsx"); t24["year"] = 2024
    tickets = pd.concat([t22, t23, t24], ignore_index=True)

    # Limpiar outliers de precio (3 filas con > 50,000 USD)
    tickets = tickets[tickets["Precio Total (USD)"] < 50_000].copy()
    tickets["Sucursal ID"] = tickets["Sucursal ID"].astype("Int64")
    tickets["Fecha Venta"] = pd.to_datetime(tickets["Fecha Venta"])
    tickets["mes"] = tickets["Fecha Venta"].dt.to_period("M").dt.to_timestamp()

    # Tabla sucursales con nombre corto
    suc["ciudad"] = suc["CIUDAD"]
    suc["lat"] = suc["COORDENADAS (lat, lon)"].str.split(",").str[0].astype(float)
    suc["lon"] = suc["COORDENADAS (lat, lon)"].str.split(",").str[1].astype(float)

    # Vendedores activos (FechaSalida = 9999)
    vend["activo"] = vend["FechaSalida"].astype(str).str.startswith("9999")

    # Ventas por sucursal y año
    vsay = (
        tickets.groupby(["Sucursal ID", "year"])["Precio Total (USD)"]
        .sum().unstack(fill_value=0).reset_index()
    )
    vsay.columns = ["suc_id", "usd_2022", "usd_2023", "usd_2024"]
    vsay["total"] = vsay[["usd_2022", "usd_2023", "usd_2024"]].sum(axis=1)
    vsay = vsay.merge(suc[["SUCURSAL_ID", "ciudad"]], left_on="suc_id", right_on="SUCURSAL_ID")

    # Vendedores activos por sucursal
    vend_suc = (
        vend.groupby("SucursalID")
        .agg(total_vend=("VendedorID", "count"), activos=("activo", "sum"),
             rotacion=("activo", lambda x: (~x).sum()))
        .reset_index().rename(columns={"SucursalID": "suc_id"})
    )

    # Variedad de productos por sucursal
    variedad = (
        tickets.groupby("Sucursal ID")["Producto ID"]
        .nunique().reset_index()
        .rename(columns={"Sucursal ID": "suc_id", "Producto ID": "n_productos"})
    )

    # Tabla maestra por sucursal
    maestra = vsay.merge(vend_suc, on="suc_id", how="left").merge(variedad, on="suc_id", how="left")

    # Color por sucursal (Bucaramanga=rojo, Pereira=verde, resto=gris/azul)
    def color_suc(ciudad):
        if ciudad == "Bucaramanga": return C_ROJO
        if ciudad == "Pereira":     return C_VERDE
        return C_AZUL
    maestra["color"] = maestra["ciudad"].apply(color_suc)
    maestra["tamaño"] = maestra["ciudad"].apply(lambda c: 16 if c in ("Bucaramanga","Pereira") else 10)

    return tickets, suc, vend, prod, cats, maestra


tickets, suc, vend, prod, cats, maestra = cargar_datos()


# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 1 – Mapa de Colombia con calor de ventas
# ═══════════════════════════════════════════════════════════════════════════════
def slide1_mapa():
    m = folium.Map(location=[4.5, -74.0], zoom_start=6,
                   tiles="CartoDB dark_matter")

    max_total = maestra["total"].max()

    for _, row in maestra.iterrows():
        suc_row = suc[suc["SUCURSAL_ID"] == row["suc_id"]].iloc[0]
        radio = 12 + 38 * (row["total"] / max_total)
        alerta = row["usd_2024"] == 0

        color = C_ROJO if alerta else (C_VERDE if row["ciudad"] == "Pereira" else C_AZUL)

        popup_html = f"""
        <div style='font-family:Arial; background:#1A1A2E; color:#F0F0F0;
                    padding:10px; border-radius:8px; min-width:180px;'>
          <b style='font-size:14px;'>{row['ciudad']}</b><br>
          {'<span style="color:#E63946; font-weight:bold;">⚠ SIN VENTAS 2024</span><br>' if alerta else ''}
          💰 Total 3 años: <b>${row['total']:,.0f} USD</b><br>
          📅 2022: ${row['usd_2022']:,.0f} | 2023: ${row['usd_2023']:,.0f} | 2024: ${row['usd_2024']:,.0f}<br>
          👥 Vendedores activos: <b>{int(row['activos'])}</b> / {int(row['total_vend'])}<br>
          📦 Productos distintos: <b>{int(row['n_productos'])}</b>
        </div>"""

        folium.CircleMarker(
            location=[suc_row["lat"], suc_row["lon"]],
            radius=radio,
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{row['ciudad']}: ${row['total']:,.0f} USD"
        ).add_to(m)

        folium.Marker(
            location=[suc_row["lat"] + 0.25, suc_row["lon"]],
            icon=folium.DivIcon(
                html=f"<div style='font-family:Arial; font-size:11px; font-weight:bold; color:{'#E63946' if alerta else '#F0F0F0'};'>{row['ciudad']}</div>",
                icon_size=(120, 20)
            )
        ).add_to(m)

    # Leyenda
    leyenda = """
    <div style='position:fixed; bottom:30px; left:30px; z-index:1000;
                background:#1A1A2E; color:#F0F0F0; padding:12px 16px;
                border-radius:8px; font-family:Arial; font-size:12px;
                border:1px solid #457B9D;'>
      <b>Ventas 2022–2024</b><br>
      <span style='color:#E63946'>●</span> Sin ventas en 2024 (riesgo)<br>
      <span style='color:#2DC653'>●</span> Mayor crecimiento<br>
      <span style='color:#457B9D'>●</span> Otras sucursales<br>
      <i>(tamaño = ventas totales)</i>
    </div>"""
    m.get_root().html.add_child(folium.Element(leyenda))

    m.save(f"{OUT}/slide1_mapa.html")
    print("✓ slide1_mapa.html")


# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 2 – Bar chart agrupado por año y sucursal
# ═══════════════════════════════════════════════════════════════════════════════
def slide2_barras_agrupadas():
    df = maestra.sort_values("total")

    fig = go.Figure()
    for anio, col, color in [("2022","usd_2022",C_AZUL), ("2023","usd_2023",C_AMARILLO), ("2024","usd_2024",C_ROJO)]:
        fig.add_trace(go.Bar(
            name=str(anio),
            x=df["ciudad"],
            y=df[col] / 1000,
            marker_color=[C_ROJO if (c == "Bucaramanga" and anio == "2024") else color for c in df["ciudad"]],
            text=[f"${v/1000:.0f}k" if v > 0 else "⚠ $0" for v in df[col]],
            textposition="outside",
            textfont=dict(size=10),
        ))

    fig.update_layout(
        barmode="group",
        xaxis_title="Sucursal",
        yaxis_title="Ventas (miles USD)",
        legend=dict(orientation="h", y=1.08, x=0.5, xanchor="center"),
        annotations=[dict(
            x="Bucaramanga", y=0, xref="x", yref="y",
            text="⚠ $0 en 2024", showarrow=True, arrowhead=2,
            arrowcolor=C_ROJO, font=dict(color=C_ROJO, size=12),
            ax=0, ay=-40
        )],
    )
    estilo_base(fig, "Ventas por Sucursal 2022–2024 (miles USD)")
    fig.write_html(f"{OUT}/slide2_barras.html")
    print("✓ slide2_barras.html")


# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 3 – Line chart evolución mensual
# ═══════════════════════════════════════════════════════════════════════════════
def slide3_lineas_temporales():
    mensuales = (
        tickets.groupby(["Sucursal ID", "mes"])["Precio Total (USD)"]
        .sum().reset_index()
        .merge(suc[["SUCURSAL_ID","ciudad"]], left_on="Sucursal ID", right_on="SUCURSAL_ID")
    )

    fig = go.Figure()
    for _, row in suc.iterrows():
        ciudad = row["ciudad"]
        d = mensuales[mensuales["ciudad"] == ciudad].sort_values("mes")
        if d.empty: continue

        if ciudad == "Bucaramanga":
            color, width, dash = C_ROJO, 4, "solid"
        elif ciudad == "Pereira":
            color, width, dash = C_VERDE, 3, "solid"
        elif ciudad == "Bogotá D.C.":
            color, width, dash = "#A8DADC", 2, "dot"
        else:
            color, width, dash = C_GRIS, 1, "solid"

        visible = True if ciudad in ("Bucaramanga","Pereira","Bogotá D.C.") else "legendonly"

        fig.add_trace(go.Scatter(
            x=d["mes"], y=d["Precio Total (USD)"] / 1000,
            mode="lines+markers",
            name=ciudad,
            line=dict(color=color, width=width, dash=dash),
            marker=dict(size=5 if ciudad in ("Bucaramanga","Pereira") else 3),
            visible=visible,
        ))

    fig.add_vline(x=pd.Timestamp("2024-01-01").timestamp() * 1000,
                  line_dash="dash", line_color=C_GRIS)

    fig.update_layout(
        xaxis_title="Mes",
        yaxis_title="Ventas (miles USD)",
        legend=dict(orientation="v", x=1.01, y=0.99),
        hovermode="x unified",
    )
    estilo_base(fig, "Evolución Mensual de Ventas por Sucursal")
    fig.write_html(f"{OUT}/slide3_lineas.html")
    print("✓ slide3_lineas.html")


# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 4 – Scatter plots: vendedores vs ventas  /  variedad vs ventas
# ═══════════════════════════════════════════════════════════════════════════════
def slide4_scatter_debate():
    df = maestra.copy()

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            "¿Más vendedores → más ventas? (Ana)",
            "¿Más variedad → más ventas? (Rafael)"
        )
    )

    for _, row in df.iterrows():
        ciudad = row["ciudad"]
        color  = row["color"]
        size   = 18 if ciudad in ("Bucaramanga","Pereira") else 12

        # Scatter A – vendedores activos vs ventas
        fig.add_trace(go.Scatter(
            x=[row["activos"]], y=[row["total"] / 1000],
            mode="markers+text",
            name=ciudad,
            text=[ciudad],
            textposition="top center",
            textfont=dict(size=9, color=color),
            marker=dict(size=size, color=color, line=dict(width=1, color="white")),
            showlegend=False,
            hovertemplate=f"<b>{ciudad}</b><br>Vendedores activos: {row['activos']}<br>Ventas: ${row['total']/1000:.1f}k USD<extra></extra>"
        ), row=1, col=1)

        # Scatter B – variedad de productos vs ventas
        fig.add_trace(go.Scatter(
            x=[row["n_productos"]], y=[row["total"] / 1000],
            mode="markers+text",
            name=ciudad,
            text=[ciudad],
            textposition="top center",
            textfont=dict(size=9, color=color),
            marker=dict(size=size, color=color, line=dict(width=1, color="white")),
            showlegend=False,
            hovertemplate=f"<b>{ciudad}</b><br>Productos distintos: {row['n_productos']}<br>Ventas: ${row['total']/1000:.1f}k USD<extra></extra>"
        ), row=1, col=2)

    # Líneas de tendencia simples
    import numpy as np
    for col_x, col_num in [("activos", 1), ("n_productos", 2)]:
        x = df[col_x].values.astype(float)
        y = (df["total"] / 1000).values
        m, b = np.polyfit(x, y, 1)
        x_line = np.linspace(x.min(), x.max(), 50)
        fig.add_trace(go.Scatter(
            x=x_line, y=m * x_line + b,
            mode="lines",
            line=dict(dash="dash", color=C_GRIS, width=1),
            showlegend=False,
        ), row=1, col=col_num)

    fig.update_xaxes(title_text="Vendedores activos", row=1, col=1)
    fig.update_xaxes(title_text="Productos distintos vendidos", row=1, col=2)
    fig.update_yaxes(title_text="Ventas totales (miles USD)", row=1, col=1)

    fig.update_layout(height=480)
    estilo_base(fig, "El Debate: ¿Qué Impulsa las Ventas?")
    fig.write_html(f"{OUT}/slide4_scatter.html")
    print("✓ slide4_scatter.html")


# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 5 – Radiografía de Bucaramanga (bar horizontal comparativa)
# ═══════════════════════════════════════════════════════════════════════════════
def slide5_radiografia():
    promedio = maestra[maestra["ciudad"] != "Bucaramanga"]

    buca = maestra[maestra["ciudad"] == "Bucaramanga"].iloc[0]
    prom = promedio.mean(numeric_only=True)

    metricas = {
        "Vendedores activos": (buca["activos"], prom["activos"]),
        "Rotación (bajas)":   (buca["rotacion"], prom["rotacion"]),
        "Productos distintos": (buca["n_productos"], prom["n_productos"]),
        "Ventas 2022 (k USD)": (buca["usd_2022"]/1000, prom["usd_2022"]/1000),
        "Ventas 2023 (k USD)": (buca["usd_2023"]/1000, prom["usd_2023"]/1000),
        "Ventas 2024 (k USD)": (buca["usd_2024"]/1000, prom["usd_2024"]/1000),
    }

    labels = list(metricas.keys())
    vals_buca = [v[0] for v in metricas.values()]
    vals_prom = [v[1] for v in metricas.values()]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Promedio otras sucursales",
        y=labels, x=vals_prom,
        orientation="h",
        marker_color=C_AZUL,
        text=[f"{v:.1f}" for v in vals_prom],
        textposition="outside",
    ))
    fig.add_trace(go.Bar(
        name="Bucaramanga",
        y=labels, x=vals_buca,
        orientation="h",
        marker_color=C_ROJO,
        text=[f"{v:.1f}" for v in vals_buca],
        textposition="outside",
    ))

    fig.update_layout(
        barmode="group",
        xaxis_title="Valor",
        legend=dict(orientation="h", y=1.05, x=0.5, xanchor="center"),
    )
    estilo_base(fig, "Radiografía: Bucaramanga vs Promedio de Otras Sucursales")
    fig.write_html(f"{OUT}/slide5_radiografia.html")
    print("✓ slide5_radiografia.html")


# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 6 – Pereira vs Bucaramanga: crecimiento y vendedores
# ═══════════════════════════════════════════════════════════════════════════════
def slide6_pereira_vs_buca():
    ciudades = ["Bucaramanga", "Pereira"]
    colores  = [C_ROJO, C_VERDE]

    mensuales = (
        tickets.groupby(["Sucursal ID", "mes"])["Precio Total (USD)"]
        .sum().reset_index()
        .merge(suc[["SUCURSAL_ID","ciudad"]], left_on="Sucursal ID", right_on="SUCURSAL_ID")
    )

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Evolución mensual de ventas", "Vendedores: activos vs rotación")
    )

    # Line chart mensual
    for ciudad, color in zip(ciudades, colores):
        d = mensuales[mensuales["ciudad"] == ciudad].sort_values("mes")
        fig.add_trace(go.Scatter(
            x=d["mes"], y=d["Precio Total (USD)"] / 1000,
            mode="lines+markers", name=ciudad,
            line=dict(color=color, width=3),
            marker=dict(size=6),
        ), row=1, col=1)

    # Bar chart vendedores
    vend_data = maestra[maestra["ciudad"].isin(ciudades)][["ciudad","activos","rotacion"]]
    for cat, color in [("activos", C_VERDE), ("rotacion", C_ROJO)]:
        label = "Activos" if cat == "activos" else "Bajas (rotación)"
        fig.add_trace(go.Bar(
            name=label,
            x=vend_data["ciudad"],
            y=vend_data[cat],
            marker_color=color,
            text=vend_data[cat],
            textposition="outside",
            showlegend=True,
        ), row=1, col=2)

    fig.update_xaxes(title_text="Mes", row=1, col=1)
    fig.update_yaxes(title_text="Ventas (miles USD)", row=1, col=1)
    fig.update_yaxes(title_text="Número de vendedores", row=1, col=2)
    fig.update_layout(barmode="group", height=460,
                      legend=dict(orientation="h", y=1.08, x=0.5, xanchor="center"))
    estilo_base(fig, "Pereira vs Bucaramanga: El Contraste")
    fig.write_html(f"{OUT}/slide6_pereira_buca.html")
    print("✓ slide6_pereira_buca.html")


# ═══════════════════════════════════════════════════════════════════════════════
# SLIDE 7 – Propuesta de acción (roadmap visual)
# ═══════════════════════════════════════════════════════════════════════════════
def slide7_roadmap():
    fases = [
        dict(
            fase="FASE 1", plazo="Mes 1–2", color=C_ROJO,
            titulo="Estabilizar el Equipo",
            acciones=[
                "Contratar 4–5 vendedores en Bucaramanga",
                "Programa de retención (bonos por permanencia)",
                "Capacitación intensiva al equipo actual",
            ],
            kpi="Meta: de 2 a 6+ vendedores activos",
        ),
        dict(
            fase="FASE 2", plazo="Mes 2–4", color=C_AMARILLO,
            titulo="Ampliar el Portafolio",
            acciones=[
                "Incorporar top 5 categorías de Bogotá/Cali",
                "Campañas de promoción agresivas",
                "Métricas semanales de tickets y conversión",
            ],
            kpi="Meta: 100+ productos / >$20k USD/mes",
        ),
        dict(
            fase="FASE 3", plazo="Mes 4–8", color=C_VERDE,
            titulo="Replicar y Expandir",
            acciones=[
                "Aplicar el modelo en Cartagena",
                "Benchmark mensual vs Pereira",
                "Evaluar Bucaramanga cada trimestre",
            ],
            kpi="Meta: Bucaramanga top 5 en 8 meses",
        ),
    ]

    # Usar un scatter vacío con annotations paper-referenced (sin flechas axref=paper)
    fig = go.Figure()

    # Rectángulos de fondo para cada fase
    xs = [0.15, 0.50, 0.85]
    shapes, annotations = [], []

    for i, (f, x) in enumerate(zip(fases, xs)):
        shapes.append(dict(
            type="rect", x0=x - 0.13, x1=x + 0.13, y0=0.05, y1=0.95,
            xref="paper", yref="paper",
            fillcolor=f["color"], opacity=0.12,
            line=dict(color=f["color"], width=2)
        ))
        texto = (
            f"<b style='font-size:14px'>{f['fase']}</b><br>"
            f"<span style='color:{f['color']}'>{f['plazo']}</span><br><br>"
            f"<b>{f['titulo']}</b><br><br>"
            + "<br>".join(f"• {a}" for a in f["acciones"])
            + f"<br><br><i>{f['kpi']}</i>"
        )
        annotations.append(dict(
            x=x, y=0.5, xref="paper", yref="paper",
            text=texto, showarrow=False,
            font=dict(size=12, color=C_TEXTO),
            align="left",
            bordercolor=f["color"], borderwidth=1, borderpad=10,
            bgcolor=C_TARJETA, width=220,
        ))

    # Flechas como formas (líneas con flecha) en coordenadas paper
    for x0, x1 in [(0.28, 0.37), (0.63, 0.72)]:
        shapes.append(dict(
            type="line", x0=x0, x1=x1, y0=0.5, y1=0.5,
            xref="paper", yref="paper",
            line=dict(color=C_GRIS, width=2),
        ))
        # Triángulo de flecha como marcador
        annotations.append(dict(
            x=x1, y=0.5, xref="paper", yref="paper",
            ax=-20, ay=0,
            showarrow=True, arrowhead=2, arrowwidth=2, arrowcolor=C_GRIS,
            text="",
        ))

    fig.update_layout(
        shapes=shapes, annotations=annotations,
        xaxis=dict(visible=False, range=[0, 1]),
        yaxis=dict(visible=False, range=[0, 1]),
        height=440,
    )
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers"))
    estilo_base(fig, "Propuesta de Acción: Primero Personas, Luego Portafolio")
    fig.write_html(f"{OUT}/slide7_roadmap.html")
    print("✓ slide7_roadmap.html")


# ═══════════════════════════════════════════════════════════════════════════════
# INDEX HTML – abre todos los slides desde un solo archivo
# ═══════════════════════════════════════════════════════════════════════════════
def generar_index():
    slides = [
        ("slide1_mapa.html",        "Slide 1 – Mapa: La alarma está encendida"),
        ("slide2_barras.html",      "Slide 2 – Ventas por sucursal 2022–2024"),
        ("slide3_lineas.html",      "Slide 3 – Evolución mensual de ventas"),
        ("slide4_scatter.html",     "Slide 4 – El debate: vendedores vs variedad"),
        ("slide5_radiografia.html", "Slide 5 – Radiografía de Bucaramanga"),
        ("slide6_pereira_buca.html","Slide 6 – Pereira vs Bucaramanga"),
        ("slide7_roadmap.html",     "Slide 7 – Propuesta de acción"),
    ]
    items = "\n".join(
        f'<li><a href="{fname}" target="_blank">{label}</a></li>'
        for fname, label in slides
    )
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>WirallesTEC – Presentación</title>
  <style>
    body {{ font-family: Inter, Arial, sans-serif; background: #1A1A2E; color: #F0F0F0;
            display: flex; flex-direction: column; align-items: center; padding: 40px; }}
    h1   {{ color: #A8DADC; margin-bottom: 6px; }}
    p    {{ color: #9E9E9E; margin-bottom: 30px; }}
    ul   {{ list-style: none; padding: 0; width: 500px; }}
    li   {{ margin: 12px 0; }}
    a    {{ display: block; padding: 14px 20px; background: #16213E;
            border: 1px solid #457B9D; border-radius: 8px; color: #A8DADC;
            text-decoration: none; font-size: 15px; transition: background 0.2s; }}
    a:hover {{ background: #457B9D; color: #F0F0F0; }}
  </style>
</head>
<body>
  <h1>WirallesTEC – Visualización para la Toma de Decisiones</h1>
  <p>Taller Final · Especialización en Analítica y Ciencia de Datos · Mayo 2026</p>
  <ul>{items}</ul>
</body>
</html>"""
    with open(f"{OUT}/index.html", "w") as f:
        f.write(html)
    print("✓ index.html")


# ── EJECUTAR TODO ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Generando gráficos WirallesTEC...\n")
    slide1_mapa()
    slide2_barras_agrupadas()
    slide3_lineas_temporales()
    slide4_scatter_debate()
    slide5_radiografia()
    slide6_pereira_vs_buca()
    slide7_roadmap()
    generar_index()
    print(f"\n✅ Todos los gráficos guardados en: {OUT}/")
    print("   Abre graficos/index.html en el navegador para verlos.")
