import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# CONFIGURAÇÃO E LAYOUT
st.set_page_config(page_title="CP1 - Dashboard de Produtividade", layout="wide")

def load_data():
    path = "src/df_diarios.csv"
    try:
        # Leitura com separador ; conforme o arquivo df_diarios.csv
        df = pd.read_csv(path, sep=";", encoding="latin1")
        
        # Limpeza de nomes de colunas
        df.columns = df.columns.str.strip()
        
        # TRATAMENTO DE DADOS:
        if 'ip_d' in df.columns:
            df['ip_d'] = pd.to_numeric(df['ip_d'].astype(str).str.replace(',', '.'), errors='coerce')
        
        if 'qntd' in df.columns:
            df['qntd'] = pd.to_numeric(
                df['qntd'].astype(str).str.replace(',', '.'),
                errors='coerce'
            )
        
        # FILTRO OBRIGATÓRIO: Apenas Mão de Obra
        if 'tipo_insumo' in df.columns:
            df = df[df['tipo_insumo'].str.contains('MAO DE OBRA', case=False, na=False)]
            
        return df.dropna(subset=['ip_d'])
    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")
        return None

df = load_data()

if df is not None:
    st.title("🏗️ Dashboard de Produtividade - Construção Civil")
    st.markdown("---")

    # Sidebar - Filtro de Obras
    st.sidebar.header("Configurações")
    obras_disponiveis = sorted(df['nome_obra'].dropna().unique())
    selecao_obras = st.sidebar.multiselect("Selecione as Obras:", obras_disponiveis, default=obras_disponiveis)

    # Filtragem dos dados conforme seleção do usuário
    df_f = df[df['nome_obra'].isin(selecao_obras)]

    # Mensagem de Gestão Obrigatória
    st.warning("**Atenção:** Os dados abaixo referem-se exclusivamente à **Mão de Obra**, garantindo que o Índice de Produtividade (IP_D) seja analisado de forma homogênea.")

    # ABAS DO DASHBOARD
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Estatísticas", "📚 Tipos de variáveis", "📈 Gráficos exploratórios", "📽️ Questão Extra"])

    with tab1:
        st.header("1. Medidas de Tendência Central e Dispersão")
        if not df_f.empty:
            c1, c2 = st.columns(2)
            
            with c1:
                st.subheader("Tendência Central")
                
                # 1. Média e Mediana
                media = df_f['ip_d'].mean()
                mediana = df_f['ip_d'].median()
                
                # 2. Moda Rigorosa (Número exato que mais repete)
                moda_series = df_f['ip_d'].mode()
                moda_rigorosa = moda_series[0] if not moda_series.empty else 0
                
                # 3. Moda por Intervalo (Classe Modal)
                # Criamos 10 faixas de valores e vemos qual tem mais registros
                if not df_f['ip_d'].empty:
                    counts, bins = np.histogram(df_f['ip_d'], bins=10)
                    index_max = np.argmax(counts)
                    faixa_inicio = bins[index_max]
                    faixa_fim = bins[index_max + 1]
                else:
                    faixa_inicio, faixa_fim = 0, 0

                # Exibição dos Cards
                st.metric("Média (Hh/Unid)", f"{media:.4f}")
                st.metric("Mediana (Hh/Unid)", f"{mediana:.4f}")
                
                st.metric("Moda Rigorosa", f"{moda_rigorosa:.4f}")
                st.metric("Moda por Intervalo", f"{faixa_inicio:.4f} - {faixa_fim:.4f}")
                
                st.write("**Interpretação das Modas:**")
                st.write(f"A **Moda Rigorosa** é o valor exato que mais apareceu. Já a **Moda por Intervalo** indica que a maior concentração de produtividade da equipe está entre **{faixa_inicio:.4f}** e **{faixa_fim:.4f}**.")

            with c2:
                st.subheader("Medidas de Dispersão")
                desvio = df_f['ip_d'].std()
                variancia = df_f['ip_d'].var()
                maximo = df_f['ip_d'].max()
                minimo = df_f['ip_d'].min()
                st.write(f"**Desvio Padrão:** {desvio:.4f}")
                st.write(f"**Variância:** {variancia:.4f}")
                st.write(f"**Coef. de Variação:** {(desvio/media)*100:.2f}%")
                st.write(f"**Amplitude:** {maximo - minimo:.4f}")
            
            st.markdown("---")
            st.subheader("📋 Tabela de Dados Filtrados (Mão de Obra)")
            # Exibe as principais colunas para conferência do grupo
            st.dataframe(df_f[['nome_obra', 'descricao', 'insumo', 'qntd', 'ip_d']], width='stretch')

    with tab2:
        st.header("2. Identificação e Classificação das Variáveis")
        
        # Tabela de Classificação
        dados_variaveis = {
            "Variável": ["nome_obra", "descricao", "tipo_insumo", "qntd", "ip_d", "data"],
            "Tipo": ["Qualitativa", "Qualitativa", "Qualitativa", "Quantitativa", "Quantitativa", "Qualitativa"],
            "Classificação": ["Nominal", "Nominal", "Nominal", "Contínua", "Contínua", "Ordinal"]
        }
        st.table(pd.DataFrame(dados_variaveis))
        
        st.markdown("---")
        st.subheader("💡 Por que cada variável é classificada assim?")
        st.markdown("""
        * **nome_obra, descricao e tipo_insumo (Qualitativas Nominais):** Representam categorias ou nomes. Não existe uma ordem matemática entre 'Obra A' e 'Obra B', nem entre 'Pedreiro' e 'Servente'. São rótulos usados para agrupamento.
        * **ip_d e qntd (Quantitativas Contínuas):** São valores numéricos que resultam de medições e podem assumir qualquer valor decimal (ex: 0,0202...). A produtividade (IP_D) é contínua pois é uma razão entre tempo e produção.
        * **data (Qualitativa Ordinal):** Embora seja um registro temporal, no contexto de organização da base, as datas estabelecem uma ordem lógica de sucessão (o que aconteceu antes e depois), permitindo analisar a evolução da obra.
        """)

    with tab3:
        st.header("3. Análise Visual de Produtividade")
        
        # Boxplot - Pergunta A
        st.subheader("Variabilidade do IP_D por Obra")

        # Criamos o gráfico com uma altura maior (height)
        fig_box = px.box(
            df_f, 
            x="nome_obra", 
            y="ip_d", 
            color="nome_obra", 
            points="outliers", # Mudamos para 'outliers' para a caixa ganhar espaço lateral
            title="Distribuição de Produtividade (Menor IP_D = Maior Eficiência)",
            height=500 # Aumenta a altura para as caixas "esticarem"
        )

        # AJUSTES DE LARGURA E ESCALA
        fig_box.update_layout(
            boxgap=0.2,      # Diminui o espaço entre as caixas (elas ficam mais largas)
            boxgroupgap=0.1, # Diminui o espaço entre os grupos
            yaxis=dict(
                # Ajusta o zoom para focar onde está a maioria dos dados (0 a 0.5 por exemplo)
                range=[0, df_f['ip_d'].quantile(0.95) * 1.2] 
            ),
            margin=dict(l=50, r=50, t=80, b=50)
        )

        st.plotly_chart(fig_box, width='stretch')

        # Gráficos de Barras - Pergunta B
        st.subheader("Produtividade Média por Serviço")
        df_ip = df_f.groupby('descricao')['ip_d'].mean().reset_index().sort_values('ip_d')
        fig_bar_ip = px.bar(df_ip, x='ip_d', y='descricao', orientation='h', 
                         title="Média de IP_D por Serviço")
        st.plotly_chart(fig_bar_ip, width='stretch')

        st.subheader("Quantidade por Grupo")
        df_qntd = df_f.groupby('grupo')['qntd'].sum().reset_index().sort_values('qntd')
        fig_bar_qntd = px.bar(
            df_qntd,
            y='qntd',
            x='grupo',
            orientation='v',
            title="Quantidade Total por Grupo",
        )
        fig_bar_qntd.update_layout(
            yaxis={'categoryorder':'total ascending'}
        )
        st.plotly_chart(fig_bar_qntd, width='stretch')

        st.subheader("Insumos por Obra")
        df_insumo = df_f.groupby(['nome_obra','insumo']).size().reset_index(name='quantidade')
        fig_bar_insumo = px.bar(
            df_insumo,
            x='nome_obra',
            y='quantidade',
            color='insumo',
            title="Distribuição de Insumos por Obra"
        )
        st.plotly_chart(fig_bar_insumo, width='stretch')

    with tab4:
        st.header("4. Questão Extra - Vídeo")
        st.video("https://www.youtube.com/watch?v=KRZzUFTmpwU")
        st.info("Interpretação: O IP_D coletado em campo deve ser comparado ao coeficiente orçado (meta). Se o IP_D de campo for maior, a obra está consumindo mais recursos do que o planejado financeiramente.")

else:
    st.error("Arquivo 'src/df_diarios.csv' não encontrado ou inválido.")