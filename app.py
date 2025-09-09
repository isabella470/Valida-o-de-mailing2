# Passo 0: Instale as bibliotecas necessárias
# pip install streamlit pandas numpy openpyxl

import streamlit as st
import pandas as pd
import numpy as np
from urllib.parse import urlparse
import io
import re

# --- Não há mais seção de configuração de nomes de colunas ---

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
    """
    try:
        match = re.search(r'/d/([a-zA-Z0-B]+)', url)
        if match:
            sheet_id = match.group(1)
            return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        else:
            return None
    except Exception:
        return None

# --- INTERFACE DO STREAMLIT ---
st.set_page_config(page_title="Validador de Escopo", layout="centered")
st.title("🚀 Painel de Validação de Escopo Inteligente")
st.markdown(
    """
    Este aplicativo verifica os links de um arquivo `.txt` contra os links da **Coluna D** de uma planilha.
    Se encontrar uma correspondência, trará **todas as informações** da linha correspondente.
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
                    
                    # --- MUDANÇA NA LÓGICA ---
                    # 1. Verifica se a planilha tem pelo menos 4 colunas (A, B, C, D)
                    if len(df_mailing.columns) < 4:
                        st.error(f"Sua planilha tem menos de 4 colunas. Não foi possível encontrar a Coluna D.")
                    else:
                        # 2. Pega o nome da quarta coluna (índice 3), seja ele qual for.
                        nome_coluna_d = df_mailing.columns[3]
                        st.write(f"Identificada a coluna de URLs para verificação: '{nome_coluna_d}' (Coluna D).")
                        
                        # 3. Cria a coluna de domínio limpo a partir da Coluna D
                        df_mailing['dominio_limpo'] = df_mailing[nome_coluna_d].apply(extrair_dominio_limpo)
                        st.write(f"✅ Mailing com {len(df_mailing)} sites carregado.")

                        st.write("🔄 Carregando arquivo TXT...")
                        df_verificacao = pd.read_csv(arquivo_txt, header=None, names=['Link_Original'])
                        df_verificacao['dominio_limpo'] = df_verificacao['Link_Original'].apply(extrair_dominio_limpo)
                        st.write(f"✅ Arquivo TXT com {len(df_verificacao)} links carregado.")

                        st.write("🔄 Cruzando informações...")
                        # 4. Faz o merge, trazendo TODAS as colunas de df_mailing
                        resultado_merge = pd.merge(df_verificacao, df_mailing, on='dominio_limpo', how='left')
                        
                        # 5. Define o Status baseado na presença de qualquer dado da planilha (usamos a primeira coluna dela como referência)
                        primeira_coluna_mailing = df_mailing.columns[0]
                        resultado_merge['Status'] = np.where(resultado_merge[primeira_coluna_mailing].notna(), 'DENTRO DO ESCOPO', 'FORA DO ESCOPO')
                        
                        # 6. Organiza as colunas do resultado final
                        # Pega todas as colunas originais do mailing
                        colunas_do_mailing = list(df_mailing.columns)
                        # Define a ordem final, colocando Status logo após Link_Original
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
