from dash import html, dcc, Input, Output
import plotly.express as px
from utils import df

def layout():
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
        html.Button('Exportar Dados', id='export-button', className='neon-button text-white font-bold py-2 px-4 rounded mb-4'),
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

def register_callbacks(app):
    @app.callback(
        [Output('error-analysis', 'figure'),
         Output('error-direction', 'figure'),
         Output('error-magnitude', 'figure'),
         Output('loading-error-analysis', 'style'),
         Output('loading-error-direction', 'style'),
         Output('loading-error-magnitude', 'style')],
        [Input('error-type', 'value')]
    )
    def update_errors(error_type):
        error_df = df[df[error_type] == False]
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

        error_direction = error_df.groupby(['direcao_prevista']).size().reset_index(name='count')
        error_direction_fig = px.bar(
            error_direction,
            x='direcao_prevista',
            y='count',
            title=f'Erros por Direção Prevista ({error_type})',
            labels={'direcao_prevista': 'Direção Prevista', 'count': 'Número de Erros'},
            template='plotly_dark',
            color='count',
            color_continuous_scale='Plasma',
            hovertemplate='Direção: %{x}<br>Erros: %{y}<extra></extra>'
        )

        error_bins = pd.qcut(df[error_type.replace('acerto', 'diff')].abs(), q=4, duplicates='drop')
        error_magnitude_metrics = df.groupby(error_bins, observed=True).agg({
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

        return error_fig, error_direction_fig, error_magnitude_fig, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}