import streamlit as st
import pandas as pd

LINHAS_POR_PAGINA = 100

def mostrar_paginado(df: pd.DataFrame, nome_df: str, linhas_por_pagina: int = LINHAS_POR_PAGINA):
    """Exibe DataFrame com paginação e botão de download."""
    if df is None or df.empty:
        st.info(f"O DataFrame '{nome_df}' está vazio ou não foi carregado.")
        return

    total_linhas = len(df)
    num_paginas = (total_linhas - 1) // linhas_por_pagina + 1

    pagina = st.number_input(
        f"Página de visualização ({nome_df})",
        min_value=1,
        max_value=num_paginas,
        value=1,
        step=1,
        key=f"pagina_{nome_df}"
    )

    inicio = (pagina - 1) * linhas_por_pagina
    fim = inicio + linhas_por_pagina
    st.dataframe(df.iloc[inicio:fim], use_container_width=True)
    st.caption(f"Exibindo linhas {inicio + 1} a {min(fim, total_linhas)} de {total_linhas}.")

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=f"📥 Baixar CSV completo ({nome_df})",
        data=csv,
        file_name=f"{nome_df}.csv",
        mime="text/csv",
        key=f"download_{nome_df}"
    )
