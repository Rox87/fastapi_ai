import os
from openai import AsyncOpenAI
from core.constants import MODELO_PADRAO

# Inicialização global do cliente (reutiliza conexões HTTP)
client = AsyncOpenAI(
    base_url=os.getenv("OPENAI_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY") or "dummy-key-for-local-tests",
)

async def processar_texto_llm(instrucao: str, texto: str) -> str:
    response = await client.chat.completions.create(
        model=MODELO_PADRAO,
        messages=[
            {"role": "system", "content": instrucao},
            {"role": "user", "content": texto},
        ],
        temperature=0.3,
        timeout=30.0,  # Evita que a Function fique travada indefinidamente
    )
    return response.choices[0].message.content or ""
