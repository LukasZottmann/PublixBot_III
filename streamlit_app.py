import streamlit as st
import openai
from PyPDF2 import PdfReader
import asyncio

# Estilo personalizado com CSS (sem bordas amarelas)
st.markdown(
    """
    <style>
    body {
        background-color: #000000; /* Fundo preto */
        color: #ffffff; /* Texto branco */
    }
    .stApp {
        background-color: #000000; /* Fundo preto */
    }
    .css-1q8dd3e p, .css-1q8dd3e h1, .css-1q8dd3e h2 {
        color: #ffd700 !important; /* Amarelo dourado nos títulos */
    }
    .stButton > button {
        background-color: #ffd700 !important; /* Botão amarelo */
        color: #000000 !important; /* Texto preto nos botões */
        border: none !important; /* Sem borda nos botões */
    }
    .stTextInput, .stTextArea, .stFileUploader {
        background-color: #1c1c1c !important; /* Fundo preto nas caixas */
        color: #ffd700 !important; /* Texto amarelo */
        border: none !important; /* Remove a borda das caixas */
    }
    .stAlert {
        background-color: #333333 !important; /* Fundo das mensagens */
        color: #ffffff !important; /* Texto das mensagens */
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

openai_api_key = st.text_input("OpenAI API Key", type="password")

if not openai_api_key:
    st.warning("Por favor, insira sua chave da OpenAI API para continuar.")
else:
    openai.api_key = openai_api_key

    uploaded_files = st.file_uploader("Faça upload de documentos (.pdf)", type=["pdf"], accept_multiple_files=True)
    question = st.text_area("Digite sua pergunta:", placeholder="Exemplo: Qual o resumo do documento?")

    def extract_text_from_pdfs(files):
        all_text = ""
        for file in files:
            reader = PdfReader(file)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    all_text += text
        return all_text

    if uploaded_files and question:
        st.write("🔄 Extraindo texto dos documentos...")
        documents_text = extract_text_from_pdfs(uploaded_files)

        async def gerar_resposta():
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Você é uma inteligência artificial desenvolvida pelo Instituto Publix especialista em gestão pública e política organizacional. Responda de forma completa e clara, citando exemplos do documento quando aplicável e estruturando a resposta com parágrafos organizados. Caso não encontre informações suficientes, peça mais detalhes."},
                    {"role": "user", "content": f"Texto do documento: {documents_text[:3000]} \n\nPergunta: {question}"}
                ]
            )
            return response["choices"][0]["message"]["content"]

        try:
            st.write("🧠 Gerando resposta...")
            answer = asyncio.run(gerar_resposta())
            st.success(f"**Resposta:** {answer}")
        except Exception as e:
            st.error(f"Erro ao gerar a resposta: {e}")
