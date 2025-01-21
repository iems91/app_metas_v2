import oracledb as odb
import pandas as pd
from datetime import datetime
from acessos import *
from feriados import *
from query import *

def processar_dados(query):
    try:
        # Conectar ao banco de dados
        connection = odb.connect(
            user=usuario_odb,
            password=senha_odb,
            dsn=conexao_odb
        )

        # Criar um cursor
        cursor = connection.cursor()

        # Executar a consulta
        cursor.execute(query)

        # Obter todos os resultados da consulta
        consulta_odb = cursor.fetchall()

        # Obter os nomes das colunas da consulta
        colunas = [col[0] for col in cursor.description]

    except odb.DatabaseError as e:
        # Capturar erros de banco de dados e exibir uma mensagem de erro
        print(f"Erro ao acessar o banco de dados: {e}")
        return pd.DataFrame()  # Retorna um DataFrame vazio em caso de erro

    finally:
        # Certifique-se de que o cursor e a conexão sejam fechados
        try:
            cursor.close()
        except:
            pass
        try:
            connection.close()
        except:
            pass

        # Criar um DataFrame com os resultados
    df = pd.DataFrame(consulta_odb, columns=colunas)

    # Retornar o DataFrame
    return df

def venda_liquida ():
    df_vendas = processar_dados(query_vendas)
    df_devolucao = processar_dados(query_devol)
    df_devolucao_avulsa = processar_dados(query_devol_avulsa)

  
    # Realizar o merge mantendo todas as linhas de df_vendas
    df_venda_liq = df_vendas.merge(
        df_devolucao[['DATA', 'CODUSUR', 'VALOR']],
        on=['DATA', 'CODUSUR'],
        how='left',
        suffixes=('', '_DEVOL_MERGED')
    ).merge(
        df_devolucao_avulsa[['DATA', 'CODUSUR', 'VALOR']],
        on=['DATA', 'CODUSUR'],
        how='left',
        suffixes=('', '_DEVOL_AVUL_MERGED')
    )
    
    # Substituir valores NaN por zero para garantir que não hajam erros no cálculo
    df_venda_liq.fillna({
        'VALOR':0,
        'VALOR_DEVOL_MERGED': 0,
        'VALOR_DEVOL_AVUL_MERGED': 0
    }, inplace=True)
 

 
    df_venda_liq['VENDA_LIQ'] = df_venda_liq['VALOR'] - df_venda_liq['VALOR_DEVOL_MERGED'] - df_venda_liq['VALOR_DEVOL_AVUL_MERGED']

        # Remover colunas desnecessárias
    df_venda_liq.drop(columns=['VALOR', 'VALOR_DEVOL_MERGED', 'VALOR_DEVOL_AVUL_MERGED'], inplace=True)


    # Retornar DataFrame processado
    return df_venda_liq

def calcular_dias_uteis(data_inicio, data_fim, feriados):
    # Converter as datas de início e fim para datetime
    data_inicio = pd.to_datetime(data_inicio)
    data_fim = pd.to_datetime(data_fim)

    # Converter a lista de feriados para datetime
    feriados = pd.to_datetime(feriados)

    # Gerar um intervalo de datas úteis
    datas = pd.date_range(start=data_inicio, end=data_fim, freq='B')

    # Excluir os feriados
    dias_uteis = datas[~datas.isin(feriados)]

    # Contar e retornar o número de dias úteis
    return len(dias_uteis)

def calcular_sabados(data_inicio, data_fim, feriados):
    # Converter as datas de início e fim para datetime
    data_inicio = pd.to_datetime(data_inicio)
    data_fim = pd.to_datetime(data_fim)

    # Converter a lista de feriados para datetime
    feriados = pd.to_datetime(feriados)

    # Gerar um intervalo de datas
    datas = pd.date_range(start=data_inicio, end=data_fim, freq='D')

    # Filtrar apenas os sábados
    sabados = datas[datas.weekday == 5]

    # Excluir os sábados que são feriados
    sabados_sem_feriados = sabados[~sabados.isin(feriados)]

    # Contar e retornar o número de sábados
    return len(sabados_sem_feriados)

