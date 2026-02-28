import streamlit as st

st.set_page_config(
    page_title="Hello",
    page_icon="👋",
)

st.write("# Bora Vencer e Acertar! 👋")

st.sidebar.success("Escolher o tipo de jogo.")

st.markdown(
    """
    O Objetivo é alimentar com os resultados anteriores.\n
    **👈 Atualizar o arquivo edsom.xlsx!
    \n
    - Download dos resultados:
        - [lotofácil](https://loterias.caixa.gov.br/Paginas/Lotofacil.aspx)
        - [Mega-sena](https://loterias.caixa.gov.br/Paginas/Mega-Sena.aspx)
    
"""
)