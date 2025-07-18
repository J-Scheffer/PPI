# python -m streamlit run Home.py

import streamlit as st
from utils.sessao import inicializar_app

inicializar_app()

st.set_page_config(page_title="Sistema de Análise Vendas", layout="wide")

st.title("📦 Sistema de Análise Vendas")

st.markdown("""
Bem-vindo ao aplicativo de análise de vendas!

Use a barra lateral para configurar os caminhos dos arquivos ou para navegar pelo dashboard.

✅ Por padrão, o sistema busca os arquivos no diretório `dados/` com os seguintes nomes e formatos CSV:

- `NotasFW_ProdInfo.csv` (dados de vendas)
- `prodMercado.csv` (cadastro de produtos)

Caso seus arquivos estejam em outro local, ajuste os caminhos na barra lateral para carregá-los corretamente.
""")
