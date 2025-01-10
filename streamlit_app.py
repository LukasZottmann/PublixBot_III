import streamlit as st
import openai
from PyPDF2 import PdfReader
import asyncio

# Estilo personalizado
st.markdown(
    """
    <style>
    .stApp {
        background-color: #000000;
        color: #ffffff;
    }
    .chat-message {
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 8px;
    }
    .user-message {
        background-color: #ffd700;
        color: #000;
        text-align: left;
    }
    .bot-message {
        background-color: #1c1c1c;
        color: #fff;
        text-align: left;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Título
st.title("💛 PublixBot Chatbot")
st.write("Carregue documentos e faça perguntas interativas com base neles!")

# Entrada de API Key
openai_api_key = st.text_input("OpenAI API Key", type="password")
if not openai_api_key:
    st.warning("Por favor, insira sua chave da OpenAI API para continuar.")
else:
    openai.api_key = openai_api_key

    # Upload de PDFs
    uploaded_files = st.file_uploader("Faça upload de documentos (.pdf)", type=["pdf"], accept_multiple_files=True)
    if uploaded_files:
        st.write("✅ Documentos carregados com sucesso!")

        # Função para extrair texto dos PDFs
        def extract_text_from_pdfs(files):
            all_text = ""
            for file in files:
                reader = PdfReader(file)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        all_text += text
            return all_text

        # Carregar o texto do documento
        documents_text = extract_text_from_pdfs(uploaded_files)
        
        # Divisão do texto em partes
        def dividir_documento(texto, chunk_size=2000):
            return [texto[i:i + chunk_size] for i in range(0, len(texto), chunk_size)]

        chunks = dividir_documento(documents_text)

        # Histórico de mensagens
        if "history" not in st.session_state:
            st.session_state.history = []

        # Campo de mensagem do usuário
        user_input = st.text_input("Digite sua pergunta:")
        if user_input:
            # Adiciona a mensagem do usuário no histórico
            st.session_state.history.append({"role": "user", "content": user_input})

            # Função para obter o trecho relevante
            def buscar_trecho_relevante(chunks, pergunta):
                for chunk in chunks:
                    if pergunta.lower() in chunk.lower():
                        return chunk
                return chunks[0]

            trecho_relevante = buscar_trecho_relevante(chunks, user_input)

            async def gerar_resposta():
                response = await openai.ChatCompletion.acreate(
                    model="gpt-4",
                    messages=st.session_state.history + [{"role": "user", "content": f"Trecho relevante: {trecho_relevante}"}],
                    temperature=0.3
                )
                return response["choices"][0]["message"]["content"]

            # Geração da resposta
            try:
                st.write("🧠 Gerando resposta...")
                answer = asyncio.run(gerar_resposta())
                st.session_state.history.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"Erro ao gerar a resposta: {e}")

        # Exibição do histórico de mensagens no formato de chat
        for message in st.session_state.history:
            if message["role"] == "user":
                st.markdown(f'<div class="chat-message user-message">{message["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-message bot-message">{message["content"]}</div>', unsafe_allow_html=True)

