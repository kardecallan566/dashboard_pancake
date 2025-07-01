from dash import html, dcc, Input, Output
import plotly.graph_objects as go
from utils import df, calculate_metrics

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
        html.Div(className='loading-spinner', id='loading-temporal', style={'display': 'none'}),
        dcc.Graph(id='temporal-accuracy'),
        html.H2('Série Temporal de Preços', className='text-xl font-semibold mb-2 text-blue-300'),
        html.Div(className='loading-spinner', id='loading-price-series', style={'display': 'none'}),
        dcc.Graph(id='price-series')
    ])

def register_callbacks(app):
    @app.callback(
        [Output('temporal-accuracy', 'figure'),
         Output('price-series', 'figure'),
         Output('loading-temporal', 'style'),
         Output('loading-price-series', 'style')],
        [Input('date-range', 'start_date'),
         Input('date-range', 'end_date')]
    )
    def update_temporal(start_date, end_date):
        filtered_df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]
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

        return temporal_fig, price_series_fig, {'display': 'none'}, {'display': 'none'}