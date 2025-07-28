from dash import html, dcc, Input, Output
import plotly.graph_objects as go
from utils import df, calculate_metrics
import pandas as pd

# Define os DataFrames
acertos_sem = df[df['acerto_sem_delta'] == True].copy().sort_values('timestamp')
acertos_com = df[df['acerto_com_delta'] == True].copy().sort_values('timestamp')

# Função para calcular blocos de acertos
def calcular_blocos(acertos, limite_bloco=10):
    acertos = acertos.reset_index(drop=True)
    blocos, bloco_atual = [], [acertos.loc[0]]

    for i in range(1, len(acertos)):
        anterior = acertos.loc[i - 1, 'timestamp']
        atual = acertos.loc[i, 'timestamp']
        intervalo = (atual - anterior).total_seconds() / 60

        if intervalo <= limite_bloco:
            bloco_atual.append(acertos.loc[i])
        else:
            blocos.append(bloco_atual)
            bloco_atual = [acertos.loc[i]]

    if bloco_atual:
        blocos.append(bloco_atual)

    blocos_data = []
    ultimo_fim = None

    for bloco in blocos:
        inicio = bloco[0]['timestamp']
        fim = bloco[-1]['timestamp']
        quantidade = len(bloco)
        tempo_entre_blocos = (inicio - ultimo_fim).total_seconds() / 60 if ultimo_fim else 0
        blocos_data.append({
            'inicio_bloco': inicio,
            'fim_bloco': fim,
            'acertos': quantidade,
            'espera_min': tempo_entre_blocos
        })
        ultimo_fim = fim

    df_blocos = pd.DataFrame(blocos_data)
    df_blocos['acertos_acumulados'] = df_blocos['acertos'].cumsum()
    return df_blocos

df_blocos_sem = calcular_blocos(acertos_sem)
df_blocos_com = calcular_blocos(acertos_com)

def layout():
    return html.Div([
        html.H1('Análise Temporal', className='text-4xl font-bold text-blue-400 mb-6'),
        dcc.DatePickerRange(
            id='date-range',
            min_date_allowed=df['timestamp'].min(),
            max_date_allowed=df['timestamp'].max(),
            initial_visible_month=df['timestamp'].min(),
            start_date=df['timestamp'].min(),
            end_date=df['timestamp'].max(),
            className='bg-gray-700 text-white p-2 rounded-lg mb-4'
        ),
        html.Button('Exportar Dados', id='export-button', className='neon-button text-white font-bold py-2 px-4 rounded mb-4'),

        html.H2('Evolução Temporal da Taxa de Acerto', className='text-xl font-semibold mb-2 text-blue-300'),
        dcc.Graph(id='temporal-accuracy'),

        html.H2('Série Temporal de Preços', className='text-xl font-semibold mb-2 text-blue-300'),
        dcc.Graph(id='price-series'),

        html.H2('Intervalo entre Acertos (Sem Delta)', className='text-xl font-semibold mb-2 text-yellow-300'),
        dcc.Graph(id='intervalo-sem'),

        html.H2('Intervalo entre Acertos (Com Delta)', className='text-xl font-semibold mb-2 text-green-300'),
        dcc.Graph(id='intervalo-com'),

        html.H2('Blocos de Acertos (Acertos por Grupo)', className='text-xl font-semibold mb-2 text-purple-300'),
        dcc.Graph(id='blocos-grafico')
    ])

def register_callbacks(app):
    @app.callback(
        [Output('temporal-accuracy', 'figure'),
         Output('price-series', 'figure'),
         Output('intervalo-sem', 'figure'),
         Output('intervalo-com', 'figure'),
         Output('blocos-grafico', 'figure')],
        [Input('date-range', 'start_date'),
         Input('date-range', 'end_date')]
    )
    def update_graficos(start_date, end_date):
        filtered_df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]

        # Temporal accuracy
        temporal_metrics = filtered_df.groupby(filtered_df['timestamp'].dt.date).agg({
            'acerto_sem_delta': 'mean',
            'acerto_com_delta': 'mean'
        }).reset_index()
        temporal_metrics['acerto_sem_delta'] *= 100
        temporal_metrics['acerto_com_delta'] *= 100

        temporal_fig = go.Figure()
        temporal_fig.add_trace(go.Scatter(
            x=temporal_metrics['timestamp'],
            y=temporal_metrics['acerto_sem_delta'],
            name='Sem Delta',
            line=dict(color='#3B82F6')
        ))
        temporal_fig.add_trace(go.Scatter(
            x=temporal_metrics['timestamp'],
            y=temporal_metrics['acerto_com_delta'],
            name='Com Delta',
            line=dict(color='#10B981')
        ))
        temporal_fig.update_layout(title='Evolução Temporal da Taxa de Acerto',
                                   xaxis_title='Data', yaxis_title='Taxa de Acerto (%)',
                                   template='plotly_dark')

        # Price series
        price_fig = go.Figure()
        price_fig.add_trace(go.Scatter(
            x=filtered_df['timestamp'], y=filtered_df['valor_real'],
            name='Valor Real', line=dict(color='#3B82F6')
        ))
        price_fig.add_trace(go.Scatter(
            x=filtered_df['timestamp'], y=filtered_df['previsao'],
            name='Previsão', line=dict(color='#10B981', dash='dash')
        ))
        price_fig.add_trace(go.Scatter(
            x=filtered_df['timestamp'], y=filtered_df['previsao_com_delta'],
            name='Previsão com Delta', line=dict(color='#8B5CF6', dash='dot')
        ))
        price_fig.update_layout(title='Série Temporal de Preços',
                                xaxis_title='Data', yaxis_title='Preço',
                                template='plotly_dark')

        # Intervalos SEM DELTA
        intervalos_sem = acertos_sem.copy()
        intervalos_sem['intervalo'] = intervalos_sem['timestamp'].diff().dt.total_seconds() / 60
        intervalos_sem = intervalos_sem.dropna()
        intervalos_sem = intervalos_sem[intervalos_sem['intervalo'] > 0]

        intervalo_fig_sem = go.Figure()
        intervalo_fig_sem.add_trace(go.Scatter(
            x=intervalos_sem['timestamp'],
            y=intervalos_sem['intervalo'],
            name='Intervalo',
            mode='lines+markers',
            line=dict(color='#F59E0B')
        ))
        intervalo_fig_sem.update_layout(
            title='Intervalo entre Acertos (Sem Delta)',
            xaxis_title='Data',
            yaxis_title='Minutos',
            template='plotly_dark'
        )

        # Intervalos COM DELTA
        intervalos_com = acertos_com.copy()
        intervalos_com['intervalo'] = intervalos_com['timestamp'].diff().dt.total_seconds() / 60
        intervalos_com = intervalos_com.dropna()
        intervalos_com = intervalos_com[intervalos_com['intervalo'] > 0]

        intervalo_fig_com = go.Figure()
        intervalo_fig_com.add_trace(go.Scatter(
            x=intervalos_com['timestamp'],
            y=intervalos_com['intervalo'],
            name='Intervalo',
            mode='lines+markers',
            line=dict(color='#22C55E')
        ))
        intervalo_fig_com.update_layout(
            title='Intervalo entre Acertos (Com Delta)',
            xaxis_title='Data',
            yaxis_title='Minutos',
            template='plotly_dark'
        )

        # Blocos de acertos acumulados
        blocos_fig = go.Figure()
        blocos_fig.add_trace(go.Bar(
            x=df_blocos_sem['inicio_bloco'],
            y=df_blocos_sem['acertos'],
            name='Acertos por Bloco',
            marker_color='#6366F1'
        ))
        blocos_fig.add_trace(go.Scatter(
            x=df_blocos_sem['inicio_bloco'],
            y=df_blocos_sem['acertos_acumulados'],
            name='Acumulado',
            mode='lines+markers',
            line=dict(color='#EAB308')
        ))
        blocos_fig.update_layout(
            title='Acertos por Bloco (Sem Delta)',
            xaxis_title='Início do Bloco',
            yaxis_title='Acertos',
            template='plotly_dark'
        )

        return temporal_fig, price_fig, intervalo_fig_sem, intervalo_fig_com, blocos_fig
