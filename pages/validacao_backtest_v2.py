import streamlit as st
import pandas as pd
import random
from datetime import datetime

# Estilização
st.markdown("""
<style>
.bola-sorte {
    background-color: #2E7D32; color: white; padding: 10px; border-radius: 50%;
    margin: 5px; font-weight: bold; display: inline-block; width: 42px; text-align: center;
    box-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}
.alerta-gemeo { color: #D32F2F; font-weight: bold; background-color: #FFEBEE; padding: 10px; border-radius: 5px; }
.sucesso-inedito { color: #388E3C; font-weight: bold; background-color: #E8F5E9; padding: 10px; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

def calcular_puro(n):
    s = sum(int(d) for d in str(n) if d.isdigit())
    return s if s <= 9 else calcular_puro(s)

def verificar_gemeos(df, jogo_gerado, col_bolas):
    """Compara o jogo com todo o histórico para ver se já houve 15 pontos igual."""
    jogo_set = set(jogo_gerado)
    # Verifica acertos em cada concurso passado
    df['acertos'] = df[col_bolas].apply(lambda row: len(jogo_set.intersection(set(row))), axis=1)
    
    max_acertos = df['acertos'].max()
    vezes_max = (df['acertos'] == max_acertos).sum()
    concurso_max = df[df['acertos'] == max_acertos]['concurso'].iloc[-1] if vezes_max > 0 else "-"
    
    return max_acertos, vezes_max, concurso_max

def gerar_jogo_sniper(df, num_puro_alvo, lista_rep, col_bolas):
    ultimo = df.sort_values('concurso').iloc[-1]
    sairam_ontem = list(ultimo[col_bolas])
    nao_sairam = [n for n in range(1, 26) if n not in sairam_ontem]
    
    for _ in range(3000): # Aumentamos as tentativas para achar o jogo perfeito
        rep = random.choice(lista_rep)
        jogo = sorted(random.sample(sairam_ontem, rep) + random.sample(nao_sairam, 15 - rep))
        
        # Filtros de Backtest e Numerologia
        if calcular_puro(sum(jogo)) == num_puro_alvo:
            pares = sum(1 for n in jogo if n % 2 == 0)
            if 7 <= pares <= 8:
                # Verificação de Ineditismo (Não queremos jogo que já fez 15)
                max_ac, _, _ = verificar_gemeos(df, jogo, col_bolas)
                if max_ac < 15: # Só aceita se nunca tiver feito 15 pontos
                    return jogo
    return None

# --- Interface ---
st.title("🎯 Gerador Sniper + Detector de Gêmeos")

arquivo = st.file_uploader("Suba sua base Excel atualizada", type="xlsx")

if arquivo:
    df = pd.read_excel(arquivo)
    df.columns = [c.strip().lower() for c in df.columns]
    col_bolas = [f'bola{i}' for i in range(1, 16)]
    
    with st.sidebar:
        data_sorteio = st.date_input("Próximo Sorteio", datetime.now())
        puro = calcular_puro(data_sorteio.strftime('%d%m%Y'))
        st.write(f"Vibração do Dia: **{puro}**")

    if st.button("🚀 Gerar e Validar Jogos"):
        for i in range(3): # Gerando 3 sugestões ultra-filtradas
            jogo = gerar_jogo_sniper(df, puro, [8, 9, 10], col_bolas)
            
            if jogo:
                st.subheader(f"Sugestão Sniper {i+1}")
                html = "".join([f'<span class="bola-sorte">{n:02d}</span>' for n in jogo])
                st.markdown(html, unsafe_allow_html=True)
                
                # Validação de Gêmeos no Painel
                max_ac, vezes, conc = verificar_gemeos(df, jogo, col_bolas)
                
                c1, c2 = st.columns(2)
                with c1:
                    if max_ac == 14:
                        st.warning(f"⚠️ Este jogo já fez 14 pontos no concurso {conc}!")
                    elif max_ac < 14:
                        st.markdown(f'<p class="sucesso-inedito">✅ Jogo Inédito (Máx: {max_ac} pts)</p>', unsafe_allow_html=True)
                with c2:
                    st.write(f"Soma: **{sum(jogo)}** | Puro: **{puro}**")
                st.divider()