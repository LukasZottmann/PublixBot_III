import streamlit as st
import openai
from PyPDF2 import PdfReader
import asyncio

# Estilo personalizado com CSS (sem contornos)
st.markdown(
    """
    <style>
    body {
        background-color: #000000;
        color: #ffffff;
    }
    .stApp {
        background-color: #000000;
    }
    .css-1q8dd3e p, .css-1q8dd3e h1, .css-1q8dd3e h2 {
        color: #ffd700 !important;
    }
    .stButton > button {
        background-color: #ffd700 !important;
        color: #000000 !important;
        border: none !important;
    }
    .stTextInput, .stTextArea, .stFileUploader {
        background-color: #1c1c1c !important;
        color: #ffd700 !important;
        border: none !important;
    }
    .stAlert {
        background-color: #333333 !important;
        color: #ffffff !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("💛 PublixBot")
st.write(
    """
    Olá, sou uma inteligência artificial pré-treinada desenvolvida pelo Instituto Publix para armazenar documentos importantes e te dar respostas com base neles.
    Para usar este aplicativo, você precisará de uma chave da API OpenAI.
    """
)

# Entrada da API Key
openai_api_key = st.text_input("OpenAI API Key", type="password")

if not openai_api_key:
    st.warning("Por favor, insira sua chave da OpenAI API para continuar.")
else:
    openai.api_key = openai_api_key

    # Upload de PDFs
    uploaded_files = st.file_uploader("Faça upload de documentos (.pdf)", type=["pdf"], accept_multiple_files=True)
    question = st.text_area("Digite sua pergunta:", placeholder="Exemplo: Qual o resumo do documento?")

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

    # Função para dividir o texto em trechos
    def dividir_documento(texto, chunk_size=1000):
        return [texto[i:i + chunk_size] for i in range(0, len(texto), chunk_size)]

    # Função para buscar o trecho mais relevante
    def buscar_trecho_relevante(chunks, pergunta):
        for chunk in chunks:
            if pergunta.lower() in chunk.lower():
                return chunk
        return chunks[0]  # Se não encontrar trecho relevante, retorna o primeiro

    if uploaded_files and question:
        st.write("🔄 Extraindo texto dos documentos...")
        documents_text = extract_text_from_pdfs(uploaded_files)

        # Dividir documento em trechos
        st.write("🔄 Dividindo documento em partes...")
        chunks = dividir_documento(documents_text)

        # Buscar o trecho mais relevante
        st.write("🔍 Buscando trecho mais relevante...")
        trecho_relevante = buscar_trecho_relevante(chunks, question)

        # Função para gerar resposta
        async def gerar_resposta():
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Responda de forma clara e direta com base no trecho do documento. Limite sua resposta a no máximo 3 parágrafos curtos."},
                    {"role": "user", "content": f"Trecho do documento: {trecho_relevante}\n\nPergunta: {question}"}
                ]
            )
            return response["choices"][0]["message"]["content"]

        try:
            st.write("🧠 Gerando resposta...")
            answer = asyncio.run(gerar_resposta())
            st.success(f"**Resposta:** {answer}")
        except Exception as e:
            st.error(f"Erro ao gerar a resposta: {e}")
