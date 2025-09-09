# CÓDIGO FINAL COM A LÓGICA DE CORRESPONDÊNCIA EXATA (IGUAL AO COLAB)

import streamlit as st
import pandas as pd
import numpy as np
from urllib.parse import urlparse
import io
import re

# --- FUNÇÃO DE LÓGICA RESTAURADA (IDÊNTICA À DO SEU CÓDIGO ORIGINAL) ---
def extrair_dominio_limpo(url: str) -> str:
    """
    Função para extrair e limpar o domínio de uma URL, mantendo subdomínios.
    Ex: 'esportes.globo.com' -> 'esportes.globo.com'
    Esta é a lógica exata do seu script original do Colab.
    """
    if not isinstance(url, str): return None
    try:
        # Melhoria: remove espaços e converte para minúsculas para evitar erros simples
        url = url.strip().lower()
        
        if not url.startswith(('http://', 'https://')): url = 'http://' + url
        dominio = urlparse(url).netloc
        if dominio.startswith('www.'):
            dominio = dominio[4:]
        return dominio
    except:
        return None

# --- O RESTO DO CÓDIGO USA A FUNÇÃO CORRETA ---
def transformar_url_para_csv(url: str) -> str:
    """
    Pega uma URL normal do Google Sheets e a transforma em um link de download direto de CSV.
    """
    try:
        # A expressão regular foi ajustada para ser mais genérica e funcionar com qualquer ID.
        match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
        if match:
            sheet_id = match.group(1)
            return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        else:
            return None
    except Exception:
        return None

# --- INTERFACE DO STREAMLIT ---
st.set_page_config(page_title="Validador de Escopo", layout="centered")
st.title("🚀 Painel de Validação de Escopo")
st.markdown(
    """
    Este aplicativo valida os links de um arquivo `.txt` contra os links da **Coluna D** de uma planilha
    usando uma **correspondência exata de domínio** (subdomínios são considerados).
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
            url_csv = transformar_url_para_csv(url_planilha)
            
            if url_csv is None:
                st.error("URL da planilha inválida. Por favor, cole a URL completa copiada do seu navegador.")
            else:
                try:
                    st.write("🔄 Acessando a planilha...")
                    df_mailing = pd.read_csv(url_csv)
                    
                    if len(df_mailing.columns) < 4:
                        st.error(f"Sua planilha tem menos de 4 colunas. Não foi possível encontrar a Coluna D.")
                    else:
                        nome_coluna_d = df_mailing.columns[3]
                        st.write(f"Identificada a coluna de URLs para verificação: '{nome_coluna_d}' (Coluna D).")
                        
                        df_mailing['dominio_limpo'] = df_mailing[nome_coluna_d].apply(extrair_dominio_limpo)
                        st.write(f"✅ Mailing com {len(df_mailing)} sites carregado.")

                        st.write("🔄 Carregando arquivo TXT...")
                        df_verificacao = pd.read_csv(arquivo_txt, header=None, names=['Link_Original'])
                        df_verificacao['dominio_limpo'] = df_verificacao['Link_Original'].apply(extrair_dominio_limpo)
                        st.write(f"✅ Arquivo TXT com {len(df_verificacao)} links carregado.")

                        st.write("🔄 Cruzando informações...")
                        resultado_merge = pd.merge(df_verificacao, df_mailing, on='dominio_limpo', how='left')
                        
                        primeira_coluna_mailing = df_mailing.columns[0]
                        resultado_merge['Status'] = np.where(resultado_merge[primeira_coluna_mailing].notna(), 'DENTRO DO ESCOPO', 'FORA DO ESCOPO')
                        
                        colunas_do_mailing = list(df_mailing.columns)
                        # Remove a coluna 'dominio_limpo' que foi adicionada ao df_mailing para não aparecer duplicada
                        if 'dominio_limpo' in colunas_do_mailing:
                            colunas_do_mailing.remove('dominio_limpo')
                            
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
                    st.error(f"❌ OCORREU UM ERRO: {e}")
                    st.error("Verifique se o link da planilha está correto e se a permissão é 'Qualquer pessoa com o link pode ver'.")
