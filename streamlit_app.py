import streamlit as st
import openai
import pdfplumber

# Configuração da página
st.set_page_config(page_title="PublixBot 1.5", page_icon="💛", layout="wide")

# Estilos personalizados
st.markdown(
    """
    <style>
    .stButton>button {
        background-color: #ffd700;
        color: black;
        font-size: 18px;
        border-radius: 12px;
        padding: 10px 20px;
    }
    .stTextInput>div>input {
        font-size: 18px;
    }
    .bot-buttons {
        display: flex;
        justify-content: space-between;
        margin-top: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Sidebar com API e upload de PDF
st.sidebar.title("⚙️ Configurações")
openai_api_key = st.sidebar.text_input("🔑 OpenAI API Key", type="password")
uploaded_files = st.sidebar.file_uploader("📄 Faça upload de documentos (.pdf)", type=["pdf"], accept_multiple_files=True)

if not openai_api_key:
    st.sidebar.warning("Por favor, insira sua chave da OpenAI API para continuar.")
else:
    openai.api_key = openai_api_key

    if uploaded_files:
        st.sidebar.success("✅ Documentos carregados com sucesso!")

        def extract_text_from_pdfs(files):
            all_text = ""
            for file in files:
                with pdfplumber.open(file) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            all_text += text + "\n"
            return all_text if all_text.strip() else "Não foi possível extrair texto do PDF."

        documents_text = extract_text_from_pdfs(uploaded_files)

        if "history" not in st.session_state:
            st.session_state.history = []

        def gerar_resposta(user_input):
            trecho_documento = documents_text[:2000]
            st.session_state.history.append({"role": "user", "content": user_input})

            try:
                with st.spinner('🧠 Processando sua pergunta...'):
                    response = openai.ChatCompletion.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "Você é um assistente de análise de documentos PDF. Responda de forma clara e concisa."},
                            *st.session_state.history,
                            {"role": "user", "content": f"Trecho do documento: {trecho_documento}\nPergunta: {user_input}"}
                        ],
                        temperature=0.3
                    )
                    answer = response["choices"][0]["message"]["content"]
                    st.session_state.history.append({"role": "assistant", "content": answer})

            except Exception as e:
                st.error(f"Erro ao gerar a resposta: {e}")

        # Interface principal
        st.title("💛 PublixBot 1.5")
        st.write("Essa é a inteligência artificial desenvolvida pelo Instituto Publix, pré-treinada com nosso conhecimento, ela é especialista em administração pública, fique à vontade para perguntar qualquer coisa!")

        # Exibir histórico de mensagens
        with st.expander("📜 Histórico de Mensagens", expanded=True):
            for message in st.session_state.history:
                if message["role"] == "user":
                    st.markdown(f"**Você:** {message['content']}")
                else:
                    st.markdown(f"**Bot:** {message['content']}")

        st.markdown("---")
        user_input = st.text_input("💬 Digite sua mensagem aqui:")

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🗑️ Limpar histórico"):
                st.session_state.history = []

        with col2:
            if len(st.session_state.history) > 0:
                resumo = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in st.session_state.history])
                st.download_button("📄 Baixar Resumo", resumo, file_name="resumo_resposta.txt")

        if user_input:
            gerar_resposta(user_input)
