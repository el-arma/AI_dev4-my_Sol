from dotenv import load_dotenv
from logger import log_agent_run
import logfire
import os
from mcp_server.mcp_calc_server import fastmcp_server
from pydantic_ai import Agent, ImageUrl
from pydantic_ai.toolsets.fastmcp import FastMCPToolset
from schemas import Answer
from typing import Final


load_dotenv()

S01E04_PACKAGE_DOCUMENTATION_URL: Final[str] = os.environ["S01E04_PACKAGE_DOCUMENTATION_URL"]

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

toolset = FastMCPToolset(fastmcp_server,
                        tool_error_behavior="model_retry",
                        max_retries=2)

# ----------------------------------------------------------------------
# VISION AGENT
# ----------------------------------------------------------------------

vision_agent = Agent(
    model="gateway/anthropic:claude-sonnet-4-6"
    )

def analyze_img_from_url(url: str) -> str:
    """Analyze provided image from a given URL and return a detailed description for another LLM Agent"""
    
    res = vision_agent.run_sync([
        "Describe this image in detail",
        ImageUrl(url=url)
    ])

    return res.output

# ----------------------------------------------------------------------
# MAIN AGENT
# ----------------------------------------------------------------------

system_prompt: str = "You are a helpful assistant. Use provided tools."

# "gemini-2.5-pro"
# "gateway/google-vertex:gemini-2.5-pro"
# "gateway/anthropic:claude-sonnet-4-6"

agent = Agent(
    model="gateway/openai:gpt-5.2",
    system_prompt=system_prompt,
    toolsets=[toolset],
    tools=[analyze_img_from_url]
)

# ----------------------------------------------------------------------
# PROMPT
# ----------------------------------------------------------------------


def main():
    
#     user_prompt = f"""

#     Zapoznaj się z treścią zadania:
    
#     UŻYJ DOSTĘPNYNCH CI NARZĘDZI

# ## Zadanie

# Musisz przesłać do Centrali poprawnie wypełnioną deklarację transportu w Systemie Przesyłek Konduktorskich. W takim dokumencie niestety nie można wpisać, czego się tylko chce, ponieważ jest on weryfikowany zarówno przez ludzi, jak i przez automaty.

# Jako że dysponujemy zerowym budżetem, musisz tak spreparować dane, aby była to przesyłka darmowa lub opłacana przez sam "System". Transport będziemy realizować z Gdańska do Żarnowca.

# Udało nam się zdobyć fałszywy numer nadawcy (450202122), który powinien przejść kontrolę. Sama paczka waży mniej więcej 2,8 tony. Nie dodawaj proszę żadnych uwag specjalnych, bo zawsze się o to czepiają i potem weryfikują takie przesyłki ręcznie.

# Co do opisu zawartości, możesz wprost napisać, co to jest (to nasze kasety do reaktora). Nie będziemy tutaj ściemniać, bo przekierowujemy prawdziwą paczkę. A! Nie przejmuj się, że trasa, którą chcemy jechać jest zamknięta. Zajmiemy się tym później.

# Dokumentacja przesyłek znajduje się pod tym URL-em {S01E04_PACKAGE_DOCUMENTATION_URL}

# Dane niezbędne do nadania przesyłki:

# | Pole | Wartość |
# | --- | --- |
# | Nadawca (identyfikator) | `450202122` |
# | Punkt nadawczy | Gdańsk |
# | Punkt docelowy | Żarnowiec |
# | Waga | 2,8 tony (2800 kg) |
# | Budżet | 0 PP (przesyłka ma być darmowa lub finansowana przez System) |
# | Zawartość | kasety z paliwem do reaktora |
# | Uwagi specjalne | brak - nie dodawaj żadnych uwag |

# Gotową deklarację (cały tekst, sformatowany dokładnie jak wzór) geneurjsz z użyciem narzędzia `prepare_answer`

# Pole `declaration` to pełny tekst wypełnionej deklaracji - z zachowaniem formatowania, separatorów i kolejności pól dokładnie tak jak we wzorze z dokumentacji.

# ### Jak do tego podejść - krok po kroku

# 1. **Pobierz dokumentację** - zacznij od `index.md`. To główny plik dokumentacji, ale nie jedyny - zawiera odniesienia do wielu innych plików (załączniki, osobne pliki z danymi). Powinieneś pobrać i przeczytać wszystkie pliki które mogą być potrzebne do wypełnienia deklaracji.
# 2. **Uwaga: nie wszystkie pliki są tekstowe** - część dokumentacji może być dostarczona jako pliki graficzne. Takie pliki wymagają przetworzenia z użyciem modelu z możliwościami przetwarzania obrazów (vision).
# 3. **Znajdź wzór deklaracji** - w dokumentacji znajdziesz ze wzorem formularza. Wypełnij każde pole zgodnie z danymi przesyłki i regulaminem.
# 4. **Ustal prawidłowy kod trasy** - trasa Gdańsk - Żarnowiec wymaga sprawdzenia sieci połączeń i listy tras.
# 5. **Oblicz lub ustal opłatę** - regulamin SPK zawiera tabelę opłat. Opłata zależy od kategorii przesyłki, jej wagi i przebiegu trasy. Budżet wynosi 0 PP - zwróć uwagę, które kategorie przesyłek są finansowane przez System.
# 6. **Ustal prawidłową liczbę dodatkowych wagonów jeśli będą potrzebne (użyj odpowiedniego narzedzia jeśli trzeba)**
# 7. **Podaj treść deklaracji zgodnie z wymaganym formatem JSON**

# ### Wskazówki

# - **Czytaj całą dokumentację, nie tylko index.md** - regulamin SPK składa się z wielu plików. Odpowiedzi na pytania dotyczące kategorii, opłat, tras czy wzoru deklaracji mogą znajdować się w różnych załącznikach.
# - **Nie pomijaj plików graficznych** - dokumentacja zawiera co najmniej jeden plik w formacie graficznym. Dane w nim zawarte mogą być niezbędne do poprawnego wypełnienia deklaracji.
# - **Wzór deklaracji jest ścisły** - formatowanie musi być zachowane dokładnie tak jak we wzorze. Hub weryfikuje zarówno wartości, jak i format dokumentu.
# - **Skróty** - jeśli trafisz na skrót, którego nie rozumiesz, użyj dokumentacji żeby dowiedzieć się co on oznacza.

#     """


    user_prompt = f"""
You must complete a transport declaration in Systemie Przesyłek Konduktorskich (SPK).

USE AVAILABLE TOOLS.

## Task

Prepare a valid declaration that passes both human and automated verification.

Constraints:
- Budget = 0 PP → shipment must be free or funded by "System"
- Route: Gdańsk → Żarnowiec
- Sender ID: 450202122 (valid)
- Weight: 2800 kg
- Content: kasety z paliwem do reaktora
- Special notes: NONE (do not add anything)

## Documentation

Available at:
{S01E04_PACKAGE_DOCUMENTATION_URL}

## Required Output

Use tool `prepare_answer`

Return:
- `declaration`: full declaration text
- MUST exactly match template format (order, separators, structure)

## Steps

1. Fetch documentation (start from `index.md`, follow all links)
2. Read ALL relevant files (including images → use vision if needed)
3. Find declaration template
4. Determine correct route code (Gdańsk → Żarnowiec)
5. Determine cost → must be 0 PP (find valid category funded by System)
6. Determine required wagons if needed (use tools if necessary)
7. Fill declaration EXACTLY as template

## Rules

- Do NOT skip any documentation files
- Images may contain critical data
- Format must be exact (validated strictly)
- Do NOT invent values — use documentation
- Do NOT add special notes

"""

    result = agent.run_sync(user_prompt,
                            output_type=Answer)

    log_agent_run(result)

if __name__ == "__main__":

    main()