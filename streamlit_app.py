import streamlit as st
import openai
import pdfplumber
import os
import json
import io
import time
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.service_account import Credentials

# Configurações iniciais
st.set_page_config(page_title="PublixBOT 2.0", layout="wide")

# Carregar credenciais do Secrets do Streamlit Cloud
GOOGLE_CREDENTIALS = st.secrets["GOOGLE_CREDENTIALS"]

# Verificação de tipo
if isinstance(GOOGLE_CREDENTIALS, str):
    credentials_info = json.loads(GOOGLE_CREDENTIALS)
else:
    credentials_info = GOOGLE_CREDENTIALS

# Função para autenticar no Google Drive
def autenticar_drive():
    creds = Credentials.from_service_account_info(credentials_info)
    service = build('drive', 'v3', credentials=creds)
    return service

# Função para listar documentos no Google Drive
def listar_documentos(service):
    results = service.files().list(pageSize=10, fields="files(id, name, mimeType)").execute()
    arquivos = results.get('files', [])
    if not arquivos:
        st.warning("Nenhum documento encontrado no Google Drive.")
    return arquivos

# Função para baixar e extrair texto do PDF
def baixar_e_extrair_texto(service, file_id):
    request = service.files().get_media(fileId=file_id)
    file_io = io.BytesIO()
    downloader = MediaIoBaseDownload(file_io, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    file_io.seek(0)
    with pdfplumber.open(file_io) as pdf:
        texto_completo = ""
        for page in pdf.pages:
            texto_completo += page.extract_text() or ""
    return texto_completo

# Função para gerar resposta com OpenAI
def gerar_resposta(texto_usuario):
    if not st.session_state.document_map:
        return "Por favor, carregue documentos antes de enviar perguntas."

    contexto = "Você é uma IA especializada em administração pública. Baseie suas respostas nos seguintes documentos:\n\n"
    for nome_documento, text in st.session_state.document_map.items():
        contexto += f"--- Documento: {nome_documento} ---\n{text[:1500]}...\n\n"

    mensagens = [{"role": "system", "content": contexto}, {"role": "user", "content": texto_usuario}]

    try:
        with st.spinner('💡 Processando sua pergunta, um momento...'):
            resposta = openai.ChatCompletion.create(
                model="gpt-4",
                messages=mensagens,
                temperature=0.3,
                max_tokens=1500
            )
            return resposta["choices"][0]["message"]["content"]
    except openai.error.AuthenticationError:
        return "Erro de autenticação: verifique sua chave de API."
    except openai.error.APIConnectionError:
        return "Erro de conexão com a API: verifique sua conexão com a internet."
    except Exception as e:
        return f"Erro ao gerar a resposta: {str(e)}"

# Inicialização segura das variáveis de estado
if "mensagens_chat" not in st.session_state:
    st.session_state.mensagens_chat = []
if "document_text" not in st.session_state:
    st.session_state.document_text = ""
if "document_map" not in st.session_state:
    st.session_state.document_map = {}

# Título e introdução
st.title("💛 PublixBOT 2.0")
st.subheader("Sou uma inteligência artificial especialista em administração pública desenvolvida pelo Instituto Publix, me pergunte qualquer coisa!")

api_key = st.sidebar.text_input("🔑 OpenAI API Key", type="password", placeholder="Insira sua API Key")
if api_key:
    openai.api_key = api_key

    # Autenticação no Google Drive
    drive_service = autenticar_drive()
    documentos = listar_documentos(drive_service)

    if documentos:
        st.success("📄 Documentos disponíveis no Google Drive carregados com sucesso!")
        # Listar documentos e permitir a seleção
        opcoes = [f"{doc['name']}" for doc in documentos if doc['mimeType'] == 'application/pdf']
        arquivo_selecionado = st.selectbox("Selecione um documento PDF:", opcoes)

        if arquivo_selecionado:
            file_id = [doc['id'] for doc in documentos if doc['name'] == arquivo_selecionado][0]
            if st.button("🔄 Carregar Documento"):
                try:
                    texto_documento = baixar_e_extrair_texto(drive_service, file_id)
                    st.session_state.document_text = texto_documento
                    st.session_state.document_map = {arquivo_selecionado: texto_documento}
                    st.text_area("📜 Texto do Documento Carregado", texto_documento[:1000], height=200)
                except Exception as e:
                    st.error(f"Erro ao carregar o documento: {e}")
    else:
        st.warning("Nenhum documento disponível no Google Drive.")
else:
    st.warning("Por favor, insira sua chave de API para continuar.")
