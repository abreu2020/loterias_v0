import streamlit as st
import pandas as pd
import plotly.express as px
import random
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Lotofácil Sniper V3", layout="wide", page_icon="🎯")

st.markdown("""
<style>
.bola-sorte {
    background-color: #1B5E20; color: white; padding: 10px; border-radius: 50%;
    margin: 5px; font-weight: bold; display: inline-block; width: 42px; text-align: center;
    box-shadow: 2px 2px 4px rgba(0,0,0,0.3); border: 2px solid #FFD700;
}
.termometro { padding: 10px; border-radius: 10px; text-align: center; margin-bottom: 10px; color: white; }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES LÓGICAS ---

def calcular_puro(n):
    s = sum(int(d) for d in str(n) if d.isdigit())
    return s if s <= 9 else calcular_puro(s)

def obter_estatisticas_puros(df):
    """Calcula o atraso atual de cada número puro (1-9)"""
    ultimo_puro = {}
    atrasos = {}
    df = df.sort_values('concurso', ascending=False)
    
    todos_puros = range(1, 10)
    for p in todos_puros:
        # Encontra o concurso mais recente onde a soma resultou no puro p
        match = df[df['soma'].apply(calcular_puro) == p]
        if not match.empty:
            atrasos[p] = int(df['concurso'].max() - match['concurso'].iloc[0])
        else:
            atrasos[p] = len(df)
    return atrasos

def gerar_jogo_v3(df, puro_escolhido, lista_repetidos, col_bolas):
    ultimo = df.sort_values('concurso').iloc[-1]
    sairam = list(ultimo[col_bolas])
    nao_sairam = [n for n in range(1, 26) if n not in sairam]
    
    # Tentativas para encontrar o jogo que vibra na frequência certa
    for _ in range(5000):
        rep = random.choice(lista_repetidos)
        jogo = sorted(random.sample(sairam, rep) + random.sample(nao_sairam, 15 - rep))
        
        soma = sum(jogo)
        if calcular_puro(soma) == puro_escolhido:
            # Filtro de Paridade Sniper (7:8 ou 8:7)
            pares = sum(1 for n in jogo if n % 2 == 0)
            if 7 <= pares <= 8:
                return jogo, soma
    return None, None

# --- INTERFACE ---

st.title("🎯 Lotofácil Sniper V3: Edição Determinante")
st.sidebar.header("📊 Configurações de Elite")

arquivo = st.sidebar.file_uploader("Base Excel Atualizada", type="xlsx")

if arquivo:
    df = pd.read_excel(arquivo)
    df.columns = [c.strip().lower() for c in df.columns]
    col_bolas = [f'bola{i}' for i in range(1, 16)]
    df['soma'] = df[col_bolas].sum(axis=1)
    
    # 1. ANÁLISE DE ATRASO (TERMÔMETRO)
    atrasos = obter_estatisticas_puros(df)
    
    st.subheader("🌡️ Termômetro de Atraso: Números Puros")
    cols = st.columns(9)
    determinantes = [1, 3, 6, 5, 9] # 4, 8 fracos
    
    for i, p in enumerate(range(1, 10)):
        cor = "#B71C1C" if atrasos[p] > 10 else "#1B5E20" if p in determinantes else "#455A64"
        with cols[i]:
            st.markdown(f"""<div class="termometro" style="background-color: {cor};">
                        <b>Puro {p}</b><br><span style="font-size: 20px;">{atrasos[p]}</span><br>atrasos</div>""", unsafe_allow_html=True)

    # 2. CÁLCULO DE VIBRAÇÃO DO DIA
    with st.sidebar:
        data_sorteio = st.date_input("Data do Próximo Sorteio", datetime.now())
        proximo_conc = int(df['concurso'].max() + 1)
        
        p_data = calcular_puro(data_sorteio.strftime('%d%m%Y'))
        p_conc = calcular_puro(proximo_conc)
        
        st.divider()
        st.write(f"📅 Puro Data: **{p_data}**")
        st.write(f"🔢 Puro Concurso: **{p_conc}**")
        
        if p_data == p_conc:
            st.success(f"💎 CONFLUÊNCIA DETECTADA: **{p_data}**")
            puro_final = p_data
        else:
            puro_final = st.selectbox("Escolha a Frequência Alvo:", [p_data, p_conc, 1, 3, 5, 6, 8, 9], 
                                      help="Sugerimos seguir os Determinantes ou a Confluência.")

    # 3. GERADOR SNIPER
    st.divider()
    num_jogos = st.slider("Quantos jogos deseja gerar?", 1, 10, 5)
    
    if st.button(f"🚀 GERAR {num_jogos} JOGOS SNIPER"):
        st.subheader(f"Sugestões para o Concurso {proximo_conc} (Vibração {puro_final})")
        
        jogos_gerados = 0
        while jogos_gerados < num_jogos:
            jogo, soma_v = gerar_jogo_v3(df, puro_final, [8, 9, 10], col_bolas)
            
            if jogo:
                jogos_gerados += 1
                with st.expander(f"Jogo Sugerido #{jogos_gerados}", expanded=True):
                    html_bolas = "".join([f'<span class="bola-sorte">{n:02d}</span>' for n in jogo])
                    st.markdown(html_bolas, unsafe_allow_html=True)
                    
                    # Verificador de Gêmeos Simplificado
                    set_j = set(jogo)
                    max_ac = df[col_bolas].apply(lambda r: len(set_j.intersection(set(r))), axis=1).max()
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Soma", soma_v)
                    c2.metric("Puro", puro_final)
                    c3.metric("Recorde Histórico", f"{max_ac} pts")
            else:
                st.error("Filtros muito rigorosos para encontrar um jogo. Tente novamente.")
                break

    # 4. GRÁFICO DE APOIO
    with st.expander("📊 Ver Mapa de Calor de Resultados"):
        df['p_res'] = df['soma'].apply(calcular_puro)
        fig = px.histogram(df, x="p_res", title="Frequência dos Números Puros", color_discrete_sequence=['#FFD700'])
        st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Aguardando base de dados para iniciar o Sniper V3...")