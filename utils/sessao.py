import streamlit as st
import traceback
import pandas as pd
from typing import Optional, Callable, Tuple
from utils.caminho import (
    caminho_valido,
)
from utils.constantes import (
    CAMINHO_PADRAO_VENDAS,
    CAMINHO_PADRAO_CADASTRO,
)

def inicializar_app():
    if "inicializado" not in st.session_state:
        st.session_state["inicializado"] = True
        st.session_state["caminho_vendas"] = CAMINHO_PADRAO_VENDAS
        st.session_state["caminho_cadastro"] = CAMINHO_PADRAO_CADASTRO
        print("⚙️ App inicializado.")

def carregar_arquivo_na_sessao(
    nome_chave: str,
    caminho: Optional[str],
    func_carregamento: Callable[[str], object]
) -> bool:
    if nome_chave in st.session_state:
        return True

    if not caminho_valido(caminho):
        st.error(f"❌ Caminho inválido para '{nome_chave}'.")
        return False

    try:
        df = func_carregamento(caminho)
        st.session_state[nome_chave] = df
        return True
    except Exception as e:
        st.error(f"❌ Erro ao carregar '{nome_chave}': {e}")
        traceback.print_exc()
        st.session_state.pop(nome_chave, None)
        return False

def df_em_cache(nome_df: str) -> bool:
    """
    Verifica se o DataFrame com o nome `nome_df` está presente e válido no session_state.

    Parâmetros:
    - nome_df: Nome da chave esperada no session_state

    Retorna:
    - True se o DataFrame está carregado e não está vazio
    - False caso contrário
    """
    df = st.session_state.get(nome_df)
    return isinstance(df, pd.DataFrame) and not df.empty

def salvar_caminhos(
    caminho_vendas: str = CAMINHO_PADRAO_VENDAS,
    caminho_cadastro: str = CAMINHO_PADRAO_CADASTRO
) -> bool:
    if not caminho_valido(caminho_vendas):
        st.error(f"❌ Arquivo de vendas não encontrado: {caminho_vendas}")
        return False

    if not caminho_valido(caminho_cadastro):
        st.error(f"❌ Arquivo de cadastro não encontrado: {caminho_cadastro}")
        return False

    st.cache_data.clear()
    st.cache_resource.clear()

    st.session_state["caminho_vendas"] = caminho_vendas
    st.session_state["caminho_cadastro"] = caminho_cadastro

    return True

def validar_df(nome: str, carregador: callable) -> pd.DataFrame:
    """
    Valida e retorna um DataFrame do session_state.
    Se não estiver carregado, tenta carregar com a função fornecida.
    """
    if nome not in st.session_state:
        carregador()

    df: Optional[pd.DataFrame] = st.session_state.get(nome)
    if not isinstance(df, pd.DataFrame) or df.empty:
        st.error(f"❌ O DataFrame '{nome}' não está disponível ou está vazio.")
        st.stop()

    return df.copy()