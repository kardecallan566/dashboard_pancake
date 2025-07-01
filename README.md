# Dashboard de Análise de Previsões - Pancake

Este projeto é um dashboard interativo desenvolvido em Python utilizando a biblioteca Dash para análise de dados financeiros do arquivo `dados.csv`. O dashboard permite explorar taxas de acerto de previsões, distribuições de direções, diferenças de preço e correlações, com filtros interativos por par de moedas e intervalo de datas.

## Funcionalidades

- **Taxa de Acerto por Hora e Dia**: Gráficos de barras mostrando a performance das previsões por hora do dia e dia da semana.
- **Taxa de Acerto por Par**: Análise da taxa de acerto para diferentes pares de moedas (ex.: BNB/USDC).
- **Distribuição de Previsões**: Gráfico de pizza com a distribuição de previsões por par.
- **Evolução Temporal**: Gráfico de linha mostrando a taxa de acerto ao longo do tempo, com filtro de intervalo de datas.
- **Análise de Erros**: Gráfico de dispersão para erros de previsão, com opção de alternar entre erros com e sem delta.
- **Distribuição de Direções**: Comparação entre direções reais e previstas.
- **Correlação entre Variáveis**: Heatmap mostrando correlações entre valores reais e previstos.
- **Diferença de Preço**: Histograma da diferença absoluta entre valores reais e previstos.
- **Filtros Interativos**: Filtros por par de moedas e intervalo de datas para análises personalizadas.
- **Design Moderno**: Interface com tema escuro, layout responsivo e estilização com Tailwind CSS.

## Requisitos

- Python 3.8+
- Dependências:
  - pandas
  - plotly
  - dash
  - seaborn
  - numpy

## Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/kardecallan566/dashboard_pancake.git
   cd dashboard_pancake
   ```

2. Crie um ambiente virtual (opcional, mas recomendado):
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. Instale as dependências:
   ```bash
   pip install pandas plotly dash seaborn numpy
   ```

4. Coloque o arquivo `dados.csv` no diretório raiz do projeto. O arquivo deve seguir o formato:
   ```
   timestamp,par,valor_real,previsao,previsao_com_delta,direcao_real,direcao_prevista,direcao_com_delta,acerto_sem_delta,acerto_com_delta,total_previsoes,acertos_sem_delta_total,acertos_com_delta_total
   2025-06-03 17:47:27,BNB/USDC,665.85,667.2789,666.463139828413,DOWN,UP,UP,False,False,1,0,0
   ...
   ```

## Como Usar

1. Execute o script do dashboard:
   ```bash
   python dashboard.py
   ```

2. Acesse o dashboard no navegador em:
   ```
   http://127.0.0.1:8050
   ```

3. Utilize os filtros interativos (par de moedas e intervalo de datas) para explorar os dados.

## Estrutura do Projeto

```
dashboard_pancake/
├── dados.csv          # Arquivo de dados (não incluído no repositório)
├── dashboard.py       # Script principal do dashboard
├── README.md          # Este arquivo
```

## Capturas de Tela

*(Adicione capturas de tela do dashboard aqui, se desejar. Você pode fazer upload das imagens para o diretório `/images` no repositório e referenciá-las, por exemplo:)*
```markdown
![Dashboard Overview](images/dashboard_overview.png)
```

## Contribuições

Contribuições são bem-vindas! Para contribuir:
1. Faça um fork do repositório.
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`).
3. Commit suas alterações (`git commit -m 'Adiciona nova funcionalidade'`).
4. Envie para o repositório remoto (`git push origin feature/nova-funcionalidade`).
5. Abra um Pull Request.

## Licença

Este projeto está licenciado sob a [MIT License](LICENSE).

## Contato

Para dúvidas ou sugestões, entre em contato via [GitHub Issues](https://github.com/kardecallan566/dashboard_pancake/issues) ou diretamente com [kardecallan566](https://github.com/kardecallan566).