import os
from openai import AsyncOpenAI
from core.constants import MODELO_PADRAO

# Inicialização global do cliente (reutiliza conexões HTTP)
client = AsyncOpenAI(
    base_url=os.getenv("OPENAI_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY") or "dummy-key-for-local-tests",
)
async def processar_texto_llm(instrucao: str, texto: str) -> str:
    # Lê o esforço de raciocínio da variável de ambiente (ex: "low", "medium", "high")
    REASONING_EFFORT = os.getenv("REASONING_EFFORT")

    # Dicionário de argumentos base para a API
    kwargs = {
        "model": MODELO_PADRAO,
        "messages": [
            {"role": "system", "content": instrucao},
            {"role": "user", "content": texto},
        ],
        "temperature": 0.3,
        "timeout": 30.0,
    }
    # Adiciona o reasoning_effort apenas se a variável de ambiente estiver definida
    if REASONING_EFFORT:
        kwargs["REASONING_EFFORT"] = REASONING_EFFORT
        kwargs.pop("temperature", None)  # Evita o erro 400 nos modelos de raciocínio

    response = await client.chat.completions.create(**kwargs)
    return response.choices[0].message.content or ""
