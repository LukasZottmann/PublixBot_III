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
st.subheader("Pergunte qualquer coisa com base no conteúdo dos documentos!")

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
    Você é uma IA especializada em administração pública.
    Responda às perguntas com base no documento fornecido.

    Trecho do documento:
    {document_text[:2000]}
    """
    mensagens = f"{contexto}\n\nUsuário: {texto_usuario}\nIA:"

    try:
        resposta = openai.Completion.create(
            engine="text-davinci-003",  # Compatível com a versão antiga
            prompt=mensagens,
            temperature=0.3,
            max_tokens=1000
        )
        mensagem_final = resposta["choices"][0]["text"].strip()

        st.session_state.historico_mensagens.append({"user": texto_usuario, "bot": mensagem_final})
        return mensagem_final

    except Exception as e:
        return f"Erro ao gerar a resposta: {e}"

# Entrada do usuário
with st.form("form_pergunta"):
    user_input = st.text_input("💬 Digite sua mensagem aqui:")
    enviado = st.form_submit_button("Enviar")
    if enviado and user_input:
        resposta_bot = gerar_resposta(user_input)
        st.write(f"**Resposta:** {resposta_bot}")

# Histórico de mensagens
st.subheader("📝 Histórico de Mensagens:")
for msg in st.session_state.historico_mensagens:
    st.markdown(f"**Você:** {msg['user']}")
    st.markdown(f"**Bot:** {msg['bot']}")

# Botão para limpar histórico
if st.button("🗑️ Limpar histórico"):
    st.session_state.historico_mensagens = []
    st.success("Histórico limpo com sucesso!")
