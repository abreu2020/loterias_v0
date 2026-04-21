import streamlit as st
import pandas as pd
import random
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Mega-Sena Sniper V1", layout="wide", page_icon="💰")

st.markdown("""
<style>
.bola-mega {
    background-color: #209824; color: white; padding: 12px; border-radius: 50%;
    margin: 5px; font-weight: bold; display: inline-block; width: 45px; text-align: center;
    box-shadow: 2px 2px 4px rgba(0,0,0,0.3); border: 2px solid #14532D;
}
.termometro-mega { padding: 10px; border-radius: 10px; text-align: center; margin-bottom: 10px; color: white; }
</style>
""", unsafe_allow_html=True)

def calcular_puro(n):
    s = sum(int(d) for d in str(n) if d.isdigit())
    return s if s <= 9 else calcular_puro(s)

def obter_atrasos_mega(df):
    atrasos = {}
    df_sorted = df.sort_values('concurso', ascending=False)
    ultimo_concurso = df['concurso'].max()
    for p in range(1, 10):
        match = df_sorted[df_sorted['soma'].apply(calcular_puro) == p]
        atrasos[p] = int(ultimo_concurso - match['concurso'].iloc[0]) if not match.empty else len(df)
    return atrasos

def gerar_jogo_mega_sniper(df, puro_alvo, rep_permitida, col_bolas):
    ultimo_sorteio = df.sort_values('concurso').iloc[-1]
    sairam_ontem = list(ultimo_sorteio[col_bolas])
    nao_sairam = [n for n in range(1, 61) if n not in sairam_ontem]
    
    for _ in range(5000):
        qtd_rep = random.choice(rep_permitida) # 0 ou 1
        qtd_novos = 6 - qtd_rep
        
        jogo = sorted(random.sample(sairam_ontem, qtd_rep) + random.sample(nao_sairam, qtd_novos))
        soma = sum(jogo)
        
        # FILTROS MEGA-SENA
        if calcular_puro(soma) == puro_alvo:
            # Filtro de Soma Saudável (150-220)
            if 130 <= soma <= 260:
                # Filtro de Paridade (Equilíbrio 3:3, 2:4 ou 4:2)
                pares = sum(1 for n in jogo if n % 2 == 0)
                if 2 <= pares <= 4:
                    return jogo, soma, qtd_rep
    return None, None, None

# --- INTERFACE ---
st.title("💰 Mega-Sena Master Sniper V1")
arquivo = st.sidebar.file_uploader("Base Mega-Sena (Excel)", type="xlsx")

if arquivo:
    df = pd.read_excel(arquivo, sheet_name='mega')
    df.columns = [c.strip().lower() for c in df.columns]
    col_bolas = [f'bola{i}' for i in range(1, 7)]
    df['soma'] = df[col_bolas].sum(axis=1)
    
    # --- TERMÔMETRO ---
    atrasos = obter_atrasos_mega(df)
    st.subheader("🌡️ Termômetro de Atraso (Soma Pura Mega)")
    cols = st.columns(9)
    for i, p in enumerate(range(1, 10)):
        cor = "#1B5E20" if atrasos[p] < 5 else "#E65100" if atrasos[p] < 15 else "#B71C1C"
        cols[i].markdown(f"""<div class="termometro-mega" style="background-color: {cor};">
                         <b>Puro {p}</b><br><span style="font-size: 20px;">{atrasos[p]}</span></div>""", unsafe_allow_html=True)

    # --- SIDEBAR ---
    with st.sidebar:
        data_sorteio = st.date_input("Data do Sorteio", datetime.now())
        p_data = calcular_puro(data_sorteio.strftime('%d%m%Y'))
        st.write(f"Vibração da Data: **{p_data}**")
        
        rep_opcoes = st.multiselect("Repetir do anterior:", [0, 1, 2], default=[0, 1])
        puro_alvo = st.selectbox("Frequência Alvo:", range(1, 10), index=p_data-1)

    # --- GERAÇÃO ---
    if st.button(f"🔥 GERAR JOGOS MEGA (ALVO {puro_alvo})"):
        for i in range(3):
            jogo, soma_v, r_usado = gerar_jogo_mega_sniper(df, puro_alvo, rep_opcoes, col_bolas)
            if jogo:
                st.write(f"### Sugestão #{i+1} | Repetição: {r_usado}")
                html = "".join([f'<span class="bola-mega">{n:02d}</span>' for n in jogo])
                st.markdown(html, unsafe_allow_html=True)
                st.caption(f"Soma Total: {soma_v} | Puro: {puro_alvo}")
                st.divider()

else:
    st.info("Aguardando base da Mega-Sena...")