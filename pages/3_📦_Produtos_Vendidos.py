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
    """Prepara os dados de produtos vendidos com formatação adequada."""
    df = calcular_vendas_agrupadas(df_vendas)
    df = adicionar_nomes_produtos(df, df_cadastro)
    df = df.rename(columns={"ProNom": "Produto"})
    
    # Garantir que as colunas numéricas estão corretas
    df["TotalItem"] = pd.to_numeric(df["TotalItem"], errors="coerce")
    df["Quantidade"] = pd.to_numeric(df["Quantidade"], errors="coerce")
    
    df = df.sort_values(by="TotalItem", ascending=False)
    df["TotalFormatado"] = df["TotalItem"].apply(
        lambda x: formatar_moeda_brasileira(x) if not pd.isna(x) else "R$ 0,00"
    )
    return df.dropna(subset=["TotalItem", "Quantidade"])

@st.cache_data
def detalhar_giro_vendas(df_vendas: pd.DataFrame, df_cadastro: pd.DataFrame, periodo: str) -> pd.DataFrame:
    """Prepara os dados para análise temporal de vendas por produto."""
    df = df_vendas.copy()

    # Verificação e limpeza inicial
    if "ProNom" in df.columns:
        df = df.drop(columns=["ProNom"])
    
    if "ProCod" not in df.columns or "ProCod" not in df_cadastro.columns:
        st.error("❌ Coluna 'ProCod' não encontrada nos DataFrames.")
        st.stop()

    # Merge com nome do produto
    df = df.merge(
        df_cadastro[["ProCod", "ProNom"]].drop_duplicates(subset=["ProCod"]),
        how="left",
        on="ProCod"
    ).rename(columns={"ProNom": "Produto"})

    # Verificações pós-merge
    required_cols = ["Produto", "Quantidade", "Data"]
    for col in required_cols:
        if col not in df.columns:
            st.error(f"❌ Coluna '{col}' não encontrada após o merge.")
            st.stop()

    # Conversão e limpeza de dados
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df["Quantidade"] = pd.to_numeric(df["Quantidade"], errors="coerce")
    df = df.dropna(subset=["Data", "Quantidade", "Produto"])

    # Criação do período
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

    return df.groupby(["Periodo", "Produto"]).agg(Quantidade=("Quantidade", "sum")).reset_index()

# ---------------- TABELA GERAL ----------------
df_produtos = preparar_produtos(df_vendas, df_cadastro)

st.markdown("### 📝 Lista de Produtos Vendidos")
st.dataframe(
    df_produtos[["Produto", "Quantidade", "TotalFormatado"]]
    .rename(columns={"Quantidade": "Qtd Vendida", "TotalFormatado": "Total R$"}),
    use_container_width=True,
    height=400
)

# ---------------- TOP N ----------------
st.markdown("### 📊 Top Produtos por Valor Vendido")

top_n = st.slider("Número de produtos no Top", min_value=5, max_value=100, value=10)
top_df = df_produtos.head(top_n).copy()

# Container com rolagem para o gráfico
with st.container():
    st.write(f"**Top {top_n} Produtos por Valor Vendido**")
    
    # Criar container com rolagem vertical
    chart_container = st.container()
    with chart_container:
        # Ajustar altura dinamicamente baseado no número de itens
        chart_height = max(400, top_n * 20)  # Mínimo 400px, 20px por item
        
        if not top_df.empty:
            # Ordenar por TotalItem para garantir a ordem correta
            top_df = top_df.sort_values("TotalItem", ascending=True)
            
            # Criar gráfico de barras horizontais com rolagem
            bar_chart = (
                alt.Chart(top_df)
                .mark_bar()
                .encode(
                    x=alt.X("TotalItem:Q", title="Total Vendido (R$)"),
                    y=alt.Y(
                        "Produto:N",
                        sort="-x",
                        title="Produto",
                        axis=alt.Axis(labelLimit=300)  # Aumenta o limite para labels longos
                    ),
                    tooltip=[
                        alt.Tooltip("Produto", title="Produto"),
                        alt.Tooltip("Quantidade:Q", title="Qtd Vendida"),
                        alt.Tooltip("TotalItem:Q", title="Total Vendido", format=",.2f")
                    ],
                    color=alt.Color(
                        "TotalItem:Q",
                        scale=alt.Scale(scheme="greens"),
                        legend=None
                    )
                )
                .properties(
                    height=chart_height,
                    width=800
                )
                .configure_axisX(grid=False)
                .configure_axisY(grid=False)
                .configure_view(strokeWidth=0)
            )
            
            st.altair_chart(bar_chart, use_container_width=True)
        else:
            st.warning("Não há dados suficientes para exibir o gráfico.")

# ---------------- GIRO DE VENDAS ----------------
st.markdown("### 🔄 Giro de Venda por Período")

opcoes_periodo = [
    "Ano", "Semestre", "Trimestre", "Mês", "Semana", "Dia da Semana", "Data"
]
periodo_selecionado = st.selectbox("Selecionar tipo de período:", opcoes_periodo)

try:
    df_giro = detalhar_giro_vendas(df_vendas, df_cadastro, periodo_selecionado)
    
    if df_giro.empty:
        st.warning("Nenhum dado disponível para o período selecionado.")
        st.stop()
    
    # Lista de períodos únicos para seleção
    periodos_disponiveis = sorted(df_giro["Periodo"].unique().tolist())
    periodo_especifico = st.selectbox("Selecionar período específico:", periodos_disponiveis)
    
    df_filtrado = df_giro[df_giro["Periodo"] == periodo_especifico]
    df_filtrado = df_filtrado.sort_values("Quantidade", ascending=False).head(100)
    
    if df_filtrado.empty:
        st.warning("Nenhum dado disponível para o período específico selecionado.")
        st.stop()
    
    # Gráfico de pizza com container de rolagem
    st.markdown(f"### 🥧 Distribuição de Vendas - {periodo_especifico}")
    
    with st.container():
        # Ajustar altura baseado no número de itens
        pie_height = max(600, len(df_filtrado) * 5)  # Ajuste dinâmico
        
        pie_chart = (
            alt.Chart(df_filtrado)
            .mark_arc()
            .encode(
                theta=alt.Theta("Quantidade:Q", stack=True),
                color=alt.Color("Produto:N", legend=None),
                tooltip=["Produto:N", "Quantidade:Q"]
            )
            .properties(height=pie_height)
        )
        
        st.altair_chart(pie_chart, use_container_width=True)
    
    # Tabela de dados com rolagem
    st.markdown("### 📋 Detalhamento dos Dados (100 itens mais vendidos)")
    with st.container():
        st.dataframe(
            df_filtrado.rename(columns={
                "Produto": "Produto",
                "Quantidade": "Qtd Vendida"
            }),
            use_container_width=True,
            height=600  # Altura fixa com rolagem interna
        )

except Exception as e:
    st.error(f"Ocorreu um erro ao processar os dados: {str(e)}")