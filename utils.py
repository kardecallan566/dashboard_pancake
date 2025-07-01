import pandas as pd
import io
from dash import dcc

# Carregar e preparar os dados
df = pd.read_csv('dados.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['hour'] = df['timestamp'].dt.hour
df['day_of_week'] = df['timestamp'].dt.day_name()
df['period_of_day'] = pd.cut(df['hour'], bins=[0, 6, 12, 18, 24], labels=['Madrugada', 'Manhã', 'Tarde', 'Noite'], right=False)
df['diff_previsao'] = df['valor_real'] - df['previsao']
df['diff_previsao_com_delta'] = df['valor_real'] - df['previsao_com_delta']
df['movement_magnitude'] = df['valor_real'].diff().abs()
volatility = df.groupby(['hour', 'day_of_week'])['valor_real'].std().reset_index(name='volatility')

# Função para calcular métricas
def calculate_metrics(df, group_by, categorical=False):
    metrics = df.groupby(group_by, observed=categorical).agg({
        'acerto_sem_delta': ['mean', 'count'],
        'acerto_com_delta': ['mean', 'count']
    }).reset_index()
    metrics.columns = [group_by if isinstance(group_by, str) else '_'.join(group_by), 'taxa_acerto_sem_delta', 'total_previsoes_sem_delta',
                      'taxa_acerto_com_delta', 'total_previsoes_com_delta']
    metrics['taxa_acerto_sem_delta'] = metrics['taxa_acerto_sem_delta'] * 100
    metrics['taxa_acerto_com_delta'] = metrics['taxa_acerto_com_delta'] * 100
    return metrics

# Função para exportar dados filtrados
def export_data(df, pair, start_date, end_date, day):
    filtered_df = df.copy()
    if pair != 'Todos':
        filtered_df = filtered_df[filtered_df['par'] == pair]
    filtered_df = filtered_df[(filtered_df['timestamp'] >= start_date) & (filtered_df['timestamp'] <= end_date)]
    if day != 'Todos':
        filtered_df = filtered_df[filtered_df['day_of_week'] == day]
    
    buffer = io.StringIO()
    filtered_df.to_csv(buffer, index=False)
    buffer.seek(0)
    return dcc.send_data_frame(filtered_df.to_csv, 'filtered_data.csv')