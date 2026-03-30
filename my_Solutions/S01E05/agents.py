from dotenv import load_dotenv
from logger import log_agent_run
import logfire
# from mcp_server.mcp_calc_server import fastmcp_server
from pydantic_ai import Agent
from pydantic_ai.toolsets.fastmcp import FastMCPToolset
from suit import task_result_verification, wait_for_API


load_dotenv()

# ----------------------------------------------------------------------
# LOGFIRE SETUP
# ----------------------------------------------------------------------

# Configure Logfire:
logfire.configure(
    send_to_logfire='if-token-present' 
    )

logfire.instrument_pydantic_ai()

# ----------------------------------------------------------------------
# MCP TOOLSET
# ----------------------------------------------------------------------

# toolset = FastMCPToolset(fastmcp_server,
#                         tool_error_behavior="model_retry",
#                         max_retries=2)

Tools = [task_result_verification, wait_for_API]


# ----------------------------------------------------------------------
# MAIN AGENT
# ----------------------------------------------------------------------

system_prompt: str = "Check avialiable tools, use it if needed."

# "gemini-2.5-pro"
# "gateway/google-vertex:gemini-2.5-pro"
# "gateway/anthropic:claude-sonnet-4-6"

agent = Agent(
    model='gateway/google-vertex:gemini-2.5-pro',
    system_prompt=system_prompt,
    # toolsets=[toolset],
    tools=Tools, 
    retries=2 # number of retires of the tool
)

# ----------------------------------------------------------------------
# PROMPT
# ----------------------------------------------------------------------

def main():
    
    user_prompt = """
Musisz **aktywować trasę kolejową o nazwie X-01** za pomocą API, do którego nie mamy dokumentacji. Wiemy tylko, że API obsługuje akcję `help`, która zwraca jego własną dokumentację — od niej należy zacząć.

Do komunikacji używaj narzędzia: task_result_verification

Jeśli napotkasz na błąd: 'API rate limit exceeded.' koniecznie uruchom funckję: wait_for_API z odpowiednimi parametrami.

parametr tasj zawsze będzie "railway"

Przykład wywołania akcji `help`:

```json
{
  "task": "railway",
  "answer": {
    "action": "help"
  }
}
```
Możesz swobodnie nawadawaćstrukturę wartości "answer", tak jak trzeba

### Krok po kroku

1. **Zacznij od `help`** — wyślij akcję `help` i dokładnie przeczytaj odpowiedź. API jest samo-dokumentujące: odpowiedź opisuje wszystkie dostępne akcje, ich parametry i kolejność wywołań potrzebną do aktywacji trasy.
2. **Postępuj zgodnie z dokumentacją API** — nie zgaduj nazw akcji ani parametrów. Używaj dokładnie tych wartości, które zwróciło `help`.
3. **Szukaj flagi w odpowiedzi** — gdy API zwróci w treści odpowiedzi flagę w formacie `{FLG:...}`, zadanie jest ukończone.

### Wskazówki

- **API jest samo-dokumentujące** — nie szukaj dokumentacji gdzie indziej. Odpowiedź na `help` to wszystko, czego potrzebujesz.
- **Czytaj błędy uważnie** — jeśli akcja się nie powiedzie, komunikat błędu zwykle precyzyjnie wskazuje co poszło nie tak (zły parametr, zła kolejność akcji itp.).
- **503 to nie awaria** — błąd 503 jest częścią zadania. Kod musi go obsługiwać automatycznie przez retry z backoffem, inaczej zadanie nie da się ukończyć.
- **Limity zapytań są bardzo restrykcyjne** — to główne utrudnienie zadania. Monitoruj nagłówki po każdym żądaniu i bezwzględnie respektuj limity. Zbyt agresywne odpytywanie spowoduje długie blokady.

    """

    result = agent.run_sync(user_prompt)

    log_agent_run(result)

if __name__ == "__main__":

    main()