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

# Permitir múltiplos uploads
uploaded_files = st.sidebar.file_uploader("📄 Faça upload de documentos (.pdf)", type="pdf", accept_multiple_files=True)

# Variáveis de estado
if "historico_mensagens" not in st.session_state:
    st.session_state.historico_mensagens = []

# Validação de chave API
if not api_key:
    st.warning("Por favor, insira sua chave de API.")
    st.stop()

openai.api_key = api_key

# Exibição do texto e entrada de mensagens
st.title("💛 PublixBot 1.5")
st.subheader("Pergunte qualquer coisa com base no conteúdo dos documentos!")

# Upload e leitura de PDFs
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

Contexto dos documentos:
{document_text[:2000]}  # Limite de caracteres para não sobrecarregar a mensagem
"""

    try:
        resposta = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": contexto},
                {"role": "user", "content": texto_usuario}
            ],
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
        st.markdown(f"**Resposta:** {resposta_bot}")

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
