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
            st.write(f"🔎 Conteúdo de {pdf_file.name} (primeiros 500 caracteres):")
            st.write(text[:500])  # Diagnóstico: Mostra os primeiros 500 caracteres de cada documento
    return combined_text, document_map

# Configuração da interface
st.set_page_config(page_title="PublixBot", layout="wide")
st.sidebar.header("Configurações")
api_key = st.sidebar.text_input("🔑 OpenAI API Key", type="password")
uploaded_files = st.sidebar.file_uploader("📄 Faça upload de documentos (.pdf)", type="pdf", accept_multiple_files=True)

# Inicialização das variáveis de estado
if "mensagens_chat" not in st.session_state:
    st.session_state.mensagens_chat = []  # Lista de dicionários com mensagens
if "document_text" not in st.session_state:
    st.session_state.document_text = ""  # Texto combinado dos documentos
if "document_map" not in st.session_state:
    st.session_state.document_map = {}  # Mapeamento dos documentos por nome

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

# Função de geração de resposta com separação dos documentos
def gerar_resposta(texto_usuario):
    if not uploaded_files:
        return "Por favor, carregue documentos antes de enviar perguntas."

    # Criar contexto com separação clara dos documentos
    contexto = "Você é uma IA especializada em administração pública, desenvolvida pelo Instituto Publix.\n"
    contexto += "Seu objetivo é responder perguntas com base nos seguintes documentos fornecidos:\n\n"
    
    for nome_documento, text in st.session_state.document_map.items():
        contexto += f"--- Documento: {nome_documento} ---\n{text[:1500]}...\n\n"  # Limita cada documento a 1500 caracteres para manter o contexto

    mensagens = [
        {"role": "system", "content": contexto},
        {"role": "user", "content": texto_usuario}
    ]

    try:
        resposta = openai.ChatCompletion.create(
            model="gpt-4",
            messages=mensagens,
            temperature=0.3,
            max_tokens=1500  # Mantido o número de tokens de resposta
        )
        return resposta["choices"][0]["message"]["content"]

    except Exception as e:
        return f"Erro ao gerar a resposta: {e}"

# Entrada do usuário e exibição contínua do chat
user_input = st.text_input("💬 Digite sua mensagem aqui:")

if user_input:
    # Gera a resposta
    resposta_bot = gerar_resposta(user_input)

    # Adiciona as mensagens como dicionários
    st.session_state.mensagens_chat.append({"user": user_input, "bot": resposta_bot})

# Estilo para cores, barra de rolagem e alinhamento das mensagens
st.markdown(
    """
    <style>
    .user-question {
        background-color: #E1F5FE;  /* Azul claro */
        text-align: right;
        padding: 10px;
        margin: 5px;
        border-radius: 15px;
        font-weight: bold;
        color: #0277BD;
    }
    .bot-response {
        background-color: #F1F8E9;  /* Verde claro */
        text-align: left;
        padding: 10px;
        margin: 5px;
        border-radius: 15px;
        color: #33691E;
    }
    .message-container {
        max-height: 500px;  /* Define altura máxima */
        overflow-y: auto;  /* Adiciona barra de rolagem */
        padding: 10px;
        border: 1px solid #ddd;
        border-radius: 10px;
        background-color: #FAFAFA;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Exibe o chat com barra de rolagem, alinhamento e cores
st.markdown("### 📝 Chat")
st.markdown('<div class="message-container">', unsafe_allow_html=True)

for mensagem in st.session_state.mensagens_chat:
    if isinstance(mensagem, dict):
        user_msg = mensagem.get("user", "Mensagem do usuário indisponível.")
        bot_msg = mensagem.get("bot", "Mensagem do bot indisponível.")
        
        st.markdown(
            f'<div class="user-question"><strong>Você:</strong> {user_msg}</div>', unsafe_allow_html=True
        )
        st.markdown(
            f'<div class="bot-response"><strong>Bot:</strong> {bot_msg}</div>', unsafe_allow_html=True
        )
    else:
        st.error("Mensagem inválida no histórico. Certifique-se de que todas as mensagens estejam no formato correto.")

st.markdown('</div>', unsafe_allow_html=True)
