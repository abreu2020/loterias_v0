import streamlit as st
import pandas as pd
import plotly.express as px
import random
import io

# --- 1. CONFIGURAÇÕES ---
st.set_page_config(page_title="Mega-Sena Intel PRO", layout="wide", page_icon="💰")

st.markdown("""
<style>
.bola-mega {
    background-color: #209824; color: white; padding: 10px 14px; border-radius: 50%;
    margin-right: 8px; font-weight: bold; display: inline-block; border: 2px solid #14532D;
    min-width: 45px; text-align: center; font-size: 18px; box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
}
</style>
""", unsafe_allow_html=True)

# --- 2. LÓGICA MATEMÁTICA AVANÇADA ---

def validar_distribuicao(jogo):
    """Verifica se não há excesso de números em uma mesma linha ou coluna da cartela."""
    # Linhas: 0-9, 10-19, etc. | Colunas: finais 1, 2, 3...
    linhas = [(n-1) // 10 for n in jogo]
    colunas = [(n-1) % 10 for n in jogo]
    
    # Filtro: Máximo de 3 números por linha ou coluna
    if any(linhas.count(l) > 3 for l in set(linhas)): return False
    if any(colunas.count(c) > 3 for c in set(colunas)): return False
    return True

def validar_jogo_mega(jogo):
    """Combina todos os filtros de segurança."""
    pares = sum(1 for n in jogo if n % 2 == 0)
    soma = sum(jogo)
    
    # Filtro Paridade: 2 a 4 pares (Ocorre em ~80% dos sorteios)
    if not (2 <= pares <= 4): return False
    # Filtro Soma: 130 a 240
    if not (130 <= soma <= 240): return False
    # Filtro Distribuição Espacial
    if not validar_distribuicao(jogo): return False
    
    return True

@st.cache_data
def carregar_dados(arquivo):
    try:
        df = pd.read_excel(arquivo, sheet_name='mega')
        df.columns = [c.strip().lower() for c in df.columns]
        col_bolas = [f'bola{i}' for i in range(1, 7)]
        for col in col_bolas:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df = df.dropna(subset=col_bolas).sort_values('concurso')
        return df, col_bolas
    except Exception as e:
        st.error(f"Erro no Excel: {e}")
        return None, None

def gerar_jogos_mega(df_stats, qtd=5):
    jogos = []
    quentes = df_stats.nlargest(15, 'Frequencia')['Número'].tolist()
    frios = df_stats.nlargest(10, 'Atraso')['Número'].tolist()
    neutros = [n for n in range(1, 61) if n not in quentes and n not in frios]

    tentativas = 0
    while len(jogos) < qtd and tentativas < 3000:
        tentativas += 1
        # Mix: 2 Quentes + 1 Frio + 3 Neutros
        amostra = random.sample(quentes, 2) + random.sample(frios, 1) + random.sample(neutros, 3)
        jogo = sorted(amostra)
        
        if validar_jogo_mega(jogo) and jogo not in jogos:
            jogos.append(jogo)
    return jogos

# --- 3. INTERFACE ---

st.title("💰 Mega-Sena Inteligente PRO")
arquivo = st.sidebar.file_uploader("Upload da Base Mega-Sena (.xlsx)", type=["xlsx"])

if arquivo:
    df, col_bolas = carregar_dados(arquivo)
    if df is not None:
        # Processamento de Estatísticas
        ultimo = df['concurso'].max()
        todos_sorteados = df[col_bolas].values.flatten()
        freq = pd.Series(todos_sorteados).value_counts()
        atr = {n: int(ultimo - df[df[col_bolas].isin([n]).any(axis=1)]['concurso'].max()) for n in range(1, 61)}
        df_stats = pd.DataFrame({'Número': range(1, 61), 'Frequencia': [freq.get(i,0) for i in range(1,61)], 'Atraso': [atr.get(i,0) for i in range(1,61)]})

        tabs = st.tabs(["📈 Tendências", "🗺️ Mapa da Cartela", "🎲 Gerador & Backtest"])

        with tabs[0]:
            st.subheader("Análise de Frequência e Atraso")
            fig_freq = px.bar(df_stats.nlargest(15, 'Frequencia'), x='Número', y='Frequencia', title="Top 15 Mais Sorteados", color='Frequencia')
            st.plotly_chart(fig_freq, use_container_width=True)

        with tabs[1]:
            st.header("Mapa de Calor da Cartela")
            st.write("Distribuição histórica de sorteios por posição na cartela (6x10).")
            
            
            
            mapa = df_stats.copy()
            mapa['Linha'] = (mapa['Número'] - 1) // 10 + 1
            mapa['Coluna'] = (mapa['Número'] - 1) % 10 + 1
            
            fig_mapa = px.scatter(mapa, x="Coluna", y="Linha", size="Frequencia", color="Frequencia",
                                  text="Número", title="Onde os números 'moram' na cartela",
                                  color_continuous_scale='Greens', height=500)
            fig_mapa.update_yaxes(autorange="reversed", tick0=1, dtick=1)
            fig_mapa.update_xaxes(tick0=1, dtick=1)
            st.plotly_chart(fig_mapa, use_container_width=True)

        with tabs[2]:
            st.header("🎲 Gerador de Jogos de Elite")
            st.info("Filtros Ativos: Paridade (2-4 pares), Soma (130-240), Máx 3 por Linha/Coluna.")
            
            if st.button("🔥 Gerar 5 Jogos Estratégicos"):
                st.session_state.jogos_mega = gerar_jogos_mega(df_stats)
            
            if 'jogos_mega' in st.session_state:
                for i, jogo in enumerate(st.session_state.jogos_mega):
                    with st.expander(f"Sugestão de Jogo {i+1}", expanded=True):
                        html = "".join([f'<span class="bola-mega">{n:02d}</span>' for n in jogo])
                        st.markdown(html, unsafe_allow_html=True)
                        
                        # Backtest Real
                        set_j = set(jogo)
                        hits = df[col_bolas].apply(lambda r: len(set_j.intersection(set(r))), axis=1).value_counts()
                        
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Quadras", hits.get(4, 0))
                        m2.metric("Quinas", hits.get(5, 0))
                        m3.metric("Senas", hits.get(6, 0))

            st.write("---")
            with st.expander("🛠️ Testador de Grupo Manual"):
                selecao = st.multiselect("Sua Pool de Números (ex: 12 números):", range(1, 61), default=[1,10,20,30,40,50,5,15,25,35,45,55])
                if st.button("Gerar da Minha Seleção"):
                    if len(selecao) < 6: st.error("Selecione pelo menos 6 números.")
                    else:
                        j_m = sorted(random.sample(selecao, 6))
                        st.markdown(f"**Jogo Gerado:** `{j_m}`")
                        res_m = df[col_bolas].apply(lambda r: len(set(j_m).intersection(set(r))), axis=1).value_counts()
                        st.write(f"Histórico: Quadras: {res_m.get(4,0)} | Quinas: {res_m.get(5,0)} | Senas: {res_m.get(6,0)}")
else:
    st.info("Aguardando base de dados Excel...")