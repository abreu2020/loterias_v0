import streamlit as st
import pandas as pd
import plotly.express as px

def calcular_numero_puro(valor):
    """Soma os dígitos de um número até restar apenas um dígito (ou o valor final)"""
    s = str(valor).replace('-', '').replace('/', '').replace(' ', '')
    soma = sum(int(digito) for digito in s if digito.isdigit())
    while soma > 9:
        soma = sum(int(d) for d in str(soma))
    return soma

def rodar_simulador(df, col_bolas):
    resultados = []
    
    # Ordenar por concurso para garantir que o "anterior" esteja correto
    df = df.sort_values('concurso').reset_index(drop=True)
    
    for i in range(1, len(df)):
        concurso_atual = df.iloc[i]
        concurso_anterior = df.iloc[i-1]
        
        # 1. Cálculo de Repetição
        set_atual = set(concurso_atual[col_bolas])
        set_anterior = set(concurso_anterior[col_bolas])
        repetidos = len(set_atual.intersection(set_anterior))
        
        # 2. Cálculo do Número Puro da Data (assumindo coluna 'data')
        # Se sua coluna data estiver em formato datetime:
        data_sorteio = pd.to_datetime(concurso_atual['data'])
        data_str = data_sorteio.strftime('%d%m%Y')
        num_puro_data = calcular_numero_puro(data_str)
        
        # 3. Cálculo do Número Puro da Soma do Resultado
        num_puro_resultado = calcular_numero_puro(concurso_atual['soma'])
        
        resultados.append({
            'concurso': concurso_atual['concurso'],
            'repetidos': repetidos,
            'puro_data': num_puro_data,
            'puro_resultado': num_puro_resultado,
            'coincidencia_pura': 1 if num_puro_data == num_puro_resultado else 0
        })
        
    return pd.DataFrame(resultados)

# --- INTERFACE DO SIMULADOR ---
st.title("🧪 Simulador de Hipóteses e Padrões")

arquivo = st.file_uploader("Suba sua base (.xlsx) para testar a teoria", type="xlsx")

if arquivo:
    df = pd.read_excel(arquivo)
    df.columns = [c.strip().lower() for c in df.columns]
    col_bolas = [f'bola{i}' for i in range(1, 16)]
    df['soma'] = df[col_bolas].sum(axis=1)
    
    if st.button("🔍 Rodar Análise de Padrões"):
        res_sim = rodar_simulador(df, col_bolas)
        
        # --- SEÇÃO 1: REPETIÇÃO ---
        st.header("1. O Padrão de Repetição")
        frequencia_rep = res_sim['repetidos'].value_counts(normalize=True) * 100
        st.write("Frequência de números repetidos do concurso anterior:")
        st.bar_chart(frequencia_rep)
        
        mais_comum = res_sim['repetidos'].mode()[0]
        st.info(f"O padrão mais comum é repetir **{mais_comum} números**. Isso ocorre em {frequencia_rep.max():.1f}% dos casos.")

        # --- SEÇÃO 2: NUMEROLOGIA DA DATA ---
        st.header("2. O Número Puro da Data")
        total_testes = len(res_sim)
        acertos_puros = res_sim['coincidencia_pura'].sum()
        percentual_puro = (acertos_puros / total_testes) * 100
        
        col1, col2 = st.columns(2)
        col1.metric("Soma da Data == Soma do Resultado", f"{acertos_puros} vezes")
        col2.metric("Taxa de Coincidência", f"{percentual_puro:.2f}%")
        
        st.write("### Tabela de Comparação (Últimos 20)")
        st.table(res_sim[['concurso', 'repetidos', 'puro_data', 'puro_resultado']].tail(20))
        
        # Insight
        if percentual_puro > 11.11: # 1/9 de chance teórica (números de 1 a 9)
            st.success("🎯 A teoria do Número Puro tem uma incidência ACIMA da média aleatória!")
        else:
            st.warning("⚖️ A teoria do Número Puro está dentro da média de probabilidade aleatória.")