import streamlit as st
import openai
import pdfplumber
import os

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

# Função para gerar resposta
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

# Configuração inicial
st.set_page_config(page_title="PublixBot", layout="wide")
st.sidebar.header("Configurações")
api_key = st.sidebar.text_input("🔑 OpenAI API Key", type="password", placeholder="Insira sua API Key")
save_api_key = st.sidebar.checkbox("Salvar API Key localmente")

if save_api_key:
    st.success("Chave de API salva com sucesso!")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key  # Salva na variável de ambiente temporariamente
else:
    openai.api_key = api_key

uploaded_files = st.sidebar.file_uploader("📄 Faça upload de documentos (.pdf)", type="pdf", accept_multiple_files=True)

# Inicialização segura das variáveis de estado
if "mensagens_chat" not in st.session_state:
    st.session_state.mensagens_chat = []  # Histórico de mensagens
if "document_text" not in st.session_state:
    st.session_state.document_text = ""  # Texto combinado dos documentos
if "document_map" not in st.session_state:
    st.session_state.document_map = {}  # Mapa de documentos por nome
if "pending_input" not in st.session_state:
    st.session_state.pending_input = ""  # Texto temporário do formulário

st.title("💛 PublixBot 2.3 - Interface Melhorada!")
st.subheader("Pergunte qualquer coisa com base nos documentos carregados!")

if uploaded_files:
    st.session_state.document_text, st.session_state.document_map = extract_text_from_pdfs(uploaded_files)
    st.success(f"📥 {len(uploaded_files)} documentos carregados com sucesso!")

    # Exibição de prévia dos documentos carregados
    with st.expander("📄 Visualizar documentos carregados"):
        for nome_documento, conteudo in st.session_state.document_map.items():
            st.markdown(f"**{nome_documento}** - Prévia das primeiras 500 palavras:")
            st.text_area(f"Conteúdo de {nome_documento}", conteudo[:500], height=200, disabled=True)
else:
    st.warning("Carregue documentos para começar.")

# Botão para limpar histórico
if st.button("🧹 Limpar histórico de mensagens"):
    st.session_state.mensagens_chat = []
    st.success("Histórico de mensagens limpo com sucesso!")

# Botão para baixar histórico
if st.button("📥 Baixar histórico do chat"):
    with open("chat_history.txt", "w") as f:
        for msg in st.session_state.mensagens_chat:
            f.write(f"Você: {msg['user']}\n")
            f.write(f"Bot: {msg['bot']}\n\n")
    with open("chat_history.txt", "rb") as f:
        st.download_button("Clique aqui para baixar", f, file_name="chat_history.txt")

# Estilo customizado para o chat
st.markdown("""
<style>
.chat-container {
    background-color: #2f2f2f;
    padding: 20px;
    border-radius: 10px;
}

.chat-bubble {
    border-radius: 15px;
    padding: 10px;
    margin-bottom: 10px;
}

.user-message {
    background-color: #1e90ff;
    color: white;
    text-align: right;
}

.bot-message {
    background-color: #32cd32;
    color: white;
    text-align: left;
    border-left: 5px solid #228b22;
}

</style>
""", unsafe_allow_html=True)

# Exibição das mensagens do chat
st.markdown("### 📝 Chat")
for mensagem in st.session_state.mensagens_chat:
    user_msg = mensagem.get("user", "Mensagem do usuário indisponível.")
    bot_msg = mensagem.get("bot", "Mensagem do bot indisponível.")
    st.markdown(f'<div class="chat-container"><div class="chat-bubble user-message">Você: {user_msg}</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="chat-container"><div class="chat-bubble bot-message">Bot: {bot_msg}</div></div>', unsafe_allow_html=True)

# Campo de entrada de mensagem com formulário
with st.form(key="input_form"):
    st.session_state.pending_input = st.text_input("💬 Sua pergunta:", value=st.session_state.pending_input)
    submit_button = st.form_submit_button("Enviar")

# Processa a entrada do formulário após envio
if submit_button and st.session_state.pending_input:
    resposta_bot = gerar_resposta(st.session_state.pending_input)
    st.session_state.mensagens_chat.append({"user": st.session_state.pending_input, "bot": resposta_bot})
    st.session_state.pending_input = ""  # Limpa o campo de entrada após envio
