import streamlit as st
from utils.sessao import salvar_caminhos
from utils.constantes import CAMINHO_PADRAO_VENDAS, CAMINHO_PADRAO_CADASTRO
from utils.sessao import inicializar_app
import tempfile
import os
import shutil

inicializar_app()

st.set_page_config(page_title="Configurar Caminhos", layout="wide")
st.title("🗂️ Configuração de Caminhos de Arquivos")
st.markdown("Use os campos abaixo para configurar os caminhos dos arquivos de dados.")

# --- Função auxiliar para salvar o arquivo enviado via upload
def salvar_upload_temp(uploaded_file, tipo: str) -> str:
    if uploaded_file is not None:
        suffix = ".csv"
        temp_dir = tempfile.gettempdir()
        caminho_final = os.path.join(temp_dir, f"{tipo}_upload{suffix}")
        with open(caminho_final, "wb") as f:
            shutil.copyfileobj(uploaded_file, f)
        return caminho_final
    return ""

# --- Upload ou caminho manual do arquivo de vendas
uploaded_vendas = st.file_uploader("📄 Selecionar Arquivo de Vendas (.csv)", type=["csv"])
caminho_vendas_texto = st.text_input(
    "📄 Ou digite o caminho do Arquivo de Vendas",
    value=st.session_state.get("caminho_vendas", CAMINHO_PADRAO_VENDAS)
)

# --- Upload ou caminho manual do arquivo de cadastro
uploaded_cadastro = st.file_uploader("📦 Selecionar Arquivo de Cadastro (.csv)", type=["csv"])
caminho_cadastro_texto = st.text_input(
    "📦 Ou digite o caminho do Arquivo de Cadastro",
    value=st.session_state.get("caminho_cadastro", CAMINHO_PADRAO_CADASTRO)
)

# --- Botão de salvar caminhos
submit = st.button("💾 Salvar Caminhos")

if submit:
    caminho_vendas_final = salvar_upload_temp(uploaded_vendas, "vendas") if uploaded_vendas else caminho_vendas_texto
    caminho_cadastro_final = salvar_upload_temp(uploaded_cadastro, "cadastro") if uploaded_cadastro else caminho_cadastro_texto

    salvar_caminhos(caminho_vendas_final, caminho_cadastro_final)
    st.success("✅ Caminhos atualizados com sucesso!")

# --- Exibe caminhos carregados
st.markdown("### 🔍 Caminhos atuais carregados")
st.write(f"**Arquivo de Vendas:** `{st.session_state.get('caminho_vendas', CAMINHO_PADRAO_VENDAS)}`")
st.write(f"**Arquivo de Cadastro:** `{st.session_state.get('caminho_cadastro', CAMINHO_PADRAO_CADASTRO)}`")
