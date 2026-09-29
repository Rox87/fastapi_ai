import pytest
from core.llm import processar_texto_llm
from core.constants import MODELO_PADRAO

@pytest.mark.asyncio
async def test_processar_texto_llm_sucesso(mocker):
    # Mocking the client.chat.completions.create method
    mock_create = mocker.patch("core.llm.client.chat.completions.create")

    # Criar um objeto de resposta fake
    class FakeMessage:
        content = "Resposta simulada do LLM"

    class FakeChoice:
        message = FakeMessage()

    class FakeResponse:
        choices = [FakeChoice()]

    # Retorna resposta simulada como async
    async def fake_create(*args, **kwargs):
        return FakeResponse()
    mock_create.side_effect = fake_create

    instrucao = "Instrução"
    texto = "Texto para processar"

    resultado = await processar_texto_llm(instrucao, texto)

    assert resultado == "Resposta simulada do LLM"
    mock_create.assert_called_once_with(
        model=MODELO_PADRAO,
        messages=[
            {"role": "system", "content": instrucao},
            {"role": "user", "content": texto},
        ],
        temperature=0.3,
        timeout=30.0,
    )

@pytest.mark.asyncio
async def test_processar_texto_llm_excecao(mocker):
    mock_create = mocker.patch("core.llm.client.chat.completions.create")
    mock_create.side_effect = Exception("Erro na API")

    with pytest.raises(Exception, match="Erro na API"):
        await processar_texto_llm("Instrução", "Texto")
