import streamlit as st
from openai import OpenAI
from PyPDF2 import PdfReader

st.title("💛 PublixBot")
st.write(
    "Olá, sou uma inteligência artificial pré-treinada desenvolvida pelo Instituto Publix para armazenar documentos importantes e te dar respostas com base neles."
    "Para usar esse aplicativo, você vai precisar de uma chave da API da OpenAI, onde você pode conseguir [aqui](https://platform.openai.com/account/api-keys). "
)

openai_api_key = st.text_input("OpenAI API Key", type="password")
if not openai_api_key:
    st.info("Por favor adicione sua chave da API do OpenAI para continuar.", icon="🗝️")
else:
    client = OpenAI(api_key=openai_api_key)

    uploaded_file = st.file_uploader(
        "Upload a document (.pdf)", type=["pdf"], accept_multiple_files=False
    )

    question = st.text_area(
        "Faça uma pergunta sobre os documentos!",
        placeholder="Você consegue me fazer um resumo?",
        disabled=not uploaded_file,
    )

    if uploaded_file and question:
        try:
            # Usando PyPDF2 para extrair texto
            reader = PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()

            # Criando a mensagem para o modelo
            messages = [
                {
                    "role": "user",
                    "content": f"Here's some documents: {text} \n\n---\n\n {question}",
                }
            ]

            # Fazendo a chamada para o OpenAI
            stream = client.chat.completions.create(
                model="gpt-4-32k",
                messages=messages,
                stream=True,
            )

            st.write_stream(stream)

        except Exception as e:
            st.error(f"Erro ao processar o PDF: {e}")
