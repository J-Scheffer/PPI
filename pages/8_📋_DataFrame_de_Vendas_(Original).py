import streamlit as st
import pandas as pd
from utils.visualizacao import mostrar_paginado
from utils.sessao import inicializar_app
from utils.processamento import carregar_df_vendas

st.set_page_config(page_title="df_vendas", layout="wide")

inicializar_app()

st.title("📋 DataFrame de Vendas (Original)")

if "df_vendas" not in st.session_state:
    carregar_df_vendas()

# Verifica se o DataFrame está carregado
df = st.session_state.get("df_vendas")

if not isinstance(df, pd.DataFrame) or df.empty:
    st.error("❌ O DataFrame 'df_vendas' não está disponível ou está vazio.")
    st.stop()

# Aqui sim você pode tipar com segurança
df_vendas: pd.DataFrame = df

# Exibe o DataFrame paginado
mostrar_paginado(df_vendas, "df_vendas")
