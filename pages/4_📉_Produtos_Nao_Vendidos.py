import streamlit as st
import pandas as pd
from typing import List, Optional
from utils.processamento import calcular_vendas_agrupadas, carregar_df_vendas, carregar_df_cadastro
from utils.sessao import inicializar_app, validar_df

# ---------------- CONFIGURAÇÃO INICIAL ----------------
st.set_page_config(page_title="Produtos Não Vendidos", layout="wide")
inicializar_app()
st.title("📉 Produtos Não Vendidos")

# ---------------- FUNÇÕES AUXILIARES ----------------

def obter_produtos_nao_vendidos(
    df_vendas: pd.DataFrame,
    df_cadastro: pd.DataFrame
) -> pd.DataFrame:
    """Retorna os produtos do cadastro que não aparecem nas vendas."""
    codigos_vendidos = set(df_vendas["ProCod"].dropna().unique())
    return df_cadastro[~df_cadastro["ProCod"].isin(codigos_vendidos)].copy()

@st.cache_data
def preparar_view(
    df: pd.DataFrame,
    colunas: List[str]
) -> pd.DataFrame:
    """Retorna somente as colunas selecionadas, se existirem no DataFrame."""
    colunas_validas = [col for col in colunas if col in df.columns]
    return df[colunas_validas]

# ---------------- CARREGAMENTO DOS DADOS ----------------

df_vendas = validar_df("df_vendas", carregar_df_vendas)
df_cadastro = validar_df("df_cadastro", carregar_df_cadastro)

# ---------------- INTERFACE DE COLUNAS ----------------

campos_disponiveis = list(df_cadastro.columns)
colunas_escolhidas = st.multiselect(
    "Colunas para exibir:",
    options=campos_disponiveis,
    default=campos_disponiveis
)

# ---------------- PROCESSAMENTO ----------------

df_nao_vendidos = obter_produtos_nao_vendidos(df_vendas, df_cadastro)
df_view = preparar_view(df_nao_vendidos, colunas_escolhidas)

# ---------------- EXIBIÇÃO ----------------

st.markdown("---")

if df_view.empty:
    st.info("✅ Todos os produtos foram vendidos no período.")
else:
    st.dataframe(df_view, use_container_width=True)

st.markdown("---")
