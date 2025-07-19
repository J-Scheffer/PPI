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

# Verificar colunas disponíveis para debug
st.sidebar.write("Colunas em df_vendas:", df_vendas.columns.tolist())
st.sidebar.write("Colunas em df_cadastro:", df_cadastro.columns.tolist())

# ---------------- FUNÇÕES AUXILIARES ----------------

@st.cache_data
def preparar_produtos(df_vendas: pd.DataFrame, df_cadastro: pd.DataFrame) -> pd.DataFrame:
    """Prepara os dados de produtos vendidos com formatação adequada."""
    try:
        df = calcular_vendas_agrupadas(df_vendas)
        
        # Verificar colunas essenciais
        colunas_necessarias = ['ProCod', 'TotalItem', 'Quantidade']
        for col in colunas_necessarias:
            if col not in df.columns:
                st.error(f"❌ Coluna essencial '{col}' não encontrada no DataFrame de vendas")
                st.stop()
        
        # Verificar produtos não cadastrados
        produtos_nao_cadastrados = df[~df['ProCod'].isin(df_cadastro['ProCod'])]['ProCod'].unique()
        if len(produtos_nao_cadastrados) > 0:
            st.warning(f"⚠️ {len(produtos_nao_cadastrados)} produtos nas vendas não estão no cadastro")
        
        # Merge mantendo todos os produtos das vendas (left join)
        df = pd.merge(
            df,
            df_cadastro[["ProCod", "ProNom"]].drop_duplicates(subset=["ProCod"]),
            how="left",
            on="ProCod"
        )
        
        # Preencher nomes faltantes
        df["ProNom"] = df["ProNom"].fillna("PRODUTO NÃO CADASTRADO")
        df = df.rename(columns={"ProNom": "Produto"})
        
        # Converter colunas numéricas
        df["TotalItem"] = pd.to_numeric(df["TotalItem"], errors="coerce")
        df["Quantidade"] = pd.to_numeric(df["Quantidade"], errors="coerce")
        
        # Remover linhas inválidas
        df = df.dropna(subset=["TotalItem", "Quantidade"])
        
        # Formatar valores
        df = df.sort_values(by="TotalItem", ascending=False)
        df["TotalFormatado"] = df["TotalItem"].apply(formatar_moeda_brasileira)
        
        return df
        
    except Exception as e:
        st.error(f"Erro ao preparar produtos: {str(e)}")
        st.stop()

@st.cache_data
def detalhar_giro_vendas(df_vendas: pd.DataFrame, df_cadastro: pd.DataFrame, periodo: str) -> pd.DataFrame:
    """Prepara os dados para análise temporal de vendas por produto."""
    try:
        df = df_vendas.copy()

        # Verificar colunas essenciais
        colunas_necessarias = ['ProCod', 'Quantidade', 'Data']
        for col in colunas_necessarias:
            if col not in df.columns:
                st.error(f"❌ Coluna essencial '{col}' não encontrada no DataFrame de vendas")
                st.stop()

        # Merge com nomes de produtos
        df = pd.merge(
            df,
            df_cadastro[["ProCod", "ProNom"]].drop_duplicates(subset=["ProCod"]),
            how="left",
            on="ProCod"
        ).rename(columns={"ProNom": "Produto"})
        
        df["Produto"] = df["Produto"].fillna("PRODUTO NÃO CADASTRADO")

        # Converter tipos
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        df["Quantidade"] = pd.to_numeric(df["Quantidade"], errors="coerce")
        df = df.dropna(subset=["Data", "Quantidade", "Produto"])

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

        return df.groupby(["Periodo", "Produto"]).agg(Quantidade=("Quantidade", "sum")).reset_index()
        
    except Exception as e:
        st.error(f"Erro ao detalhar giro de vendas: {str(e)}")
        st.stop()

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

# Tabela com rolagem para mais de 20 itens
if top_n > 20:
    st.markdown(f"**Mostrando {top_n} produtos (role para ver todos)**")
    table_height = 500  # Altura fixa com rolagem
else:
    table_height = None  # Altura automática

st.dataframe(
    top_df[["Produto", "Quantidade", "TotalFormatado"]]
    .rename(columns={"Quantidade": "Qtd Vendida", "TotalFormatado": "Total R$"}),
    use_container_width=True,
    height=table_height
)

# Gráfico de barras
if not top_df.empty:
    top_df = top_df.sort_values("TotalItem", ascending=True)
    
    bar_chart = (
        alt.Chart(top_df)
        .mark_bar()
        .encode(
            x=alt.X("TotalItem:Q", title="Total Vendido (R$)"),
            y=alt.Y("Produto:N", sort="-x", title="Produto", axis=alt.Axis(labelLimit=300)),
            tooltip=[
                alt.Tooltip("Produto", title="Produto"),
                alt.Tooltip("Quantidade:Q", title="Qtd Vendida"),
                alt.Tooltip("TotalItem:Q", title="Total Vendido", format=",.2f")
            ],
            color=alt.Color("TotalItem:Q", scale=alt.Scale(scheme="greens"), legend=None)
        )
        .properties(
            height=max(400, len(top_df) * 20),
            title=f"Top {top_n} Produtos por Valor Vendido"
        )
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

df_giro = detalhar_giro_vendas(df_vendas, df_cadastro, periodo_selecionado)

if not df_giro.empty:
    periodos_disponiveis = sorted(df_giro["Periodo"].unique().tolist())
    periodo_especifico = st.selectbox("Selecionar período específico:", periodos_disponiveis)
    
    df_filtrado = df_giro[df_giro["Periodo"] == periodo_especifico]
    df_filtrado = df_filtrado.sort_values("Quantidade", ascending=False)
    
    # Gráfico de pizza (Top 100)
    st.markdown(f"### 🥧 Distribuição de Vendas - {periodo_especifico} (Top 100)")
    pie_chart = (
        alt.Chart(df_filtrado.head(100))
        .mark_arc()
        .encode(
            theta=alt.Theta("Quantidade:Q", stack=True),
            color=alt.Color("Produto:N", legend=None),
            tooltip=["Produto:N", "Quantidade:Q"]
        )
        .properties(height=500)
    )
    st.altair_chart(pie_chart, use_container_width=True)
    
    # Tabela completa
    st.markdown(f"### 📋 Detalhamento Completo ({len(df_filtrado)} itens)")
    st.dataframe(
        df_filtrado.rename(columns={"Quantidade": "Qtd Vendida"}),
        use_container_width=True,
        height=600
    )
else:
    st.warning("Nenhum dado disponível para o período selecionado.")