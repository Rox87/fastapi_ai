import pytest
import json
import azure.functions as func

from function_app import processar

class DummyHttpRequest:
    def __init__(self, json_body, headers=None):
        self._json_body = json_body
        self.headers = headers or {}

    def get_json(self):
        if self._json_body is ValueError:
            raise ValueError()
        return self._json_body

@pytest.mark.asyncio
async def test_processar_sucesso(mocker):
    # Mock das dependências no core
    mocker.patch("function_app.verificar_rate_limit", return_value=True)
    mocker.patch("function_app.processar_texto_llm", return_value="Resumo final.")

    req = DummyHttpRequest(
        json_body={"modo": "resumir", "texto": "Um texto qualquer"},
        headers={"X-User-ID": "test_user"}
    )

    # Chama o endpoint
    res = await processar(req)

    assert res.status_code == 200
    body = json.loads(res.get_body())
    assert body["resultado"] == "Resumo final."
    assert body["modo"] == "resumir"

@pytest.mark.asyncio
async def test_processar_rate_limit_excedido(mocker):
    mocker.patch("function_app.verificar_rate_limit", return_value=False)

    req = DummyHttpRequest(
        json_body={"modo": "resumir", "texto": "Um texto qualquer"},
        headers={"X-User-ID": "test_user"}
    )

    res = await processar(req)

    assert res.status_code == 429
    body = json.loads(res.get_body())
    assert "excedido" in body["erro"]

@pytest.mark.asyncio
async def test_processar_json_invalido():
    req = DummyHttpRequest(json_body=ValueError)

    res = await processar(req)

    assert res.status_code == 400
    body = json.loads(res.get_body())
    assert "JSON válido" in body["erro"]

@pytest.mark.asyncio
async def test_processar_campos_obrigatorios():
    req = DummyHttpRequest(json_body={"modo": "resumir"}) # Sem 'texto'

    res = await processar(req)

    assert res.status_code == 400
    body = json.loads(res.get_body())
    assert "obrigatórios" in body["erro"]

@pytest.mark.asyncio
async def test_processar_modo_nao_suportado():
    req = DummyHttpRequest(json_body={"modo": "invalido", "texto": "Um texto qualquer"})

    res = await processar(req)

    assert res.status_code == 400
    body = json.loads(res.get_body())
    assert "não suportado" in body["erro"]

@pytest.mark.asyncio
async def test_processar_falha_llm(mocker):
    mocker.patch("function_app.verificar_rate_limit", return_value=True)
    mocker.patch("function_app.processar_texto_llm", side_effect=Exception("Erro simulado"))

    req = DummyHttpRequest(
        json_body={"modo": "resumir", "texto": "Um texto qualquer"}
    )

    res = await processar(req)

    assert res.status_code == 502
    body = json.loads(res.get_body())
    assert "Falha na comunicação" in body["erro"]
