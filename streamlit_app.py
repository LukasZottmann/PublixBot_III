import streamlit as st
import openai
import pdfplumber
import asyncio

st.set_page_config(page_title="PublixBot Chatbot", layout="wide")

# Sidebar com chave da API e upload
st.sidebar.title("⚙️ Configurações")
openai_api_key = st.sidebar.text_input("🔑 OpenAI API Key", type="password")
uploaded_files = st.sidebar.file_uploader("📄 Faça upload de documentos (.pdf)", type=["pdf"], accept_multiple_files=True)

if not openai_api_key:
    st.sidebar.warning("Por favor, insira sua chave da OpenAI API para continuar.")
else:
    openai.api_key = openai_api_key

    if uploaded_files:
        st.sidebar.success("✅ Documentos carregados com sucesso!")

        # Função de extração de texto com PDFplumber
        def extract_text_from_pdfs(files):
            all_text = ""
            for file in files:
                try:
                    with pdfplumber.open(file) as pdf:
                        for page in pdf.pages:
                            text = page.extract_text()
                            if text:
                                all_text += text + "\n"
                except Exception as e:
                    st.error(f"Erro ao ler o arquivo {file.name}: {e}")
            return all_text if all_text.strip() else "Não foi possível extrair texto do PDF."

        documents_text = extract_text_from_pdfs(uploaded_files)

        if "history" not in st.session_state:
            st.session_state.history = []

        async def gerar_resposta(user_input):
            trecho_documento = documents_text[:2000]
            st.session_state.history.append({"role": "user", "content": user_input})

            response = await openai.ChatCompletion.acreate(
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

        # Área principal com o campo de perguntas
        st.title("💛 PublixBot Chatbot")
        st.write("Faça perguntas interativas com base nos documentos enviados!")

        user_input = st.text_input("Digite sua pergunta:")
        if user_input:
            try:
                st.write("🧠 Gerando resposta...")
                asyncio.run(gerar_resposta(user_input))
            except Exception as e:
                st.error(f"Erro ao gerar a resposta: {e}")

        # Botão para limpar o histórico de mensagens
        if st.button("🗑️ Limpar histórico"):
            st.session_state.history = []

        # Exibição do histórico de mensagens
        with st.expander("📜 Histórico de Mensagens", expanded=True):
            for message in st.session_state.history:
                if message["role"] == "user":
                    st.markdown(f"**Você:** {message['content']}")
                else:
                    st.markdown(f"**Bot:** {message['content']}")
