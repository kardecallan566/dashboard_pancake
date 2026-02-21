from dash import html, Input, Output
from dash import dcc
import plotly.express as px
import plotly.graph_objects as go
from utils import df, calculate_metrics
from typing import cast
import pandas as pd

options1 = [{'label': day, 'value': day} for day in df['day_of_week'].unique()] + [{'label': 'Todos', 'value': 'Todos'}]
options = cast(list[dict[str, str]], options1)

def calcular_intervalos_entre_acertos(df, coluna_alvo='acerto_sem_delta'):
    df = df.sort_values('timestamp')
    df_acertos = df[df[coluna_alvo] == True].copy()
    df_acertos['intervalo'] = df_acertos['timestamp'].diff().dt.total_seconds() / 60  # em minutos
    return df_acertos['intervalo'].dropna()

def contar_acertos_consecutivos_por(df, coluna_grupo, coluna_alvo):
    df_sorted = df.sort_values('timestamp')
    df_sorted['grupo'] = df_sorted[coluna_grupo]
    resultados = {}

    for grupo, grupo_df in df_sorted.groupby('grupo'):
        atual = None
        contador = 0
        sequencias = []
        for valor in grupo_df[coluna_alvo]:
            if valor == True:
                contador = contador + 1 if atual else 1
                atual = True
            else:
                if contador > 1:
                    sequencias.append(contador)
                contador = 0
                atual = False
        if contador > 1:
            sequencias.append(contador)
        resultados[grupo] = len(sequencias)
    return resultados

def contar_sequencias_com_intervalo_fixo(df, coluna_alvo='acerto_sem_delta', intervalos=[5, 10, 15, 30, 60]):
    df = df.sort_values('timestamp')
    acertos = df[df[coluna_alvo] == True].copy()
    acertos['timestamp'] = pd.to_datetime(acertos['timestamp'])
    
    resultados = []

    for intervalo in intervalos:
        intervalo_td = pd.Timedelta(minutes=intervalo)
        sequencias = 0
        i = 0

        while i < len(acertos) - 1:
            count = 1
            while (i + count < len(acertos)) and (acertos.iloc[i + count]['timestamp'] - acertos.iloc[i + count - 1]['timestamp'] == intervalo_td):
                count += 1
            if count > 1:
                sequencias += 1
                i = i + count  # pula toda a sequência
            else:
                i += 1
        resultados.append({'intervalo_min': intervalo, 'quantidade': sequencias})
    
    return pd.DataFrame(resultados)

def layout():
    return html.Div([
        html.H1('Análise por Hora e Dia', className='text-4xl font-bold text-blue-400 mb-6'),
        dcc.Dropdown(
            id='day-filter',
            options=options,
            value='Todos',
            className='bg-gray-700 text-white p-2 rounded-lg w-1/2 mb-4'
        ),
        html.Button('Exportar Dados', id='export-button', className='neon-button text-white font-bold py-2 px-4 rounded mb-4'),
        html.H2('Taxa de Acerto por Hora', className='text-xl font-semibold mb-2 text-blue-300'),
        html.Div(className='loading-spinner', id='loading-hourly', style={'display': 'none'}),
        dcc.Graph(id='hourly-accuracy'),
        html.H2('Taxa de Acerto por Dia da Semana', className='text-xl font-semibold mb-2 text-blue-300'),
        html.Div(className='loading-spinner', id='loading-daily', style={'display': 'none'}),
        dcc.Graph(id='daily-accuracy'),
        html.H2('Taxa de Acerto por Período do Dia', className='text-xl font-semibold mb-2 text-blue-300'),
        html.Div(className='loading-spinner', id='loading-period', style={'display': 'none'}),
        dcc.Graph(id='period-accuracy'),
        html.H2('Taxa de Acerto por Hora e Dia', className='text-xl font-semibold mb-2 text-blue-300'),
        html.Div(className='loading-spinner', id='loading-heatmap', style={'display': 'none'}),
        dcc.Graph(id='hour-day-heatmap'),
        html.H2('Sequência de Acertos por Hora', className='text-xl font-semibold mb-2 text-blue-300'),
        dcc.Graph(id='sequencia-hora'),

        html.H2('Sequência de Acertos por Dia da Semana', className='text-xl font-semibold mb-2 text-blue-300'),
        dcc.Graph(id='sequencia-dia'),
        html.H2('Intervalos Entre Acertos (Sem Delta)', className='text-xl font-semibold mb-2 text-blue-300'),
        dcc.Graph(id='intervalo-acertos'),
        html.H2('Acertos por Intervalo de Tempo Fixo (10 minutos)', className='text-xl font-semibold mb-2 text-blue-300'),
        dcc.Graph(id='acertos-por-janela'),
        html.H2('Sequências com Intervalo Fixo Entre Acertos (Sem Delta)', className='text-xl font-semibold mb-2 text-blue-300'),
        dcc.Graph(id='sequencia-fixa'),
    ])

def register_callbacks(app):
    @app.callback(
            [
        Output('hourly-accuracy', 'figure'),
        Output('daily-accuracy', 'figure'),
        Output('period-accuracy', 'figure'),
        Output('hour-day-heatmap', 'figure'),
        Output('sequencia-hora', 'figure'),
        Output('sequencia-dia', 'figure'),
        Output('intervalo-acertos', 'figure'),
        Output('acertos-por-janela', 'figure'),
        Output('sequencia-fixa', 'figure'),
        Output('loading-hourly', 'style'),
        Output('loading-daily', 'style'),
        Output('loading-period', 'style'),
        Output('loading-heatmap', 'style'),
        

    ],
    [Input('day-filter', 'value')]
)
    def update_hour_day(day):
        filtered_df = df if day == 'Todos' else df[df['day_of_week'] == day]
        hourly_metrics = calculate_metrics(filtered_df, 'hour')
        daily_metrics = calculate_metrics(filtered_df, 'day_of_week')
        period_metrics = calculate_metrics(filtered_df, 'period_of_day', categorical=True)

        hourly_fig = go.Figure()
        hourly_fig.add_trace(go.Bar(
            x=hourly_metrics['hour'],
            y=hourly_metrics['taxa_acerto_sem_delta'],
            name='Sem Delta',
            marker_color='#3B82F6',
            hovertemplate='Hora: %{x}<br>Taxa: %{y:.2f}%<extra></extra>'
        ))
        hourly_fig.add_trace(go.Bar(
            x=hourly_metrics['hour'],
            y=hourly_metrics['taxa_acerto_com_delta'],
            name='Com Delta',
            marker_color='#10B981',
            hovertemplate='Hora: %{x}<br>Taxa: %{y:.2f}%<extra></extra>'
        ))
        hourly_fig.update_layout(
            title='Taxa de Acerto por Hora do Dia',
            xaxis_title='Hora',
            yaxis_title='Taxa de Acerto (%)',
            barmode='group',
            template='plotly_dark',
            hovermode='x unified'
        )

        daily_fig = go.Figure()
        daily_fig.add_trace(go.Bar(
            x=daily_metrics['day_of_week'],
            y=daily_metrics['taxa_acerto_sem_delta'],
            name='Sem Delta',
            marker_color='#3B82F6',
            hovertemplate='Dia: %{x}<br>Taxa: %{y:.2f}%<extra></extra>'
        ))
        daily_fig.add_trace(go.Bar(
            x=daily_metrics['day_of_week'],
            y=daily_metrics['taxa_acerto_com_delta'],
            name='Com Delta',
            marker_color='#10B981',
            hovertemplate='Dia: %{x}<br>Taxa: %{y:.2f}%<extra></extra>'
        ))
        daily_fig.update_layout(
            title='Taxa de Acerto por Dia da Semana',
            xaxis_title='Dia da Semana',
            yaxis_title='Taxa de Acerto (%)',
            barmode='group',
            template='plotly_dark',
            hovermode='x unified'
        )

        period_fig = go.Figure()
        period_fig.add_trace(go.Bar(
            x=period_metrics['period_of_day'],
            y=period_metrics['taxa_acerto_sem_delta'],
            name='Sem Delta',
            marker_color='#3B82F6',
            hovertemplate='Período: %{x}<br>Taxa: %{y:.2f}%<extra></extra>'
        ))
        period_fig.add_trace(go.Bar(
            x=period_metrics['period_of_day'],
            y=period_metrics['taxa_acerto_com_delta'],
            name='Com Delta',
            marker_color='#10B981',
            hovertemplate='Período: %{x}<br>Taxa: %{y:.2f}%<extra></extra>'
        ))
        period_fig.update_layout(
            title='Taxa de Acerto por Período do Dia',
            xaxis_title='Período do Dia',
            yaxis_title='Taxa de Acerto (%)',
            barmode='group',
            template='plotly_dark',
            hovermode='x unified'
        )

        heatmap_data = filtered_df.pivot_table(
            values='acerto_sem_delta',
            index='day_of_week',
            columns='hour',
            aggfunc='mean'
        ) * 100
        heatmap_fig = px.imshow(
            heatmap_data,
            title='Taxa de Acerto por Hora e Dia',
            labels={'color': 'Taxa de Acerto (%)', 'hour': 'Hora', 'day_of_week': 'Dia da Semana'},
            template='plotly_dark',
            color_continuous_scale='Plasma',
            text_auto='.1f'
        )
        # Acertos consecutivos por hora
        hora_sem = contar_acertos_consecutivos_por(filtered_df, 'hour', 'acerto_sem_delta')
        hora_com = contar_acertos_consecutivos_por(filtered_df, 'hour', 'acerto_com_delta')

        sequencia_hora_fig = go.Figure()
        sequencia_hora_fig.add_trace(go.Bar(
            x=list(hora_sem.keys()),
            y=list(hora_sem.values()),
            name='Sem Delta',
            marker_color='#3B82F6'
        ))
        sequencia_hora_fig.add_trace(go.Bar(
            x=list(hora_com.keys()),
            y=list(hora_com.values()),
            name='Com Delta',
            marker_color='#10B981'
        ))
        sequencia_hora_fig.update_layout(
            title='Sequência de Acertos por Hora',
            xaxis_title='Hora',
            yaxis_title='Quantidade de Sequências',
            barmode='group',
            template='plotly_dark'
        )

        # Acertos consecutivos por dia da semana
        dia_sem = contar_acertos_consecutivos_por(filtered_df, 'day_of_week', 'acerto_sem_delta')
        dia_com = contar_acertos_consecutivos_por(filtered_df, 'day_of_week', 'acerto_com_delta')

        sequencia_dia_fig = go.Figure()
        sequencia_dia_fig.add_trace(go.Bar(
            x=list(dia_sem.keys()),
            y=list(dia_sem.values()),
            name='Sem Delta',
            marker_color='#3B82F6'
        ))
        sequencia_dia_fig.add_trace(go.Bar(
            x=list(dia_com.keys()),
            y=list(dia_com.values()),
            name='Com Delta',
            marker_color='#10B981'
        ))
        sequencia_dia_fig.update_layout(
            title='Sequência de Acertos por Dia da Semana',
            xaxis_title='Dia da Semana',
            yaxis_title='Quantidade de Sequências',
            barmode='group',
            template='plotly_dark'
        )
        # Cálculo do intervalo entre acertos SEM DELTA
        intervalos_sem = df[df['acerto_sem_delta'] == True].copy()
        intervalos_sem['intervalo'] = intervalos_sem['timestamp'].diff().dt.total_seconds() / 60
        intervalos_sem = intervalos_sem.dropna()
        intervalos_sem = intervalos_sem[intervalos_sem['intervalo'] > 0]

        # Cálculo do intervalo entre acertos COM DELTA
        intervalos_com = df[df['acerto_com_delta'] == True].copy()
        intervalos_com['intervalo'] = intervalos_com['timestamp'].diff().dt.total_seconds() / 60
        intervalos_com = intervalos_com.dropna()
        intervalos_com = intervalos_com[intervalos_com['intervalo'] > 0]

        # Gráfico combinado
        intervalo_fig = go.Figure()

        intervalo_fig.add_trace(go.Bar(
            x=intervalos_sem['timestamp'],
            y=intervalos_sem['intervalo'],
            name='Sem Delta',
            marker=dict(color='#F59E0B'),
            hovertemplate='Data: %{x}<br>Minutos: %{y:.2f}<extra></extra>'
        ))

        intervalo_fig.add_trace(go.Bar(
            x=intervalos_com['timestamp'],
            y=intervalos_com['intervalo'],
            name='Com Delta',
            marker=dict(color='#10B981'),
            hovertemplate='Data: %{x}<br>Minutos: %{y:.2f}<extra></extra>'
        ))

        intervalo_fig.update_layout(
            title='Tempo entre Acertos (Sem e Com Delta)',
            xaxis_title='Data',
            yaxis_title='Intervalo (minutos)',
            barmode='group',  # barras lado a lado
            template='plotly_dark',
            hovermode='x unified',
            legend=dict(x=0.01, y=0.99, bgcolor='rgba(0,0,0,0)')
        )
                # Defina o intervalo de tempo fixo (em minutos)
        intervalo_minutos = 15
        intervalo_tempo = f'{intervalo_minutos}min'

        # Usar a cópia do DataFrame filtrado para segurança
        df_intervalado = filtered_df.copy()
        df_intervalado = df_intervalado.set_index('timestamp')
        df_intervalado = df_intervalado.sort_index()

        # Arredonda os timestamps para o intervalo desejado
        df_intervalado['janela'] = df_intervalado.index.floor(intervalo_tempo)

        # Conta acertos SEM DELTA
        contagem_sem = df_intervalado[df_intervalado['acerto_sem_delta'] == True].groupby('janela').size().reset_index(name='acertos_sem_delta')

        # Conta acertos COM DELTA
        contagem_com = df_intervalado[df_intervalado['acerto_com_delta'] == True].groupby('janela').size().reset_index(name='acertos_com_delta')

        # Merge
        contagem_total = pd.merge(contagem_sem, contagem_com, on='janela', how='outer').fillna(0)

        # Gráfico
        acertos_intervalo_fig = go.Figure()
        acertos_intervalo_fig.add_trace(go.Bar(
            x=contagem_total['janela'],
            y=contagem_total['acertos_sem_delta'],
            name='Sem Delta',
            marker_color='#3B82F6'
        ))
        acertos_intervalo_fig.add_trace(go.Bar(
            x=contagem_total['janela'],
            y=contagem_total['acertos_com_delta'],
            name='Com Delta',
            marker_color='#10B981'
        ))
        acertos_intervalo_fig.update_layout(
            title=f'Quantidade de Acertos a Cada {intervalo_minutos} Minutos',
            xaxis_title='Janela de Tempo',
            yaxis_title='Quantidade de Acertos',
            barmode='group',
            template='plotly_dark',
            hovermode='x unified'
        )
        sequencias_df = contar_sequencias_com_intervalo_fixo(filtered_df, 'acerto_sem_delta')

        fig_intervalos_fixos = go.Figure()
        fig_intervalos_fixos.add_trace(go.Bar(
            x=sequencias_df['intervalo_min'],
            y=sequencias_df['quantidade'],
            name='Sem Delta',
            marker_color='#3B82F6'
        ))
        fig_intervalos_fixos.update_layout(
            title='Quantidade de Sequências com Intervalo Fixo Entre Acertos (Sem Delta)',
            xaxis_title='Intervalo Fixo (min)',
            yaxis_title='Quantidade de Sequências',
            template='plotly_dark'
        )


        return (
    hourly_fig, daily_fig, period_fig, heatmap_fig,
    sequencia_hora_fig, sequencia_dia_fig,intervalo_fig,acertos_intervalo_fig,
    {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}
)