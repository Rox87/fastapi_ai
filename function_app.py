import os
import json
import time
import logging
import threading
import azure.functions as func
from openai import AsyncOpenAI
from cachetools import TTLCache

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Prompts suportados
PROMPTS_POR_MODO = {
    "resumir": "Resuma o texto a seguir de forma concisa em tópicos:",
    "corrigir": "Corrija a gramática e melhore a clareza do texto a seguir:",
    "traduzir_en": "Traduza o texto a seguir para o inglês mantendo o tom natural:",
}

# Inicialização global do cliente (reutiliza conexões HTTP)
client = AsyncOpenAI(
    base_url=os.getenv("OPENAI_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY"),
)
MODELO_PADRAO = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Cache e trava para concorrência entre threads
rate_limit_cache = TTLCache(maxsize=10000, ttl=60)
rate_limit_lock = threading.Lock()


def verificar_rate_limit(user_id: str, max_reqs: int = 100, janela_segundos: int = 60) -> bool:
    """Verifica e atualiza o histórico de requisições de forma thread-safe."""
    agora = time.time()

    with rate_limit_lock:
        historico = rate_limit_cache.get(user_id, [])
        # Filtra timestamps anteriores à janela de 60s
        historico_recente = [t for t in historico if agora - t < janela_segundos]

        if len(historico_recente) >= max_reqs:
            return False

        historico_recente.append(agora)
        rate_limit_cache[user_id] = historico_recente
        return True


@app.route(route="processar", methods=["POST"])
async def processar(req: func.HttpRequest) -> func.HttpResponse:
    # 1. Identificação do usuário
    user_id = req.headers.get("X-User-ID")
    if not user_id:
        user_id = req.headers.get("x-forwarded-for", "anonymous").split(",")[0].strip()

    # 2. Rate limit
    if not verificar_rate_limit(user_id=user_id, max_reqs=100, janela_segundos=60):
        return func.HttpResponse(
            body=json.dumps({"erro": "Limite de 100 requisições por minuto excedido."}),
            status_code=429,
            mimetype="application/json",
            headers={"Retry-After": "60"}
        )

    # 3. Validação do JSON de entrada
    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            body=json.dumps({"erro": "Corpo da requisição deve ser um JSON válido."}),
            status_code=400,
            mimetype="application/json"
        )

    modo = req_body.get("modo")
    texto = req_body.get("texto")

    if not modo or not texto or not isinstance(texto, str):
        return func.HttpResponse(
            body=json.dumps({"erro": "Os campos 'modo' e 'texto' (string) são obrigatórios."}),
            status_code=400,
            mimetype="application/json"
        )

    instrucao = PROMPTS_POR_MODO.get(modo)
    if not instrucao:
        return func.HttpResponse(
            body=json.dumps({
                "erro": f"Modo '{modo}' não suportado.",
                "modos_disponiveis": list(PROMPTS_POR_MODO.keys())
            }),
            status_code=400,
            mimetype="application/json"
        )

    # 4. Chamada assíncrona ao LLM com Timeout explícito
    try:
        response = await client.chat.completions.create(
            model=MODELO_PADRAO,
            messages=[
                {"role": "system", "content": instrucao},
                {"role": "user", "content": texto},
            ],
            temperature=0.3,
            timeout=30.0,  # Evita que a Function fique travada indefinidamente
        )

        resultado = response.choices[0].message.content or ""

        return func.HttpResponse(
            body=json.dumps({"resultado": resultado, "modo": modo}),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logging.exception("Falha ao invocar a API de LLM.")
        return func.HttpResponse(
            body=json.dumps({"erro": "Falha na comunicação com o serviço de IA."}),
            status_code=502,  # Bad Gateway (erro do upstream, não do seu código)
            mimetype="application/json"
        )
