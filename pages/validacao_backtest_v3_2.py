import streamlit as st
import pandas as pd
import plotly.express as px
import random
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Lotofácil Sniper V3.2", layout="wide", page_icon="🎯")

st.markdown("""
<style>
.bola-sorte {
    background-color: #1B5E20; color: white; padding: 10px; border-radius: 50%;
    margin: 5px; font-weight: bold; display: inline-block; width: 42px; text-align: center;
    box-shadow: 2px 2px 4px rgba(0,0,0,0.3); border: 2px solid #FFD700;
}
.termometro { padding: 10px; border-radius: 10px; text-align: center; margin-bottom: 10px; color: white; font-family: sans-serif; }
.info-label { font-size: 14px; font-weight: bold; color: #555; }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES CORE ---

def calcular_puro(n):
    s = sum(int(d) for d in str(n) if d.isdigit())
    return s if s <= 9 else calcular_puro(s)

def obter_atrasos(df):
    atrasos = {}
    df_sorted = df.sort_values('concurso', ascending=False)
    ultimo_concurso = df['concurso'].max()
    for p in range(1, 10):
        match = df_sorted[df_sorted['soma'].apply(calcular_puro) == p]
        atrasos[p] = int(ultimo_concurso - match['concurso'].iloc[0]) if not match.empty else len(df)
    return atrasos

def gerar_jogo_sniper_v3(df, puro_alvo, lista_rep, col_bolas, dezenas_fixas=[]):
    """
    LOGICA DE ISOLAMENTO V3.2:
    Inclui dezenas fixas e completa o jogo respeitando a quantidade de repetidos.
    """
    ultimo_sorteio = df.sort_values('concurso').iloc[-1]
    sairam_ontem = set(ultimo_sorteio[col_bolas])
    nao_sairam_ontem = set(n for n in range(1, 26) if n not in sairam_ontem)
    
    # Identifica quais fixas são repetidas e quais são novas
    fixas_set = set(dezenas_fixas)
    fixas_repetidas = fixas_set.intersection(sairam_ontem)
    fixas_novas = fixas_set.intersection(nao_sairam_ontem)

    # Tentativas para bater todos os filtros simultaneamente
    for _ in range(7000):
        qtd_rep_alvo = random.choice(lista_rep)
        qtd_novos_alvo = 15 - qtd_rep_alvo
        
        # Verifica se as dezenas fixas permitem atingir a quantidade de repetidos/novos escolhida
        if len(fixas_repetidas) > qtd_rep_alvo or len(fixas_novas) > qtd_novos_alvo:
            continue
            
        # Completa o grupo de repetidas
        faltam_rep = qtd_rep_alvo - len(fixas_repetidas)
        pool_rep = list(sairam_ontem - fixas_set)
        grupo_rep = list(fixas_repetidas) + random.sample(pool_rep, faltam_rep)
        
        # Completa o grupo de novas
        faltam_novas = qtd_novos_alvo - len(fixas_novas)
        pool_novos = list(nao_sairam_ontem - fixas_set)
        grupo_novos = list(fixas_novas) + random.sample(pool_novos, faltam_novas)
        
        jogo = sorted(grupo_rep + grupo_novos)
        soma = sum(jogo)
        
        # FILTRO 1: NUMEROLOGIA
        if calcular_puro(soma) == puro_alvo:
            # FILTRO 2: PARIDADE (Equilíbrio 7:8 ou 8:7)
            pares = sum(1 for n in jogo if n % 2 == 0)
            if 7 <= pares <= 8:
                return jogo, soma, qtd_rep_alvo
                
    return None, None, None

# --- INTERFACE ---

st.title("🎯 Lotofácil Sniper V3.2 - Módulo Dezenas Fixas")

arquivo = st.sidebar.file_uploader("Suba sua Base Excel", type="xlsx")

if arquivo:
    df = pd.read_excel(arquivo)
    df.columns = [c.strip().lower() for c in df.columns]
    col_bolas = [f'bola{i}' for i in range(1, 16)]
    df['soma'] = df[col_bolas].sum(axis=1)
    
    # --- TERMÔMETRO ---
    atrasos = obter_atrasos(df)
    st.subheader("🌡️ Termômetro de Atraso dos Números Puros")
    cols = st.columns(9)
    determinantes = [1, 3, 5, 6, 9]
    for i, p in enumerate(range(1, 10)):
        # Alerta visual para atrasos críticos (como o 4)
        cor = "#B71C1C" if atrasos[p] > 15 else "#1B5E20" if p in determinantes else "#455A64"
        cols[i].markdown(f"""<div class="termometro" style="background-color: {cor};">
                         <b>Puro {p}</b><br><span style="font-size: 20px;">{atrasos[p]}</span></div>""", unsafe_allow_html=True)

    # --- SIDEBAR E CÁLCULOS ---
    with st.sidebar:
        st.header("⚙️ Filtros Sniper")
        
        # NOVO: MÓDULO DE DEZENAS FIXAS
        st.subheader("📌 Dezenas Estratégicas")
        fixas = st.multiselect("Fixar Dezenas (Máx 5):", options=list(range(1, 26)), max_selections=5)
        
        st.divider()
        data_sorteio = st.date_input("Próximo Sorteio", datetime.now())
        proximo_conc = int(df['concurso'].max() + 1)
        
        p_data = calcular_puro(data_sorteio.strftime('%d%m%Y'))
        p_conc = calcular_puro(proximo_conc)
        
        st.write(f"Vibração Data: **{p_data}**")
        st.write(f"Vibração Concurso: **{p_conc}**")
        
        st.divider()
        rep_selecionada = st.multiselect("Repetidos do Anterior:", [7, 8, 9, 10, 11], default=[8, 9])
        
        puro_alvo = st.selectbox("Frequência Alvo (Soma):", [4, 6, 3, 1, p_data, p_conc, 2, 5, 7, 8, 9], index=0)

    # --- BOTÃO DE AÇÃO ---
    st.divider()
    qtd_jogos = st.slider("Quantidade de Jogos", 1, 30, 10)
    
    if st.button(f"🔥 EXECUTAR OPERAÇÃO: ALVO {puro_alvo} | FIXAS: {fixas}"):
        st.subheader(f"Sugestões Geradas - Foco no Puro {puro_alvo}")
        
        sucessos = 0
        for _ in range(qtd_jogos):
            jogo, soma_v, r_usado = gerar_jogo_sniper_v3(df, puro_alvo, rep_selecionada, col_bolas, dezenas_fixas=fixas)
            
            if jogo:
                sucessos += 1
                with st.expander(f"Sugestão #{sucessos} | Repetiu {r_usado} do anterior", expanded=True):
                    html_bolas = "".join([f'<span class="bola-sorte">{n:02d}</span>' for n in jogo])
                    st.markdown(html_bolas, unsafe_allow_html=True)
                    
                    c1, c2, c3 = st.columns(3)
                    c1.write(f"**Soma:** {soma_v}")
                    c2.write(f"**Puro:** {puro_alvo}")
                    
                    set_j = set(jogo)
                    max_ac = df[col_bolas].apply(lambda r: len(set_j.intersection(set(r))), axis=1).max()
                    c3.write(f"**Recorde Histórico:** {max_ac} pts")
            else:
                st.warning("Filtros muito restritos para as dezenas fixas escolhidas. Tente reduzir as fixas ou aumentar a lista de repetição.")
                break
else:
    st.warning("Aguardando upload da base de dados no menu lateral.")