import streamlit as st
import pandas as pd
import altair as alt
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

    df_group = df.groupby("Cliente").agg(
        total_vendas=("TotalVenda", "sum"),
        num_compras=("Data", "count"),
        itens_totais=("QuantidadeItens", "sum")
    ).reset_index()

    # DEBUG: mostrar tipos e amostras
    st.write("📊 Tipos em df_group:")
    st.write(df_group.dtypes)

    st.write("🔢 Valores únicos de num_compras antes da limpeza:")
    st.write(df_group["num_compras"].unique())

    # Forçar num_compras a ser numérico e tratar problemas
    df_group["num_compras"] = pd.to_numeric(df_group["num_compras"], errors="coerce")
    df_group["num_compras"] = df_group["num_compras"].fillna(0)

    # Calcular ticket médio com proteção contra divisão por zero
    df_group["ticket_medio"] = df_group["total_vendas"] / df_group["num_compras"].where(df_group["num_compras"] != 0, pd.NA)
    df_group["ticket_medio"] = df_group["ticket_medio"].fillna(0)

    # DEBUG: valores finais
    st.write("✅ Dados após tratamento:")
    st.write(df_group.head())

    total_customers = df_group.shape[0]
    returning_customers = df_group[df_group["num_compras"] > 1].shape[0]

    return total_customers, returning_customers, df_group

# ---------------- CARREGAMENTO DE DADOS ----------------

df_vendas_agrupado = validar_df("df_vendas_agrupado", processa_df_venda_agrupado)
df_cadastro = validar_df("df_cadastro", carregar_df_cadastro)

# ---------------- FILTRO DE CLIENTES ----------------

ignorar_99999 = st.checkbox("Ignorar cliente 99999", value=True)
if ignorar_99999:
    df_vendas_agrupado = df_vendas_agrupado[df_vendas_agrupado["Cliente"] != 99999]

# ---------------- CÁLCULO DE MÉTRICAS ----------------

total_customers, returning_customers, df_clientes = calcular_metricas_clientes(df_vendas_agrupado)
return_rate = (returning_customers / total_customers * 100) if total_customers else 0

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
df_clientes["total_vendas_fmt"] = df_clientes["total_vendas"].map(formatar_moeda_brasileira)
df_clientes["ticket_medio_fmt"] = df_clientes["ticket_medio"].map(formatar_moeda_brasileira)

df_display = df_clientes.rename(columns={
    "Cliente": "Cliente",
    "total_vendas_fmt": "Total Vendido",
    "num_compras": "Compras",
    "ticket_medio_fmt": "Ticket Médio",
    "itens_totais": "Itens Totais"
})[
    ["Cliente", "Total Vendido", "Compras", "Ticket Médio", "Itens Totais"]
]

st.dataframe(df_display, use_container_width=True)

# ---------------- GRÁFICO TOP CLIENTES ----------------

st.markdown("### 📊 Top Clientes por Valor Vendido")

top_n = st.slider("Top N Clientes", min_value=5, max_value=50, value=10, step=1)
top_df = df_clientes.head(top_n)

chart = (
    alt.Chart(top_df)
    .mark_bar()
    .encode(
        x=alt.X("total_vendas:Q", title="Total Vendido"),
        y=alt.Y("Cliente:N", sort="-x", title="Cliente"),
        color=alt.Color("total_vendas:Q", scale=alt.Scale(scheme="blues"), legend=None),
        tooltip=[
            alt.Tooltip("Cliente", title="Cliente"),
            alt.Tooltip("num_compras:Q", title="Compras"),
            alt.Tooltip("ticket_medio:Q", title="Ticket Médio", format=",.2f")
        ]
    )
    .properties(height=400, title=f"Top {top_n} Clientes por Valor Vendido")
)

st.altair_chart(chart, use_container_width=True)
