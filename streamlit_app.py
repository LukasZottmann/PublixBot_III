import streamlit as st
from openai import OpenAI
from PyPDF2 import PdfReader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter

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
                text = page.extract_text()
                if text:
                    all_text += text
        return all_text

    # Função para dividir o texto em chunks
    def dividir_documento(texto, chunk_size=1000, chunk_overlap=100):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        chunks = text_splitter.split_text(texto)
        return chunks

    # Função para criar o índice FAISS
    def criar_indexacao_vetorial(texto):
        embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        chunks = dividir_documento(texto)
        vetor_faiss = FAISS.from_texts(chunks, embeddings)
        return vetor_faiss

    # Função para buscar trechos relevantes
    def buscar_trechos_relevantes(query, vetor_faiss, k=3):
        trechos_relevantes = vetor_faiss.similarity_search(query, k=k)
        return trechos_relevantes

    # Processa os arquivos carregados e a pergunta
    if uploaded_files and question:
        try:
            # Extrai o texto de todos os PDFs
            documents = extract_text_from_pdfs(uploaded_files)

            # Cria o índice vetorial dos documentos
            st.write("🔄 Criando índice vetorial dos documentos...")
            vetor_faiss = criar_indexacao_vetorial(documents)
            st.write("✅ Índice vetorial criado!")

            # Busca trechos relevantes
            st.write("🔍 Buscando trechos mais relevantes...")
            trechos_relevantes = buscar_trechos_relevantes(question, vetor_faiss, k=3)

            # Concatena os trechos relevantes para formar o contexto
            contexto = "\n\n".join([trecho.page_content for trecho in trechos_relevantes])

            # Define as mensagens para o modelo
            messages = [
                {
                    "role": "user",
                    "content": f"Baseado nos documentos: \n\n{contexto}\n\n---\n\n Pergunta: {question}",
                }
            ]

            # Faz a chamada para o modelo
            st.write("✉️ Gerando resposta...")
            response = client.chat_completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
            )

            # Mostra a resposta
            resposta_final = response["choices"][0]["message"]["content"]
            st.write(f"**Resposta:** {resposta_final}")

        except Exception as e:
            st.error(f"Erro ao processar os PDFs: {e}")
