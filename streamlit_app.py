import streamlit as st
from openai import OpenAI
from PyPDF2 import PdfReader

st.title("💛 PublixBot")
st.write(
    "Olá, sou uma inteligência artificial pré-treinada desenvolvida pelo Instituto Publix para armazenar documentos importantes e te dar respostas com base neles."
    "Para usar esse aplicativo, você vai precisar de uma chave da API da OpenAI, que você pode conseguir [aqui](https://platform.openai.com/account/api-keys). "
)

# Solicita a chave da API
openai_api_key = st.text_input("OpenAI API Key", type="password")
if not openai_api_key:
    st.info("Por favor adicione sua chave da API do OpenAI para continuar.", icon="🗝️")
else:
    client = OpenAI(api_key=openai_api_key)

    # Upload de múltiplos arquivos
    uploaded_files = st.file_uploader(
        "Upload documentos (.pdf)", type=["pdf"], accept_multiple_files=True
    )

    # Campo para a pergunta
    question = st.text_area(
        "Faça uma pergunta sobre os documentos!",
        placeholder="Você consegue me fazer um resumo?",
        disabled=not uploaded_files,
    )

    # Função para extrair texto de múltiplos PDFs
    def extract_text_from_pdfs(files):
        all_text = ""
        for file in files:
            reader = PdfReader(file)
            for page in reader.pages:
                all_text += page.extract_text()
        return all_text

    # Processa os arquivos carregados e a pergunta
    if uploaded_files and question:
        try:
            # Extrai o texto de todos os PDFs
            documents = extract_text_from_pdfs(uploaded_files)

            # Define as mensagens para o modelo
            messages = [
                {
                    "role": "user",
                    "content": f"Here's some documents: {documents[:30000]} \n\n---\n\n {question}",
                }
            ]

            # Faz a chamada para o modelo
            stream = client.chat.completions.create(
                model="gpt-3.5-turbo",  # Substitua por "gpt-4-32k" se necessário
                messages=messages,
                stream=True,
            )

            # Mostra a resposta
            st.write_stream(stream)

        except Exception as e:
            st.error(f"Erro ao processar os PDFs: {e}")
