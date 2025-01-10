import streamlit as st
import openai
import pdfplumber

st.set_page_config(page_title="PublixBot 1.5", page_icon="💛", layout="wide")

# Estilo personalizado
st.markdown("""
    <style>
    .stButton>button {
        background-color: #ffd700;
        color: black;
        font-size: 18px;
        border-radius: 12px;
        padding: 10px 20px;
    }
    .chat-container {
        background-color: #1e1e1e;
        padding: 15px;
        border-radius: 10px;
        overflow-y: auto;
        max-height: 400px;
    }
    </style>
    """, unsafe_allow_html=True)

st.sidebar.title("⚙️ Configurações")
openai_api_key = st.sidebar.text_input("🔑 OpenAI API Key", type="password")
uploaded_files = st.sidebar.file_uploader("📄 Faça upload de documentos (.pdf)", type=["pdf"], accept_multiple_files=True)

# Inicialização do estado
if "history" not in st.session_state:
    st.session_state.history = []
if "documents_text" not in st.session_state:
    st.session_state.documents_text = ""

# Função para extrair texto
def extract_text_from_pdfs(files):
    all_text = ""
    for file in files:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    all_text += text.replace("\n", " ") + " "
    return all_text if all_text.strip() else "Erro ao extrair o texto do PDF."

if uploaded_files:
    st.session_state.documents_text = extract_text_from_pdfs(uploaded_files)

# Função para dividir o texto em blocos menores
def dividir_em_blocos(texto, tamanho=1500):
    return [texto[i:i+tamanho] for i in range(0, len(texto), tamanho)]

# Função para gerar resposta com blocos relevantes
def gerar_resposta(user_input):
    if not st.session_state.documents_text:
        st.error("Nenhum documento foi carregado.")
        return

    blocos = dividir_em_blocos(st.session_state.documents_text)
    contexto = f"Pergunta: {user_input}\n\nTexto do documento:"
    mensagens = [{"role": "system", "content": "Você é um assistente que analisa documentos PDF e responde com precisão."}]
    mensagens.append({"role": "user", "content": contexto + blocos[0]})

    try:
        with st.spinner('🧠 Processando sua pergunta...'):
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=mensagens,
                temperature=0.3
            )
            answer = response["choices"][0]["message"]["content"]
            st.session_state.history.append({"role": "assistant", "content": answer})
    except Exception as e:
        st.error(f"Erro ao gerar a resposta: {e}")

# Interface do usuário
st.title("💛 PublixBot 1.5")
st.write("Essa é a inteligência artificial desenvolvida pelo Instituto Publix, pré-treinada com nosso conhecimento, ela é especialista em administração pública, fique à vontade para perguntar qualquer coisa!")

# Exibir histórico de mensagens
st.markdown("---")
st.write("📝 **Histórico de Mensagens:**")
chat_container = st.container()

with chat_container:
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for message in st.session_state.history:
        if message["role"] == "user":
            st.markdown(f'<div class="user-message">**Você:** {message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="bot-message">**Bot:** {message["content"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")
user_input = st.text_input("💬 Digite sua mensagem aqui:")

if user_input:
    st.session_state.history.append({"role": "user", "content": user_input})
    gerar_resposta(user_input)

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("🗑️ Limpar histórico"):
        st.session_state.history = []

with col2:
    if len(st.session_state.history) > 0:
        resumo = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in st.session_state.history])
        st.download_button("📄 Baixar Resumo", resumo, file_name="resumo_resposta.txt")
