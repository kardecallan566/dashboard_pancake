from dash import html, dcc
import plotly.express as px
from utils import df, calculate_metrics
import plotly.graph_objects as go
import pandas as pd

def register_callbacks(app):
    pass 

def contar_sequencias(series):
    acertos_seq = {}
    erros_seq = {}
    atual = series.iloc[0]
    contador = 1

    for valor in series.iloc[1:]:
        if valor == atual:
            contador += 1
        else:
            if atual:
                acertos_seq[contador] = acertos_seq.get(contador, 0) + 1
            else:
                erros_seq[contador] = erros_seq.get(contador, 0) + 1
            atual = valor
            contador = 1

    # Última sequência
    if atual:
        acertos_seq[contador] = acertos_seq.get(contador, 0) + 1
    else:
        erros_seq[contador] = erros_seq.get(contador, 0) + 1

    return acertos_seq, erros_seq

def gerar_grafico_sequencias(df, usar_com_delta=True):
    coluna = 'acerto_com_delta' if usar_com_delta else 'acerto_sem_delta'
    acertos_seq, erros_seq = contar_sequencias(df[coluna])

    acertos_x = list(acertos_seq.keys())
    acertos_y = list(acertos_seq.values())
    erros_x = list(erros_seq.keys())
    erros_y = list(erros_seq.values())

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=acertos_x,
        y=acertos_y,
        name='Acertos',
        marker_color='limegreen',
        hovertemplate='Tamanho: %{x}<br>Frequência: %{y}<extra></extra>'
    ))

    fig.add_trace(go.Bar(
        x=erros_x,
        y=erros_y,
        name='Erros',
        marker_color='crimson',
        hovertemplate='Tamanho: %{x}<br>Frequência: %{y}<extra></extra>'
    ))

    fig.update_layout(
        title='Distribuição de Sequências de Acertos e Erros (Com Delta)',
        xaxis_title='Tamanho da Sequência',
        yaxis_title='Frequência',
        barmode='group',
        template='plotly_dark',
        legend_title_text='Tipo',
        hovermode='x unified'
    )

    return dcc.Graph(figure=fig)

def layout():
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df_sorted = df.sort_values('timestamp')

    total_previsoes = len(df)
    taxa_sem_delta = df['acerto_sem_delta'].mean() * 100
    taxa_com_delta = df['acerto_com_delta'].mean() * 100
    acertos_sem_total = df['acerto_sem_delta'].sum()
    acertos_com_total = df['acerto_com_delta'].sum()
    ultima_previsao = df_sorted['timestamp'].max().strftime('%d/%m/%Y %H:%M')

    taxa_diaria = df.groupby(df['timestamp'].dt.date).agg({
        'acerto_sem_delta': 'mean',
        'acerto_com_delta': 'mean'
    }) * 100

    taxa_media_diaria_sem = taxa_diaria['acerto_sem_delta'].mean()
    taxa_media_diaria_com = taxa_diaria['acerto_com_delta'].mean()

    return html.Div([
        html.H1('Resumo Geral', className='text-4xl font-bold text-blue-400 mb-6'),

        html.Div(className='grid grid-cols-1 md:grid-cols-3 gap-4 mb-8', children=[
            html.Div(className='bg-gray-800 p-4 rounded-lg card', children=[
                html.H3('Taxa de Acerto (Sem Delta)', className='text-lg font-semibold'),
                html.P(f"{taxa_sem_delta:.2f}%", className='text-2xl text-blue-400')
            ]),
            html.Div(className='bg-gray-800 p-4 rounded-lg card', children=[
                html.H3('Taxa de Acerto (Com Delta)', className='text-lg font-semibold'),
                html.P(f"{taxa_com_delta:.2f}%", className='text-2xl text-green-400')
            ]),
            html.Div(className='bg-gray-800 p-4 rounded-lg card', children=[
                html.H3('Total de Previsões', className='text-lg font-semibold'),
                html.P(f"{total_previsoes}", className='text-2xl text-purple-400')
            ]),
            html.Div(className='bg-gray-800 p-4 rounded-lg card', children=[
                html.H3('Acertos Sem Delta', className='text-lg font-semibold'),
                html.P(f"{acertos_sem_total} ({(acertos_sem_total / total_previsoes * 100):.2f}%)", className='text-2xl text-blue-300')
            ]),
            html.Div(className='bg-gray-800 p-4 rounded-lg card', children=[
                html.H3('Acertos Com Delta', className='text-lg font-semibold'),
                html.P(f"{acertos_com_total} ({(acertos_com_total / total_previsoes * 100):.2f}%)", className='text-2xl text-green-300')
            ]),
            html.Div(className='bg-gray-800 p-4 rounded-lg card', children=[
                html.H3('Última Previsão', className='text-lg font-semibold'),
                html.P(f"{ultima_previsao}", className='text-2xl text-yellow-400')
            ]),
            html.Div(className='bg-gray-800 p-4 rounded-lg card col-span-2', children=[
                html.H3('Taxa Média Diária (Sem Delta)', className='text-lg font-semibold'),
                html.P(f"{taxa_media_diaria_sem:.2f}%", className='text-2xl text-blue-400')
            ]),
            html.Div(className='bg-gray-800 p-4 rounded-lg card col-span-2', children=[
                html.H3('Taxa Média Diária (Com Delta)', className='text-lg font-semibold'),
                html.P(f"{taxa_media_diaria_com:.2f}%", className='text-2xl text-green-400')
            ]),
        ]),

        html.Div(className='bg-gray-800 p-4 rounded-lg card col-span-2', children=[
            html.H3('Sequências de Acertos e Erros (Com Delta)', className='text-lg font-semibold mb-2'),
            gerar_grafico_sequencias(df, usar_com_delta=True)
        ]),
         html.Div(className='bg-gray-800 p-4 rounded-lg card col-span-2', children=[
            html.H3('Sequências de Acertos e Erros (Sem Delta)', className='text-lg font-semibold mb-2'),
            gerar_grafico_sequencias(df, usar_com_delta=False)
        ]),

        html.Button('Exportar Dados', id='export-button', className='neon-button text-white font-bold py-2 px-4 rounded')
    ])
