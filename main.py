import dash
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State
from dash.dependencies import ALL
from datetime import datetime
import seaborn as sns
import numpy as np
import io
import base64

# Carregar o CSV
df = pd.read_csv('dados.csv')

# Converter a coluna timestamp para datetime
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Extrair hora, dia da semana e período do dia
df['hour'] = df['timestamp'].dt.hour
df['day_of_week'] = df['timestamp'].dt.day_name()
df['period_of_day'] = pd.cut(df['hour'], bins=[0, 6, 12, 18, 24], labels=['Madrugada', 'Manhã', 'Tarde', 'Noite'], right=False)

# Calcular diferenças de preço e magnitude de movimento
df['diff_previsao'] = df['valor_real'] - df['previsao']
df['diff_previsao_com_delta'] = df['valor_real'] - df['previsao_com_delta']
df['movement_magnitude'] = df['valor_real'].diff().abs()

# Calcular volatilidade
volatility = df.groupby(['hour', 'day_of_week'])['valor_real'].std().reset_index(name='volatility')

# Função para calcular métricas
def calculate_metrics(df, group_by, categorical=False):
    metrics = df.groupby(group_by, observed=categorical).agg({
        'acerto_sem_delta': ['mean', 'count'],
        'acerto_com_delta': ['mean', 'count']
    }).reset_index()
    metrics.columns = [group_by, 'taxa_acerto_sem_delta', 'total_previsoes_sem_delta',
                      'taxa_acerto_com_delta', 'total_previsoes_com_delta']
    metrics['taxa_acerto_sem_delta'] = metrics['taxa_acerto_sem_delta'] * 100
    metrics['taxa_acerto_com_delta'] = metrics['taxa_acerto_com_delta'] * 100
    return metrics

# Calcular métricas iniciais
hourly_metrics = calculate_metrics(df, 'hour')
daily_metrics = calculate_metrics(df, 'day_of_week')
pair_metrics = calculate_metrics(df, 'par')
period_metrics = calculate_metrics(df, 'period_of_day', categorical=True)

# Inicializar o Dash
app = Dash(__name__, external_stylesheets=[
    'https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css',
    'https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap'
])
app.config.suppress_callback_exceptions = True

# Estilo CSS personalizado
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Dashboard de Previsões</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                background: linear-gradient(135deg, #0d1b2a 0%, #1b263b 100%);
                color: #e2e8f0;
                font-family: 'Orbitron', sans-serif;
                position: relative;
                overflow-x: hidden;
            }
            .particle {
                position: absolute;
                background: rgba(59, 130, 246, 0.3);
                border-radius: 50%;
                animation: float 10s infinite;
            }
            @keyframes float {
                0% { transform: translateY(0); opacity: 0.3; }
                50% { opacity: 0.1; }
                100% { transform: translateY(-100vh); opacity: 0; }
            }
            .loading-spinner {
                border: 4px solid #3B82F6;
                border-top: 4px solid transparent;
                border-radius: 50%;
                width: 24px;
                height: 24px;
                animation: spin 1s linear infinite;
                margin: auto;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            .card {
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }
            .card:hover {
                transform: translateY(-5px);
                box-shadow: 0 0 15px rgba(59, 130, 246, 0.5);
            }
        </style>
    </head>
    <body>
        <div class="particle" style="width: 4px; height: 4px; left: 10%; top: 100%;"></div>
        <div class="particle" style="width: 3px; height: 3px; left: 25%; top: 100%; animation-delay: 1s;"></div>
        <div class="particle" style="width: 5px; height: 5px; left: 40%; top: 100%; animation-delay: 2s;"></div>
        <div class="particle" style="width: 2px; height: 2px; left: 60%; top: 100%; animation-delay: 3s;"></div>
        <div class="particle" style="width: 4px; height: 4px; left: 80%; top: 100%; animation-delay: 4s;"></div>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Layout do dashboard
app.layout = html.Div(className='flex min-h-screen', children=[
    # Menu lateral
    html.Div(className='w-64 bg-gray-900 p-4 shadow-lg', children=[
        html.H2('Navegação', className='text-2xl font-bold text-blue-400 mb-6'),
        dcc.Link('Resumo', href='/', className='block py-2 px-4 text-lg text-gray-300 hover:bg-gray-800 hover:text-blue-400 rounded transition duration-200'),
        dcc.Link('Análise Temporal', href='/temporal', className='block py-2 px-4 text-lg text-gray-300 hover:bg-gray-800 hover:text-blue-400 rounded transition duration-200'),
        dcc.Link('Análise por Hora e Dia', href='/hour-day', className='block py-2 px-4 text-lg text-gray-300 hover:bg-gray-800 hover:text-blue-400 rounded transition duration-200'),
        dcc.Link('Análise por Par', href='/pair', className='block py-2 px-4 text-lg text-gray-300 hover:bg-gray-800 hover:text-blue-400 rounded transition duration-200'),
        dcc.Link('Análise de Erros', href='/errors', className='block py-2 px-4 text-lg text-gray-300 hover:bg-gray-800 hover:text-blue-400 rounded transition duration-200'),
        dcc.Link('Análise Avançada', href='/advanced', className='block py-2 px-4 text-lg text-gray-300 hover:bg-gray-800 hover:text-blue-400 rounded transition duration-200')
    ]),
    
    # Conteúdo principal
    html.Div(className='flex-1 p-6', children=[
        dcc.Location(id='url', refresh=False),
        html.Div(id='page-content'),
        dcc.Download(id='download-dataframe')
    ])
])

# Layouts das páginas
def resumo_layout():
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
        html.Button('Exportar Dados', id='btn-export', className='bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded mb-4 transition duration-200'),
        html.H2('Distribuição de Previsões por Par', className='text-xl font-semibold mb-2 text-blue-300'),
        html.Div(className='loading-spinner', id='loading-pair', style={'display': 'none'}),
        dcc.Graph(id='pair-distribution')
    ])

def temporal_layout():
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
        html.Button('Exportar Dados', id='btn-export-temporal', className='bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded mb-4 transition duration-200'),
        html.H2('Evolução Temporal da Taxa de Acerto', className='text-xl font-semibold mb-2 text-blue-300'),
        html.Div(className='loading-spinner', id='loading-temporal', style={'display': 'none'}),
        dcc.Graph(id='temporal-accuracy'),
        html.H2('Série Temporal de Preços', className='text-xl font-semibold mb-2 text-blue-300'),
        html.Div(className='loading-spinner', id='loading-price-series', style={'display': 'none'}),
        dcc.Graph(id='price-series')
    ])

def hour_day_layout():
    return html.Div([
        html.H1('Análise por Hora e Dia', className='text-4xl font-bold text-blue-400 mb-6'),
        dcc.Dropdown(
            id='day-filter',
            options=[{'label': str(day), 'value': str(day)} for day in df['day_of_week'].unique()] + [{'label': 'Todos', 'value': 'Todos'}],  # type: ignore
            value='Todos',
            className='bg-gray-700 text-white p-2 rounded-lg w-1/2 mb-4'
        ),
        html.Button('Exportar Dados', id='btn EXPORT-hour-day', className='bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded mb-4 transition duration-200'),
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
        dcc.Graph(id='hour-day-heatmap')
    ])

def pair_layout():
    return html.Div([
        html.H1('Análise por Par', className='text-4xl font-bold text-blue-400 mb-6'),
        dcc.Dropdown(
            id='pair-filter',
            options=list([{'label': par, 'value': par} for par in df['par'].unique()] + [{'label': 'Todos', 'value': 'Todos'}]),
            value='Todos',
            className='bg-gray-700 text-white p-2 rounded-lg w-1/2 mb-4'
        ),
        html.Button('Exportar Dados', id='btn-export-pair', className='bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded mb-4 transition duration-200'),
        html.H2('Taxa de Acerto por Par', className='text-xl font-semibold mb-2 text-blue-300'),
        html.Div(className='loading-spinner', id='loading-pair-accuracy', style={'display': 'none'}),
        dcc.Graph(id='pair-accuracy'),
        html.H2('Distribuição de Direções', className='text-xl font-semibold mb-2 text-blue-300'),
        html.Div(className='loading-spinner', id='loading-direction', style={'display': 'none'}),
        dcc.Graph(id='direction-distribution'),
        html.H2('Taxa de Acerto por Par e Período', className='text-xl font-semibold mb-2 text-blue-300'),
        html.Div(className='loading-spinner', id='loading-pair-period', style={'display': 'none'}),
        dcc.Graph(id='pair-period-accuracy')
    ])

def errors_layout():
    return html.Div([
        html.H1('Análise de Erros', className='text-4xl font-bold text-blue-400 mb-6'),
        dcc.Dropdown(
            id='error-type',
            options=[
                {'label': 'Sem Delta', 'value': 'acerto_sem_delta'},
                {'label': 'Com Delta', 'value': 'acerto_com_delta'}
            ],
            value='acerto_sem_delta',
            className='bg-gray-700 text-white p-2 rounded-lg w-1/2 mb-4'
        ),
        html.Button('Exportar Dados', id='btn-export-errors', className='bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded mb-4 transition duration-200'),
        html.H2('Distribuição de Erros por Hora e Dia', className='text-xl font-semibold mb-2 text-blue-300'),
        html.Div(className='loading-spinner', id='loading-error-analysis', style={'display': 'none'}),
        dcc.Graph(id='error-analysis'),
        html.H2('Erros por Direção Prevista', className='text-xl font-semibold mb-2 text-blue-300'),
        html.Div(className='loading-spinner', id='loading-error-direction', style={'display': 'none'}),
        dcc.Graph(id='error-direction'),
        html.H2('Taxa de Acerto por Intervalo de Erro Absoluto', className='text-xl font-semibold mb-2 text-blue-300'),
        html.Div(className='loading-spinner', id='loading-error-magnitude', style={'display': 'none'}),
        dcc.Graph(id='error-magnitude')
    ])

def advanced_layout():
    return html.Div([
        html.H1('Análise Avançada', className='text-4xl font-bold text-blue-400 mb-6'),
        html.Button('Exportar Dados', id='btn-export-advanced', className='bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded mb-4 transition duration-200'),
        html.H2('Correlação entre Variáveis', className='text-xl font-semibold mb-2 text-blue-300'),
        html.Div(className='loading-spinner', id='loading-correlation', style={'display': 'none'}),
        dcc.Graph(id='correlation-heatmap'),
        html.H2('Volatilidade por Hora e Dia', className='text-xl font-semibold mb-2 text-blue-300'),
        html.Div(className='loading-spinner', id='loading-volatility', style={'display': 'none'}),
        dcc.Graph(id='volatility-analysis'),
        html.H2('Taxa de Acerto por Magnitude de Movimento', className='text-xl font-semibold mb-2 text-blue-300'),
        html.Div(className='loading-spinner', id='loading-movement', style={'display': 'none'}),
        dcc.Graph(id='movement-magnitude'),
        html.H2('Sequências de Acertos/Erros', className='text-xl font-semibold mb-2 text-blue-300'),
        html.Div(className='loading-spinner', id='loading-sequences', style={'display': 'none'}),
        dcc.Graph(id='sequence-analysis')
    ])

# Callback para mudar o conteúdo da página
@app.callback(Output('page-content', 'children'), Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/temporal':
        return temporal_layout()
    elif pathname == '/hour-day':
        return hour_day_layout()
    elif pathname == '/pair':
        return pair_layout()
    elif pathname == '/errors':
        return errors_layout()
    elif pathname == '/advanced':
        return advanced_layout()
    else:
        return resumo_layout()

# Callback para exportar dados
@app.callback(
    Output('download-dataframe', 'data'),
    Input('btn-export', 'n_clicks'),
    Input('btn-export-temporal', 'n_clicks'),
    Input('btn-export-hour-day', 'n_clicks'),
    Input('btn-export-pair', 'n_clicks'),
    Input('btn-export-errors', 'n_clicks'),
    Input('btn-export-advanced', 'n_clicks'),
    State('pair-filter', 'value'),
    State('date-range', 'start_date'),
    State('date-range', 'end_date'),
    State('day-filter', 'value'),
    prevent_initial_call=True
)
def export_data(n1, n2, n3, n4, n5, n6, pair, start_date, end_date, day):
    ctx_id = dash.callback_context.triggered_id

    filtered_df = df.copy()

    if pair and pair != 'Todos':
        filtered_df = filtered_df[filtered_df['par'] == pair]
    if start_date and end_date:
        filtered_df = filtered_df[(filtered_df['timestamp'] >= start_date) & (filtered_df['timestamp'] <= end_date)]
    if day and day != 'Todos':
        filtered_df = filtered_df[filtered_df['day_of_week'] == day]

    return dcc.send_data_frame(filtered_df.to_csv, filename="filtered_data.csv")


# Callbacks para atualizar os gráficos
@app.callback(
    [Output('pair-distribution', 'figure'),
     Output('temporal-accuracy', 'figure'),
     Output('price-series', 'figure'),
     Output('hourly-accuracy', 'figure'),
     Output('daily-accuracy', 'figure'),
     Output('period-accuracy', 'figure'),
     Output('hour-day-heatmap', 'figure'),
     Output('pair-accuracy', 'figure'),
     Output('direction-distribution', 'figure'),
     Output('pair-period-accuracy', 'figure'),
     Output('error-analysis', 'figure'),
     Output('error-direction', 'figure'),
     Output('error-magnitude', 'figure'),
     Output('correlation-heatmap', 'figure'),
     Output('volatility-analysis', 'figure'),
     Output('movement-magnitude', 'figure'),
     Output('sequence-analysis', 'figure'),
     Output('loading-pair', 'style'),
     Output('loading-temporal', 'style'),
     Output('loading-price-series', 'style'),
     Output('loading-hourly', 'style'),
     Output('loading-daily', 'style'),
     Output('loading-period', 'style'),
     Output('loading-heatmap', 'style'),
     Output('loading-pair-accuracy', 'style'),
     Output('loading-direction', 'style'),
     Output('loading-pair-period', 'style'),
     Output('loading-error-analysis', 'style'),
     Output('loading-error-direction', 'style'),
     Output('loading-error-magnitude', 'style'),
     Output('loading-correlation', 'style'),
     Output('loading-volatility', 'style'),
     Output('loading-movement', 'style'),
     Output('loading-sequences', 'style')],
    [Input('pair-filter', 'value'),
     Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('day-filter', 'value'),
     Input('error-type', 'value')]
)
def update_dashboard(pair, start_date, end_date, day, error_type):
    # Mostrar spinners de carregamento
    loading_style = {'display': 'block'}
    loaded_style = {'display': 'none'}
    
    # Filtrar dados
    filtered_df = df.copy()
    if pair != 'Todos':
        filtered_df = filtered_df[filtered_df['par'] == pair]
    filtered_df = filtered_df[(filtered_df['timestamp'] >= start_date) & (filtered_df['timestamp'] <= end_date)]
    if day != 'Todos':
        filtered_df = filtered_df[filtered_df['day_of_week'] == day]
    
    # Recalcular métricas
    hourly_metrics = calculate_metrics(filtered_df, 'hour')
    daily_metrics = calculate_metrics(filtered_df, 'day_of_week')
    period_metrics = calculate_metrics(filtered_df, 'period_of_day', categorical=True)
    pair_metrics = calculate_metrics(filtered_df, 'par')
    pair_period_metrics = calculate_metrics(filtered_df.groupby(['par', 'period_of_day'], observed=True), ['par', 'period_of_day'], categorical=True)
    
    # Gráfico: Distribuição de Previsões por Par
    pair_counts = filtered_df['par'].value_counts().reset_index()
    pair_counts.columns = ['par', 'count']
    pair_dist_fig = px.pie(pair_counts, names='par', values='count', title='Distribuição de Previsões por Par',
                           template='plotly_dark', color_discrete_sequence=px.colors.sequential.Plasma)
    
    # Gráfico: Evolução Temporal da Taxa de Acerto
    temporal_metrics = filtered_df.groupby(filtered_df['timestamp'].dt.date).agg({
        'acerto_sem_delta': 'mean',
        'acerto_com_delta': 'mean'
    }).reset_index()
    temporal_metrics['acerto_sem_delta'] = temporal_metrics['acerto_sem_delta'] * 100
    temporal_metrics['acerto_com_delta'] = temporal_metrics['acerto_com_delta'] * 100
    temporal_fig = go.Figure()
    temporal_fig.add_trace(go.Scatter(
        x=temporal_metrics['timestamp'],
        y=temporal_metrics['acerto_sem_delta'],
        name='Sem Delta',
        mode='lines+markers',
        line=dict(color='#3B82F6'),
        hovertemplate='Data: %{x}<br>Taxa: %{y:.2f}%<extra></extra>'
    ))
    temporal_fig.add_trace(go.Scatter(
        x=temporal_metrics['timestamp'],
        y=temporal_metrics['acerto_com_delta'],
        name='Com Delta',
        mode='lines+markers',
        line=dict(color='#10B981'),
        hovertemplate='Data: %{x}<br>Taxa: %{y:.2f}%<extra></extra>'
    ))
    temporal_fig.update_layout(
        title='Evolução Temporal da Taxa de Acerto',
        xaxis_title='Data',
        yaxis_title='Taxa de Acerto (%)',
        template='plotly_dark',
        hovermode='x unified'
    )
    
    # Gráfico: Série Temporal de Preços
    price_series_fig = go.Figure()
    price_series_fig.add_trace(go.Scatter(
        x=filtered_df['timestamp'],
        y=filtered_df['valor_real'],
        name='Valor Real',
        mode='lines',
        line=dict(color='#3B82F6'),
        hovertemplate='Data: %{x}<br>Preço: %{y:.2f}<extra></extra>'
    ))
    price_series_fig.add_trace(go.Scatter(
        x=filtered_df['timestamp'],
        y=filtered_df['previsao'],
        name='Previsão',
        mode='lines',
        line=dict(color='#10B981', dash='dash'),
        hovertemplate='Data: %{x}<br>Preço: %{y:.2f}<extra></extra>'
    ))
    price_series_fig.add_trace(go.Scatter(
        x=filtered_df['timestamp'],
        y=filtered_df['previsao_com_delta'],
        name='Previsão com Delta',
        mode='lines',
        line=dict(color='#8B5CF6', dash='dot'),
        hovertemplate='Data: %{x}<br>Preço: %{y:.2f}<extra></extra>'
    ))
    price_series_fig.update_layout(
        title='Série Temporal de Preços',
        xaxis_title='Data',
        yaxis_title='Preço',
        template='plotly_dark',
        hovermode='x unified'
    )
    
    # Gráfico: Taxa de Acerto por Hora
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
    
    # Gráfico: Taxa de Acerto por Dia da Semana
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
    
    # Gráfico: Taxa de Acerto por Período do Dia
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
    
    # Gráfico: Heatmap de Taxa de Acerto por Hora e Dia
    heatmap_data = filtered_df.pivot_table(
        values='acerto_sem_delta' if error_type == 'acerto_sem_delta' else 'acerto_com_delta',
        index='day_of_week',
        columns='hour',
        aggfunc='mean'
    ) * 100
    heatmap_fig = px.imshow(
        heatmap_data,
        title=f'Taxa de Acerto por Hora e Dia ({error_type})',
        labels={'color': 'Taxa de Acerto (%)', 'hour': 'Hora', 'day_of_week': 'Dia da Semana'},
        template='plotly_dark',
        color_continuous_scale='Plasma'
    )
    
    # Gráfico: Taxa de Acerto por Par
    pair_fig = go.Figure()
    pair_fig.add_trace(go.Bar(
        x=pair_metrics['par'],
        y=pair_metrics['taxa_acerto_sem_delta'],
        name='Sem Delta',
        marker_color='#3B82F6',
        hovertemplate='Par: %{x}<br>Taxa: %{y:.2f}%<extra></extra>'
    ))
    pair_fig.add_trace(go.Bar(
        x=pair_metrics['par'],
        y=pair_metrics['taxa_acerto_com_delta'],
        name='Com Delta',
        marker_color='#10B981',
        hovertemplate='Par: %{x}<br>Taxa: %{y:.2f}%<extra></extra>'
    ))
    pair_fig.update_layout(
        title='Taxa de Acerto por Par',
        xaxis_title='Par',
        yaxis_title='Taxa de Acerto (%)',
        barmode='group',
        template='plotly_dark',
        hovermode='x unified'
    )
    
    # Gráfico: Distribuição de Direções
    direction_counts = filtered_df[['direcao_real', 'direcao_prevista']].melt(var_name='tipo', value_name='direcao')
    direction_counts = direction_counts.groupby(['tipo', 'direcao']).size().reset_index(name='count')
    direction_fig = px.pie(direction_counts, names='direcao', values='count', facet_col='tipo',
                           title='Distribuição de Direções (Real vs Prevista)', template='plotly_dark',
                           color_discrete_sequence=px.colors.sequential.Plasma)
    
    # Gráfico: Taxa de Acerto por Par e Período
    pair_period_fig = px.bar(
        pair_period_metrics,
        x='par',
        y='taxa_acerto_sem_delta' if error_type == 'acerto_sem_delta' else 'taxa_acerto_com_delta',
        color='period_of_day',
        barmode='group',
        title=f'Taxa de Acerto por Par e Período ({error_type})',
        labels={'par': 'Par', 'taxa_acerto_sem_delta': 'Taxa de Acerto (%)', 'taxa_acerto_com_delta': 'Taxa de Acerto (%)', 'period_of_day': 'Período'},
        template='plotly_dark',
        color_discrete_sequence=px.colors.sequential.Plasma
    )
    
    # Gráfico: Análise de Erros
    error_df = filtered_df[filtered_df[error_type] == False]
    error_counts = error_df.groupby(['hour', 'day_of_week']).size().reset_index(name='count')
    error_fig = px.scatter(
        error_counts,
        x='hour',
        y='day_of_week',
        size='count',
        color='count',
        title=f'Distribuição de Erros ({error_type})',
        labels={'hour': 'Hora', 'day_of_week': 'Dia da Semana', 'count': 'Número de Erros'},
        template='plotly_dark',
        color_continuous_scale='Plasma',
        hover_data={'count': True}
    )
    
    # Gráfico: Erros por Direção Prevista
    error_direction = error_df.groupby(['direcao_prevista']).size().reset_index(name='count')
    error_direction_fig = px.bar(
        error_direction,
        x='direcao_prevista',
        y='count',
        title=f'Erros por Direção Prevista ({error_type})',
        labels={'direcao_prevista': 'Direção Prevista', 'count': 'Número de Erros'},
        template='plotly_dark',
        color='count',
        color_continuous_scale='Plasma'
    )
    
    # Gráfico: Taxa de Acerto por Intervalo de Erro Absoluto
    error_bins = pd.qcut(filtered_df[error_type.replace('acerto', 'diff')].abs(), q=4, duplicates='drop')
    error_magnitude_metrics = filtered_df.groupby(error_bins, observed=True).agg({
        'acerto_sem_delta': 'mean',
        'acerto_com_delta': 'mean'
    }).reset_index()
    error_magnitude_metrics['acerto_sem_delta'] = error_magnitude_metrics['acerto_sem_delta'] * 100
    error_magnitude_metrics['acerto_com_delta'] = error_magnitude_metrics['acerto_com_delta'] * 100
    error_magnitude_fig = go.Figure()
    error_magnitude_fig.add_trace(go.Bar(
        x=error_magnitude_metrics[error_type.replace('acerto', 'diff')],
        y=error_magnitude_metrics['acerto_sem_delta'],
        name='Sem Delta',
        marker_color='#3B82F6',
        hovertemplate='Erro Absoluto: %{x}<br>Taxa: %{y:.2f}%<extra></extra>'
    ))
    error_magnitude_fig.add_trace(go.Bar(
        x=error_magnitude_metrics[error_type.replace('acerto', 'diff')],
        y=error_magnitude_metrics['acerto_com_delta'],
        name='Com Delta',
        marker_color='#10B981',
        hovertemplate='Erro Absoluto: %{x}<br>Taxa: %{y:.2f}%<extra></extra>'
    ))
    error_magnitude_fig.update_layout(
        title='Taxa de Acerto por Intervalo de Erro Absoluto',
        xaxis_title='Intervalo de Erro Absoluto',
        yaxis_title='Taxa de Acerto (%)',
        barmode='group',
        template='plotly_dark',
        hovermode='x unified'
    )
    
    # Gráfico: Correlação entre Variáveis
    corr_matrix = filtered_df[['valor_real', 'previsao', 'previsao_com_delta']].corr()
    corr_fig = px.imshow(corr_matrix, text_auto=True, title='Correlação entre Variáveis',
                         template='plotly_dark', color_continuous_scale='Plasma')
    
    # Gráfico: Volatilidade
    volatility_fig = px.scatter(
        volatility,
        x='hour',
        y='day_of_week',
        size='volatility',
        color='volatility',
        title='Volatilidade por Hora e Dia',
        labels={'hour': 'Hora', 'day_of_week': 'Dia da Semana', 'volatility': 'Volatilidade'},
        template='plotly_dark',
        color_continuous_scale='Plasma',
        hover_data={'volatility': ':.2f'}
    )
    
    # Gráfico: Taxa de Acerto por Magnitude de Movimento
    bins = pd.qcut(filtered_df['movement_magnitude'], q=4, duplicates='drop')
    movement_metrics = filtered_df.groupby(bins, observed=True).agg({
        'acerto_sem_delta': 'mean',
        'acerto_com_delta': 'mean'
    }).reset_index()
    movement_metrics['acerto_sem_delta'] = movement_metrics['acerto_sem_delta'] * 100
    movement_metrics['acerto_com_delta'] = movement_metrics['acerto_com_delta'] * 100
    movement_fig = go.Figure()
    movement_fig.add_trace(go.Bar(
        x=movement_metrics['movement_magnitude'],
        y=movement_metrics['acerto_sem_delta'],
        name='Sem Delta',
        marker_color='#3B82F6',
        hovertemplate='Magnitude: %{x}<br>Taxa: %{y:.2f}%<extra></extra>'
    ))
    movement_fig.add_trace(go.Bar(
        x=movement_metrics['movement_magnitude'],
        y=movement_metrics['acerto_com_delta'],
        name='Com Delta',
        marker_color='#10B981',
        hovertemplate='Magnitude: %{x}<br>Taxa: %{y:.2f}%<extra></extra>'
    ))
    movement_fig.update_layout(
        title='Taxa de Acerto por Magnitude de Movimento',
        xaxis_title='Magnitude de Movimento',
        yaxis_title='Taxa de Acerto (%)',
        barmode='group',
        template='plotly_dark',
        hovermode='x unified'
    )
    
    # Gráfico: Sequências de Acertos/Erros
    sequences = []
    current_streak = 0
    current_type = None
    for idx, row in filtered_df.iterrows():
        status = row[error_type]
        if current_type is None:
            current_type = status
            current_streak = 1
        elif status == current_type:
            current_streak += 1
        else:
            sequences.append({'type': 'Acerto' if current_type else 'Erro', 'length': current_streak})
            current_type = status
            current_streak = 1
    sequences.append({'type': 'Acerto' if current_type else 'Erro', 'length': current_streak})
    sequence_df = pd.DataFrame(sequences)
    sequence_fig = px.histogram(
        sequence_df,
        x='length',
        color='type',
        title=f'Distribuição de Sequências de Acertos/Erros ({error_type})',
        labels={'length': 'Tamanho da Sequência', 'count': 'Frequência'},
        template='plotly_dark',
        color_discrete_sequence=['#3B82F6', '#EF4444']
    )
    
    return (
        pair_dist_fig, temporal_fig, price_series_fig, hourly_fig, daily_fig, period_fig,
        heatmap_fig, pair_fig, direction_fig, pair_period_fig, error_fig, error_direction_fig,
        error_magnitude_fig, corr_fig, volatility_fig, movement_fig, sequence_fig,
        loaded_style, loaded_style, loaded_style, loaded_style, loaded_style, loaded_style,
        loaded_style, loaded_style, loaded_style, loaded_style, loaded_style, loaded_style,
        loaded_style, loaded_style, loaded_style, loaded_style, loaded_style
    )

# Rodar o servidor
if __name__ == '__main__':
    app.run(debug=True)