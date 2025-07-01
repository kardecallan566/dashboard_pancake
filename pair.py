from dash import html, dcc, Input, Output
import plotly.express as px
import plotly.graph_objects as go
from utils import df, calculate_metrics

def layout():
    return html.Div([
        html.H1('Análise por Par', className='text-4xl font-bold text-blue-400 mb-6'),
        dcc.Dropdown(
            id='pair-filter',
            options=[{'label': par, 'value': par} for par in df['par'].unique()] + [{'label': 'Todos', 'value': 'Todos'}],
            value='Todos',
            className='bg-gray-700 text-white p-2 rounded-lg w-1/2 mb-4'
        ),
        html.Button('Exportar Dados', id='export-button', className='neon-button text-white font-bold py-2 px-4 rounded mb-4'),
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

def register_callbacks(app):
    @app.callback(
        [Output('pair-accuracy', 'figure'),
         Output('direction-distribution', 'figure'),
         Output('pair-period-accuracy', 'figure'),
         Output('loading-pair-accuracy', 'style'),
         Output('loading-direction', 'style'),
         Output('loading-pair-period', 'style')],
        [Input('pair-filter', 'value')]
    )
    def update_pair(pair):
        filtered_df = df if pair == 'Todos' else df[df['par'] == pair]
        pair_metrics = calculate_metrics(filtered_df, 'par')
        pair_period_metrics = calculate_metrics(filtered_df.groupby(['par', 'period_of_day'], observed=True), ['par', 'period_of_day'], categorical=True)

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

        direction_counts = filtered_df[['direcao_real', 'direcao_prevista']].melt(var_name='tipo', value_name='direcao')
        direction_counts = direction_counts.groupby(['tipo', 'direcao']).size().reset_index(name='count')
        direction_fig = px.pie(direction_counts, names='direcao', values='count', facet_col='tipo',
                              title='Distribuição de Direções (Real vs Prevista)', template='plotly_dark',
                              color_discrete_sequence=px.colors.sequential.Plasma)

        pair_period_fig = px.bar(
            pair_period_metrics,
            x='par_period_of_day',
            y='taxa_acerto_sem_delta',
            color='period_of_day',
            barmode='group',
            title='Taxa de Acerto por Par e Período',
            labels={'par_period_of_day': 'Par', 'taxa_acerto_sem_delta': 'Taxa de Acerto (%)', 'period_of_day': 'Período'},
            template='plotly_dark',
            color_discrete_sequence=px.colors.sequential.Plasma
        )

        return pair_fig, direction_fig, pair_period_fig, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}