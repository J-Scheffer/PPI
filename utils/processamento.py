import pandas as pd
from typing import Union, IO, Optional
import streamlit as st  
from utils.constantes import DIAS_SEMANA_PT

def calcular_vendas_agrupadas(df_vendas: pd.DataFrame) -> pd.DataFrame:
    if not {"ProCod", "Quantidade", "TotalItem"}.issubset(df_vendas.columns):
        raise ValueError("Colunas necessárias não estão presentes no DataFrame.")
    return df_vendas.groupby("ProCod")[["Quantidade", "TotalItem"]].sum().reset_index()

def adicionar_nomes_produtos(df_vendidos: pd.DataFrame, df_cadastro: pd.DataFrame) -> pd.DataFrame:
    return pd.merge(df_vendidos, df_cadastro, on="ProCod", how="left")

def carregar_df_cadastro(caminho: Optional[Union[str, IO]] = None) -> None:
    """Carrega o arquivo de cadastro e retorna apenas as colunas de código e nome do produto."""
    
    if caminho is None:
        caminho = st.session_state.get("caminho_cadastro")

    if not caminho:
        st.error("❌ Caminho para o arquivo de cadastro não foi definido.")
        st.stop()
    
    df = pd.read_csv(caminho, delimiter=";", decimal=".")
    st.session_state["df_cadastro"] = df

def carregar_df_vendas(caminho: Optional[Union[str, IO]] = None) -> None:
    """
    Carrega os dados de vendas a partir de um caminho, adiciona colunas temporais
    e salva no session_state como 'df_vendas'.
    """
    # Recupera o caminho padrão da sessão, se não for fornecido diretamente
    if caminho is None:
        caminho = st.session_state.get("caminho_vendas")

    if not caminho:
        st.error("❌ Caminho para o arquivo de vendas não foi definido.")
        st.stop()

    try:
        df = pd.read_csv(caminho, delimiter=";", decimal=".", low_memory=False)
    except Exception as e:
        st.error(f"❌ Falha ao carregar o arquivo de vendas: {e}")
        st.stop()

    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df = df.dropna(subset=["Data"])  # Garante que todas as datas são válidas

    # Criação de colunas temporais (vetorizadas)
    df["Ano"] = df["Data"].dt.year
    df["Semestre"] = df["Data"].dt.month.apply(lambda m: "S1" if m <= 6 else "S2")
    df["Trimestre"] = df["Data"].dt.to_period("Q").astype(str)
    df["MesPeriodo"] = df["Data"].dt.to_period("M").astype(str)
    df["SemanaInicioDt"] = df["Data"].dt.to_period("W").astype(str)
    df["Dia"] = df["Data"].dt.strftime("%Y-%m-%d")
    df["DiaSemana"] = df["Data"].dt.day_name().map(DIAS_SEMANA_PT)

    st.session_state["df_vendas"] = df

def processa_df_venda_agrupado() -> None:
    """Agrupa as vendas por controle, com colunas temporais derivadas."""
    
    if "df_vendas" not in st.session_state:
        carregar_df_vendas()
        
    df = st.session_state.get("df_vendas")
    
    if df is None or "Controle" not in df.columns:
        st.error("❌ DataFrame de vendas não disponível ou mal formatado.")
        return

    df_vendas_agrupado = (
        df.groupby("Controle", as_index=False)
          .agg({
              "Cliente": "first",
              "TotalItem": "sum",
              "Data": "first",
              "ProCod": "count",
              "Controle": "first",
              "Ano": "first",
              "Semestre": "first",
              "Trimestre": "first",
              "MesPeriodo": "first",
              "SemanaInicioDt": "first",
              "Dia": "first",
              "DiaSemana": "first",
              "Bairro": "first",
          })
          .rename(columns={
              "TotalItem": "TotalVenda",
              "ProCod": "QuantidadeItens"
          })
    )

    df_vendas_agrupado["Ano"] = df_vendas_agrupado["Data"].dt.year
    df_vendas_agrupado["MesPeriodo"] = df_vendas_agrupado["Data"].dt.to_period("M").astype(str)
    df_vendas_agrupado["DiaSemana"] = df_vendas_agrupado["Data"].dt.day_name().map(DIAS_SEMANA_PT)

    st.session_state["df_vendas_agrupado"] = df_vendas_agrupado
