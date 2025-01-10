import streamlit as st
import openai
import pdfplumber
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

# Configuração da página precisa ser o primeiro comando
st.set_page_config(page_title="PublixBot", layout="wide")

# Inicializando o modelo de embeddings semânticos
@st.cache_resource
def load_embedding_model():
    return SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

embedding_model = load_embedding_model()

# Função para extrair texto do PDF
def extract_text_from_pdf(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        text = " ".join([page.extract_text() or "" for page in pdf.pages])
    return text

# Função para dividir o texto em parágrafos
def split_into_paragraphs(text, max_length=500):
    paragraphs = text.split("\n\n")
    return [p.strip() for p in paragraphs if len(p.strip()) > 50 and len(p.strip()) <= max_length]

# Função para encontrar o trecho mais relevante
def find_relevant_paragraphs(query, paragraphs):
    query_embedding = embedding_model.encode([query])
    paragraph_embeddings = embedding_model.encode(paragraphs)
    similarities = cosine_similarity(query_embedding, paragraph_embeddings)
    best_index = similarities.argmax()
    return paragraphs[best_index]

st.sidebar.header("Configurações")
api_key = st.sidebar.text_input("🔑 OpenAI API Key", type="password")
uploaded_file = st.sidebar.file_uploader("📄 Faça upload de documentos (.pdf)", type="pdf")

if "historico_mensagens" not in st.session_state:
    st.session_state.historico_mensagens = []

if not api_key:
    st.warning("Por favor, insira sua chave de API.")
    st.stop()

openai.api_key = api_key

st.title("💛 PublixBot 1.5")
st.subheader("Essa é a inteligência artificial desenvolvida pelo Instituto Publix. Pergunte qualquer coisa com base no conteúdo dos documentos!")

if uploaded_file:
    document_text = extract_text_from_pdf(uploaded_file)
    paragraphs = split_into_paragraphs(document_text)
    st.success("📥 Documento carregado com sucesso!")
else:
    st.warning("Carregue um documento para começar.")

def gerar_resposta(texto_usuario):
    if not uploaded_file:
        return "Por favor, carregue um documento antes de enviar perguntas."

    paragrafo_relevante = find_relevant_paragraphs(texto_usuario, paragraphs)
    contexto = f"Contexto extraído do documento:\n{paragrafo_relevante}"

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

with st.container():
    user_input = st.text_input("💬 Digite sua mensagem aqui:", key="user_input")
    if user_input:
        resposta_bot = gerar_resposta(user_input)

st.subheader("📝 Histórico de Mensagens:")
st.markdown(
    """
    <style>
    .user-question {
        background-color: #FFEB3B;
        padding: 10px;
        border-radius: 10px;
        font-weight: bold;
    }
    .bot-response {
        background-color: transparent;
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
