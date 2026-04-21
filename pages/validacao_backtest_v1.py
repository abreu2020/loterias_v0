import streamlit as st
import pandas as pd
import random
from datetime import datetime

# Estilização de Bolas
st.markdown("""
<style>
.bola-sorte {
    background-color: #2E7D32; color: white; padding: 10px; border-radius: 50%;
    margin: 5px; font-weight: bold; display: inline-block; width: 40px; text-align: center;
}
.destaque-puro { color: #FFD700; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

def calcular_puro(n):
    s = sum(int(d) for d in str(n) if d.isdigit())
    return s if s <= 9 else calcular_puro(s)

def gerar_jogo_sniper(df, num_puro_alvo, lista_rep):
    # 1. Pega os dados do último concurso real
    ultimo = df.sort_values('concurso').iloc[-1]
    sairam_ontem = list(ultimo[[f'bola{i}' for i in range(1, 16)]])
    nao_sairam = [n for n in range(1, 26) if n not in sairam_ontem]
    
    # 2. Tenta gerar um jogo que passe nos filtros
    for _ in range(2000):
        rep = random.choice(lista_rep) # 8, 9 ou 10
        jogo = random.sample(sairam_ontem, rep) + random.sample(nao_sairam, 15 - rep)
        jogo = sorted(jogo)
        
        # Filtro de Numerologia e Paridade
        if calcular_puro(sum(jogo)) == num_puro_alvo:
            pares = sum(1 for n in jogo if n % 2 == 0)
            if 7 <= pares <= 8: # O equilíbrio mais comum
                return jogo
    return None

# --- UI ---
st.title("🎯 Lotofácil Sniper: Versão Pós-Backtest")

arquivo = st.file_uploader("Suba sua base atualizada", type="xlsx")

if arquivo:
    df = pd.read_excel(arquivo)
    df.columns = [c.strip().lower() for c in df.columns]
    
    with st.sidebar:
        st.header("Configurações")
        data_escolhida = st.date_input("Data do Próximo Sorteio", datetime.now())
        puro_dia = calcular_puro(data_escolhida.strftime('%d%m%Y'))
        st.write(f"Número Puro do Dia: **{puro_dia}**")

    if st.button("🚀 Gerar Jogos com Base no Sucesso do Backtest"):
        st.subheader(f"Jogos para a Frequência {puro_dia}")
        # Usando a trava de 8, 9 e 10 que deu 78.8% de sucesso
        for i in range(5):
            jogo = gerar_jogo_sniper(df, puro_dia, [8, 9, 10])
            if jogo:
                html = "".join([f'<span class="bola-sorte">{n:02d}</span>' for n in jogo])
                st.markdown(html, unsafe_allow_html=True)
                st.caption(f"Soma: {sum(jogo)} | Redução Pura: {puro_dia}")
                st.divider()