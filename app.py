# Passo 0: Instale as bibliotecas necessárias
# pip install streamlit pandas numpy openpyxl

import streamlit as st
import pandas as pd
import numpy as np
from urllib.parse import urlparse
import io
import re

# --- FUNÇÕES DE LÓGICA ---

def extrair_dominio_limpo(url):
    """Função para extrair e limpar o domínio de uma URL."""
    if not isinstance(url, str): return None
    try:
        if not url.startswith(('http://', 'https://')): url = 'http://' + url
        dominio = urlparse(url).netloc
        if dominio.startswith('www.'): dominio = dominio[4:]
        return dominio
    except:
        return None

def transformar_url_para_csv(url: str) -> str:
    """
    Pega uma URL normal do Google Sheets e a transforma em um link de download direto de CSV.
    Ex: .../d/SHEET_ID/edit -> .../d/SHEET_ID/export?format=csv
    """
    try:
        # Extrai o ID da planilha da URL usando uma expressão regular
        match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
        if match:
            sheet_id = match.group(1)
            return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        else:
            # Se não encontrar o padrão, retorna None para indicar um erro
            return None
    except Exception:
        return None

# --- INTERFACE DO STREAMLIT ---

st.set_page_config(page_title="Validador de Escopo", layout="centered")
st.title("🚀 Painel de Validação de Escopo")
st.markdown(
    """
    Ajuste a permissão da sua planilha para **"Qualquer pessoa com o link pode ver"**.
    Depois, cole o link normal da planilha abaixo e suba seu arquivo `.txt`.
    """
)

# --- ENTRADAS DO USUÁRIO ---
url_planilha = st.text_input(
    "1. Cole o link normal da sua planilha Google Sheets",
    placeholder="https://docs.google.com/spreadsheets/d/1a2b3c4d..."
)

arquivo_txt = st.file_uploader(
    "2. Suba seu arquivo .TXT com os links",
    type=['txt']
)

# --- BOTÃO E LÓGICA DE PROCESSAMENTO ---

if st.button("✅ Gerar Relatório", type="primary"):
    if not url_planilha or arquivo_txt is None:
        st.warning("Por favor, preencha o link da planilha e suba o arquivo .TXT.")
    else:
        with st.spinner("Processando..."):
            # Transforma a URL normal em um link de download CSV
            url_csv = transformar_url_para_csv(url_planilha)
            
            if url_csv is None:
                st.error("URL da planilha inválida. Por favor, cole a URL completa copiada do seu navegador.")
            else:
                try:
                    # --- Carrega a planilha usando o link transformado ---
                    st.write("🔄 Acessando a planilha...")
                    df_mailing = pd.read_csv(url_csv)
                    
                    if 'start_url' not in df_mailing.columns:
                        st.error(f"A coluna 'start_url' não foi encontrada na planilha. Verifique o cabeçalho. Colunas encontradas: {list(df_mailing.columns)}")
                    else:
                        df_mailing['dominio_limpo'] = df_mailing['start_url'].apply(extrair_dominio_limpo)
                        st.write(f"✅ Mailing com {len(df_mailing)} sites carregado.")

                        # --- Carrega o arquivo TXT ---
                        st.write("🔄 Carregando arquivo TXT...")
                        df_verificacao = pd.read_csv(arquivo_txt, header=None, names=['Link_Original'])
                        df_verificacao['dominio_limpo'] = df_verificacao['Link_Original'].apply(extrair_dominio_limpo)
                        st.write(f"✅ Arquivo TXT com {len(df_verificacao)} links carregado.")

                        # --- Cruza as informações ---
                        st.write("🔄 Cruzando informações...")
                        resultado_merge = pd.merge(df_verificacao, df_mailing[['dominio_limpo', 'id_boxnet', 'nome_boxnet', 'start_url']], on='dominio_limpo', how='left')
                        
                        # --- Organiza o resultado ---
                        resultado_merge['Status'] = np.where(resultado_merge['id_boxnet'].notna(), 'DENTRO DO ESCOPO', 'FORA DO ESCOPO')
                        resultado_merge.rename(columns={'start_url': 'Link_no_Mailing'}, inplace=True)
                        colunas_finais = ['Link_Original', 'Status', 'id_boxnet', 'nome_boxnet', 'Link_no_Mailing']
                        resultado_final = resultado_merge.reindex(columns=colunas_finais)

                        # --- Prepara o arquivo para download ---
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            resultado_final.to_excel(writer, index=False, sheet_name='Resultado')
                        dados_excel = output.getvalue()
                        
                        st.success("🎉 Processo concluído!")

                        # --- Botão de Download ---
                        st.download_button(
                            label="📥 Baixar Relatório em Excel",
                            data=dados_excel,
                            file_name="resultado_comparacao.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                except Exception as e:
                    st.error(f"❌ OCORREU UM ERRO: {e}")
                    st.error("Verifique se a permissão da planilha está como 'Qualquer pessoa com o link pode ver'.")