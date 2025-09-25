# pages/Validador_Impresso.py
import streamlit as st
import pandas as pd
import re
import io

# =============================
# CSS com NOVA IMAGEM DE FUNDO
# =============================
st.markdown(
    """
    <style>
    /* Fundo da aplicação */
    .stApp {
        background-image: url("https://raw.githubusercontent.com/isabella470/Valida-o-de-mailing2/main/Gemini_Generated_Image_9p12259p12259p12.png"); /* <<-- NOVA IMAGEM DE FUNDO AQUI */
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }

    section.main > div {
        background-color: rgba(0, 0, 0, 0.6);
        backdrop-filter: blur(12px);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 8px 20px rgba(0,0,0,0.6);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    h1, h2, h3, h4, h5, h6, p, span, label, .st-emotion-cache-16idsys p {
        color: #FAFAFA;
        text-shadow: 1px 1px 4px rgba(0,0,0,0.8);
    }
    
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stMultiSelect > div > div,
    .stSelectbox > div > div {
        background-color: rgba(0,0,0,0.6);
        color: #FAFAFA;
    }

    .stFileUploader > div {
        border: 2px dashed rgba(0, 200, 83, 0.6);
        background-color: rgba(0, 200, 83, 0.08);
    }
    
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        border: 1px solid #00C853; /* Cor verde para diferenciar */
        background-color: transparent;
        color: #00C853;
        font-weight: bold;
        transition: all 0.2s ease-in-out;
        box-shadow: 1px 1px 5px rgba(0,0,0,0.5);
    }

    .stButton > button:hover {
        background-color: #00C853;
        color: white;
        border-color: #00C853;
    }
    
    </style>
    """,
    unsafe_allow_html=True
)


# =============================
# Função utilitária (mantida)
# =============================
def transformar_url_para_csv(url: str) -> str:
    try:
        match = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
        if match:
            sheet_id = match.group(1)
            return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    except:
        pass
    return None

# =============================
# Interface da página
# =============================
st.title("Painel Escopo Impresso📰")
st.markdown("Busque por um ou mais veículos na sua planilha base de mailing, com filtro opcional por **região**.")

url_planilha = st.text_input(
    "Passo 1: Cole o link da sua planilha base (Google Sheets)",
    placeholder="https://docs.google.com/spreadsheets/d/..."
)

@st.cache_data
def carregar_planilha(url_csv):
    df = pd.read_csv(url_csv)
    # Garante que as colunas de texto não sejam interpretadas como outros tipos
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str)
    return df

# =============================
# Lógica de busca ATUALIZADA
# =============================
if url_planilha:
    url_csv = transformar_url_para_csv(url_planilha)
    if url_csv is None:
        st.error("URL de planilha inválida. Verifique o link.")
    else:
        try:
            with st.spinner("Lendo dados da planilha..."):
                df_mailing = carregar_planilha(url_csv)
            st.success("Planilha lida com sucesso!")

            headers = list(df_mailing.columns)
            
            # --- Passo 2: Seleção das colunas ---
            st.markdown("**Passo 2: Selecione as colunas para a busca**")
            col1, col2 = st.columns(2)
            with col1:
                coluna_veiculo = st.selectbox(
                    "Coluna do 'Veículo'",
                    options=headers,
                    index=0
                )
            with col2:
                coluna_regiao = st.selectbox(
                    "Coluna da 'Região'",
                    options=headers,
                    index=1 if len(headers) > 1 else 0
                )

            # --- Passo 3: Filtro Opcional de Região ---
            st.markdown("**Passo 3: Restringir a busca por região?**")
            filtrar_regiao = st.toggle("Ativar filtro de região")

            regioes_selecionadas = []
            if filtrar_regiao:
                # Pega valores únicos da coluna de região, remove nulos (NaN) e ordena
                regioes_unicas = sorted(df_mailing[coluna_regiao].dropna().unique())
                regioes_selecionadas = st.multiselect(
                    "Selecione uma ou mais regiões",
                    options=regioes_unicas
                )

            # --- Passo 4: Fornecer os nomes dos veículos ---
            st.markdown("**Passo 4: Forneça os nomes dos veículos para buscar**")
            tab1, tab2 = st.tabs(["✏️ Digitar Nomes", "📄 Upload de TXT"])

            with tab1:
                nomes_colados = st.text_area(
                    "Cole os nomes aqui (um por linha)",
                    placeholder="Folha de S.Paulo\nO Globo\nJornal que não existe\nCorreio Braziliense"
                )

            with tab2:
                arquivo_txt = st.file_uploader(
                    "Suba seu arquivo .TXT com os nomes",  
                    type=["txt"]
                )

            if st.button("🔎 Buscar Veículos"):
                
                lista_de_termos = []
                if arquivo_txt:
                    string_data = io.StringIO(arquivo_txt.getvalue().decode("utf-8")).read()
                    lista_de_termos = [line.strip() for line in string_data.splitlines() if line.strip()]
                elif nomes_colados.strip():
                    lista_de_termos = [line.strip() for line in nomes_colados.strip().split('\n') if line.strip()]

                if not lista_de_termos:
                    st.warning("Por favor, forneça nomes de veículos para a busca.")
                elif filtrar_regiao and not regioes_selecionadas:
                    st.warning("Filtro de região ativado. Por favor, selecione pelo menos uma região.")
                else:
                    with st.spinner("Buscando e organizando resultados..."):
                        
                        # ================================================================= #
                        # NOVA LÓGICA DE BUSCA E CONSTRUÇÃO DE RESULTADO                    #
                        # ================================================================= #

                        # 1. Prepara o DataFrame para a busca
                        df_para_busca = df_mailing.copy()
                        if filtrar_regiao and regioes_selecionadas:
                            df_para_busca = df_para_busca[df_para_busca[coluna_regiao].isin(regioes_selecionadas)]
                        
                        # Cria uma coluna de busca otimizada (minúscula e sem espaços)
                        df_para_busca['search_col'] = df_para_busca[coluna_veiculo].astype(str).str.lower().str.strip()

                        # 2. Itera sobre a lista de termos original para manter a ordem
                        resultados_finais = []
                        for termo_original in lista_de_termos:
                            termo_limpo = termo_original.lower().strip()
                            
                            # Procura pelo termo na coluna otimizada
                            match = df_para_busca[df_para_busca['search_col'] == termo_limpo]

                            if not match.empty:
                                # 3a. Se encontrou, adiciona os resultados encontrados
                                resultados_finais.append(match.drop(columns=['search_col']))
                            else:
                                # 3b. Se não encontrou, cria uma linha de placeholder
                                placeholder_data = {col: 'Não encontrado' for col in df_mailing.columns}
                                placeholder_data[coluna_veiculo] = termo_original # Usa o nome original
                                placeholder_df = pd.DataFrame([placeholder_data])
                                resultados_finais.append(placeholder_df)
                        
                        # 4. Consolida e exibe os resultados
                        if resultados_finais:
                            df_resultados_final = pd.concat(resultados_finais, ignore_index=True)
                            st.success("Busca concluída! Exibindo resultados na ordem solicitada:")
                            st.dataframe(df_resultados_final)
                        else:
                            st.error("Nenhum termo foi fornecido para a busca.")
                        # ================================================================= #
                        # FIM DA NOVA LÓGICA                                                #
                        # ================================================================= #

        except Exception as e:
            st.error(f"Ocorreu um erro: {e}")
