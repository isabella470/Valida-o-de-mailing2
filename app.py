import streamlit as st
import pandas as pd
import numpy as np
from urllib.parse import urlparse
import io
import re

# Configuração da página (tem que vir logo no começo)
st.set_page_config(
    page_title="Validador de Escopo",
    layout="centered"
)

# Carregar CSS
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("style.css")

# --- INTERFACE DO STREAMLIT ---
st.title("Painel de Validação de Mailing 🎯")
st.markdown("Agora você pode escolher qual coluna da sua planilha contém os URLs a serem verificados.")

# PASSO 1: Obter o link da planilha
url_planilha = st.text_input(
    "Passo 1: Cole o link da sua planilha Google Sheets",
    placeholder="https://docs.google.com/spreadsheets/d/..."
)

# Continua só se tiver link
if url_planilha:
    try:
        def extrair_dominio_limpo(url: str) -> str:
            if not isinstance(url, str): return None
            try:
                url = url.strip().lower()
                if not url.startswith(('http://', 'https://')):
                    url = 'http://' + url
                dominio = urlparse(url).netloc
                if dominio.startswith('www.'):
                    dominio = dominio[4:]
                return dominio
            except:
                return None

        def transformar_url_para_csv(url: str) -> str:
            try:
                match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
                if match:
                    sheet_id = match.group(1)
                    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
                else:
                    return None
            except Exception:
                return None

        url_csv = transformar_url_para_csv(url_planilha)
        if url_csv is None:
            st.error("URL da planilha inválida. Verifique o link.")
        else:
            with st.spinner("Lendo cabeçalhos da planilha..."):
                df_mailing = pd.read_csv(url_csv)
                headers = list(df_mailing.columns)
            
            st.success("Planilha lida com sucesso!")

            # PASSO 2: Selecionar coluna
            coluna_url_selecionada = st.selectbox(
                "Passo 2: Da lista abaixo, qual coluna contém os URLs?",
                options=headers,
                index=3 if len(headers) > 3 else 0
            )

            # PASSO 3: Upload do TXT
            arquivo_txt = st.file_uploader("Passo 3: Suba seu arquivo .TXT com os links", type=['txt'])

            # PASSO 4: Botão final
            if st.button("✅ Gerar Relatório", type="primary"):
                if arquivo_txt is None:
                    st.warning("Por favor, suba o arquivo .TXT.")
                else:
                    with st.spinner("Processando tudo..."):
                        df_mailing['dominio_limpo'] = df_mailing[coluna_url_selecionada].apply(extrair_dominio_limpo)
                        st.write(f"✅ Mailing com {len(df_mailing)} sites carregado.")

                        df_verificacao = pd.read_csv(arquivo_txt, header=None, names=['Link_Original'])
                        df_verificacao['dominio_limpo'] = df_verificacao['Link_Original'].apply(extrair_dominio_limpo)

                        resultado_merge = pd.merge(df_verificacao, df_mailing, on='dominio_limpo', how='left')
                        
                        primeira_coluna_mailing = df_mailing.columns[0]
                        resultado_merge['Status'] = np.where(
                            resultado_merge[primeira_coluna_mailing].notna(),
                            'DENTRO DO ESCOPO',
                            'FORA DO ESCOPO'
                        )
                        
                        colunas_do_mailing = [c for c in df_mailing.columns if c != 'dominio_limpo']
                        colunas_finais = ['Link_Original', 'Status'] + colunas_do_mailing
                        resultado_final = resultado_merge[colunas_finais]

                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            resultado_final.to_excel(writer, index=False, sheet_name='Resultado')
                        dados_excel = output.getvalue()
                        
                        st.success("🎉 Processo concluído!")

                        st.download_button(
                            label="📥 Baixar Relatório em Excel",
                            data=dados_excel,
                            file_name="resultado_comparacao.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )

    except Exception as e:
        st.error(f"❌ ERRO: {e}")


