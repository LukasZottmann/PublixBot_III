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

# Inicializando a variável credentials_info para evitar erros
credentials_info = None

# Carregar credenciais do arquivo JSON enviado
def carregar_credenciais(uploaded_file):
    try:
        return json.load(uploaded_file)
    except Exception as e:
        st.error(f"Erro ao carregar credenciais: {e}")
        return None

# Upload do arquivo de credenciais
uploaded_file = st.sidebar.file_uploader("Faça upload do arquivo de credenciais (.json)", type="json")
if uploaded_file:
    credentials_info = carregar_credenciais(uploaded_file)

# Função para autenticar no Google Drive
def autenticar_drive(credentials_info):
    try:
        creds = Credentials.from_service_account_info(credentials_info)
        service = build('drive', 'v3', credentials=creds)
        return service
    except Exception as e:
        st.error(f"Erro na autenticação do Google Drive: {e}")
        return None

# Função para listar documentos no Google Drive
def listar_documentos(service):
    try:
        results = service.files().list(pageSize=50, fields="files(id, name, mimeType)").execute()
        arquivos = results.get('files', [])
        if not arquivos:
            st.warning("Nenhum documento encontrado no Google Drive.")
        return arquivos
    except Exception as e:
        st.error(f"Erro ao listar documentos: {e}")
        return []

# Função para baixar e extrair texto do PDF
def baixar_e_extrair_texto(service, file_id):
    try:
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
    except Exception as e:
        st.error(f"Erro ao baixar ou processar o documento: {e}")
        return ""

# Função para gerar resposta com OpenAI
def gerar_resposta(texto_usuario):
    if not st.session_state.document_map:
        return "Por favor, carregue documentos antes de enviar perguntas."

    # Construindo o contexto a partir dos documentos carregados
    contexto = "Você é uma IA especializada em administração pública. Use as informações a seguir para responder com base nos documentos:\n\n"
    for nome_documento, text in st.session_state.document_map.items():
        # Truncar o texto para evitar excesso de tokens
        texto_resumido = text[:2000]  # Limite ajustado para tokens
        contexto += f"--- Documento: {nome_documento} ---\n{texto_resumido}\n\n"

    # Mensagens enviadas ao modelo
    mensagens = [
        {"role": "system", "content": contexto},
        {"role": "user", "content": texto_usuario}
    ]

    try:
        with st.spinner('💡 Processando sua pergunta, um momento...'):
            resposta = openai.ChatCompletion.create(
                model="gpt-4",
                messages=mensagens,
                temperature=0.3,
                max_tokens=500  # Limitar a resposta para garantir clareza
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

# Configurar chave da API OpenAI
api_key = st.sidebar.text_input("🔑 OpenAI API Key", type="password", placeholder="Insira sua API Key")
if api_key:
    openai.api_key = api_key

    # Autenticar no Google Drive apenas se as credenciais foram carregadas
    if credentials_info:
        drive_service = autenticar_drive(credentials_info)
        if drive_service:
            documentos = listar_documentos(drive_service)

            if documentos:
                st.sidebar.success("📄 Documentos disponíveis no Google Drive carregados com sucesso!")
                # Listar documentos e permitir a seleção múltipla na sidebar
                opcoes = [f"{doc['name']}" for doc in documentos if doc['mimeType'] == 'application/pdf']
                arquivos_selecionados = st.sidebar.multiselect("Selecione um ou mais documentos PDF:", opcoes)

                if arquivos_selecionados:
                    if st.sidebar.button("🔄 Carregar Documentos"):
                        for arquivo in arquivos_selecionados:
                            file_id = [doc['id'] for doc in documentos if doc['name'] == arquivo][0]
                            texto_documento = baixar_e_extrair_texto(drive_service, file_id)
                            if texto_documento:
                                st.session_state.document_map[arquivo] = texto_documento
                        st.sidebar.success("Documentos carregados com sucesso!")
                        with st.expander("📜 Visualizar documentos carregados"):
                            for nome_documento, texto in st.session_state.document_map.items():
                                st.text_area(f"Conteúdo de {nome_documento}", texto[:500], height=200)
        else:
            st.error("Erro ao autenticar no Google Drive.")
else:
    st.warning("Por favor, insira sua chave de API e carregue o arquivo de credenciais para continuar.")

# Estilo customizado para o chat
st.markdown("""
<style>
.chat-bubble {
    border-radius: 10px;
    padding: 10px;
    margin-bottom: 10px;
}
.user-message {
    background-color: #d3d3d3;
    color: #333333;
    text-align: right;
}
.bot-message {
    background-color: #fff8dc;
    color: #333333;
    text-align: left;
}
</style>
""", unsafe_allow_html=True)

# Exibição das mensagens do chat
st.markdown("### 📝 Chat")
for mensagem in st.session_state.mensagens_chat:
    user_msg = mensagem.get("user", "Mensagem do usuário indisponível.")
    bot_msg = mensagem.get("bot", "Mensagem do bot indisponível.")
    st.markdown(f'<div class="chat-bubble user-message"><strong>Você:</strong> {user_msg}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="chat-bubble bot-message"><strong>Bot:</strong> {bot_msg}</div>', unsafe_allow_html=True)

# Entrada de mensagem
st.markdown("---")
user_input = st.text_input("💬 Sua pergunta:")

if user_input:
    resposta_bot = gerar_resposta(user_input)
    st.session_state.mensagens_chat.append({"user": user_input, "bot": resposta_bot})
    st.text_input("💬 Sua pergunta:", value="", key="dummy", label_visibility="hidden")

# Botões abaixo da área de perguntas
col1, col2 = st.columns(2)
with col1:
    if st.button("🧹 Limpar histórico de mensagens"):
        st.session_state.mensagens_chat = []
        st.success("Histórico de mensagens limpo com sucesso!")
with col2:
    if st.button("📥 Baixar histórico do chat"):
        with open("chat_history.txt", "w") as f:
            for msg in st.session_state.mensagens_chat:
                f.write(f"Você: {msg['user']}\n")
                f.write(f"Bot: {msg['bot']}\n\n")
        with open("chat_history.txt", "rb") as f:
            st.download_button("Clique aqui para baixar", f, file_name="chat_history.txt")
