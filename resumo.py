from dash import html, dcc
import plotly.express as px
from utils import df, calculate_metrics

def layout():
    pair_counts = df['par'].value_counts().reset_index()
    pair_counts.columns = ['par', 'count']
    pair_dist_fig = px.pie(pair_counts, names='par', values='count', title='Distribuição de Previsões por Par',
                           template='plotly_dark', color_discrete_sequence=px.colors.sequential.Plasma)

    return html.Div([
        html.H1('Resumo Geral', className='text-4xl font-bold text-blue-400 mb-6'),
        html.Div(className='grid grid-cols-1 md:grid-cols-3 gap-4 mb-8', children=[
            html.Div(className='bg-gray-800 p-4 rounded-lg card', children=[
                html.H3('Taxa de Acerto (Sem Delta)', className='text-lg font-semibold'),
                html.P(f"{df['acerto_sem_delta'].mean() * 100:.2f}%", className='text-2xl text-blue-400')
            ]),
            html.Div(className='bg-gray-800 p-4 rounded-lg card', children=[
                html.H3('Taxa de Acerto (Com Delta)', className='text-lg font-semibold'),
                html.P(f"{df['acerto_com_delta'].mean() * 100:.2f}%", className='text-2xl text-green-400')
            ]),
            html.Div(className='bg-gray-800 p-4 rounded-lg card', children=[
                html.H3('Total de Previsões', className='text-lg font-semibold'),
                html.P(f"{len(df)}", className='text-2xl text-purple-400')
            ])
        ]),
        html.Button('Exportar Dados', id='export-button', className='neon-button text-white font-bold py-2 px-4 rounded mb-4'),
        html.H2('Distribuição de Previsões por Par', className='text-xl font-semibold mb-2 text-blue-300'),
        html.Div(className='loading-spinner', id='loading-pair', style={'display': 'none'}),
        dcc.Graph(id='pair-distribution', figure=pair_dist_fig)
    ])

def register_callbacks(app):
    return None