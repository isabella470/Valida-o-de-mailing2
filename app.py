import streamlit as st
import pandas as pd
import numpy as np
from urllib.parse import urlparse
import io
import re

# ------------- CONFIG (tem que vir antes de qualquer st.* que renderize) -------------
st.set_page_config(page_title="Validador de Escopo", layout="centered")

# Carrega CSS
def local_css(file_name="style.css"):
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Arquivo style.css não encontrado. Verifique o diretório.")

local_css("style.css")

# ---------- INTERFACE (somente um título + primeiro input visível) ----------
st.title("🚀 Painel de Validação de Escopo Flexível")
st.markdown("Agora você pode escolher qual coluna da sua planilha contém os URLs a serem verificados.")

# Passo 1: obter link (a partir daqui o resto só aparece se preencher)
url_planilha = st.text_input(
    "Passo 1: Cole o link da sua planilha Google Sheets",
    placeholder="https://docs.google.com/spreadsheets/d/..."
)

# ---------------- funções utilitárias ----------------
def extrair_dominio_limpo(url: str) -> str:
    if not isinstance(url, str): return None
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

# ------------- lógica que aparece só quando usuário cola a planilha -------------
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
                    df_mailing["dominio_limpo"] = df_mailing[coluna_url_selecionada].apply(extrair_dominio_limpo)
                    df_verificacao = pd.read_csv(arquivo_txt, header=None, names=["Link_Original"])
                    df_verificacao["dominio_limpo"] = df_verificacao["Link_Original"].apply(extrair_dominio_limpo)

                    resultado_merge = pd.merge(df_verificacao, df_mailing, on="dominio_limpo", how="left")
                    primeira_coluna_mailing = df_mailing.columns[0]
                    resultado_merge["Status"] = np.where(resultado_merge[primeira_coluna_mailing].notna(), "DENTRO DO ESCOPO", "FORA DO ESCOPO")

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
