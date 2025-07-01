from dash import html, dcc, Input, Output
import plotly.express as px
import plotly.graph_objects as go
from utils import df, calculate_metrics

def layout():
    return html.Div([
        html.H1('Análise por Hora e Dia', className='text-4xl font-bold text-blue-400 mb-6'),
        dcc.Dropdown(
            id='day-filter',
            options=[{'label': day, 'value': day} for day in df['day_of_week'].unique()] + [{'label': 'Todos', 'value': 'Todos'}],
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
        dcc.Graph(id='hour-day-heatmap')
    ])

def register_callbacks(app):
    @app.callback(
        [Output('hourly-accuracy', 'figure'),
         Output('daily-accuracy', 'figure'),
         Output('period-accuracy', 'figure'),
         Output('hour-day-heatmap', 'figure'),
         Output('loading-hourly', 'style'),
         Output('loading-daily', 'style'),
         Output('loading-period', 'style'),
         Output('loading-heatmap', 'style')],
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

        return hourly_fig, daily_fig, period_fig, heatmap_fig, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}