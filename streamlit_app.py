import streamlit as st
import openai
import pdfplumber
import asyncio

st.title("💛 PublixBot Chatbot")
st.write("Carregue documentos e faça perguntas interativas com base neles!")

# Entrada da API Key
openai_api_key = st.text_input("OpenAI API Key", type="password")
if not openai_api_key:
    st.warning("Por favor, insira sua chave da OpenAI API para continuar.")
else:
    openai.api_key = openai_api_key

    uploaded_files = st.file_uploader("Faça upload de documentos (.pdf)", type=["pdf"], accept_multiple_files=True)
    if uploaded_files:
        st.write("✅ Documentos carregados com sucesso!")

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

        if len(documents_text) > 0:
            st.write("📝 **Prévia do texto extraído:**")
            st.code(documents_text[:500])

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

        user_input = st.text_input("Digite sua pergunta:")
        if user_input:
            try:
                st.write("🧠 Gerando resposta...")
                asyncio.run(gerar_resposta(user_input))
            except Exception as e:
                st.error(f"Erro ao gerar a resposta: {e}")

        # Estilo corrigido com um container com barra de rolagem
        st.markdown(
            """
            <style>
            .chat-container {
                height: 400px;  /* Altura fixa */
                overflow-y: auto;  /* Barra de rolagem automática */
                border: 1px solid #666;
                padding: 15px;
                border-radius: 10px;
                background-color: #f4f4f9;
            }
            .user-bubble {
                background-color: #ffd700;
                color: black;
                padding: 10px;
                border-radius: 12px;
                margin-bottom: 10px;
                text-align: left;
                max-width: 70%;
                align-self: flex-end;
            }
            .bot-bubble {
                background-color: #1c1c1c;
                color: white;
                padding: 10px;
                border-radius: 12px;
                margin-bottom: 10px;
                text-align: left;
                max-width: 70%;
                align-self: flex-start;
            }
            </style>
            <div class="chat-container">
            """,
            unsafe_allow_html=True
        )

        # Exibição das mensagens no chat com o container corrigido
        for message in st.session_state.history:
            if message["role"] == "user":
                st.markdown(f'<div class="user-bubble">{message["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="bot-bubble">{message["content"]}</div>', unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
