import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz 

# 1. Configuração da página
st.set_page_config(page_title="Metro Mondego Horários", layout="centered")
st.title("🚇 Horários Metro Mondego")

# 2. Carregar a Base de Dados
@st.cache_data
def carregar_dados():
    return pd.read_csv("horarios1.csv")

df = carregar_dados()

st.divider()

# 3. Interface de Pesquisa
st.subheader("Consultar Próximas Partidas")

col1, col2, col3 = st.columns(3)
lista_estacoes = df['Estacao'].unique().tolist() 

with col1:
    origem = st.selectbox("Local de Saída", lista_estacoes)
with col2:
    destino = st.selectbox("Local de Chegada", lista_estacoes, index=len(lista_estacoes)-1)
with col3:
    st.write("Hora de Partida")
    col_h, col_m = st.columns(2)
    
    # FORÇAR O FUSO HORÁRIO DE PORTUGAL AQUI:
    fuso_portugal = pytz.timezone('Europe/Lisbon')
    hora_atual = datetime.now(fuso_portugal)
    
    with col_h:
        # Dropdown para as horas (00 a 23)
        lista_horas = [f"{i:02d}" for i in range(24)]
        h = st.selectbox("Horas", lista_horas, index=hora_atual.hour, label_visibility="collapsed")
        
    with col_m:
        # Dropdown para os minutos (de 5 em 5)
        lista_minutos = [f"{i:02d}" for i in range(0, 60, 5)]
        # Arredonda o minuto atual para o múltiplo de 5 mais próximo para definir o default
        minuto_atual_arredondado = (hora_atual.minute // 5) * 5
        index_minuto = lista_minutos.index(f"{minuto_atual_arredondado:02d}")
        m = st.selectbox("Min", lista_minutos, index=index_minuto, label_visibility="collapsed")

# 4. Lógica de Cálculo e Filtragem
if origem == destino:
    st.warning("A estação de saída e chegada não podem ser a mesma.")
else:
    # Definir o dia da semana atual no fuso de Portugal
    dia_semana = hora_atual.weekday()
    if dia_semana == 5:
        tipo_dia = "Sábados"
    elif dia_semana == 6:
        tipo_dia = "Domingos e Feriados"
    else:
        tipo_dia = "Dias Úteis"
        
    # Descobrir o sentido usando a ordem das estações (1 ou 2)
    ordem_origem = df[df['Estacao'] == origem]['Ordem'].values[0]
    ordem_destino = df[df['Estacao'] == destino]['Ordem'].values[0]
    sentido_viagem = 1 if ordem_origem < ordem_destino else 2
    
    # Juntar a hora e os minutos escolhidos no formato "HH:MM"
    hora_filtro_str = f"{h}:{m}"
    
    # Procurar metros a partir da hora selecionada
    filtro_origem = df[
        (df['Tipo_Dia'] == tipo_dia) & 
        (df['Sentido'] == sentido_viagem) & 
        (df['Estacao'] == origem) & 
        (df['Hora'] >= hora_filtro_str)
    ].sort_values(by='Hora')
    
    st.write(f"A calcular rota de **{origem}** para **{destino}** a partir das **{hora_filtro_str}**...")
    
    resultados_mostrados = 0
    
    # Vamos verificar viagem a viagem
    for index, row in filtro_origem.iterrows():
        if resultados_mostrados >= 3: 
            break
            
        id_viagem_atual = row['ID_Viagem'] 
        hora_partida = row['Hora']
        
        # Procurar a que horas ESTE metro específico (mesmo ID) chega ao destino
        chegada_df = df[(df['ID_Viagem'] == id_viagem_atual) & (df['Estacao'] == destino)]
        
        # Se encontrou o metro no destino
        if not chegada_df.empty:
            hora_chegada = chegada_df['Hora'].values[0]
            
            # Calcular os minutos de diferença entre a partida e a chegada
            formato_hora = "%H:%M"
            tempo_inicio = datetime.strptime(hora_partida, formato_hora)
            tempo_fim = datetime.strptime(hora_chegada, formato_hora)
            
            # Correção para viagens que passam a meia-noite
            if tempo_fim < tempo_inicio:
                tempo_fim += timedelta(days=1)
            
            minutos_viagem = int((tempo_fim - tempo_inicio).total_seconds() / 60)
            
            # Desenhar o dashboard com os resultados
            st.success(f"🚇 **Metro #{id_viagem_atual}**")
            metrica1, metrica2, metrica3 = st.columns(3)
            with metrica1:
                st.metric(label="Partida", value=hora_partida)
            with metrica2:
                st.metric(label="Chegada", value=hora_chegada)
            with metrica3:
                st.metric(label="Tempo de Viagem", value=f"{minutos_viagem} min")
                
            resultados_mostrados += 1

    if resultados_mostrados == 0:
        st.info("Não há metros disponíveis para este trajeto a partir da hora selecionada.")
