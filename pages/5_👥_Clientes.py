import pandas as pd
import streamlit as st

def calcular_metricas_clientes(df_vendas_agrupado):
    # Agrupamento por cliente
    df_group = df_vendas_agrupado.groupby("Cliente").agg(
        total_vendas=pd.NamedAgg(column="Valor_Total", aggfunc="sum"),
        num_compras=pd.NamedAgg(column="Nota Fiscal", aggfunc="nunique"),
        itens_totais=pd.NamedAgg(column="Quantidade", aggfunc="sum")
    ).reset_index()

    # Debug: tipos antes da conversão
    st.markdown("📊 **Tipos em df_group:**")
    st.dataframe(df_group.dtypes)

    # Debug: valores únicos de num_compras
    st.markdown("🔎 **Valores únicos de num_compras antes da limpeza:**")
    st.dataframe(df_group["num_compras"].value_counts().reset_index())

    # Ignorar cliente de teste (se existir)
    if 99999 in df_group["Cliente"].values:
        st.checkbox("🔴 Ignorar cliente 99999", value=True)
        df_group = df_group[df_group["Cliente"] != 99999]

    # Conversão segura da coluna total_vendas
    try:
        df_group["total_vendas"] = pd.to_numeric(df_group["total_vendas"], errors="coerce")
    except Exception as e:
        st.error(f"Erro ao converter total_vendas para numérico: {e}")

    # Debug: depois da conversão
    st.markdown("🔧 **Total vendas após conversão:**")
    st.dataframe(df_group["total_vendas"].head())

    # Evitar divisão por zero com proteção
    df_group["ticket_medio"] = df_group.apply(
        lambda row: row["total_vendas"] / row["num_compras"] if row["num_compras"] > 0 else 0,
        axis=1
    )

    # Total de clientes
    total_clientes = df_group["Cliente"].nunique()

    # Clientes que compraram mais de uma vez
    clientes_retorno = df_group[df_group["num_compras"] > 1]["Cliente"].nunique()

    return total_clientes, clientes_retorno, df_group
