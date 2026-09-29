PROMPTS_POR_MODO = {
    "resumir": "Resuma o texto a seguir de forma concisa em tópicos:",
    "corrigir": "Corrija a gramática e melhore a clareza do texto a seguir:",
    "traduzir_en": "Traduza o texto a seguir para o inglês mantendo o tom natural:",
}

import os
MODELO_PADRAO = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
