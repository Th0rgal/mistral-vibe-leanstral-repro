# Focused Leanstral 1.5 template bug report

**Subject:** Leanstral 1.5 official chat template breaks tool-result turns under llama.cpp

Hello Mistral team,

I tested `mistralai/Leanstral-1.5-119B-A6B` as the third-party
`Frosty40/Leanstral-1.5-119B-A6B-GGUF-NVFP4` quant under llama.cpp b9294 on a
DGX Spark. The GGUF did not contain `tokenizer.chat_template`, so llama.cpp initially selected an
incompatible ChatML-style fallback and returned textual pseudo-calls instead of structured
`message.tool_calls`.

Loading Mistral's official `chat_template.jinja` fixed the first turn: the local endpoint returned
native tool calls in 10/10 identical requests. However, every tool-result follow-up then failed with
HTTP 500:

```text
Error: Not enough arguments provided to macro 'render_content'
```

The official template defines:

```jinja
macro render_content(content, context_name, supported_types_desc, support_thinking, support_images)
```

but its `role == 'tool'` branch calls the macro without `support_thinking`. Adding
`support_thinking=false` to that call fixes the second and subsequent agent turns.

After that one-line correction and removal of legacy ChatML stops for Leanstral 1.5:

| Check | Result |
|---|---:|
| Externally exposed route, HTTP 200 | 10/10 |
| Native `message.tool_calls` | 10/10 |
| Textual pseudo-calls | 0/10 |
| Direct llama.cpp tool-result follow-ups | 3/3 HTTP 200 |
| Router tool-result follow-ups | 3/3 HTTP 200 |
| Stock Vibe three-task panel | 63 native calls and 63 executed results; zero pseudo-calls |

The repaired local lane reached the public verifier correctly on all three tasks but scored 0/3:
it made no proof edits and 12 of its tool results were errors, mostly because it targeted nonexistent
or fabricated filesystem paths despite receiving the exact isolated workspace path. All agent
processes exited normally and all artifacts were complete, so these are genuine model/agent failures,
not transport failures. The earlier hosted panel also scored 0/3 despite 60 native Vibe calls; its
concrete ERC-4626 and Uniswap proof attempts did not compile. I am treating proof quality separately
from the deterministic template defect, and I cannot attribute the local path behavior to NVFP4
without a same-runtime quantization ablation.

The full reproduction, exact request shape, scripts, prompts, tool counts, verifier errors, model provenance, and sanitized evidence are here:

- Repository: https://github.com/Th0rgal/mistral-vibe-leanstral-repro
- Comparison: https://github.com/Th0rgal/mistral-vibe-leanstral-repro/blob/main/COMPARISON.md
- Evidence: https://github.com/Th0rgal/mistral-vibe-leanstral-repro/tree/evidence/2026-07-19/artifacts

Could you please:

1. correct the missing `support_thinking` argument in the official template's tool-result branch;
2. publish the supported llama.cpp template/parser configuration alongside the existing vLLM recommendation;
3. make Vibe report raw tool sentinels as a template/parser mismatch instead of silently ending the turn; and
4. confirm whether the observed 300k–440k cumulative tokens per 12-turn built-in Vibe task is expected?

Thanks,
Thomas
