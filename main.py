import dash
from dash import html, dcc, Output, Input, State, callback_context
from dash.dependencies import ALL
import resumo, temporal, hour_day, pair, errors, advanced, other
from utils import df, export_data

# Inicializar o Dash
app = dash.Dash(__name__, external_stylesheets=[
    'https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css',
    'https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap'
])

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
                background: linear-gradient(135deg, #0a1128 0%, #14213d 100%);
                color: #e2e8f0;
                font-family: 'Orbitron', sans-serif;
                position: relative;
                overflow-x: hidden;
            }
            .particle {
                position: absolute;
                background: rgba(59, 130, 246, 0.15);
                border-radius: 50%;
                animation: float 12s infinite;
            }
            @keyframes float {
                0% { transform: translateY(0); opacity: 0.15; }
                50% { opacity: 0.08; }
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
            .neon-button {
                background: #1e40af;
                box-shadow: 0 0 8px #3B82F6, 0 0 15px #3B82F6;
                transition: all 0.3s ease;
            }
            .neon-button:hover {
                box-shadow: 0 0 12px #3B82F6, 0 0 25px #3B82F6;
                background: #2563eb;
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

# Layout principal
app.layout = html.Div(className='flex min-h-screen', children=[
    # Menu lateral
    html.Div(className='w-64 bg-gray-900 p-4 shadow-lg', children=[
        html.H2('Navegação', className='text-2xl font-bold text-blue-400 mb-6'),
        dcc.Link('Resumo', href='/', className='block py-2 px-4 text-lg text-gray-300 hover:bg-gray-800 hover:text-blue-400 rounded transition duration-200'),
        dcc.Link('Análise Temporal', href='/temporal', className='block py-2 px-4 text-lg text-gray-300 hover:bg-gray-800 hover:text-blue-400 rounded transition duration-200'),
        dcc.Link('Análise por Hora e Dia', href='/hour-day', className='block py-2 px-4 text-lg text-gray-300 hover:bg-gray-800 hover:text-blue-400 rounded transition duration-200'),
        dcc.Link('Análise por Par', href='/other', className='block py-2 px-4 text-lg text-gray-300 hover:bg-gray-800 hover:text-blue-400 rounded transition duration-200'),
    ]),
    
    # Conteúdo principal
    html.Div(className='flex-1 p-6', children=[
        dcc.Location(id='url', refresh=False),
        html.Div(id='page-content'),
        dcc.Download(id='download-dataframe')
    ])
])

# Registrar callbacks das páginas
resumo.register_callbacks(app)
temporal.register_callbacks(app)
hour_day.register_callbacks(app)
other.register_callbacks(app)

# Callback para exportação de dados
@app.callback(
    Output('download-dataframe', 'data'),
    Input({'type': 'export-button', 'index': ALL}, 'n_clicks'),
    [State('pair-filter', 'value'),
     State('date-range', 'start_date'),
     State('date-range', 'end_date'),
     State('day-filter', 'value')],
    prevent_initial_call=True
)
def export_data(n_clicks, pair, start_date, end_date, day):
    if not callback_context.triggered:
        return None
    return export_data(df, pair or 'Todos', start_date, end_date, day or 'Todos')

# Callback para mudar o conteúdo da página
@app.callback(Output('page-content', 'children'), Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/temporal':
        return temporal.layout()
    elif pathname == '/hour-day':
        return hour_day.layout()
    elif pathname == '/other':
        return other.layout()
    else:
        return resumo.layout()

# Rodar o servidor
if __name__ == '__main__':
    app.run(debug=True)