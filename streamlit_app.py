import streamlit as st
import openai
import pdfplumber

# Função para extrair texto de múltiplos PDFs
def extract_text_from_pdfs(uploaded_files):
    combined_text = ""
    for pdf_file in uploaded_files:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                combined_text += page.extract_text() or ""
    return combined_text

# Configuração da interface
st.set_page_config(page_title="PublixBot", layout="wide")
st.sidebar.header("Configurações")
api_key = st.sidebar.text_input("🔑 OpenAI API Key", type="password")
uploaded_files = st.sidebar.file_uploader("📄 Faça upload de documentos (.pdf)", type="pdf", accept_multiple_files=True)

# Variáveis de estado para o chat
if "mensagens_chat" not in st.session_state:
    st.session_state.mensagens_chat = []

# Validação de chave API
if not api_key:
    st.warning("Por favor, insira sua chave de API.")
    st.stop()

openai.api_key = api_key

# Exibição do título e upload de documentos
st.title("💛 PublixBot 1.5")
st.subheader("Pergunte qualquer coisa com base nos documentos carregados!")

if uploaded_files:
    document_text = extract_text_from_pdfs(uploaded_files)
    st.success(f"📥 {len(uploaded_files)} documentos carregados com sucesso!")
else:
    st.warning("Carregue documentos para começar.")

# Função de geração de resposta
def gerar_resposta(texto_usuario):
    if not uploaded_files:
        return "Por favor, carregue documentos antes de enviar perguntas."

    contexto = f"""
    Você é uma IA especializada em administração pública, desenvolvida pelo Instituto Publix. 
    Seu objetivo é responder perguntas de forma clara, assertiva e detalhada com base nos documentos fornecidos.

    Contexto do(s) documento(s):
    {document_text[:3000]}  # Limite de caracteres para manter o desempenho
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
        return resposta["choices"][0]["message"]["content"]

    except Exception as e:
        return f"Erro ao gerar a resposta: {e}"

# Entrada do usuário e exibição contínua do chat
with st.container():
    user_input = st.text_input("💬 Digite sua mensagem aqui:", key="user_input")
    if user_input:
        # Gera a resposta
        resposta_bot = gerar_resposta(user_input)

        # Atualiza o chat com a nova mensagem
        st.session_state.mensagens_chat.append(f"**Você:** {user_input}")
        st.session_state.mensagens_chat.append(f"**Bot:** {resposta_bot}")

        # Limpa o campo de entrada após enviar
        st.experimental_rerun()

# Exibe o chat contínuo
st.markdown("### 📝 Chat")
st.write("\n".join(st.session_state.mensagens_chat))
