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
# CSS com o Tema Branco e Sombra de Contraste
# =============================
st.markdown(
    """
    <style>
    /* Fundo da aplicação */
    .stApp {
        background-image: url("https://raw.githubusercontent.com/isabella470/Valida-o-de-mailing2/main/Gemini_Generated_Image_ej6ecpej6ecpej6e.png");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }

    /* Contêiner principal com vidro fosco leve */
    section.main > div {
        background-color: rgba(0, 0, 0, 0.7);
        backdrop-filter: blur(12px);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 8px 20px rgba(0,0,0,0.6);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Títulos e textos brancos com sombra escura para legibilidade */
    h1, h2, h3, h4, h5, h6, p, span, label {
        color: #FAFAFA; /* Letras Brancas */
        text-shadow: 2px 2px 8px rgba(0, 0, 0, 0.9); /* <<-- SOMBRA FORTE PARA CONTRASTE */
    }

    /* Botões estilizados com o tema branco */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        border: 1px solid #FFFFFF;
        background-color: transparent;
        color: #FFFFFF;
        font-weight: bold;
        transition: all 0.2s ease-in-out;
        box-shadow: 1px 1px 5px rgba(0,0,0,0.5);
    }

    .stButton > button:hover {
        background-color: #FFFFFF;
        color: #000000; /* Texto preto para contraste no botão branco */
        border-color: #FFFFFF;
    }

    .stButton > button:active {
        background-color: #DDDDDD; /* Tom mais escuro para o clique */
        border-color: #DDDDDD;
    }

    /* Inputs, textarea e uploader legíveis com o tema branco */
    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stFileUploader > div,
    .stTextArea > div > div > textarea {
        background-color: rgba(0,0,0,0.6);
        color: #FAFAFA;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.4); /* Borda branca sutil */
        padding: 0.4rem;
    }

    /* Uploader de arquivos com destaque branco */
    .stFileUploader > div {
        border: 2px dashed rgba(255, 255, 255, 0.6);
        background-color: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 0.5rem;
    }
    
    /* Scrollbars customizadas com o tema branco */
    ::-webkit-scrollbar { width: 10px; }
    ::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.5); border-radius: 5px; }
    ::-webkit-scrollbar-track { background: rgba(0,0,0,0.2); }
    </style>
    """,
    unsafe_allow_html=True
)

# =============================
# Interface inicial
# =============================
st.title("Painel Escopo Web 📊")
st.markdown("Escolha a coluna da sua planilha com URLs e como deseja comparar os links.")

url_planilha = st.text_input(
    "Passo 1: Cole o link da sua planilha",
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

        st.markdown("**Passo 3: Escolha como deseja fornecer os links para comparação:**")
        tab1, tab2 = st.tabs(["📄 Upload de TXT", "✏️ Colar links"])

        # --- Opção 1: Upload de TXT ---
        with tab1:
            arquivo_txt = st.file_uploader("Suba seu arquivo .TXT com os links", type=["txt"])

        # --- Opção 2: Colar links ---
        with tab2:
            links_colados = st.text_area(
                "Cole seus links aqui (um por linha)",
                placeholder="https://exemplo.com\nhttps://teste.com"
            )

        if st.button("✅ Gerar Relatório"):
            if (arquivo_txt is None) and (not links_colados.strip()):
                st.warning("Por favor, forneça os links via arquivo ou colando na tela.")
            else:
                with st.spinner("Processando..."):
                    df_mailing["dominio_limpo"] = df_mailing[coluna_url_selecionada].apply(extrair_dominio_limpo)

                    if arquivo_txt:
                        df_verificacao = pd.read_csv(arquivo_txt, header=None, names=["Link_Original"])
                    else:
                        lista_links = [l.strip() for l in links_colados.strip().split("\n") if l.strip()]
                        df_verificacao = pd.DataFrame(lista_links, columns=["Link_Original"])

                    df_verificacao["dominio_limpo"] = df_verificacao["Link_Original"].apply(extrair_dominio_limpo)

                    resultado_merge = pd.merge(df_verificacao, df_mailing, on="dominio_limpo", how="left")
                    primeira_coluna_mailing = df_mailing.columns[0]
                    resultado_merge["Status"] = np.where(
                        resultado_merge[primeira_coluna_mailing].notna(),
                        "DENTRO DO ESCOPO",
                        "FORA DO ESCOPO"
                    )

                    colunas_do_mailing = [c for c in df_mailing.columns if c != "dominio_limpo"]
                    colunas_finais = ["Link_Original", "Status"] + colunas_do_mailing
                    resultado_final = resultado_merge[colunas_finais]

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

