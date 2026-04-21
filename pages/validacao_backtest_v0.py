import streamlit as st
import pandas as pd
import plotly.express as px

def calcular_puro(n):
    s = sum(int(d) for d in str(n) if d.isdigit())
    return s if s <= 9 else calcular_puro(s)

def rodar_backtest_confluencia(df, col_bolas):
    relatorio = []
    df = df.sort_values('concurso').reset_index(drop=True)
    
    for i in range(len(df)):
        linha = df.iloc[i]
        
        # 1. Puro do Resultado (Soma das 15 dezenas)
        puro_res = calcular_puro(linha['soma'])
        
        # 2. Puro da Data (DDMMYYYY)
        data_str = pd.to_datetime(linha['data']).strftime('%d%m%Y')
        puro_data = calcular_puro(data_str)
        
        # 3. Puro do Número do Concurso (Ex: 3050 -> 8)
        puro_concurso = calcular_puro(linha['concurso'])
        
        relatorio.append({
            'concurso': linha['concurso'],
            'puro_res': puro_res,
            'puro_data': puro_data,
            'puro_concurso': puro_concurso,
            'match_data': 1 if puro_data == puro_res else 0,
            'match_concurso': 1 if puro_concurso == puro_res else 0,
            'confluencia_total': 1 if (puro_data == puro_res and puro_concurso == puro_res) else 0
        })
    
    return pd.DataFrame(relatorio)

# --- Interface ---
st.title("🧪 Backtest de Convergência: Data vs Concurso")

arquivo = st.file_uploader("Suba a base para o teste de confluência", type="xlsx")

if arquivo:
    df_base = pd.read_excel(arquivo)
    df_base.columns = [c.strip().lower() for c in df_base.columns]
    col_bolas = [f'bola{i}' for i in range(1, 16)]
    df_base['soma'] = df_base[col_bolas].sum(axis=1)
    
    if st.button("🔍 Analisar Sincronia"):
        res = rodar_backtest_confluencia(df_base, col_bolas)
        total = len(res)
        
        # Métricas
        m1, m2, m3 = st.columns(3)
        acc_data = (res['match_data'].sum() / total) * 100
        acc_concurso = (res['match_concurso'].sum() / total) * 100
        acc_dupla = (res['confluencia_total'].sum() / total) * 100
        
        m1.metric("Sucesso pela Data", f"{acc_data:.2f}%")
        m2.metric("Sucesso pelo Concurso", f"{acc_concurso:.2f}%")
        m3.metric("Confluência (Data + Conc)", f"{acc_dupla:.2f}%")
        
        st.write("---")
        st.subheader("📈 Mapa de Calor de Resultados")
        st.write("Veja se existe algum Número Puro que domina os resultados:")
        
        fig = px.histogram(res, x="puro_res", color_discrete_sequence=['#2E7D32'], 
                           title="Distribuição dos Números Puros nos Resultados")
        st.plotly_chart(fig)
        
        st.subheader("📋 Últimos Concursos e suas Sincronias")
        st.dataframe(res[['concurso', 'puro_data', 'puro_concurso', 'puro_res']].tail(15))