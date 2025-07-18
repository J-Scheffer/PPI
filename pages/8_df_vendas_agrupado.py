import streamlit as st
import pandas as pd
from utils.visualizacao import mostrar_paginado
from utils.sessao import inicializar_app
from utils.processamento import processa_df_venda_agrupado

st.set_page_config(page_title="df_vendas_agrupado", layout="wide")

inicializar_app()

st.title("📋 DataFrame de Vendas (Agrupado)")

if "df_vendas_agrupado" not in st.session_state:
    processa_df_venda_agrupado()

df = st.session_state.get("df_vendas_agrupado")

if not isinstance(df, pd.DataFrame) or df.empty:
    st.error("❌ O DataFrame 'df_vendas_agrupado' não está disponível ou está vazio.")
    st.stop()

df_vendas_agrupado: pd.DataFrame = df

mostrar_paginado(df_vendas_agrupado, "df_vendas_agrupado")
