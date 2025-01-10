import streamlit as st
import openai
import pdfplumber
from langchain.vectorstores.faiss import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Função para extrair texto do PDF
def extract_text_from_pdf(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

# Função para criar index FAISS a partir do texto do documento
def create_faiss_index(text):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_text(text)
    embeddings = OpenAIEmbeddings(openai_api_key=openai.api_key)
    index = FAISS.from_texts(chunks, embeddings)
    return index

# Configuração da interface Streamlit
st.set_page_config(page_title="PublixBot", layout="wide")
st.sidebar.header("Configurações")
api_key = st.sidebar.text_input("🔑 OpenAI API Key", type="password")
uploaded_file = st.sidebar.file_uploader("📄 Faça upload de documentos (.pdf)", type="pdf")

# Variáveis de estado
if "historico_mensagens" not in st.session_state:
    st.session_state.historico_mensagens = []
if "index" not in st.session_state:
    st.session_state.index = None

# Validação de chave API
if not api_key:
    st.warning("Por favor, insira sua chave de API.")
    st.stop()

openai.api_key = api_key

# Exibição do título e informações iniciais
st.title("💛 PublixBot 1.5")
st.subheader("Essa é a inteligência artificial desenvolvida pelo Instituto Publix, pré-treinada com nosso conhecimento. Ela é especialista em administração pública. Pergunte qualquer coisa!")

# Upload e leitura de PDF
if uploaded_file:
    document_text = extract_text_from_pdf(uploaded_file)
    st.session_state.index = create_faiss_index(document_text)
    st.success("📥 Documento carregado e indexado com sucesso!")
else:
    st.warning("Carregue um documento para começar.")

# Função de geração de resposta
def gerar_resposta(texto_usuario):
    if not st.session_state.index:
        return "Por favor, carregue um documento antes de enviar perguntas."

    try:
        # Busca os trechos mais semelhantes
        similar_docs = st.session_state.index.similarity_search(texto_usuario, k=3)
        contexto = "\n\n".join([doc.page_content for doc in similar_docs])

        # Monta a mensagem com o contexto relevante
        mensagens = [
            {"role": "system", "content": f"Base de dados: {contexto}"},
            {"role": "user", "content": texto_usuario}
        ]

        # Geração da resposta com OpenAI
        resposta = openai.ChatCompletion.create(
            model="gpt-4",
            messages=mensagens,
            temperature=0.3,
            max_tokens=1000
        )
        mensagem_final = resposta["choices"][0]["message"]["content"]

        # Armazena a conversa no histórico
        st.session_state.historico_mensagens.append({"user": texto_usuario, "bot": mensagem_final})
        return mensagem_final

    except Exception as e:
        return f"Erro ao gerar a resposta: {e}"

# Interface de entrada do usuário
with st.container():
    user_input = st.text_input("💬 Digite sua mensagem aqui:")
    if user_input:
        resposta_bot = gerar_resposta(user_input)
        st.write(f"**Resposta:** {resposta_bot}")

# Exibição do histórico de mensagens
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
