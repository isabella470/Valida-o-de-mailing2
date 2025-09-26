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
# CSS com o Tema (sem alterações)
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
st.markdown("Busque por um ou mais veículos na sua planilha base de mailing")

url_planilha = st.text_input(
    "Passo 1: Cole o link da sua planilha",
    placeholder="https://docs.google.com/spreadsheets/d/..."
)

# =============================
# Funções utilitárias (sem alterações)
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
# Lógica de validação (MODIFICADA)
# =============================
if url_planilha:
    url_csv = transformar_url_para_csv(url_planilha)
    if url_csv is None:
        st.error("URL de planilha inválida. Verifique o link.")
    else:
        with st.spinner("Lendo cabeçalhos da planilha..."):
            try:
                df_mailing = pd.read_csv(url_csv, on_bad_lines='skip')
                # Garante que todas as colunas sejam tratadas como texto para evitar erros no .str.contains
                for col in df_mailing.columns:
                    df_mailing[col] = df_mailing[col].astype(str)
            except Exception as e:
                st.error(f"Erro ao ler CSV da planilha: {e}")
                st.stop()

            headers = list(df_mailing.columns)
        st.success("Planilha lida com sucesso!")

        # Passo 2 - Selecionar coluna de URL (para normalização)
        coluna_url_selecionada = st.selectbox(
            "Passo 2: Qual coluna contém os URLs para extração de domínio?",
            options=headers,
            index=3 if len(headers) > 3 else 0,
            help="Esta coluna será usada para criar uma base de domínios limpos para a busca exata."
        )

        # >>> NOVO: Passo 3 - Selecionar coluna onde a busca será feita
        coluna_busca_selecionada = st.selectbox(
            "Passo 3: Em qual coluna da planilha você quer buscar?",
            options=headers,
            index=3 if len(headers) > 3 else 0,
            help="Seus termos de busca serão comparados com o conteúdo desta coluna."
        )

        # >>> NOVO: Passo 4 - Escolher o método de busca
        metodo_busca = st.radio(
            "Passo 4: Como você quer buscar?",
            options=["Correspondência Parcial (Contém o termo)", "Correspondência Exata do Domínio"],
            horizontal=True,
            help=(
                "**Parcial:** Busca se o seu termo (ex: 'globo') aparece em qualquer parte do texto da coluna selecionada.\n\n"
                "**Exata:** Compara o domínio limpo do seu link (ex: 'globo.com') com o domínio limpo da coluna de URL."
            )
        )

        st.markdown("**Passo 5: Forneça os termos ou links para comparação:**")
        tab1, tab2 = st.tabs(["📄 Upload de TXT", "✏️ Colar Texto"])

        with tab1:
            arquivo_txt = st.file_uploader("Suba seu arquivo .TXT com os termos de busca", type=["txt"])

        with tab2:
            links_colados = st.text_area(
                "Cole seus termos ou links aqui (um por linha)",
                placeholder="exemplo.com\nportal de teste\nhttps://outrodominio.net"
            )

        if st.button("✅ Gerar Relatório"):
            if (arquivo_txt is None) and (not links_colados.strip()):
                st.warning("Por favor, forneça os termos para busca via arquivo ou colando na tela.")
            else:
                with st.spinner("Processando... Cruzando informações..."):
                    # Prepara o DataFrame da planilha base
                    df_mailing["dominio_limpo"] = df_mailing[coluna_url_selecionada].apply(extrair_dominio_limpo)
                    
                    # Prepara o DataFrame com os termos a serem buscados
                    if arquivo_txt:
                        df_verificacao = pd.read_csv(arquivo_txt, header=None, names=["Termo_Busca"])
                    else:
                        lista_links = [l.strip() for l in links_colados.strip().split("\n") if l.strip()]
                        df_verificacao = pd.DataFrame(lista_links, columns=["Termo_Busca"])

                    # >>> LÓGICA DE BUSCA ATUALIZADA <<<
                    resultados_encontrados = []
                    
                    if metodo_busca == "Correspondência Exata do Domínio":
                        # Limpa os termos de busca para extrair domínios
                        df_verificacao["dominio_limpo"] = df_verificacao["Termo_Busca"].apply(extrair_dominio_limpo)
                        # Faz o merge (junção) pela coluna de domínio limpo
                        resultado_merge = pd.merge(df_verificacao, df_mailing, on="dominio_limpo", how="left")
                    
                    else: # Correspondência Parcial (Contém o termo)
                        # Itera por cada termo a ser buscado
                        for termo in df_verificacao["Termo_Busca"]:
                            # Busca o termo na coluna selecionada da planilha base (ignora maiúsculas/minúsculas)
                            # O 'na=False' evita erros se houver células vazias
                            match = df_mailing[df_mailing[coluna_busca_selecionada].str.contains(termo, case=False, na=False, regex=False)]
                            
                            if not match.empty:
                                # Se encontrou, pega a primeira correspondência
                                primeiro_resultado = match.iloc[0].to_dict()
                                primeiro_resultado["Termo_Busca"] = termo
                                resultados_encontrados.append(primeiro_resultado)
                            else:
                                # Se não encontrou, adiciona um registro vazio
                                resultados_encontrados.append({"Termo_Busca": termo})
                        
                        # Constrói o DataFrame final a partir da lista de resultados
                        resultado_merge = pd.DataFrame(resultados_encontrados)

                    # --- Lógica para montagem do relatório final (comum aos dois métodos) ---
                    primeira_coluna_mailing = df_mailing.columns[0]
                    resultado_merge["Status"] = np.where(
                        resultado_merge[primeira_coluna_mailing].notna(),
                        "DENTRO DO ESCOPO",
                        "FORA DO ESCOPO"
                    )

                    colunas_do_mailing = [c for c in df_mailing.columns if c != "dominio_limpo"]
                    # Renomeia a coluna de busca para 'Termo_Original' se necessário
                    if 'Termo_Busca' in resultado_merge.columns:
                        resultado_merge = resultado_merge.rename(columns={'Termo_Busca': 'Termo_Original'})
                    elif 'Link_Original' in resultado_merge.columns:
                         resultado_merge = resultado_merge.rename(columns={'Link_Original': 'Termo_Original'})
                    
                    # Organiza as colunas para o resultado final
                    colunas_finais = ["Termo_Original", "Status"] + colunas_do_mailing
                    # Garante que todas as colunas necessárias existam, preenchendo com nulo se faltar
                    for col in colunas_finais:
                        if col not in resultado_merge.columns:
                            resultado_merge[col] = np.nan
                    
                    resultado_final = resultado_merge[colunas_finais]

                    # Geração do arquivo Excel para download
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine="openpyxl") as writer:
                        resultado_final.to_excel(writer, index=False, sheet_name="Resultado")
                    dados_excel = output.getvalue()

                    st.success("🎉 Processo concluído!")
                    
                    st.download_button(
                        label="📥 Baixar Relatório em Excel",
                        data=dados_excel,
                        file_name="resultado_validacao_escopo.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
