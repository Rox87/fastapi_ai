import pytest
from core.rate_limit import verificar_rate_limit, rate_limit_cache

@pytest.fixture(autouse=True)
def clean_cache():
    rate_limit_cache.clear()

def test_verificar_rate_limit_sucesso():
    # Primeira requisicao deve passar
    assert verificar_rate_limit("user_1", max_reqs=1, janela_segundos=60) is True

def test_verificar_rate_limit_excedido():
    # Passa na primeira
    assert verificar_rate_limit("user_2", max_reqs=1, janela_segundos=60) is True
    # Falha na segunda porque o max_reqs é 1
    assert verificar_rate_limit("user_2", max_reqs=1, janela_segundos=60) is False

def test_verificar_rate_limit_janela_passou(mocker):
    # Simular o tempo passando para janela de 10s
    mock_time = mocker.patch("core.rate_limit.time.time")

    mock_time.return_value = 1000.0
    assert verificar_rate_limit("user_3", max_reqs=1, janela_segundos=10) is True

    # Ainda dentro da janela
    mock_time.return_value = 1005.0
    assert verificar_rate_limit("user_3", max_reqs=1, janela_segundos=10) is False

    # Fora da janela
    mock_time.return_value = 1015.0
    assert verificar_rate_limit("user_3", max_reqs=1, janela_segundos=10) is True
