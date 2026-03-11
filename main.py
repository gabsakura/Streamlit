import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Produtividade",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .header-title {
        color: #1f77b4;
        font-size: 32px;
        font-weight: bold;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Título
st.markdown("<div class='header-title'>📊 Dashboard de Produtividade</div>", unsafe_allow_html=True)
st.markdown("Análise de dados de mão de obra em obras de construção civil")
st.divider()

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

@st.cache_data
def carregar_dados(arquivo_csv):
    """Carrega e processa os dados do CSV"""
    df = pd.read_csv(arquivo_csv, sep=';', encoding='iso-8859-1')
    
    # Converter colunas numéricas
    colunas_numericas = ['qntd', 'qs', 'ip_d', 'ip_acum']
    for col in colunas_numericas:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.').astype(float)
    
    # Converter data
    if 'data' in df.columns:
        df['data'] = pd.to_datetime(df['data'], errors='coerce')
    
    # Filtrar apenas mão de obra
    df = df[df['tipo_insumo'] == 'MAO DE OBRA'].copy()
    
    return df

def calcular_estatisticas(valores):
    """Calcula estatísticas descritivas"""
    valores = valores.dropna()
    
    if len(valores) == 0:
        return {
            'média': 0, 'mediana': 0, 'moda': 0, 'desvio_padrao': 0,
            'minimo': 0, 'maximo': 0, 'q1': 0, 'q3': 0, 'count': 0
        }
    
    try:
        moda_result = stats.mode(valores, keepdims=True)
        moda = moda_result.mode[0] if len(moda_result.mode) > 0 else valores.mean()
    except:
        moda = valores.mean()
    
    return {
        'média': float(valores.mean()),
        'mediana': float(valores.median()),
        'moda': float(moda),
        'desvio_padrao': float(valores.std()),
        'minimo': float(valores.min()),
        'maximo': float(valores.max()),
        'q1': float(valores.quantile(0.25)),
        'q3': float(valores.quantile(0.75)),
        'count': len(valores)
    }

def aplicar_filtros(df, filtros):
    """Aplica filtros aos dados"""
    df_filtrado = df.copy()
    
    if filtros['obra'] and filtros['obra'] != 'Todas as obras':
        df_filtrado = df_filtrado[df_filtrado['nome_obra'] == filtros['obra']]
    
    if filtros['bloco'] and filtros['bloco'] != 'Todos os blocos':
        df_filtrado = df_filtrado[df_filtrado['caderno'] == filtros['bloco']]
    
    if filtros['servico'] and filtros['servico'] != 'Todos os serviços':
        df_filtrado = df_filtrado[df_filtrado['descricao'] == filtros['servico']]
    
    if filtros['data_inicio']:
        df_filtrado = df_filtrado[df_filtrado['data'] >= pd.Timestamp(filtros['data_inicio'])]
    
    if filtros['data_fim']:
        df_filtrado = df_filtrado[df_filtrado['data'] <= pd.Timestamp(filtros['data_fim'])]
    
    return df_filtrado

# ============================================================================
# CARREGAMENTO DE DADOS
# ============================================================================

# Upload ou usar arquivo padrão
st.sidebar.markdown("### 📁 Carregar Dados")
arquivo_carregado = st.sidebar.file_uploader("Escolha um arquivo CSV", type=['csv'])

if arquivo_carregado is not None:
    df = carregar_dados(arquivo_carregado)
    st.sidebar.success(f"✅ Dados carregados: {len(df)} registros")
else:
    # Tentar carregar do arquivo padrão
    try:
        df = carregar_dados('df_diarios.csv')
        st.sidebar.info("📂 Usando arquivo padrão")
    except:
        st.error("❌ Nenhum arquivo encontrado. Por favor, faça upload de um arquivo CSV.")
        st.stop()

# ============================================================================
# PAINEL DE FILTROS
# ============================================================================

st.sidebar.markdown("### 🔍 Filtros")

# Obter valores únicos
obras = ['Todas as obras'] + sorted(df['nome_obra'].dropna().unique().tolist())
blocos = ['Todos os blocos'] + sorted(df['caderno'].dropna().unique().tolist())
servicos = ['Todos os serviços'] + sorted(df['descricao'].dropna().unique().tolist())

# Seletores
filtros = {
    'obra': st.sidebar.selectbox("Obra", obras),
    'bloco': st.sidebar.selectbox("Bloco/Caderno", blocos),
    'servico': st.sidebar.selectbox("Serviço", servicos),
    'data_inicio': st.sidebar.date_input("Data Inicial", value=None),
    'data_fim': st.sidebar.date_input("Data Final", value=None)
}

# Botão para limpar filtros
if st.sidebar.button("🔄 Limpar Filtros"):
    st.rerun()

# Aplicar filtros
df_filtrado = aplicar_filtros(df, filtros)

st.sidebar.divider()
st.sidebar.markdown(f"**Registros:** {len(df_filtrado)} / {len(df)}")

# ============================================================================
# ESTATÍSTICAS DESCRITIVAS
# ============================================================================

st.markdown("### 📈 Resumo Geral")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total de Registros", f"{len(df_filtrado):,}")

with col2:
    st.metric("Quantidade Média Produzida", f"{df_filtrado['qntd'].mean():.2f}")

with col3:
    st.metric("Horas Médias Empregadas", f"{df_filtrado['qs'].mean():.2f}")

st.divider()

# Calcular estatísticas
stats_qntd = calcular_estatisticas(df_filtrado['qntd'])
stats_qs = calcular_estatisticas(df_filtrado['qs'])
stats_ip = calcular_estatisticas(df_filtrado['ip_d'])

# Exibir estatísticas em abas
tab1, tab2, tab3 = st.tabs(["📊 Quantidade Produzida", "⏱️ Horas Empregadas", "🎯 Produtividade (IP)"])

with tab1:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Média", f"{stats_qntd['média']:.4f}")
    with col2:
        st.metric("Mediana", f"{stats_qntd['mediana']:.4f}")
    with col3:
        st.metric("Moda", f"{stats_qntd['moda']:.4f}")
    with col4:
        st.metric("Desvio Padrão", f"{stats_qntd['desvio_padrao']:.4f}")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Mínimo", f"{stats_qntd['minimo']:.4f}")
    with col2:
        st.metric("Máximo", f"{stats_qntd['maximo']:.4f}")
    with col3:
        st.metric("Q1 (25%)", f"{stats_qntd['q1']:.4f}")
    with col4:
        st.metric("Q3 (75%)", f"{stats_qntd['q3']:.4f}")

with tab2:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Média", f"{stats_qs['média']:.4f}")
    with col2:
        st.metric("Mediana", f"{stats_qs['mediana']:.4f}")
    with col3:
        st.metric("Moda", f"{stats_qs['moda']:.4f}")
    with col4:
        st.metric("Desvio Padrão", f"{stats_qs['desvio_padrao']:.4f}")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Mínimo", f"{stats_qs['minimo']:.4f}")
    with col2:
        st.metric("Máximo", f"{stats_qs['maximo']:.4f}")
    with col3:
        st.metric("Q1 (25%)", f"{stats_qs['q1']:.4f}")
    with col4:
        st.metric("Q3 (75%)", f"{stats_qs['q3']:.4f}")

with tab3:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Média", f"{stats_ip['média']:.4f}")
    with col2:
        st.metric("Mediana", f"{stats_ip['mediana']:.4f}")
    with col3:
        st.metric("Moda", f"{stats_ip['moda']:.4f}")
    with col4:
        st.metric("Desvio Padrão", f"{stats_ip['desvio_padrao']:.4f}")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Mínimo", f"{stats_ip['minimo']:.4f}")
    with col2:
        st.metric("Máximo", f"{stats_ip['maximo']:.4f}")
    with col3:
        st.metric("Q1 (25%)", f"{stats_ip['q1']:.4f}")
    with col4:
        st.metric("Q3 (75%)", f"{stats_ip['q3']:.4f}")

st.divider()

# ============================================================================
# GRÁFICOS DE ANÁLISE
# ============================================================================

st.markdown("### 📉 Análises e Gráficos")

# Verificar se há dados para exibir
if len(df_filtrado) == 0:
    st.warning("⚠️ Nenhum dado encontrado com os filtros selecionados. Ajuste os filtros e tente novamente.")
else:
    # Top 10 Serviços por Produtividade
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Top 10 Serviços por Produtividade Média")
        
        top_servicos = df_filtrado.groupby('descricao').agg({
            'ip_d': 'mean',
            'descricao': 'count'
        }).rename(columns={'descricao': 'count'}).sort_values('ip_d', ascending=False).head(10)
        
        if len(top_servicos) > 0:
            fig = px.bar(
                top_servicos.reset_index(),
                x='descricao',
                y='ip_d',
                title="",
                labels={'ip_d': 'Produtividade Média', 'descricao': 'Serviço'},
                color='ip_d',
                color_continuous_scale='Blues'
            )
            fig.update_layout(height=400, xaxis_tickangle=-30 , showlegend=False)
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("Sem dados para exibir")

    # Produtividade por Obra
    with col2:
        st.markdown("#### Produtividade Média por Obra")
        
        prod_obra = df_filtrado.groupby('nome_obra')['ip_d'].mean().sort_values(ascending=False)
        
        if len(prod_obra) > 0:
            fig = px.bar(
                prod_obra.reset_index(),
                x='nome_obra',
                y='ip_d',
                title="",
                labels={'ip_d': 'Produtividade Média', 'nome_obra': 'Obra'},
                color='ip_d',
                color_continuous_scale='Purples'
            )
            fig.update_layout(height=400, xaxis_tickangle=0, showlegend=False)
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("Sem dados para exibir")

    # Série Temporal
    st.markdown("#### Produtividade ao Longo do Tempo")

    df_tempo = df_filtrado.groupby(df_filtrado['data'].dt.date)['ip_d'].mean().reset_index()
    df_tempo.columns = ['Data', 'Produtividade Média']

    if len(df_tempo) > 0:
        fig = px.line(
            df_tempo,
            x='Data',
            y='Produtividade Média',
            title="",
            markers=True
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("Sem dados para exibir")

    # Scatter Plot: Quantidade vs Horas
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Relação: Quantidade vs Horas Empregadas")
        
        # Limitar a 1000 pontos para melhor performance
        df_scatter = df_filtrado.sample(min(1000, len(df_filtrado)))
        
        if len(df_scatter) > 0:
            fig = px.scatter(
                df_scatter,
                x='qntd',
                y='qs',
                color='ip_d',
                hover_data=['descricao', 'insumo'],
                title="",
                labels={'qntd': 'Quantidade Produzida', 'qs': 'Horas Empregadas', 'ip_d': 'Produtividade'},
                color_continuous_scale='Viridis'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("Sem dados para exibir")

    # Distribuição de Produtividade
    with col2:
        st.markdown("#### Distribuição de Produtividade (IP)")
        
        # Criar bins de forma segura
        ip_max = df_filtrado['ip_d'].max()
        ip_min = df_filtrado['ip_d'].min()
        
        # Ajustar bins dinamicamente baseado nos dados
        if ip_max <= 0.5:
            bins = [ip_min - 0.1, 0.5, ip_max + 0.1]
            labels = [f'{ip_min:.2f}-0.5', f'0.5-{ip_max:.2f}']
        elif ip_max <= 1:
            bins = [ip_min - 0.1, 0.5, 1, ip_max + 0.1]
            labels = [f'{ip_min:.2f}-0.5', '0.5-1', f'1-{ip_max:.2f}']
        elif ip_max <= 2:
            bins = [ip_min - 0.1, 0.5, 1, 2, ip_max + 0.1]
            labels = [f'{ip_min:.2f}-0.5', '0.5-1', '1-2', f'2-{ip_max:.2f}']
        elif ip_max <= 5:
            bins = [ip_min - 0.1, 0.5, 1, 2, 5, ip_max + 0.1]
            labels = [f'{ip_min:.2f}-0.5', '0.5-1', '1-2', '2-5', f'5-{ip_max:.2f}']
        else:
            bins = [ip_min - 0.1, 0.5, 1, 2, 5, ip_max + 0.1]
            labels = [f'{ip_min:.2f}-0.5', '0.5-1', '1-2', '2-5', f'>5']
        
        df_filtrado_copy = df_filtrado.copy()
        df_filtrado_copy['ip_bin'] = pd.cut(df_filtrado_copy['ip_d'], bins=bins, labels=labels, include_lowest=True)
        
        dist = df_filtrado_copy['ip_bin'].value_counts().sort_index()
        
        if len(dist) > 0:
            fig = px.bar(
                x=dist.index.astype(str),
                y=dist.values,
                title="",
                labels={'x': 'Faixa de Produtividade', 'y': 'Quantidade de Registros'},
                color=dist.values,
                color_continuous_scale='Oranges'
            )
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("Sem dados para exibir")

st.divider()

# ============================================================================
# TABELA DE DADOS
# ============================================================================

st.markdown("### 📋 Dados Filtrados")

if len(df_filtrado) > 0:
    # Colunas a exibir
    colunas_exibir = ['nome_obra', 'caderno', 'descricao', 'insumo', 'qntd', 'qs', 'ip_d', 'data']
    df_exibir = df_filtrado[colunas_exibir].copy()
    df_exibir.columns = ['Obra', 'Bloco', 'Serviço', 'Insumo', 'Qtd', 'Horas', 'Produtividade', 'Data']

    # Formatar números
    df_exibir['Qtd'] = df_exibir['Qtd'].apply(lambda x: f"{x:.2f}")
    df_exibir['Horas'] = df_exibir['Horas'].apply(lambda x: f"{x:.2f}")
    df_exibir['Produtividade'] = df_exibir['Produtividade'].apply(lambda x: f"{x:.4f}")
    df_exibir['Data'] = df_exibir['Data'].astype(str).str.split(' ').str[0]

    # Exibir tabela
    st.dataframe(df_exibir, width='stretch', height=400)

    # Botão para download
    csv = df_exibir.to_csv(index=False, encoding='utf-8')
    st.download_button(
        label="📥 Baixar dados como CSV",
        data=csv,
        file_name="dados_produtividade.csv",
        mime="text/csv"
    )
else:
    st.warning("⚠️ Nenhum dado para exibir com os filtros selecionados.")

st.divider()

# ============================================================================
# RODAPÉ
# ============================================================================

st.markdown("""
    ---
    **Dashboard de Produtividade** | Desenvolvido com Streamlit)""")