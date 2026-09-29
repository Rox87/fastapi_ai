import time
import threading
from cachetools import TTLCache

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
