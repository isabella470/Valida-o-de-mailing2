# pages/Validador_Impresso.py
import streamlit as st
import pandas as pd
import re

# =============================
# Configuração da página
# =============================
st.set_page_config(
    page_title="Validador de Escopo Impresso", 
    layout="centered",
    page_icon="📰"
)

# =============================
# Reaplicar o CSS para manter a consistência visual
# (O ideal seria colocar isso em um módulo compartilhado, mas para simplificar, vamos repetir)
# =============================
st.markdown(
    """
    <style>
    /* Fundo da aplicação */
    .stApp {
        background-image: url("https://raw.githubusercontent.com/isabella470/Valida-o-de-mailing2/3d6b54a4c8b1b593e94856a84dd83d5e089404bf/abre.jpg");
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
    .stSelectbox > div > div {
        background-color: rgba(0,0,0,0.6);
        color: #FAFAFA;
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
# Função utilitária (copiada para esta página)
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
st.title("Painel de Validação de Impresso 📰")
st.markdown("Busque por um veículo na sua planilha base de mailing e veja todas as informações.")

url_planilha = st.text_input(
    "Passo 1: Cole o link da sua planilha base (Google Sheets)",
    placeholder="https://docs.google.com/spreadsheets/d/..."
)

# Cache para não recarregar a planilha toda vez que o usuário digitar algo
@st.cache_data
def carregar_planilha(url_csv):
    df = pd.read_csv(url_csv)
    return df

# =============================
# Lógica de busca
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
            coluna_veiculo = st.selectbox(
                "Passo 2: Qual coluna contém o nome do 'Veículo'?",
                options=headers,
                index=0  # Sugere a primeira coluna por padrão
            )

            termo_busca = st.text_input(
                "Passo 3: Digite o nome do veículo que deseja buscar",
                placeholder="Ex: Folha de S.Paulo"
            )

            if st.button("🔎 Buscar Veículo"):
                if not termo_busca.strip():
                    st.warning("Por favor, digite um nome para buscar.")
                else:
                    with st.spinner("Buscando..."):
                        # Converte a coluna para string para evitar erros e busca de forma case-insensitive
                        resultados = df_mailing[
                            df_mailing[coluna_veiculo].astype(str).str.contains(termo_busca, case=False, na=False)
                        ]

                        if not resultados.empty:
                            st.success(f"Encontramos {len(resultados)} resultado(s) para '{termo_busca}':")
                            # Exibe os resultados em uma tabela interativa
                            st.dataframe(resultados)
                        else:
                            st.error(f"Nenhum veículo encontrado com o nome '{termo_busca}'. Verifique o nome e a coluna selecionada.")

        except Exception as e:
            st.error(f"Erro ao ler ou processar a planilha: {e}")
