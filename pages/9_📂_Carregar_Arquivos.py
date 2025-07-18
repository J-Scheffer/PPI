import streamlit as st
from utils.sessao import salvar_caminhos
from utils.constantes import CAMINHO_PADRAO_VENDAS, CAMINHO_PADRAO_CADASTRO
from utils.sessao import inicializar_app

inicializar_app()

st.set_page_config(page_title="Configurar Caminhos", layout="wide")
st.title("🗂️ Configuração de Caminhos de Arquivos")
st.markdown("Use os campos abaixo para configurar os caminhos dos arquivos de dados.")

caminho_vendas = st.text_input(
    "📄 Caminho do Arquivo de Vendas",
    value=st.session_state.get("caminho_vendas", CAMINHO_PADRAO_VENDAS)
)
caminho_cadastro = st.text_input(
    "📦 Caminho do Arquivo de Cadastro",
    value=st.session_state.get("caminho_cadastro", CAMINHO_PADRAO_CADASTRO)
)

submit = st.button("💾 Salvar Caminhos")

if submit:
    salvar_caminhos(caminho_vendas, caminho_cadastro)

st.markdown("### 🔍 Caminhos atuais carregados")
st.write(f"**Arquivo de Vendas:** `{st.session_state.get('caminho_vendas', CAMINHO_PADRAO_VENDAS)}`")
st.write(f"**Arquivo de Cadastro:** `{st.session_state.get('caminho_cadastro', CAMINHO_PADRAO_CADASTRO)}`")
