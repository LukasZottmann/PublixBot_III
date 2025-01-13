import streamlit as st
import openai
import pdfplumber

# Função para extrair texto de múltiplos PDFs
def extract_text_from_pdfs(uploaded_files):
    combined_text = ""
    document_map = {}
    for pdf_file in uploaded_files:
        with pdfplumber.open(pdf_file) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text += page_text
            document_map[pdf_file.name] = text
            combined_text += f"\n\n--- Documento: {pdf_file.name} ---\n{text}\n"
    return combined_text, document_map

# Configuração da interface
st.set_page_config(page_title="PublixBot", layout="wide")
st.sidebar.header("Configurações")
api_key = st.sidebar.text_input("🔑 OpenAI API Key", type="password")
uploaded_files = st.sidebar.file_uploader("📄 Faça upload de documentos (.pdf)", type="pdf", accept_multiple_files=True)

# Inicialização das variáveis de estado
if "mensagens_chat" not in st.session_state:
    st.session_state.mensagens_chat = []  # Lista de mensagens
if "document_text" not in st.session_state:
    st.session_state.document_text = ""  # Texto combinado dos documentos
if "document_map" not in st.session_state:
    st.session_state.document_map = {}  # Mapa de documentos por nome

# Validação de chave API
if not api_key:
    st.warning("Por favor, insira sua chave de API.")
    st.stop()

openai.api_key = api_key

# Exibição do título e upload de documentos
st.title("💛 PublixBot 1.5")
st.subheader("Pergunte qualquer coisa com base nos documentos carregados!")

if uploaded_files:
    st.session_state.document_text, st.session_state.document_map = extract_text_from_pdfs(uploaded_files)
    st.success(f"📥 {len(uploaded_files)} documentos carregados com sucesso!")
else:
    st.warning("Carregue documentos para começar.")

# Função de geração de resposta
def gerar_resposta(texto_usuario):
    if not uploaded_files:
        return "Por favor, carregue documentos antes de enviar perguntas."

    contexto = "Você é uma IA especializada em administração pública.\n"
    contexto += "Baseie suas respostas nos seguintes documentos:\n\n"
    for nome_documento, text in st.session_state.document_map.items():
        contexto += f"--- Documento: {nome_documento} ---\n{text[:1500]}...\n\n"

    mensagens = [{"role": "system", "content": contexto}, {"role": "user", "content": texto_usuario}]

    try:
        resposta = openai.ChatCompletion.create(
            model="gpt-4",
            messages=mensagens,
            temperature=0.3,
            max_tokens=1500
        )
        return resposta["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Erro ao gerar a resposta: {e}"

# Estilo customizado para a área de chat
st.markdown("""
<style>
.scroll-container {
    height: 500px;
    overflow-y: auto;
    background-color: #f0f0f5;
    padding: 20px;
    border-radius: 10px;
    border: 1px solid #ccc;
}

.chat-bubble {
    border-radius: 15px;
    padding: 10px;
    margin-bottom: 10px;
}

.user-message {
    background-color: #dbeafe;
    color: #1d4ed8;
    text-align: right;
}

.bot-message {
    background-color: #d1fae5;
    color: #065f46;
    text-align: left;
}
</style>
""", unsafe_allow_html=True)

# Caixa de chat com barra de rolagem
st.markdown("### 📝 Chat")
with st.container():
    st.markdown('<div class="scroll-container">', unsafe_allow_html=True)
    
    # Exibição do histórico de mensagens dentro do contêiner rolável
    for mensagem in st.session_state.mensagens_chat:
        user_msg = mensagem.get("user", "Mensagem do usuário indisponível.")
        bot_msg = mensagem.get("bot", "Mensagem do bot indisponível.")
        st.markdown(f'<div class="chat-bubble user-message">**Você:** {user_msg}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="chat-bubble bot-message">**Bot:** {bot_msg}</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Campo de entrada de mensagem fora do bloco rolável, mas na mesma área do contêiner
with st.form(key="input_form"):
    user_input = st.text_input("💬 Sua pergunta:", key="input_text")
    submit_button = st.form_submit_button("Enviar")
    if submit_button and user_input:
        resposta_bot = gerar_resposta(user_input)
        st.session_state.mensagens_chat.append({"user": user_input, "bot": resposta_bot})
