# runtime config - UNTESTED

from pydantic_ai.models.openrouter import OpenRouterModelSettings

settings = OpenRouterModelSettings(
    # --- ROUTING / PROVIDER ---
    openrouter_provider={
        "order": ["Anthropic", "openai"],   # provider order
        "allow_fallbacks": False,            # whether to fallback to other providers
        "require_parameters": True,          # only providers supporting all parameters
        "data_collection": "deny",           # "allow" | "deny" — whether the provider can collect data
        "only": ["Anthropic"],               # provider whitelist
        "ignore": ["azure"],                 # provider blacklist
        "quantizations": ["fp16", "bf16"],   # filter by quantization
        "sort": "price",                     # "price" | "throughput"
    },

    # --- COSTS / USAGE ---
    openrouter_usage={
        "include": True,   # return cost details in the response
    },

    # --- FALLBACK MODELS ---
    openrouter_fallback_models=[
        "anthropic/claude-haiku-4.5",
        "openai/gpt-4o-mini",
    ],

    # --- REASONING (for models that support it) ---
    openrouter_reasoning={
        "effort": "high",       # "xhigh"|"high"|"medium"|"low"|"minimal"|"none"
        # OR:
        # "max_tokens": 5000,   # Anthropic-style, do not combine with effort
        # "exclude": False,     # whether to hide reasoning tokens from the response
    },
)