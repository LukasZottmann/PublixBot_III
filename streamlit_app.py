import streamlit as st
import openai
from PyPDF2 import PdfReader

st.title("💛 PublixBot")
st.write(
    "Olá, sou uma inteligência artificial pré-treinada desenvolvida pelo Instituto Publix para armazenar documentos importantes e te dar respostas com base neles. "
    "Para usar este aplicativo, você precisará de uma chave da API OpenAI."
)

# Solicita a chave da API OpenAI
openai_api_key = st.text_input("OpenAI API Key", type="password")

if not openai_api_key:
    st.warning("Por favor, insira sua chave da OpenAI API para continuar.")
else:
    openai.api_key = openai_api_key

    # Upload de múltiplos PDFs
    uploaded_files = st.file_uploader("Faça upload de documentos (.pdf)", type=["pdf"], accept_multiple_files=True)

    # Campo para a pergunta
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

    if uploaded_files and question:
        # Extrai o texto dos PDFs
        st.write("🔄 Extraindo texto dos documentos...")
        documents_text = extract_text_from_pdfs(uploaded_files)

        # Faz a chamada para o modelo OpenAI
        try:
            st.write("🧠 Gerando resposta...")
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Você é um assistente que responde com base em documentos carregados."},
                    {"role": "user", "content": f"Texto do documento: {documents_text[:3000]} \n\nPergunta: {question}"}
                ]
            )
            answer = response["choices"][0]["message"]["content"]
            st.success(f"**Resposta:** {answer}")
        except Exception as e:
            st.error(f"Erro ao gerar a resposta: {e}")
