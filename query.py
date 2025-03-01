csv_url_geral = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vRA2PlCiKzo29vA9GKN3oss25Nk_etlpusY2JUBACo1H43SgF1q7vxDdsREFmdRWqM65a5ftrxXFaCG/pub?output=csv'
csv_url_codusur = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vRY7dXT_QGrI8wf7G1Qv3IX8zqnj6AuSmhMUBuIMR27bcknn3CKLmw51Hsft1wuwasPAkjkMngOj7p8/pub?output=csv'
query_vendas ="""
    select
        v.CODUSUR, trunc(v.dtsaida) DATA, sum(v.vlvenda) VALOR
    from 
        view_vendas_resumo_faturamento v
    where 
        condvenda = 1
        and codsupervisor = 1
        and dtcancel is null
    group by 
        v.codusur, v.dtsaida
"""

query_devol ="""
    select
        d.CODUSUR, trunc(d.dtent) DATA, sum(d.vldevolucao) VALOR
    from 
        view_devol_resumo_faturamento d
    where 
        condvenda = 1
        and dtcancel is null
        and codsupervisor = 1
    group by 
        d.codusur, d.dtent
"""

query_devol_avulsa = """
    select
        a.CODUSUR, trunc(a.dtent) DATA, sum(a.vldevolucao) VALOR
    from 
        view_devol_resumo_faturavulsa a
    where
        codsupervisor = 1
    group by 
        a.codusur, a.dtent 
"""