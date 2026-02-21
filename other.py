from dash import html, dcc, Input, Output
import plotly.graph_objects as go
from utils import df
import pandas as pd
from typing import cast

# ==============================
# IDs PREFIXADOS (evita conflito multipágina)
# ==============================

ID_PREFIX = "hourday"

def pid(name: str):
    return f"{ID_PREFIX}-{name}"

# ==============================
# DROPDOWN OPTIONS
# ==============================

options1 = [{'label': day, 'value': day} for day in df['day_of_week'].unique()]
options1.append({'label': 'Todos', 'value': 'Todos'})
options = cast(list[dict[str, str]], options1)

# ==============================
# LAYOUT
# ==============================

def layout():
    return html.Div([
        html.H1('Análise por Hora e Dia', className='text-4xl font-bold text-blue-400 mb-6'),

        dcc.Dropdown(
            id=pid('day-filter'),
            options=options,
            value='Todos',
            className='bg-gray-700 text-white p-2 rounded-lg w-1/2 mb-4'
        ),

        dcc.Graph(id=pid('hourly-accuracy')),
        dcc.Graph(id=pid('daily-accuracy')),
        dcc.Graph(id=pid('hourly-taxa')),
        dcc.Graph(id=pid('daily-taxa')),
        dcc.Graph(id=pid('heatmap')),
    ])

# ==============================
# CALLBACK
# ==============================

def register_callbacks(app):

    @app.callback(
        Output(pid('hourly-accuracy'), 'figure'),
        Output(pid('daily-accuracy'), 'figure'),
        Output(pid('hourly-taxa'), 'figure'),
        Output(pid('daily-taxa'), 'figure'),
        Output(pid('heatmap'), 'figure'),
        Input(pid('day-filter'), 'value')
    )
    def update_hour_day(day):

        filtered_df = df if day == 'Todos' else df[df['day_of_week'] == day]
        filtered_df = filtered_df.copy()
        filtered_df['timestamp'] = pd.to_datetime(filtered_df['timestamp'])

        # Criar coluna semana ISO
        filtered_df['week'] = filtered_df['timestamp'].dt.isocalendar().week

        # ==========================================
        # 1️⃣ ACERTOS POR HORA (SEPARADO POR SEMANA)
        # ==========================================

        acertos_hora_semana = (
            filtered_df[filtered_df['acerto_sem_delta'] == True]
            .groupby(['week', 'hour'])
            .size()
            .reset_index(name='quantidade')
        )

        hourly_fig = go.Figure()

        for semana in sorted(acertos_hora_semana['week'].unique()):
            df_semana = acertos_hora_semana[acertos_hora_semana['week'] == semana]

            hourly_fig.add_trace(go.Bar(
                x=df_semana['hour'],
                y=df_semana['quantidade'],
                name=f'Semana {semana}'
            ))

        hourly_fig.update_layout(
            title='Quantidade de Acertos por Hora (Separado por Semana)',
            xaxis_title='Hora',
            yaxis_title='Quantidade de Acertos',
            barmode='group',
            template='plotly_dark'
        )

        # ==========================================
        # 2️⃣ ACERTOS POR DIA DA SEMANA
        # ==========================================

        acertos_dia = (
            filtered_df[filtered_df['acerto_sem_delta'] == True]
            .groupby('day_of_week')
            .size()
            .reset_index(name='quantidade')
        )

        daily_fig = go.Figure()

        daily_fig.add_trace(go.Bar(
            x=acertos_dia['day_of_week'],
            y=acertos_dia['quantidade'],
            marker_color='#3B82F6'
        ))

        daily_fig.update_layout(
            title='Quantidade de Acertos por Dia da Semana',
            xaxis_title='Dia da Semana',
            yaxis_title='Quantidade',
            template='plotly_dark'
        )

        taxa_hora = (
            filtered_df
            .groupby('hour')
            .agg(
                total_operacoes=('acerto_sem_delta', 'count'),
                total_acertos=('acerto_sem_delta', 'sum')
            )
            .reset_index()
        )

        taxa_hora['taxa_acerto'] = (
            taxa_hora['total_acertos'] / taxa_hora['total_operacoes']
        ) * 100

        fig_hour = go.Figure()

        fig_hour.add_trace(go.Bar(
            x=taxa_hora['hour'],
            y=taxa_hora['taxa_acerto'],
        ))

        fig_hour.update_layout(
            title='Taxa de Acerto (%) por Hora',
            xaxis_title='Hora',
            yaxis_title='Taxa de Acerto (%)',
            template='plotly_dark'
        )
        taxa_dia = (
            filtered_df
            .groupby('day_of_week')
            .agg(
                total_operacoes=('acerto_sem_delta', 'count'),
                total_acertos=('acerto_sem_delta', 'sum')
            )
            .reset_index()
        )

        taxa_dia['taxa_acerto'] = (
            taxa_dia['total_acertos'] / taxa_dia['total_operacoes']
        ) * 100

        fig_day = go.Figure()

        fig_day.add_trace(go.Bar(
            x=taxa_dia['day_of_week'],
            y=taxa_dia['taxa_acerto'],
        ))

        fig_day.update_layout(
            title='Taxa de Acerto (%) por Dia da Semana',
            xaxis_title='Dia da Semana',
            yaxis_title='Taxa de Acerto (%)',
            template='plotly_dark'
        )

        heatmap_df = (
            filtered_df
            .groupby(['day_of_week', 'hour'])
            .agg(
                total=('acerto_sem_delta', 'count'),
                acertos=('acerto_sem_delta', 'sum')
            )
            .reset_index()
        )

        heatmap_df['taxa'] = (heatmap_df['acertos'] / heatmap_df['total']) * 100

        pivot = heatmap_df.pivot(
            index='day_of_week',
            columns='hour',
            values='taxa'
        )

        fig_heat = go.Figure(
            data=go.Heatmap(
                z=pivot.values,
                x=pivot.columns,
                y=pivot.index,
                colorscale='Viridis'
            )
        )

        fig_heat.update_layout(
            title='Heatmap Taxa de Acerto (%) - Hora x Dia',
            template='plotly_dark'
        )

        return hourly_fig, daily_fig, fig_hour,fig_day, fig_heat