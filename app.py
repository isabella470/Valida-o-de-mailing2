import streamlit as st
import pandas as pd
import numpy as np
from urllib.parse import urlparse
import io
import re

# =============================
# Configuração da página
# =============================
st.set_page_config(page_title="Validador de Escopo", layout="centered")

# =============================
# CSS com fundo + estilos
# =============================
st.markdown(
    """
    <style>
    /* Fundo do app */
    .stApp {
        background-image: url("https://raw.githubusercontent.com/isabella470/Valida-o-de-mailing2/main/abre.jpg");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }

    /* Contêiner principal com efeito vidro fosco */
    section.main > div {
        background-color: rgba(14, 17, 23, 0.85);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Títulos */
    h1 {
        color: #FF4B4B;
        text-align: center;
    }

    /* Botões */
    .stButton > button {
        width: 100%;
        border-radius: 5px;
        border: 1px solid #FF4B4B;
        background-color: transparent;
        color: #FF4B4B;
        transition: all 0.2s ease-in-out;
    }

    .stButton > button:hover {
        background-color: #FF4B4B;
        color: white;
        border-color: #FF4B4B;
    }

    .stButton > button:active {
        background-color: #E03C3C;
        border-color: #E03C3C;
    }

    /* Uploader de arquivos */
    .stFileUploader > div {
        border: 2px dashed rgba(255, 75, 75, 0.5);
        background-color: rgba(255, 75, 75, 0.05);
        border-radius: 10px;
    }

    /* Texto geral */
    body, .stTextInput > div > div > input, .stSelectbox > div > div {
        color: #FAFAFA;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# =============================
# Interface inicial
# =============================
st.title("Painel de Validação de Escopo 🎯📊")
st.markdown("Aqui você pode escolher qual coluna da sua planilha contém os URLs a serem verificados.")

url_planilha = st.text_input(
    "Passo 1: Cole o link da sua planilha Google Sheets",
    placeholder="https://docs.google.com/spreadsheets/d/..."
)

# =============================
# Funções utilitárias
# =============================
def extrair_dominio_limpo(url: str) -> str:
    if not isinstance(url, str): 
        return None
    try:
        url = url.strip().lower()
        if not url.startswith(("http://", "https://")):
            url = "http://" + url
        dominio = urlparse(url).netloc
        if dominio.startswith("www."):
            dominio = dominio[4:]
        return dominio
    except:
        return None

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
# Lógica de validação
# =============================
if url_planilha:
    url_csv = transformar_url_para_csv(url_planilha)
    if url_csv is None:
        st.error("URL de planilha inválida. Verifique o link.")
    else:
        with st.spinner("Lendo cabeçalhos da planilha..."):
            try:
                df_mailing = pd.read_csv(url_csv)
            except Exception as e:
                st.error(f"Erro ao ler CSV da planilha: {e}")
                st.stop()

            headers = list(df_mailing.columns)
        st.success("Planilha lida com sucesso!")

        coluna_url_selecionada = st.selectbox(
            "Passo 2: Da lista abaixo, qual coluna contém os URLs?",
            options=headers,
            index=3 if len(headers) > 3 else 0
        )

        arquivo_txt = st.file_uploader("Passo 3: Suba seu arquivo .TXT com os links", type=["txt"])

        if st.button("✅ Gerar Relatório"):
            if arquivo_txt is None:
                st.warning("Por favor, suba o arquivo .TXT.")
            else:
                with st.spinner("Processando..."):
                    # Limpeza de domínios
                    df_mailing["dominio_limpo"] = df_mailing[coluna_url_selecionada].apply(extrair_dominio_limpo)
                    df_verificacao = pd.read_csv(arquivo_txt, header=None, names=["Link_Original"])
                    df_verificacao["dominio_limpo"] = df_verificacao["Link_Original"].apply(extrair_dominio_limpo)

                    # Merge para verificação
                    resultado_merge = pd.merge(df_verificacao, df_mailing, on="dominio_limpo", how="left")
                    primeira_coluna_mailing = df_mailing.columns[0]
                    resultado_merge["Status"] = np.where(
                        resultado_merge[primeira_coluna_mailing].notna(),
                        "DENTRO DO ESCOPO",
                        "FORA DO ESCOPO"
                    )

                    # Seleciona colunas finais
                    colunas_do_mailing = [c for c in df_mailing.columns if c != "dominio_limpo"]
                    colunas_finais = ["Link_Original", "Status"] + colunas_do_mailing
                    resultado_final = resultado_merge[colunas_finais]

                    # Exportar para Excel
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine="openpyxl") as writer:
                        resultado_final.to_excel(writer, index=False, sheet_name="Resultado")
                    dados_excel = output.getvalue()

                    st.success("🎉 Processo concluído!")
                    st.download_button(
                        label="📥 Baixar Relatório em Excel",
                        data=dados_excel,
                        file_name="resultado_comparacao.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
