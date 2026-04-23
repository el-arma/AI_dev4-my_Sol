from dataclasses import dataclass, field
from pydantic_ai.usage import RunUsage

# (input_per_1M_tokens, output_per_1M_tokens) in USD
PRICING: dict[str, tuple[float, float]] = {
    "gemini-2.5-flash":   (0.15,  0.60),
    "gemini-2.5-pro":     (1.25, 10.00),
    "claude-sonnet-4-6":  (3.00, 15.00),
    "claude-haiku-4-5":   (0.80,  4.00),
    "gpt-4o":             (2.50, 10.00),
    "gpt-5.2":            (1.75, 14.00),
    "gpt-5.4":            (2.50, 15.00),
}


def _normalize(model: str) -> str:
    """Strip gateway/provider prefixes to match PRICING keys."""
    for key in PRICING:
        if model == key or model.endswith(f":{key}") or model.endswith(f"/{key}"):
            return key
    return model


@dataclass
class _ModelStats:
    input_tokens: int = 0
    output_tokens: int = 0
    requests: int = 0


@dataclass
class CostTracker:
    _stats: dict[str, _ModelStats] = field(default_factory=dict)

    def sum_tokkens(self, model: str, usage: RunUsage) -> None:

        key = _normalize(model)

        if key not in self._stats:
            self._stats[key] = _ModelStats()

        s = self._stats[key]

        s.input_tokens  += usage.input_tokens  or 0
        s.output_tokens += usage.output_tokens or 0
        s.requests      += usage.requests      or 0

    def summary(self) -> None:
        if not self._stats:
            print("CostTracker: no runs recorded.")
            return

        total_cost = 0.0
        rows: list[tuple[str, int, int, int, float]] = []

        for model, s in self._stats.items():
            price = PRICING.get(model)
            if price:
                cost = (s.input_tokens * price[0] + s.output_tokens * price[1]) / 1_000_000
            else:
                cost = float("nan")
            total_cost += cost if cost == cost else 0  # skip nan
            rows.append((model, s.input_tokens, s.output_tokens, s.requests, cost))

        col_w = max(len(r[0]) for r in rows) + 2
        header = f"{'Model':<{col_w}} {'Input tok':>12} {'Output tok':>12} {'Requests':>10} {'Cost (USD)':>12}"
        sep = "-" * (len(header) + 20)

        print()
        print("=== Cost Summary ===")
        print(sep)
        print(header)
        print(sep)
        for model, inp, out, req, cost in rows:
            cost_str = f"${cost:.6f}" if cost == cost else "unknown"
            print(f"{model:<{col_w}} {inp:>12,} {out:>12,} {req:>10,} {cost_str:>12}")
        print(sep)
        total_inp = sum(r[1] for r in rows)
        total_out = sum(r[2] for r in rows)
        total_req = sum(r[3] for r in rows)
        print(f"{'TOTAL':<{col_w}} {total_inp:>12,} {total_out:>12,} {total_req:>10,} ${total_cost:>11.6f}")
        print()
