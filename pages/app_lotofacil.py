import streamlit as st
import pandas as pd
import plotly.express as px
import random
import io

# --- 1. CONFIGURAÇÕES E ESTILIZAÇÃO ---
st.set_page_config(page_title="LotoAnalytics PRO", layout="wide", page_icon="📊")

st.markdown("""
<style>
.bola {
    background-color: #2E7D32; color: white; padding: 8px 12px; border-radius: 50%;
    margin-right: 5px; font-weight: bold; display: inline-block; border: 2px solid #1B5E20;
    min-width: 40px; text-align: center; margin-bottom: 5px;
}
.bola-ciclo {
    background-color: #E64A19; border: 2px solid #BF360C;
}
</style>
""", unsafe_allow_html=True)

# --- 2. MOTOR DE CÁLCULOS ---

@st.cache_data
def carregar_dados(arquivo_upload):
    try:
        df = pd.read_excel(arquivo_upload)
        df.columns = [c.strip().lower() for c in df.columns]
        col_bolas = [f'bola{i}' for i in range(1, 16)]
        for col in col_bolas:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df = df.dropna(subset=col_bolas).sort_values('concurso')
        df['soma'] = df[col_bolas].sum(axis=1)
        df['pares'] = df[col_bolas].apply(lambda x: sum(n % 2 == 0 for n in x), axis=1)
        return df, col_bolas
    except Exception as e:
        st.error(f"Erro ao processar: {e}")
        return None, None

def calcular_ciclo(df, col_bolas):
    """Calcula o estado atual do ciclo das dezenas."""
    todos_numeros = set(range(1, 26))
    sorteados_no_ciclo = set()
    concursos_no_ciclo = 0
    
    # Percorre do mais recente para trás até encontrar o início do ciclo
    for _, row in df.sort_values('concurso', ascending=False).iterrows():
        bolas_sorteadas = set(row[col_bolas])
        sorteados_no_ciclo.update(bolas_sorteadas)
        concursos_no_ciclo += 1
        if sorteados_no_ciclo == todos_numeros:
            break
            
    # Números que faltam para o ciclo atual
    # Para o gerador, olhamos o ciclo em aberto
    abertos = set()
    for _, row in df.sort_values('concurso', ascending=False).iterrows():
        abertos.update(set(row[col_bolas]))
        if abertos == todos_numeros: # Ciclo anterior fechou aqui
            # Precisamos pegar apenas o que foi sorteado após o último fechamento
            break
            
    # Lógica simplificada: Quais dezenas não saíram nos últimos X concursos desde que o último ciclo fechou
    numeros_faltantes = []
    sorteados_recentes = set()
    for _, row in df.sort_values('concurso', ascending=False).iterrows():
        sorteados_recentes.update(set(row[col_bolas]))
        if len(sorteados_recentes) == 25:
            # Achamos o ponto de fechamento. O ciclo atual começou após isso.
            break
    
    # Mas para o usuário, o que importa é: desde o último concurso, quem não saiu?
    # Vamos calcular quem falta baseado no progresso atual
    faltantes = sorted(list(todos_numeros - sorteados_recentes)) # Isso se o ciclo estivesse fechado agora
    # Na verdade, queremos os que faltam para o ciclo em aberto:
    progresso_atual = set()
    concursos_contados = 0
    for _, row in df.sort_values('concurso', ascending=False).iterrows():
        bolas = set(row[col_bolas])
        if len(progresso_atual.union(bolas)) == 25 and concursos_contados > 0:
             # O ciclo anterior fechou aqui. O novo ciclo começou no concurso seguinte.
             break
        progresso_atual.update(bolas)
        concursos_contados += 1
    
    faltantes_ciclo = sorted(list(todos_numeros - progresso_atual))
    return faltantes_ciclo, concursos_contados

def gerar_jogos_blindados_v2(df_stats, faltantes_ciclo, qtd=5):
    jogos = []
    todos = set(range(1, 26))
    
    # Prioridade 1: Números do Ciclo (Faltantes)
    # Se faltarem muitos, pegamos uma parte. Se faltarem poucos, pegamos quase todos.
    pool_ciclo = set(faltantes_ciclo)
    
    # Prioridade 2: Frequentes (removendo os do ciclo para não duplicar)
    frequentes = set(df_stats.nlargest(12, 'Frequencia')['Número'].tolist()) - pool_ciclo
    
    # Prioridade 3: Atrasados (removendo os já escolhidos)
    disp_atraso = todos - pool_ciclo - frequentes
    atrasados = set(df_stats[df_stats['Número'].isin(disp_atraso)].nlargest(7, 'Atraso')['Número'].tolist())
    
    neutros = todos - pool_ciclo - frequentes - atrasados

    while len(jogos) < qtd:
        # Lógica de montagem:
        # Se tem 3 faltantes no ciclo, incluímos os 3.
        # Completamos com frequentes, atrasados e neutros.
        n_ciclo = len(pool_ciclo)
        escolha_ciclo = list(pool_ciclo) 
        
        n_restante = 15 - n_ciclo
        # Distribuição dinâmica
        amostra = escolha_ciclo + \
                  random.sample(list(frequentes), min(len(frequentes), 6)) + \
                  random.sample(list(atrasados), min(len(atrasados), 3)) + \
                  random.sample(list(neutros), max(0, 15 - n_ciclo - 6 - 3))
        
        # Ajusta para exatamente 15 caso a soma varie
        if len(amostra) > 15: amostra = random.sample(amostra, 15)
        
        combinacao = sorted(amostra)
        n_pares = sum(1 for n in combinacao if n % 2 == 0)
        
        if 6 <= n_pares <= 9 and combinacao not in jogos:
            jogos.append(combinacao)
    return jogos

# --- 3. INTERFACE ---

st.sidebar.header("📁 Base de Dados")
arquivo_excel = st.sidebar.file_uploader("Upload .xlsx", type=["xlsx"])

if arquivo_excel:
    df, col_bolas = carregar_dados(arquivo_excel)
    if df is not None:
        stats = pd.DataFrame() # Placeholder para função abaixo
        def calcular_stats_local(df, col_bolas):
            ultimo = df['concurso'].max()
            todos_nums = df[col_bolas].values.flatten()
            freq = pd.Series(todos_nums).value_counts()
            atr = {n: int(ultimo - df[df[col_bolas].isin([n]).any(axis=1)]['concurso'].max()) for n in range(1, 26)}
            return pd.DataFrame({'Número': range(1, 26), 'Frequencia': [freq.get(i,0) for i in range(1,26)], 'Atraso': [atr[i] for i in range(1,26)]})
        
        stats = calcular_stats_local(df, col_bolas)
        faltantes, contagem_ciclo = calcular_ciclo(df, col_bolas)
        
        menu = st.tabs(["📊 Histórico", "🔄 Ciclo Atual", "⌛ Atrasos", "🎲 Gerador Inteligente", "🎲 Gerador Manual"])

        with menu[0]:
            st.metric("Total de Concursos", len(df))
            st.plotly_chart(px.line(df.tail(50), x='concurso', y='soma', title="Evolução da Soma"), use_container_width=True)
            st.write(df.tail())

        with menu[1]:
            st.header("🔄 O Ciclo das Dezenas")
            st.write(f"O ciclo atual está no **{contagem_ciclo}º concurso**.")
            
            if not faltantes:
                st.success("O ciclo fechou no último concurso! Um novo ciclo começa agora.")
            else:
                st.warning(f"Faltam {len(faltantes)} dezenas para fechar o ciclo:")
                html_ciclo = "".join([f'<span class="bola bola-ciclo">{n:02d}</span>' for n in faltantes])
                st.markdown(html_ciclo, unsafe_allow_html=True)
                st.info("Estatisticamente, essas dezenas têm alta tendência de sorteio nos próximos concursos.")

        with menu[2]:
            st.plotly_chart(px.bar(stats, x='Número', y='Atraso', color='Atraso', color_continuous_scale='Reds'), use_container_width=True)
            st.write(stats)

        with menu[3]:
            st.header("🎲 Gerador Baseado em Ciclo e Estatística")
            st.write("Esta inteligência prioriza as dezenas faltantes do ciclo + as mais frequentes.")
            
            if st.button("🚀 Gerar Jogos Estratégicos"):
                st.session_state.jogos_v2 = gerar_jogos_blindados_v2(stats, faltantes)
            
            if 'jogos_v2' in st.session_state:
                for i, jogo in enumerate(st.session_state.jogos_v2):
                    with st.expander(f"Sugestão {i+1}", expanded=True):
                        html_bolas = "".join([f'<span class="bola {"bola-ciclo" if n in faltantes else ""}">{n:02d}</span>' for n in jogo])
                        st.markdown(html_ciclo, unsafe_allow_html=True) # Legenda
                        st.markdown(html_bolas, unsafe_allow_html=True)
                        st.caption("Laranja = Números do Ciclo | Verde = Estatísticos")
                        
                        # Backtest
                        jogo_set = set(jogo)
                        res = df[col_bolas].apply(lambda row: len(jogo_set.intersection(set(row))), axis=1).value_counts()
                        m = st.columns(5)
                        for p in range(11, 16):
                            m[p-11].metric(f"{p} pts", res.get(p, 0))

        with menu[4]:
            st.header("🎲 Gerador Baseado em Dados Informados")
            st.write("Informar os números para simulação.")
            
            with st.expander("🛠️ Testador de Grupo Manual"):
                selecao = st.multiselect("Selecione sua pool (ex: 18 números):", range(1, 26), default=list(range(1, 16)))
                if st.button("Gerar 1 Jogo da Seleção e Testar"):
                    if len(selecao) < 15: st.warning("Selecione ao menos 15 números.")
                    
                    else:
                        st.write(selecao)
                        j_man = sorted(random.sample(selecao, 15))
                        jogo_set = set(j_man)
                        st.markdown(f"**Jogo Manual:** `{' - '.join([f'{n:02d}' for n in j_man])}`")
                        res = df[col_bolas].apply(lambda row: len(jogo_set.intersection(set(row))), axis=1).value_counts()
                        #rm = backtest_jogo(df, j_man, col_bolas)
                        m = st.columns(5)
                        for p in range(11, 16):
                            m[p-11].metric(f"{p} pts", res.get(p, 0))
                        #st.write(f"Histórico: **11pts**: {rm.get(11,0)} | **12pts**: {rm.get(12,0)} | **13pts**: {rm.get(13,0)} | **14+**: {rm.get(14,0)+rm.get(15,0)}")
                        st.write(f"Histórico: **11pts**: {res.get(11,0)} | **12pts**: {res.get(12,0)} | **13pts**: {res.get(13,0)} | **14+**: {res.get(14,0)+res.get(15,0)}")
                        
else:
    st.info("Aguardando Excel...")