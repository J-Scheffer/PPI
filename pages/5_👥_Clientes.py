import streamlit as st
import pandas as pd
from utils.processamento import (
    carregar_df_vendas,
    carregar_df_cadastro,
    adicionar_nomes_produtos
)
from utils.moeda import formatar_moeda_brasileira
from utils.sessao import inicializar_app

# Inicializar sessão
inicializar_app()

st.title("👥 Clientes")

@st.cache_data
def calcular_metricas_clientes(df_vendas_agrupado):
    df_group = df_vendas_agrupado.groupby("Cliente").agg(
        total_vendas=pd.NamedAgg(column="Valor_Total", aggfunc="sum"),
        num_compras=pd.NamedAgg(column="Nota Fiscal", aggfunc="nunique"),
        itens_totais=pd.NamedAgg(column="Quantidade", aggfunc="sum")
    ).reset_index()

    # Ignorar cliente de teste, se existir
    if 99999 in df_group["Cliente"].values:
        df_group = df_group[df_group["Cliente"] != 99999]

    # Garantir que total_vendas seja numérico
    df_group["total_vendas"] = pd.to_numeric(df_group["total_vendas"], errors="coerce")

    # Calcular ticket médio com proteção contra divisão por zero
    df_group["ticket_medio"] = df_group.apply(
        lambda row: row["total_vendas"] / row["num_compras"] if row["num_compras"] > 0 else 0,
        axis=1
    )

    total_clientes = df_group["Cliente"].nunique()
    clientes_retorno = df_group[df_group["num_compras"] > 1]["Cliente"].nunique()

    return total_clientes, clientes_retorno, df_group

# Carregar dados
df_vendas = carregar_df_vendas()
df_cadastro = carregar_df_cadastro()

# Adicionar nomes dos produtos
df_vendas = adicionar_nomes_produtos(df_vendas, df_cadastro)

# Exibir opção para excluir cliente de teste
ignorar_cliente = st.checkbox("🚫 Ignorar cliente 99999", value=True)
if ignorar_cliente:
    df_vendas = df_vendas[df_vendas["Cliente"] != 99999]

# Calcular métricas
total_customers, returning_customers, df_clientes = calcular_metricas_clientes(df_vendas)

# Exibir métricas
col1, col2 = st.columns(2)
col1.metric("👤 Total de Clientes", total_customers)
col2.metric("🔁 Clientes que Retornaram", returning_customers)

# Exibir tabela de clientes com formatação
df_mostrar = df_clientes.copy()
df_mostrar["total_vendas"] = df_mostrar["total_vendas"].apply(formatar_moeda_brasileira)
df_mostrar["ticket_medio"] = df_mostrar["ticket_medio"].apply(formatar_moeda_brasileira)
st.dataframe(df_mostrar, use_container_width=True)
