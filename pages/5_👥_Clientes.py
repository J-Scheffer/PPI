import streamlit as st
import pandas as pd
import altair as alt

from utils.processamento import (
    calcular_vendas_agrupadas,
    adicionar_nomes_produtos,
    carregar_df_vendas,
    carregar_df_cadastro
)

from utils.moeda import formatar_moeda_brasileira
from utils.sessao import inicializar_app

st.set_page_config(page_title="Clientes", page_icon="👥")
inicializar_app()

st.title("👥 Análise de Clientes")

# Carregamento de dados
@st.cache_data

def carregar_dados():
    try:
        df_vendas = carregar_df_vendas()
        df_cadastro = carregar_df_cadastro()

        if df_vendas is None or df_vendas.empty:
            st.error("Erro: Dados de vendas não carregados corretamente.")
            return None, None

        if df_cadastro is None or df_cadastro.empty:
            st.error("Erro: Dados de cadastro não carregados corretamente.")
            return None, None

        return df_vendas, df_cadastro

    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None, None

# Métricas
@st.cache_data

def calcular_metricas_clientes(df):
    df_group = df.groupby("CliCod").agg({
        "NumNota": "nunique",
        "ValorTotal": "sum"
    }).rename(columns={
        "NumNota": "num_compras",
        "ValorTotal": "total_vendas"
    }).reset_index()

    df_group["ticket_medio"] = df_group.apply(
        lambda row: row["total_vendas"] / row["num_compras"] if pd.notnull(row["num_compras"]) and row["num_compras"] > 0 else 0,
        axis=1
    )

    total_customers = df_group.shape[0]
    returning_customers = df_group[df_group["num_compras"] > 1].shape[0]

    return total_customers, returning_customers, df_group

# Processamento

df_vendas, df_cadastro = carregar_dados()

if df_vendas is not None and df_cadastro is not None:
    df_vendas = adicionar_nomes_produtos(df_vendas, df_cadastro)
    df_vendas_agrupado = calcular_vendas_agrupadas(df_vendas)

    total_customers, returning_customers, df_clientes = calcular_metricas_clientes(df_vendas_agrupado)

    st.subheader("Métricas Gerais")
    col1, col2 = st.columns(2)
    col1.metric("Total de Clientes", total_customers)
    col2.metric("Clientes que Recompraram", returning_customers)

    st.subheader("Ticket Médio por Cliente")
    df_top_ticket = df_clientes.sort_values("ticket_medio", ascending=False).head(10)

    chart = alt.Chart(df_top_ticket).mark_bar().encode(
        x=alt.X("ticket_medio:Q", title="Ticket Médio", axis=alt.Axis(format=",.2f")),
        y=alt.Y("CliCod:N", sort="-x", title="Código do Cliente")
    ).properties(width=700, height=400)

    st.altair_chart(chart, use_container_width=True)

    st.subheader("Dados de Clientes")
    st.dataframe(df_clientes)
else:
    st.warning("Dados não disponíveis para análise.")
