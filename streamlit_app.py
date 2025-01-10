import streamlit as st
import openai
import pdfplumber
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os

# Função para extrair texto do PDF
def extract_text_from_pdf(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

# Configuração da interface
st.set_page_config(page_title="PublixBot", layout="wide")
st.sidebar.header("Configurações")
api_key = st.sidebar.text_input("🔑 OpenAI API Key", type="password")
uploaded_file = st.sidebar.file_uploader("📄 Faça upload de documentos (.pdf)", type="pdf")

# Variáveis de estado
if "historico_mensagens" not in st.session_state:
    st.session_state.historico_mensagens = []
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None

# Validação de chave API
if not api_key:
    st.warning("Por favor, insira sua chave de API.")
    st.stop()

openai.api_key = api_key

# Exibição do texto e entrada de mensagens
st.title("💛 PublixBot 1.5")
st.subheader("Essa é a inteligência artificial desenvolvida pelo Instituto Publix, pré-treinada com nosso conhecimento. Ela é especialista em administração pública. Pergunte qualquer coisa!")

# Função para criar a base de conhecimento com FAISS
def criar_base_conhecimento(texto_documento):
    st.info("🔄 Criando base de conhecimento...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    documentos = text_splitter.create_documents([texto_documento])
    embeddings = OpenAIEmbeddings(openai_api_key=api_key)
    vector_store = FAISS.from_documents(documentos, embeddings)
    vector_store.save_local("faiss_base")  # Salva localmente
    st.success("✅ Base de conhecimento criada com sucesso!")
    return vector_store

# Função para carregar a base de conhecimento
def carregar_base_conhecimento():
    if os.path.exists("faiss_base"):
        return FAISS.load_local("faiss_base", OpenAIEmbeddings(openai_api_key=api_key))
    else:
        return None

# Upload e leitura de PDF
if uploaded_file:
    document_text = extract_text_from_pdf(uploaded_file)
    st.success("📥 Documento carregado com sucesso!")
    st.session_state.vector_store = criar_base_conhecimento(document_text)
else:
    st.session_state.vector_store = carregar_base_conhecimento()

# Função de geração de resposta com análise semântica
def gerar_resposta(texto_usuario):
    if not uploaded_file and not st.session_state.vector_store:
        return "Por favor, carregue um documento antes de enviar perguntas."

    # Busca na base de conhecimento
    if st.session_state.vector_store:
        docs_encontrados = st.session_state.vector_store.similarity_search(texto_usuario, k=3)
        contexto_documento = "\n\n".join([doc.page_content for doc in docs_encontrados])
    else:
        contexto_documento = "Nenhum documento disponível para análise."

    contexto = f"""
Você é uma IA especializada em administração pública, desenvolvida pelo Instituto Publix.
Seu objetivo é responder perguntas de forma clara, assertiva e detalhada com base nos documentos fornecidos.

Contexto relevante:
{contexto_documento}
"""
    mensagens = [
        {"role": "system", "content": contexto},
        {"role": "user", "content": texto_usuario}
    ]

    try:
        resposta = openai.ChatCompletion.create(
            model="gpt-4",
            messages=mensagens,
            temperature=0.3,
            max_tokens=1000
        )
        mensagem_final = resposta["choices"][0]["message"]["content"]

        st.session_state.historico_mensagens.append({"user": texto_usuario, "bot": mensagem_final})
        return mensagem_final

    except Exception as e:
        return f"Erro ao gerar a resposta: {e}"

# Entrada do usuário
with st.container():
    user_input = st.text_input("💬 Digite sua mensagem aqui:", key="user_input")
    if user_input:
        resposta_bot = gerar_resposta(user_input)

# Histórico de mensagens com estilos customizados
st.subheader("📝 Histórico de Mensagens:")
st.markdown(
    """
    <style>
    .user-question {
        background-color: #FFEB3B;  /* Amarelo claro */
        padding: 10px;
        border-radius: 10px;
        font-weight: bold;
    }
    .bot-response {
        background-color: transparent;  /* Transparente, volta ao fundo padrão */
        padding: 10px;
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

for msg in st.session_state.historico_mensagens:
    st.markdown(f'<div class="user-question">**Você:** {msg["user"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="bot-response">**Bot:** {msg["bot"]}</div>', unsafe_allow_html=True)

# Botões de limpar histórico e baixar resumo
col1, col2 = st.columns(2)
with col1:
    if st.button("🗑️ Limpar histórico"):
        st.session_state.historico_mensagens = []
        st.success("Histórico limpo com sucesso!")

with col2:
    if st.button("📄 Baixar Resumo"):
        if st.session_state.historico_mensagens:
            resumo_texto = "\n".join(f"Pergunta: {msg['user']}\nResposta: {msg['bot']}" for msg in st.session_state.historico_mensagens)
            st.download_button(
                "Baixar resumo",
                data=resumo_texto,
                file_name="resumo_chat.txt",
                mime="text/plain"
            )
        else:
            st.warning("Nenhuma conversa para baixar o resumo.")
