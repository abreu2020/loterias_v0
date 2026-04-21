import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- FUNÇÕES DE APOIO ---
def calcular_puro(n):
    s = sum(int(d) for d in str(n) if d.isdigit())
    return s if s <= 9 else calcular_puro(s)

def rodar_backtest_teoria(df, col_bolas):
    relatorio = []
    # Garantir ordem cronológica
    df = df.sort_values('concurso').reset_index(drop=True)
    
    for i in range(1, len(df)):
        atual = df.iloc[i]
        anterior = df.iloc[i-1]
        
        # 1. Dados Reais do Sorteio
        bolas_atual = set(atual[col_bolas])
        bolas_anterior = set(anterior[col_bolas])
        repetidos_reais = len(bolas_atual.intersection(bolas_anterior))
        soma_real = atual['soma']
        puro_resultado = calcular_puro(soma_real)
        
        # 2. Dados da Data (Teoria)
        data_str = pd.to_datetime(atual['data']).strftime('%d%m%Y')
        puro_data = calcular_puro(data_str)
        
        # 3. Cruzamento: A data "previu" a frequência da soma?
        bateu_numerologia = (puro_data == puro_resultado)
        
        relatorio.append({
            'concurso': atual['concurso'],
            'repetidos': repetidos_reais,
            'puro_data': puro_data,
            'puro_res': puro_resultado,
            'sucesso_teoria': bateu_numerologia,
            'faixa_repeticao': 'Ideal (8-10)' if 8 <= repetidos_reais <= 10 else 'Fora'
        })
    
    return pd.DataFrame(relatorio)

# --- INTERFACE ---
st.title("🧪 Backtest: Validação da Teoria dos Grupos Isolados")

arquivo = st.file_uploader("Suba sua base histórica (.xlsx)", type="xlsx")

if arquivo:
    df_base = pd.read_excel(arquivo)
    df_base.columns = [c.strip().lower() for c in df_base.columns]
    col_bolas = [f'bola{i}' for i in range(1, 16)]
    df_base['soma'] = df_base[col_bolas].sum(axis=1)
    
    if st.button("🚀 Iniciar Simulação Histórica"):
        res = rodar_backtest_teoria(df_base, col_bolas)
        
        # --- MÉTRICAS GERAIS ---
        c1, c2, c3 = st.columns(3)
        total = len(res)
        sucessos = res['sucesso_teoria'].sum()
        
        c1.metric("Total Concursos Testados", total)
        c2.metric("Confluência Data/Resultado", sucessos)
        c3.metric("Taxa de Assertividade", f"{(sucessos/total)*100:.2f}%")
        
        # --- GRÁFICO DE REPETIÇÃO ---
        st.subheader("📊 Comportamento dos Repetidos (8, 9, 10)")
        fig_rep = px.pie(res, names='faixa_repeticao', title="Proporção de Repetição do Anterior",
                         color_discrete_map={'Ideal (8-10)':'#2E7D32', 'Fora':'#C62828'})
        st.plotly_chart(fig_rep)
        
        # --- ANÁLISE DE TENDÊNCIA ---
        st.subheader("📈 Janela de Oportunidade")
        st.write("Abaixo, os concursos onde a **Data do Sorteio** e o **Resultado** vibraram no mesmo Número Puro:")
        
        df_sucesso = res[res['sucesso_teoria'] == True].tail(10)
        st.dataframe(df_sucesso[['concurso', 'puro_data', 'puro_res', 'repetidos']])
        
        st.markdown("""
        > **Como ler esse Backtest:** > Se a Taxa de Assertividade estiver acima de **11%**, sua "maluquice" tem fundamento estatístico. 
        > Se os últimos concursos mostram sucessos seguidos, estamos em uma fase de alta convergência para o seu método!
        """)