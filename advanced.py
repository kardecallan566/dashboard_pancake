from dash import html, dcc, Input, Output
import plotly.express as px
import plotly.graph_objects as go
from utils import df, volatility, calculate_metrics
import pandas as pd

def layout():
    return html.Div([
        html.H1('Análise Avançada', className='text-4xl font-bold text-blue-400 mb-6'),
        html.Button('Exportar Dados', id='export-button', className='neon-button text-white font-bold py-2 px-4 rounded mb-4'),
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
        dcc.Graph(id='sequence-analysis'),
        html.H2('Erro Absoluto vs Magnitude de Movimento', className='text-xl font-semibold mb-2 text-blue-300'),
        html.Div(className='loading-spinner', id='loading-error-vs-movement', style={'display': 'none'}),
        dcc.Graph(id='error-vs-movement')
    ])

def register_callbacks(app):
    @app.callback(
        [Output('correlation-heatmap', 'figure'),
         Output('volatility-analysis', 'figure'),
         Output('movement-magnitude', 'figure'),
         Output('sequence-analysis', 'figure'),
         Output('error-vs-movement', 'figure'),
         Output('loading-correlation', 'style'),
         Output('loading-volatility', 'style'),
         Output('loading-movement', 'style'),
         Output('loading-sequences', 'style'),
         Output('loading-error-vs-movement', 'style')],
        [Input('error-type', 'value')]
    )
    def update_advanced(error_type):
        corr_matrix = df[['valor_real', 'previsao', 'previsao_com_delta']].corr()
        corr_fig = px.imshow(corr_matrix, text_auto=True, title='Correlação entre Variáveis',
                             template='plotly_dark', color_continuous_scale='Plasma')

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

        bins = pd.qcut(df['movement_magnitude'], q=4, duplicates='drop')
        movement_metrics = df.groupby(bins, observed=True).agg({
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

        sequences = []
        current_streak = 0
        current_type = None
        for idx, row in df.iterrows():
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

        error_vs_movement_fig = px.scatter(
            df,
            x='movement_magnitude',
            y=error_type.replace('acerto', 'diff').abs(),
            color='par',
            title=f'Erro Absoluto vs Magnitude de Movimento ({error_type})',
            labels={'movement_magnitude': 'Magnitude de Movimento', error_type.replace('acerto', 'diff'): 'Erro Absoluto'},
            template='plotly_dark',
            color_discrete_sequence=px.colors.sequential.Plasma,
            hover_data={'par': True, error_type: True}
        )

        return (corr_fig, volatility_fig, movement_fig, sequence_fig, error_vs_movement_fig,
                {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'})