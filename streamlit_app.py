import streamlit as st
import openai
import pdfplumber

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

# Validação de chave API
if not api_key:
    st.warning("Por favor, insira sua chave de API.")
    st.stop()

openai.api_key = api_key

# Exibição do texto e entrada de mensagens
st.title("💛 PublixBot 1.5")
st.subheader("Essa é a inteligência artificial desenvolvida pelo Instituto Publix, pré-treinada com nosso conhecimento. Ela é especialista em administração pública. Pergunte qualquer coisa!")

# Upload e leitura de PDF
if uploaded_file:
    document_text = extract_text_from_pdf(uploaded_file)
    st.success("📥 Documento carregado com sucesso!")
else:
    st.warning("Carregue um documento para começar.")

# Função de geração de resposta
def gerar_resposta(texto_usuario):
    if not uploaded_file:
        return "Por favor, carregue um documento antes de enviar perguntas."

    contexto = f"""
Você é uma IA especializada em administração pública, desenvolvida pelo Instituto Publix. 
Seu objetivo é responder perguntas de forma clara, assertiva e detalhada com base nos documentos fornecidos.

Contexto do documento:
{document_text[:2000]}  # Limite de caracteres para não sobrecarregar a mensagem
"""
    mensagens = [
        {"role": "system", "content": contexto},
        {"role": "user", "content": texto_usuario}
    ]

    try:
        resposta = openai.ChatCompletion.acreate(  # Atualizado para a nova versão
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
