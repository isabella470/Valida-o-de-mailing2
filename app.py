# Passo 0: Instale as bibliotecas necessárias
# pip install streamlit pandas numpy openpyxl

import streamlit as st
import pandas as pd
import numpy as np
from urllib.parse import urlparse
import io
import re

# --- CONFIGURAÇÃO PRINCIPAL ---
# ▼▼▼ AQUI: Altere o texto abaixo para ser EXATAMENTE igual ao cabeçalho da sua Coluna D ▼▼▼
NOME_DA_COLUNA_DE_URLS = "start_url"  # Por exemplo: "URL", "Site", "Link do Site"
# --- FIM DA CONFIGURAÇÃO ---


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
            url_csv = transformar_url_para_csv(url_planilha)
            
            if url_csv is None:
                st.error("URL da planilha inválida. Por favor, cole a URL completa copiada do seu navegador.")
            else:
                try:
                    st.write("🔄 Acessando a planilha...")
                    df_mailing = pd.read_csv(url_csv)
                    
                    # <-- MUDANÇA AQUI 1: Usamos a variável para checar se a coluna de URL existe.
                    colunas_necessarias = [NOME_DA_COLUNA_DE_URLS, 'id_boxnet', 'nome_boxnet', 'pais', 'estado', 'id klipbo']
                    if not all(coluna in df_mailing.columns for coluna in colunas_necessarias):
                        st.error(f"Uma ou mais colunas necessárias não foram encontradas na planilha. Verifique se os cabeçalhos estão corretos: {colunas_necessarias}")
                    else:
                        # <-- MUDANÇA AQUI 2: Usamos a variável para dizer qual coluna contém os URLs.
                        df_mailing['dominio_limpo'] = df_mailing[NOME_DA_COLUNA_DE_URLS].apply(extrair_dominio_limpo)
                        st.write(f"✅ Mailing com {len(df_mailing)} sites carregado.")

                        st.write("🔄 Carregando arquivo TXT...")
                        df_verificacao = pd.read_csv(arquivo_txt, header=None, names=['Link_Original'])
                        df_verificacao['dominio_limpo'] = df_verificacao['Link_Original'].apply(extrair_dominio_limpo)
                        st.write(f"✅ Arquivo TXT com {len(df_verificacao)} links carregado.")

                        st.write("🔄 Cruzando informações...")
                        # <-- MUDANÇA AQUI 3: Adicionamos a variável na lista de colunas a serem mescladas.
                        colunas_para_mesclar = ['dominio_limpo', 'id_boxnet', 'nome_boxnet', NOME_DA_COLUNA_DE_URLS, 'pais', 'estado', 'id klipbo']
                        resultado_merge = pd.merge(df_verificacao, df_mailing[colunas_para_mesclar], on='dominio_limpo', how='left')
                        
                        resultado_merge['Status'] = np.where(resultado_merge['id_boxnet'].notna(), 'DENTRO DO ESCOPO', 'FORA DO ESCOPO')
                        
                        # <-- MUDANÇA AQUI 4: Usamos a variável para renomear a coluna de URL no relatório final.
                        resultado_merge.rename(columns={NOME_DA_COLUNA_DE_URLS: 'Link_no_Mailing'}, inplace=True)
                        
                        colunas_finais = ['Link_Original', 'Status', 'id_boxnet', 'id klipbo', 'nome_boxnet', 'Link_no_Mailing', 'pais', 'estado']
                        resultado_final = resultado_merge.reindex(columns=colunas_finais)

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
                    st.error("Verifique se a permissão da planilha está como 'Qualquer pessoa com o link pode ver' e se todos os nomes das colunas estão corretos.")
