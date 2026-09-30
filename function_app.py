import os
import json
import logging
import azure.functions as func

from core.constants import PROMPTS_POR_MODO
from core.rate_limit import verificar_rate_limit
from core.llm import processar_texto_llm

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="processar", methods=["POST"])
async def processar(req: func.HttpRequest) -> func.HttpResponse:
    # 1. Identificação do usuário
    user_id = req.headers.get("X-User-ID")
    if not user_id:
        user_id = req.headers.get("x-forwarded-for", "anonymous").split(",")[0].strip()

    # 2. Rate limit
    if not verificar_rate_limit(user_id=user_id, max_reqs=60, janela_segundos=60):
        return func.HttpResponse(
            body=json.dumps({"status":"error","erro": "Limite de 60 requisições por minuto excedido."}),
            status_code=429,
            mimetype="application/json",
            headers={"Retry-After": "60"}
        )

    # 3. Validação do JSON de entrada
    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            body=json.dumps({"status":"error","erro": "Corpo da requisição deve ser um JSON válido."}),
            status_code=400,
            mimetype="application/json"
        )

    modo = req_body.get("modo")
    texto = req_body.get("texto")

    if not modo or not texto or not isinstance(texto, str):
        return func.HttpResponse(
            body=json.dumps({"status":"error","erro": "Os campos 'modo' e 'texto' (string) são obrigatórios."}),
            status_code=400,
            mimetype="application/json"
        )

    instrucao = PROMPTS_POR_MODO.get(modo)
    if not instrucao:
        return func.HttpResponse(
            body=json.dumps({
                "status":"error",
                "erro": f"Modo '{modo}' não suportado.",
                "modos_disponiveis": list(PROMPTS_POR_MODO.keys())
            }),
            status_code=400,
            mimetype="application/json"
        )

    # 4. Chamada assíncrona ao LLM com Timeout explícito
    try:
        resultado = await processar_texto_llm(instrucao, texto)

        return func.HttpResponse(
            body=json.dumps({"status":"sucesso","resultado": resultado}),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logging.exception("Falha ao invocar a API de LLM.")
        return func.HttpResponse(
            body=json.dumps({"status":"error","erro": "Falha na comunicação com o serviço de IA."}),
            status_code=502,  # Bad Gateway (erro do upstream, não do seu código)
            mimetype="application/json"
        )
