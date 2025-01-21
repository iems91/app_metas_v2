import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
import pytz
from datetime import datetime, timedelta
from dash.exceptions import PreventUpdate
from flask_caching import Cache
from flask_compress import Compress 
from feriados import *
from metas import *
from function import *
from config import *

rca_nao_controla = [1,6,7,11,9998,9999]

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
Compress(app.server)  # Ativa a compressão gzip para otimizar transferência de dados

# Configuração do cache
cache = Cache(app.server, config={
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 300
})


# df_vendas = processar_dados(query_vendas)

# # Extraindo os anos únicos da coluna 'DATA' do df_vendas
# anos_vendas = df_vendas['DATA'].dt.year.unique()
# opcoes_anos = [{'label': str(ano), 'value': ano} for ano in sorted(anos_vendas, reverse=True)]

# meses_vendas = df_vendas['DATA'].dt.month.unique()
# opcoes_meses = [{'label': str(mes), 'value': mes} for mes in sorted(meses_vendas, reverse=True)]

# # Adicionar a opção "Todos" no dropdown
# opcoes_anos.insert(0, {'label': 'Todos', 'value': 'Todos'})
# opcoes_meses.insert(0, {'label': 'Todos', 'value': 'Todos'})

app.layout = html.Div([
    dbc.Container([
        dcc.Store(id='dataset_venda_liq', data={}),
        dcc.Store(id='dataset_metas_codusur', data={}),
        dcc.Store(id='data_atual', data={}),
        dcc.Store(id='meta_ano', data={}),
        dcc.Store(id='meta_mes', data={}),
        dcc.Store(id='meta_semana', data={}),
        dcc.Store(id='meta_sabado', data={}),
        dcc.Interval(id='interval-dynamic', interval=30*1000, n_intervals=0),
        dcc.Interval(id='interval-static', interval=43200*1000, n_intervals=0),
        dbc.Row([
            dbc.Col([
                dbc.Card(
                    dbc.CardBody([
                        # dbc.Row([
                        #     dbc.Col([
                        #         dcc.Dropdown(
                        #             id='dropdown-ano',
                        #             options=opcoes_anos,
                        #             value='Todos',  # Valor padrão
                        #             clearable=False,
                        #             style={'width': '100%', 'color': 'black'}
                        #         )
                        #     ], sm=12, md=6),
                        #     dbc.Col([
                        #         dcc.Dropdown(
                        #             id='dropdown-mes',
                        #             options=opcoes_meses,
                        #             value='Todos',  # Valor padrão
                        #             clearable=False,
                        #             style={'width': '100%', 'color': 'black'}
                        #         )
                        #     ], sm=12, md=6)
                        # ],className='g-2 my-auto', style={'margin-top': '7px'}),
                        dbc.Row([
                            dbc.Col([
                                dcc.Graph(id='graph1', className='dbc', config=config_graph)
                            ], sm=12, md=4),
                            dbc.Col([
                                dcc.Graph(id='graph2', className='dbc', config=config_graph)
                            ], sm=12, md=4),
                            dbc.Col([
                                dcc.Graph(id='graph3', className='dbc', config=config_graph)
                            ], sm=12, md=4)
                        ], className='g-2 my-auto', style={'margin-top': '7px'}),
                        dbc.Row([
                            dbc.Col([
                                dcc.Graph(id='graph4', className='dbc', config=config_graph)
                            ], sm=12, md=12)
                        ], className='g-2 my-auto', style={'margin-top': '7px'})
                    ])
                , style=tab_card)
            ], sm=12, lg=12),
        ], className='g-2 my-auto', style={'margin-top': '7px'}),
    ], fluid=True, style={'height': '100vh'})
])

@app.callback(
    Output('dataset_metas_codusur', 'data'),
    Output('data_atual', 'data'),
    Output('meta_ano', 'data'),
    Output('meta_mes', 'data'),
    Output('meta_semana', 'data'),
    Output('meta_sabado', 'data'),
    Input('interval-static', 'n_intervals')    
)
@cache.memoize()
def update_data(n_intervals):
    tz = pytz.timezone('America/Sao_Paulo')
    data_atual = datetime.now(tz).date()
       
    df_metas_geral = pd.read_csv(csv_url_geral)
    primeira_linha = df_metas_geral.iloc[0]
    meta_ano = primeira_linha['META_ANO']
    meta_mes = primeira_linha['META_MES']
    meta_semana = primeira_linha['META_SEMANA']
    meta_sabado = primeira_linha['META_SABADO']

    df_metas_usuario = pd.read_csv(csv_url_codusur)

    df_metas_usuario = df_metas_usuario[~df_metas_usuario['CODUSUR'].isin(rca_nao_controla)]
    df_metas_usuario_store = df_metas_usuario.to_dict('records')
    
    return  df_metas_usuario_store, data_atual, meta_ano, meta_mes, meta_semana, meta_sabado
@app.callback(
    Output('dataset_venda_liq', 'data'),
    Input('interval-dynamic', 'n_intervals')
)
@cache.memoize()
def update_dynamic_data(n_intervals):
    df_venda_liq_geral = venda_liquida()
    df_venda_liq_geral_store = df_venda_liq_geral.to_dict('records')
    return df_venda_liq_geral_store
@app.callback(
    Output('graph1', 'figure'),
    Input('dataset_venda_liq', 'data'),
    Input('data_atual', 'data'),
    Input('meta_ano','data')
)
def graph1(dataset_venda_liq, data_atual, meta_ano):
    if not dataset_venda_liq:
        raise PreventUpdate
   
    data_atual = datetime.fromisoformat(data_atual).date()
    
    inicial = data_atual.replace(month=1, day=1)
    final = data_atual.replace(month=12, day=31)
   
    dias_uteis_ano = calcular_dias_uteis(inicial, final, feriados)
    dias_uteis_to_date = calcular_dias_uteis(inicial, data_atual, feriados)
    sabados_ano = calcular_sabados(inicial, final, feriados)
    sabados_to_date = calcular_sabados(inicial, data_atual, feriados)
    
 
    # Gerar o range de dias úteis entre as datas fornecidas
    filtro_dias_uteis = pd.date_range(start=inicial, end=final, freq='B')

    df1 = pd.DataFrame.from_dict(dataset_venda_liq).reset_index()
    # Filtrar o DataFrame para incluir apenas os registros em dias úteis
    df1['DATA'] = pd.to_datetime(df1['DATA'], errors='coerce')

    df_semana = df1[df1['DATA'].isin(filtro_dias_uteis)]
    # Agora você pode somar a coluna 'VENDA_LIQ' com base nesse filtro
    
    total_vendas_semana = df_semana['VENDA_LIQ'].sum()

    # Gerar um intervalo de datas
    datas = pd.date_range(start=inicial, end=final, freq='D')
    # Filtrar apenas os sábados
    sabados = datas[datas.weekday == 5]
    df_sabado = df1[df1['DATA'].isin(sabados)]
    total_vendas_sabados = df_sabado['VENDA_LIQ'].sum()
    
    projecao_semana = (total_vendas_semana/dias_uteis_to_date)*dias_uteis_ano
    projecao_sabado = (total_vendas_sabados/sabados_to_date)*sabados_ano
    projecao_total = projecao_semana + projecao_sabado
    
    total_vendas = total_vendas_semana + total_vendas_sabados
    
    perc_atingido = (total_vendas/meta_ano)*100
    projecao_total_percent = (projecao_total/meta_ano)*100
    
    
    
    fig1 = go.Figure(go.Indicator(
        mode="gauge+number",
        value=perc_atingido,
        number={"suffix": "%", "valueformat": ",.2f"},
        title={"text": "Atingimento da meta do Ano"},
        gauge={
            'axis': {'range': [None, 100], 
                     'tickwidth': 1, 
                     'tickcolor': "black",
                     'showticklabels': True,
                     'tickvals': [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]  # Marcas no eixo
                     },  # Ajuste o intervalo conforme necessário
            'bar': {'color': "darkgreen"},
            'bgcolor': "lightgray",
            'steps': [
                {'range': [0, 100], 'color': "white"},

            ],
            'threshold': {
                'line': {'color': "red", 'width': 7},
                'thickness': 0.95,
                'value': projecao_total_percent
            }
    }
    ))
    
    fig1.update_layout(
        main_config,
        height=400,
        template=template_theme,
        margin=dict(t=50, b=10, l=40, r = 40)
    )
    fig1.add_annotation(
        x=0.5, y=0,  # Posição do texto,  # Posição do texto
        text= f"Projeção: {projecao_total_percent:.2f}%",  # Quebra de linha com <br>
        showarrow=False,
        font=dict(size=25)
    ) 
    return fig1



@app.callback(
    Output('graph2', 'figure'),
    Input('dataset_venda_liq', 'data'),
    Input('data_atual', 'data'),
    Input('meta_mes', 'data')
)
def graph2(dataset_venda_liq, data_atual, meta_mes):
    if not dataset_venda_liq:
        raise PreventUpdate
   
    data_atual = datetime.fromisoformat(data_atual).date()
    inicial = data_atual.replace(day=1)
    proximo_mes = (inicial + timedelta(days=31)).replace(day=1)   
    final = proximo_mes - timedelta(days=1)
    ontem = data_atual - timedelta(days=1)
   
    dias_uteis_mes = calcular_dias_uteis(inicial, final, feriados)
    dias_uteis_mes_to_date = calcular_dias_uteis(inicial, data_atual, feriados)
   
    sabados_mes = calcular_sabados(inicial, final, feriados)
    sabados_to_mes_date = calcular_sabados(inicial, data_atual, feriados)
    
    # Gerar o range de dias úteis entre as datas fornecidas
    filtro_dias_uteis_mes = pd.date_range(start=inicial, end=final, freq='B')

    df2 = pd.DataFrame.from_dict(dataset_venda_liq).reset_index()
    # Filtrar o DataFrame para incluir apenas os registros em dias úteis
    df2['DATA'] = pd.to_datetime(df2['DATA'], errors='coerce')

    df_semana = df2[df2['DATA'].isin(filtro_dias_uteis_mes)]
    # Agora você pode somar a coluna 'VENDA_LIQ' com base nesse filtro
    
    total_vendas_semana = df_semana['VENDA_LIQ'].sum()
    if pd.isna(total_vendas_semana):
        total_vendas_semana = 0
    else:
        pass
    
    
    # Gerar um intervalo de datas
    datas = pd.date_range(start=inicial, end=final, freq='D')
    # Filtrar apenas os sábados
    sabados = datas[datas.weekday == 5]
    df_sabado = df2[df2['DATA'].isin(sabados)]
    total_vendas_sabados = df_sabado['VENDA_LIQ'].sum()
    

    projecao_semana = (total_vendas_semana / dias_uteis_mes_to_date * dias_uteis_mes) if dias_uteis_mes_to_date != 0 else 0
    projecao_sabado = (total_vendas_sabados / sabados_to_mes_date * sabados_mes) if sabados_to_mes_date != 0 else 0   
    projecao_total = projecao_semana+projecao_sabado
    total_vendas = total_vendas_semana + total_vendas_sabados
    
    perc_atingido = (total_vendas/meta_mes)*100
    projecao_total_percent = (projecao_total/meta_mes)*100
    
    fig2 = go.Figure(go.Indicator(
        mode="gauge+number",
        value=perc_atingido,
        number={"suffix": "%", "valueformat": ",.2f"},
        title={"text": "Atingimento da meta do Mês"},
        gauge={
            'axis': {'range': [None, 100], 
                     'tickwidth': 1, 
                     'tickcolor': "black",
                     'showticklabels': True,
                     'tickvals': [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]  # Marcas no eixo
                     },  # Ajuste o intervalo conforme necessário
            'bar': {'color': "darkgreen"},
            'bgcolor': "lightgray",
            'steps': [
                {'range': [0, 100], 'color': "white"},

            ],
            'threshold': {
                'line': {'color': "red", 'width': 7},
                'thickness': 0.95,
                'value': projecao_total_percent
            }
    }
    ))
  
    fig2.update_layout(
        main_config,
        height=400,
        template=template_theme,
        margin=dict(t=50, b=10, l=40, r = 40)
    )
    
    fig2.add_annotation(
        x=0.5, y=0,  # Posição do texto
        text= f"Projeção: {projecao_total_percent:.2f}%",  # Quebra de linha com <br>
        showarrow=False,
        font=dict(size=25)
    )   


    return fig2

@app.callback(
    Output('graph3', 'figure'),
    Input('dataset_venda_liq', 'data'),
    Input('data_atual', 'data'),
    Input('meta_semana', 'data'),
    Input('meta_sabado', 'data')
)
def graph3(dataset_venda_liq, data_atual, meta_semana, meta_sabado):
    if not dataset_venda_liq:
        raise PreventUpdate
    
    data_atual = datetime.fromisoformat(data_atual).date()
    inicial = data_atual.replace(day=1)
    proximo_mes = (inicial + timedelta(days=31)).replace(day=1)   
    final = proximo_mes - timedelta(days=1)
    ontem = data_atual - timedelta(days=1)
    

    
    # Gerar um intervalo de datas
    datas = pd.date_range(start=inicial, end=ontem, freq='D')
    datas_exceto_hoje = pd.date_range(start=inicial, end=ontem, freq='B')
    sabados_exceto_hoje = datas[datas.weekday == 5]

    df3 = pd.DataFrame.from_dict(dataset_venda_liq).reset_index()
    df3['DATA'] = pd.to_datetime(df3['DATA'], errors='coerce')
    df_hoje = df3[df3['DATA'].dt.date == data_atual]

 
    if data_atual.weekday() == 5:
        df_sabado_exceto_hoje = df3[df3['DATA'].isin(sabados_exceto_hoje)]
        sabados_restantes = calcular_sabados(data_atual, final, feriados)
        total_vendas_sabados_exceto_hoje = df_sabado_exceto_hoje['VENDA_LIQ'].sum()
        meta_hoje = (meta_sabado - total_vendas_sabados_exceto_hoje) / sabados_restantes
              
    else:
        df_dias_uteis_exceto_hoje = df3[~df3['CODUSUR'].isin(rca_nao_controla)]
        df_dias_uteis_exceto_hoje = df3[df3['DATA'].isin(datas_exceto_hoje)]
        dias_uteis_restantes = calcular_dias_uteis(data_atual, final, feriados)
        total_vendas_dias_uteis_ate_ontem = df_dias_uteis_exceto_hoje['VENDA_LIQ'].sum()
        meta_hoje = (meta_semana - total_vendas_dias_uteis_ate_ontem) / dias_uteis_restantes
    
    total_vendas_hoje = df_hoje['VENDA_LIQ'].sum()
    perc_atingido_hoje = (total_vendas_hoje/meta_hoje)*100
    
    fig3 = go.Figure(go.Indicator(
        mode="gauge+number",
        value=perc_atingido_hoje,
        number={"suffix": "%", "valueformat": ",.2f"},
        title={"text": "Atingimento da meta do dia"},
        gauge={
            'axis': {'range': [None, 100], 
                     'tickwidth': 1, 
                     'tickcolor': "black",
                     'showticklabels': True,
                     'tickvals': [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]  # Marcas no eixo
                     },  # Ajuste o intervalo conforme necessário
            'bar': {'color': "darkgreen"},
            'bgcolor': "lightgray",
            'steps': [
                {'range': [0, 100], 'color': "white"},

            ],
        }
    ))
    
    fig3.update_layout(
        main_config,
        height=400,
        template=template_theme,
        margin=dict(t=50, b=10, l=40, r = 40)
    )

    return fig3

@app.callback(
    Output('graph4', 'figure'),
    Input('dataset_venda_liq', 'data'),
    Input('dataset_metas_codusur', 'data'),
    Input('data_atual', 'data')
)
def graph4(dataset_venda_liq, dataset_metas_codusur, data_atual):
    if not dataset_venda_liq:
        raise PreventUpdate
    
    df_metas_usuario = pd.DataFrame.from_dict(dataset_metas_codusur).reset_index()

    
    data_atual = datetime.fromisoformat(data_atual).date()
    inicial = data_atual.replace(day=1)
    proximo_mes = (inicial + timedelta(days=31)).replace(day=1)   
    final = proximo_mes - timedelta(days=1)
    ontem = data_atual - timedelta(days=1)
    
    
    # Gerar um intervalo de datas
    datas = pd.date_range(start=inicial, end=data_atual, freq='D')
    datas_exceto_hoje = pd.date_range(start=inicial, end=ontem, freq='B')
    sabados_exceto_hoje = datas[datas.weekday == 5]

    df4 = pd.DataFrame.from_dict(dataset_venda_liq).reset_index()
    df4['DATA'] = pd.to_datetime(df4['DATA'], errors='coerce')
    df_hoje = df4[df4['DATA'].dt.date == data_atual]


    
    if data_atual.weekday() == 5:  # Se for sábado
        # Filtra as vendas dos sábados anteriores (exceto o sábado atual)
        df_sabado_exceto_hoje = df4[df4['DATA'].isin(sabados_exceto_hoje)]
        
        # Calcula os sábados restantes no mês a partir da data atual
        sabados_restantes = calcular_sabados(data_atual, final, feriados)
        
        # Calcula a venda líquida acumulada por CODUSUR nos sábados anteriores
        df_total_vendas_sabados_exceto_hoje = df_sabado_exceto_hoje.groupby('CODUSUR', as_index=False)['VENDA_LIQ'].sum()
        
        # Filtra apenas os resultados que estão em lista_rca
        df_total_vendas_sabados_exceto_hoje = df_total_vendas_sabados_exceto_hoje[~df_total_vendas_sabados_exceto_hoje['CODUSUR'].isin(rca_nao_controla)]
        
        # Mescla com o DataFrame de metas para calcular o META_HOJE para cada vendedor
        df_merged = pd.merge(df_metas_usuario, df_total_vendas_sabados_exceto_hoje, on='CODUSUR', suffixes=('_METAS', '_VENDAS'), how='left')
        
        # Calcula a meta de hoje para cada vendedor com base nos sábados restantes
        df_merged['META_HOJE'] = (df_merged['META_SABADO'] - df_merged['VENDA_LIQ']) / sabados_restantes
        
        # Mescla com o DataFrame `df_hoje` para incluir as vendas do dia atual
        df_merged = pd.merge(df_merged, df_hoje, on='CODUSUR', suffixes=('_MERGE', '_HOJE'), how='left')
        
        # Remove colunas desnecessárias e calcula o percentual de atingimento
        df_meta_hoje = df_merged.drop(['DATA'], axis=1)
        df_meta_hoje = df_meta_hoje[df_meta_hoje['META_SABADO'] != 0]

        
        df_meta_hoje.fillna(0, inplace=True)  # Substituir valores nulos por 0
        df_meta_hoje['META_HOJE']= (df_meta_hoje['META_SABADO']-df_meta_hoje['VENDA_LIQ_MERGE'])/sabados_restantes
        df_meta_hoje['PERC_ATINGIDO'] = (df_meta_hoje['VENDA_LIQ_HOJE'] / df_meta_hoje['META_HOJE']) * 100

              
    else:
        df_dias_uteis_exceto_hoje = df4[df4['DATA'].isin(datas_exceto_hoje)]
        dias_uteis_restantes = calcular_dias_uteis(data_atual, final, feriados)
        df_total_vendas_dias_uteis_exceto_hoje = df_dias_uteis_exceto_hoje.groupby('CODUSUR', as_index=False)['VENDA_LIQ'].sum()
        df_total_vendas_dias_uteis_exceto_hoje = df_total_vendas_dias_uteis_exceto_hoje[~df_total_vendas_dias_uteis_exceto_hoje['CODUSUR'].isin(rca_nao_controla)]

        df_merged = pd.merge(df_metas_usuario, df_total_vendas_dias_uteis_exceto_hoje, on='CODUSUR', suffixes=('_METAS', '_VENDAS'))
        
        if data_atual == inicial:
            df_merged['CODUSUR'] = df_metas_usuario['CODUSUR']
            df_merged['META_HOJE'] = df_metas_usuario['META_SEMANA']/dias_uteis_restantes
            df_merged.reset_index()

        else:
            df_merged['META_HOJE'] = (df_merged['META_SEMANA']-df_merged['VENDA_LIQ'])/dias_uteis_restantes
        
        df_merged = pd.merge(df_merged, df_hoje, on='CODUSUR', suffixes=('_MERGE', '_HOJE'), how='left')
        df_meta_hoje = df_merged.drop(['DATA'], axis=1)
        df_meta_hoje['PERC_ATINGIDO'] = (df_meta_hoje['VENDA_LIQ_HOJE']/df_meta_hoje['META_HOJE'])*100
        df_meta_hoje = df_meta_hoje.dropna(subset=['CODUSUR', 'PERC_ATINGIDO'])
        cores_barras = [
                'blue' if perc < 80 else 
                'blue' if 80 <= perc < 100 else 
                'blue' if 100 <= perc < 120 else 
                'blue'
                for perc in df_meta_hoje['PERC_ATINGIDO']
            ]


    fig4 = go.Figure(go.Bar(
        x=df_meta_hoje['PERC_ATINGIDO'],  # Valores no eixo x (Percentual de atingimento)
        y=df_meta_hoje['CODUSUR'].astype(str),        # Valores no eixo y (Nomes dos vendedores)
        orientation='h',                  # Orientação horizontal
        text=[f'{p:.2f}%' for p in df_meta_hoje['PERC_ATINGIDO']],  # Exibir o percentual com 2 casas decimais
        textfont=dict(
            size=16,
            family='Arial'
        ),
            marker=dict(
                color=cores_barras  # Cor das barras
            ),
        textposition='auto', # Posição do texto
        width=0.8  
    ))

    # Adicionando título e labels
    fig4.update_layout(
        main_config,
        title='Percentual de Atingimento de Meta diária por Vendedor',
        xaxis_title='Percentual de Atingimento (%)',
        yaxis_title='Vendedores (RCA)',
        xaxis=dict(range=[0, 100]),  # Definindo o intervalo do eixo x de 0 a 100%
        height=600,
        template=template_theme,
        margin=dict(t=50, b=10, l=40, r = 40),
        yaxis=dict(
            tickfont=dict(
                size=25,
                family='Arial'
            )  
        )
    )

    # Exibindo o gráfico
    return fig4

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8350, debug=False)

