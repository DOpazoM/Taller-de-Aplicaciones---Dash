
import pandas as pd
import numpy as np
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
from sklearn.cluster import KMeans
import zipfile


# Leer Archivo en formato .ZIP
with zipfile.ZipFile('11OCLicitacion.zip', 'r') as zip_ref:
    with zip_ref.open('11OCLicitacion.csv') as archivo:
        df_dash = pd.read_csv(
            archivo,
            encoding='latin1',
            sep=';'
        )

# Convertir Variables numéricas que vienen como texto
columnas_numericas = [
    'MontoNetoOC',
    'DescuentosOC',
    'CargosOC',
    'ImpuestosOC',
    'MontoTotalOC',
    'ImpuestosOC_CLP',
    'MontoNetoOC_CLP',
    'CantidadItem',
    'MontoNetoItem',
    'DescuentoItem',
    'MontoTotalItem',
    'MontoNetoItemCLP'
]

for col in columnas_numericas:
    df_dash[col] = (
        df_dash[col]
        .astype(str)
        .str.replace('.', '', regex=False)
        .str.replace(',', '.', regex=False)
    )

    df_dash[col] = pd.to_numeric(
        df_dash[col],
        errors='coerce'
    )

# Convertir a formato fecha variables que vienen como texto

df_dash['FechaEnvioOC'] = pd.to_datetime(
    df_dash['FechaEnvioOC'],
    errors='coerce'
)

# Agregar Variables Calendario

df_dash['Año'] = df_dash['FechaEnvioOC'].dt.year

df_dash['Mes'] = df_dash['FechaEnvioOC'].dt.month

df_dash['MesNombre'] = df_dash['FechaEnvioOC'].dt.strftime('%b')

df_dash['AñoMes'] = df_dash['FechaEnvioOC'].dt.to_period('M').astype(str)

# Cracion de Aplicacion
app = Dash(__name__)
server = app.server

# Cracion de Indicadores

total_oc = df_dash['codigoOC'].nunique()

monto_total = df_dash['MontoNetoOC_CLP'].sum()

total_proveedores = df_dash['ProveedorRUT'].nunique()

total_instituciones = df_dash['UnidadCompraRUT'].nunique()

print("Órdenes:", total_oc)
print("Monto:", monto_total)
print("Proveedores:", total_proveedores)
print("Instituciones:", total_instituciones)

# Evoluciones de compras
df_temporal = (
    df_dash
    .groupby('AñoMes')
    .agg(
        Monto=('MontoNetoOC_CLP', 'sum'),
        Ordenes=('codigoOC', 'nunique')
    )
    .reset_index()
)

fig_evolucion = px.line(
    df_temporal,
    x='AñoMes',
    y='Monto',
    markers=True,
    title='Evolución mensual del monto de compras'
)

# Compras por region
df_region = (
    df_dash
    .groupby('RegionUnidadCompra')
    .agg(
        Monto=('MontoNetoOC_CLP', 'sum'),
        Ordenes=('codigoOC', 'nunique')
    )
    .reset_index()
    .sort_values('Monto', ascending=False)
)

fig_region = px.bar(
    df_region.head(15),
    x='RegionUnidadCompra',
    y='Monto',
    title='Monto de compras por región'
)

# Top Proovedores
df_proveedores = (
    df_dash
    .groupby('Proveedor')
    .agg(
        Monto=('MontoNetoOC_CLP', 'sum'),
        Ordenes=('codigoOC', 'nunique')
    )
    .reset_index()
    .sort_values('Monto', ascending=False)
)

fig_proveedores = px.bar(
    df_proveedores.head(10),
    x='Monto',
    y='Proveedor',
    orientation='h',
    title='Top 10 proveedores por monto'
)

# Compras por sectores
df_sector = (
    df_dash
    .groupby('Sector')
    .agg(
        Monto=('MontoNetoOC_CLP', 'sum'),
        Ordenes=('codigoOC', 'nunique')
    )
    .reset_index()
    .sort_values('Monto', ascending=False)
)

fig_sector = px.bar(
    df_sector,
    x='Sector',
    y='Monto',
    title='Compras por sector'
)

# Estados de las Ordenes
df_estado = (
    df_dash['EstadoOC']
    .value_counts()
    .reset_index()
)

df_estado.columns = ['Estado', 'Cantidad']

fig_estado = px.pie(
    df_estado,
    names='Estado',
    values='Cantidad',
    title='Estado de las órdenes de compra'
)

# Cracion de Layout
app.layout = html.Div([

    html.H1(
        "Dashboard de Órdenes de Compra",
        style={
            'textAlign': 'center'
        }
    ),

    html.Hr(),

    # ==========================
    # FILTROS
    # ==========================

    html.Div([

        html.Div([
            html.Label("Región"),

            dcc.Dropdown(
                id='filtro-region',
                options=[
                    {
                        'label': x,
                        'value': x
                    }
                    for x in sorted(
                        df_dash['RegionUnidadCompra']
                        .dropna()
                        .unique()
                    )
                ],
                multi=True,
                placeholder="Seleccione región"
            )

        ], style={
            'width': '24%',
            'display': 'inline-block',
            'marginRight': '1%'
        }),

        html.Div([

            html.Label("Sector"),

            dcc.Dropdown(
                id='filtro-sector',
                options=[
                    {
                        'label': x,
                        'value': x
                    }
                    for x in sorted(
                        df_dash['Sector']
                        .dropna()
                        .unique()
                    )
                ],
                multi=True,
                placeholder="Seleccione sector"
            )

        ], style={
            'width': '24%',
            'display': 'inline-block',
            'marginRight': '1%'
        }),

        html.Div([

            html.Label("Estado"),

            dcc.Dropdown(
                id='filtro-estado',
                options=[
                    {
                        'label': x,
                        'value': x
                    }
                    for x in sorted(
                        df_dash['EstadoOC']
                        .dropna()
                        .unique()
                    )
                ],
                multi=True,
                placeholder="Seleccione estado"
            )

        ], style={
            'width': '24%',
            'display': 'inline-block',
            'marginRight': '1%'
        }),

        html.Div([

            html.Label("Tamaño proveedor"),

            dcc.Dropdown(
                id='filtro-tamano',
                options=[
                    {
                        'label': x,
                        'value': x
                    }
                    for x in sorted(
                        df_dash['TamanoProveedor']
                        .dropna()
                        .unique()
                    )
                ],
                multi=True,
                placeholder="Seleccione tamaño"
            )

        ], style={
            'width': '24%',
            'display': 'inline-block'
        })

    ]),

    html.Br(),

    # ==========================
    # INDICADORES
    # ==========================

    html.Div([

        html.Div([
            html.H4("Órdenes de compra"),
            html.H2(id='kpi-ordenes')
        ], style={
            'width': '23%',
            'display': 'inline-block',
            'textAlign': 'center'
        }),

        html.Div([
            html.H4("Monto total"),
            html.H2(id='kpi-monto')
        ], style={
            'width': '23%',
            'display': 'inline-block',
            'textAlign': 'center'
        }),

        html.Div([
            html.H4("Proveedores"),
            html.H2(id='kpi-proveedores')
        ], style={
            'width': '23%',
            'display': 'inline-block',
            'textAlign': 'center'
        }),

        html.Div([
            html.H4("Instituciones"),
            html.H2(id='kpi-instituciones')
        ], style={
            'width': '23%',
            'display': 'inline-block',
            'textAlign': 'center'
        })

    ]),

    html.Hr(),

    # ==========================
    # GRÁFICOS
    # ==========================

    html.Div([

        dcc.Graph(
            id='grafico-evolucion'
        )

    ]),

    html.Div([

        html.Div([
            dcc.Graph(
                id='grafico-region'
            )
        ], style={
            'width': '49%',
            'display': 'inline-block'
        }),

        html.Div([
            dcc.Graph(
                id='grafico-sector'
            )
        ], style={
            'width': '49%',
            'display': 'inline-block'
        })

    ]),

    html.Div([

        html.Div([
            dcc.Graph(
                id='grafico-proveedores'
            )
        ], style={
            'width': '49%',
            'display': 'inline-block'
        }),

        html.Div([
            dcc.Graph(
                id='grafico-estado'
            )
        ], style={
            'width': '49%',
            'display': 'inline-block'
        })

    ])

])

@app.callback(

    Output('kpi-ordenes', 'children'),
    Output('kpi-monto', 'children'),
    Output('kpi-proveedores', 'children'),
    Output('kpi-instituciones', 'children'),

    Output('grafico-evolucion', 'figure'),
    Output('grafico-region', 'figure'),
    Output('grafico-sector', 'figure'),
    Output('grafico-proveedores', 'figure'),
    Output('grafico-estado', 'figure'),

    Input('filtro-region', 'value'),
    Input('filtro-sector', 'value'),
    Input('filtro-estado', 'value'),
    Input('filtro-tamano', 'value')

)
def actualizar_dashboard(
    regiones,
    sectores,
    estados,
    tamanos
):

    datos = df_dash.copy()

    # ==========================
    # FILTROS
    # ==========================

    if regiones:
        datos = datos[
            datos['RegionUnidadCompra'].isin(regiones)
        ]

    if sectores:
        datos = datos[
            datos['Sector'].isin(sectores)
        ]

    if estados:
        datos = datos[
            datos['EstadoOC'].isin(estados)
        ]

    if tamanos:
        datos = datos[
            datos['TamanoProveedor'].isin(tamanos)
        ]

    # ==========================
    # KPIs
    # ==========================

    ordenes = datos['codigoOC'].nunique()

    monto = datos['MontoNetoOC_CLP'].sum()

    proveedores = datos['ProveedorRUT'].nunique()

    instituciones = datos['UnidadCompraRUT'].nunique()

    # ==========================
    # EVOLUCIÓN
    # ==========================

    temporal = (
        datos
        .groupby('AñoMes')
        .agg(
            Monto=('MontoNetoOC_CLP', 'sum')
        )
        .reset_index()
    )

    fig_evolucion = px.line(
        temporal,
        x='AñoMes',
        y='Monto',
        markers=True,
        title='Evolución mensual de compras'
    )

    # ==========================
    # REGIONES
    # ==========================

    region = (
        datos
        .groupby('RegionUnidadCompra')
        .agg(
            Monto=('MontoNetoOC_CLP', 'sum')
        )
        .reset_index()
        .sort_values(
            'Monto',
            ascending=False
        )
        .head(15)
    )

    fig_region = px.bar(
        region,
        x='RegionUnidadCompra',
        y='Monto',
        title='Monto por región'
    )

    # ==========================
    # SECTOR
    # ==========================

    sector = (
        datos
        .groupby('Sector')
        .agg(
            Monto=('MontoNetoOC_CLP', 'sum')
        )
        .reset_index()
        .sort_values(
            'Monto',
            ascending=False
        )
    )

    fig_sector = px.bar(
        sector,
        x='Sector',
        y='Monto',
        title='Monto por sector'
    )

    # ==========================
    # PROVEEDORES
    # ==========================

    proveedores_df = (
        datos
        .groupby('Proveedor')
        .agg(
            Monto=('MontoNetoOC_CLP', 'sum')
        )
        .reset_index()
        .sort_values(
            'Monto',
            ascending=False
        )
        .head(10)
    )

    fig_proveedores = px.bar(
        proveedores_df,
        x='Monto',
        y='Proveedor',
        orientation='h',
        title='Top 10 proveedores'
    )

    # ==========================
    # ESTADOS
    # ==========================

    estado = (
        datos['EstadoOC']
        .value_counts()
        .reset_index()
    )

    estado.columns = [
        'Estado',
        'Cantidad'
    ]

    fig_estado = px.pie(
        estado,
        names='Estado',
        values='Cantidad',
        title='Estado de órdenes'
    )

    # ==========================
    # RETORNAR
    # ==========================

    return (

        f"{ordenes:,}",

        f"${monto:,.0f}",

        f"{proveedores:,}",

        f"{instituciones:,}",

        fig_evolucion,

        fig_region,

        fig_sector,

        fig_proveedores,

        fig_estado

    )

import os

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8050)),
        debug=False
    )
