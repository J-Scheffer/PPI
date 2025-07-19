import streamlit as st
import pandas as pd
import altair as alt
import math
from typing import Tuple
from utils.moeda import formatar_moeda_brasileira
from utils.processamento import carregar_df_cadastro, processa_df_venda_agrupado
from utils.sessao import inicializar_app, validar_df

# ---------------- CONFIGURAÇÃO INICIAL ----------------
st.set_page_config(page_title="Dados dos Clientes", layout="wide")
inicializar_app()
st.title("👥 Análise de Clientes")

# ---------------- FUNÇÕES AUXILIARES ----------------

@st.cache_data
def calcular_metricas_clientes(df_vendas_agrupado: pd.DataFrame) -> Tuple[int, int, pd.DataFrame]:
    """
    Calcula estatísticas relacionadas aos clientes:
    - Total de clientes
    - Quantos retornaram (mais de uma compra)
    - DataFrame com métricas por cliente
    """
    df = df_vendas_agrupado.copy()

    # Garante que as colunas numéricas são tratadas corretamente
    df["TotalVenda"] = pd.to_numeric(df["TotalVenda"], errors="coerce")
    df["QuantidadeItens"] = pd.to_numeric(df["QuantidadeItens"], errors="coerce")

    df_group = df.groupby("Cliente").agg(
        total_vendas=("TotalVenda", "sum"),
        num_compras=("Data", "count"),
        itens_totais=("QuantidadeItens", "sum")
    ).reset_index()

    # Cálculo seguro do ticket médio
    df_group["ticket_medio"] = df_group.apply(
        lambda row: row["total_vendas"] / row["num_compras"] if row["num_compras"] > 0 else 0,
        axis=1
    )

    total_customers = df_group.shape[0]
    returning_customers = df_group[df_group["num_compras"] > 1].shape[0]

    return total_customers, returning_customers, df_group

# ---------------- CARREGAMENTO DE DADOS ----------------

# Usando a abordagem mais segura do segundo código
if "df_vendas_agrupado" not in st.session_state:
    processa_df_venda_agrupado()

df_vendas_agrupado = st.session_state.get("df_vendas_agrupado")
if not isinstance(df_vendas_agrupado, pd.DataFrame) or df_vendas_agrupado.empty:
    st.error("❌ O DataFrame 'df_vendas_agrupado' não está disponível ou está vazio.")
    st.stop()

df_cadastro = validar_df("df_cadastro", carregar_df_cadastro)

# ---------------- FILTRO DE CLIENTES ----------------

ignorar_99999 = st.checkbox("Ignorar cliente 99999", value=True)
if ignorar_99999:
    df_vendas_agrupado = df_vendas_agrupado[df_vendas_agrupado["Cliente"] != 99999]

# ---------------- CÁLCULO DE MÉTRICAS ----------------

total_customers, returning_customers, df_clientes = calcular_metricas_clientes(df_vendas_agrupado)

# Cálculo seguro da taxa de retorno
return_rate = 0
if total_customers > 0:
    return_rate = (returning_customers / total_customers * 100)

# ---------------- EXIBIÇÃO DE KPIs ----------------

col1, col2, col3, col4 = st.columns(4)
col1.metric("Clientes", total_customers)
col2.metric("Clientes Retornaram", returning_customers)
col3.metric("Taxa de Retorno", f"{return_rate:.1f}%")
col4.metric("Compras Totais", df_vendas_agrupado.shape[0])

st.markdown("---")

# ---------------- TABELA DE CLIENTES ----------------

st.markdown("### 📋 Perfil dos Clientes")

df_clientes = df_clientes.sort_values("total_vendas", ascending=False)

# Formatação segura dos valores monetários
df_clientes["total_vendas_fmt"] = df_clientes["total_vendas"].apply(
    lambda x: formatar_moeda_brasileira(x) if not pd.isna(x) else "R$ 0,00"
)
df_clientes["ticket_medio_fmt"] = df_clientes["ticket_medio"].apply(
    lambda x: formatar_moeda_brasileira(x) if not pd.isna(x) else "R$ 0,00"
)

df_display = df_clientes.rename(columns={
    "Cliente": "Cliente",
    "total_vendas_fmt": "Total Vendido",
    "num_compras": "Compras",
    "ticket_medio_fmt": "Ticket Médio",
    "itens_totais": "Itens Totais"
})[["Cliente", "Total Vendido", "Compras", "Ticket Médio", "Itens Totais"]]

st.dataframe(df_display, use_container_width=True)

# ---------------- GRÁFICO TOP CLIENTES ----------------
st.markdown("### 📊 Top Clientes por Valor Vendido")

top_n = st.slider("Top N Clientes", min_value=5, max_value=50, value=10, step=1)
top_df = df_clientes.head(top_n).copy()

# Ajustes para o gráfico
if not top_df.empty:
    # Ajustar altura dinamicamente baseado no número de clientes
    chart_height = max(300, top_n * 25)  # Mínimo 300px, 25px por cliente
    
    chart = (
        alt.Chart(top_df)
        .mark_bar(
            cornerRadiusTopLeft=3,
            cornerRadiusTopRight=3,
            size=20  # Largura das barras
        )
        .encode(
            x=alt.X("total_vendas:Q", 
                   title="Total Vendido (R$)",
                   axis=alt.Axis(format=",.2f")),
            y=alt.Y("Cliente:N", 
                   sort="-x",
                   title="Clientes",
                   axis=alt.Axis(labelLimit=200)),  # Aumentar limite para labels longos
            color=alt.Color("total_vendas:Q",
                          legend=None,
                          scale=alt.Scale(scheme="blues")),
            tooltip=[
                alt.Tooltip("Cliente", title="ID Cliente"),
                alt.Tooltip("total_vendas:Q", title="Total Vendido", format=",.2f"),
                alt.Tooltip("num_compras:Q", title="N° de Compras"),
                alt.Tooltip("ticket_medio:Q", title="Ticket Médio", format=",.2f"),
                alt.Tooltip("itens_totais:Q", title="Itens Comprados")
            ]
        )
        .properties(
            height=chart_height,
            width=800,  # Largura fixa para melhor visualização
            title=f"Top {top_n} Clientes por Valor Vendido"
        )
        .configure_axis(
            grid=False,
            labelFontSize=12,
            titleFontSize=14
        )
        .configure_view(
            strokeWidth=0  # Remove borda
        )
    )
    
    st.altair_chart(chart, use_container_width=True)
else:
    st.warning("Não há dados suficientes para exibir o gráfico.")