import streamlit as st
import pandas as pd
import altair as alt
from typing import Tuple, Optional
from utils.processamento import (
    calcular_vendas_agrupadas,
    adicionar_nomes_produtos,
    carregar_df_vendas,
    carregar_df_cadastro
)
from utils.moeda import formatar_moeda_brasileira
from utils.sessao import inicializar_app, validar_df

# ---------------- CONFIGURAÇÃO INICIAL ----------------
st.set_page_config(page_title="Produtos Vendidos", layout="wide")
inicializar_app()
st.title("📦 Produtos Vendidos")

# ---------------- CARREGAMENTO DOS DADOS ----------------
df_vendas = validar_df("df_vendas", carregar_df_vendas)
df_cadastro = validar_df("df_cadastro", carregar_df_cadastro)

# ---------------- FUNÇÕES AUXILIARES ----------------

@st.cache_data
def preparar_produtos(df_vendas: pd.DataFrame, df_cadastro: pd.DataFrame) -> pd.DataFrame:
    df = calcular_vendas_agrupadas(df_vendas)
    df = adicionar_nomes_produtos(df, df_cadastro)
    df = df.rename(columns={"ProNom": "Produto"})
    df = df.sort_values(by="TotalItem", ascending=False)
    df["TotalFormatado"] = df["TotalItem"].map(formatar_moeda_brasileira)
    return df

@st.cache_data
def detalhar_giro_vendas(df_vendas: pd.DataFrame, df_cadastro: pd.DataFrame, periodo: str) -> pd.DataFrame:
    df = df_vendas.copy()

    # Remover ProNom duplicado da tabela de vendas (evita conflito no merge)
    if "ProNom" in df.columns:
        df = df.drop(columns=["ProNom"])

    # Merge com nome do produto
    df = df.merge(df_cadastro[["ProCod", "ProNom"]], how="left", on="ProCod")
    df = df.rename(columns={"ProNom": "Produto"})

    # Verificações
    if "Produto" not in df.columns or df["Produto"].isna().all():
        st.error("❌ Coluna 'Produto' não existe ou está totalmente vazia após o merge.")
        st.stop()

    if "Quantidade" not in df.columns:
        st.error("❌ Coluna 'Quantidade' não encontrada no DataFrame de vendas.")
        st.stop()

    if "Data" not in df.columns:
        st.error("❌ Coluna 'Data' não encontrada no DataFrame de vendas.")
        st.stop()

    # Datas
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df = df.dropna(subset=["Data"])

    # Criar coluna de período
    if periodo == "Ano":
        df["Periodo"] = df["Data"].dt.year
    elif periodo == "Semestre":
        df["Periodo"] = df["Data"].dt.year.astype(str) + " - S" + ((df["Data"].dt.month - 1) // 6 + 1).astype(str)
    elif periodo == "Trimestre":
        df["Periodo"] = df["Data"].dt.year.astype(str) + " - T" + ((df["Data"].dt.month - 1) // 3 + 1).astype(str)
    elif periodo == "Mês":
        df["Periodo"] = df["Data"].dt.to_period("M").astype(str)
    elif periodo == "Semana":
        df["Periodo"] = df["Data"].dt.strftime("%Y - Semana %U")
    elif periodo == "Dia da Semana":
        df["Periodo"] = df["Data"].dt.day_name()
    elif periodo == "Data":
        df["Periodo"] = df["Data"].dt.date
    else:
        st.error("❌ Período inválido selecionado.")
        st.stop()

    # Agrupamento
    df_grouped = df.groupby(["Periodo", "Produto"]).agg(Quantidade=("Quantidade", "sum")).reset_index()

    return df_grouped

# ---------------- TABELA GERAL ----------------
df_produtos = preparar_produtos(df_vendas, df_cadastro)

st.markdown("### 📝 Lista de Produtos Vendidos")
st.dataframe(
    df_produtos[["Produto", "Quantidade", "TotalFormatado"]]
    .rename(columns={"Quantidade": "Qtd Vendida", "TotalFormatado": "Total R$"}),
    use_container_width=True
)

# ---------------- TOP N ----------------
top_n = st.slider("Número de produtos no Top", min_value=5, max_value=100, value=10)
top_df = df_produtos.head(top_n)

st.markdown(f"### 📊 Top {top_n} Produtos por Valor Vendido")
bar_chart = (
    alt.Chart(top_df)
    .mark_bar()
    .encode(
        x=alt.X("TotalItem:Q", title="Total Vendido"),
        y=alt.Y("Produto:N", sort="-x", title="Produto"),
        tooltip=[
            alt.Tooltip("Produto", title="Produto"),
            alt.Tooltip("Quantidade:Q", title="Qtd Vendida"),
            alt.Tooltip("TotalItem:Q", title="Total Vendido", format=",.2f")
        ],
        color=alt.Color("TotalItem:Q", scale=alt.Scale(scheme="greens"), legend=None)
    )
    .properties(height=400)
)
st.altair_chart(bar_chart, use_container_width=True)

# ---------------- GIRO DE VENDAS ----------------
st.markdown("### 🔄 Giro de Venda por Período")

opcoes_periodo = [
    "Ano", "Semestre", "Trimestre", "Mês", "Semana", "Dia da Semana", "Data"
]
periodo_selecionado = st.selectbox("Selecionar tipo de período:", opcoes_periodo)

df_giro = detalhar_giro_vendas(df_vendas, df_cadastro, periodo_selecionado)

# Lista de períodos únicos para o usuário escolher um período específico
periodos_disponiveis = df_giro["Periodo"].unique().tolist()
periodo_especifico = st.selectbox("Selecionar período específico:", periodos_disponiveis)

df_filtrado = df_giro[df_giro["Periodo"] == periodo_especifico]

# Limitar aos 100 itens mais vendidos no período
df_filtrado = df_filtrado.sort_values(by="Quantidade", ascending=False).head(100)

# Mensagem explicativa
st.markdown(
    f"### 🥧 Gráfico de Pizza - Período: {periodo_especifico}\n"
    "_Exibindo os **100 produtos mais vendidos** no período selecionado._"
)

# Gráfico de pizza com os dados limitados
pie_chart = (
    alt.Chart(df_filtrado)
    .mark_arc()
    .encode(
        theta=alt.Theta(field="Quantidade", type="quantitative"),
        color=alt.Color(field="Produto", type="nominal"),
        tooltip=["Produto", "Quantidade"]
    )
    .properties(height=500, width=500)
)

st.altair_chart(pie_chart, use_container_width=True)


# Exibe a tabela dos dados usados na pizza
st.markdown("### 📋 Detalhamento dos Dados do Período Selecionado")
st.dataframe(
    df_filtrado.rename(columns={
        "Produto": "Produto",
        "Quantidade": "Qtd Vendida"
    }),
    use_container_width=True
)