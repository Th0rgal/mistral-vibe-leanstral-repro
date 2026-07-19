# Leanstral 1.5 tool calling: hosted API vs local NVFP4

Minimal, sanitized reproduction of two related behaviors:

1. **Protocol interoperability:** the hosted Mistral API returns structured native `tool_calls`, while the tested NVFP4 Leanstral 1.5 under llama.cpp returns empty responses or raw tool sentinel text in assistant `content`.
2. **Agent outcome:** hosted Leanstral executes multi-turn tool loops through Vibe and Lean MCP, but still scores 0/3 on the frozen Lean panel. The local NVFP4 route also scores 0/3 and makes less progress because stock Vibe cannot execute its textual pseudo-calls.

Start with [`COMPARISON.md`](COMPARISON.md). It contains the exact request shape, 10-attempt direct probe, three-task results, proof attempts, verifier errors, interpretation, and questions for Mistral.

Versions and provenance:

- Hosted model: `labs-leanstral-1-5`
- Local base: `mistralai/Leanstral-1.5-119B-A6B`
- Local quant: `Frosty40/Leanstral-1.5-119B-A6B-GGUF-NVFP4`
- Local runtime: llama.cpp / GGUF NVFP4 4-bit
- Vibe: `2.21.0`
- Benchmark: `lfglabs-dev/ethereum-verification-benchmark@2b27270b66a1fc248e4ff594ba323698648ef02c`
- Lean: `4.24.0`; `lean-lsp-mcp`: `0.28.0`

No API key, subscription secret, token prefix, hash, credential length, private endpoint, or private filesystem identity is committed.

## Hosted-vs-NVFP4 comparison status

The complete three-task comparison ran after a second key rotation. Both hosted and self-hosted lanes scored 0/3, but their behavior differed substantially:

| Lane | Score | Native/executed tools | Files changed or submitted | Tokens |
|---|---:|---:|---:|---:|
| Hosted Leanstral + Vibe 2.21.0 | 0/3 | 60 / 60 | 1/3 | 1,201,624 |
| NVFP4 llama.cpp + Vibe 2.21.0 | 0/3 | 0 / 0 | 0/3 | 9,586 |
| Hosted Leanstral standalone | 0/3 | 13 Lean MCP calls | 1/3 | 196,415 |
| NVFP4 standalone JSON fallback | 0/3 | 6 Lean MCP calls | 0/3 | 74,748 |

Hosted Leanstral's native Mistral tool protocol works: it executed multi-turn tool loops, while the NVFP4 llama.cpp route emitted only textual pseudo-calls under stock Vibe. Hosted Leanstral produced two concrete proof attempts, but neither compiled: an ERC-4626 `grind` attempt left an arithmetic goal, and a Uniswap `simp only [grind_norm]; exact hK` attempt hit Lean's recursion-depth limit.

See [`COMPARISON.md`](COMPARISON.md) for the detailed evidence. [`SUPPORT_MESSAGE.md`](SUPPORT_MESSAGE.md) is a concise message ready to send to Mistral.

## Reproduce the tool-protocol difference

```bash
export MISTRAL_API_KEY='replace-locally; never commit'
python3 scripts/probe_tool_calling.py \
  --base-url https://api.mistral.ai/v1 \
  --endpoint-label mistral-api \
  --api-key-env MISTRAL_API_KEY \
  --model labs-leanstral-1-5 \
  --attempts 10 \
  --output /tmp/tool-probe-hosted.json
```

The probe uses only Python's standard library, records no credential or private endpoint, and emits a normalized artifact. Run the same command against any local OpenAI-compatible endpoint using `--base-url-env`, its API-key environment variable, and its exposed model ID.

## Three public Lean task examples

The examples are pinned to [`lfglabs-dev/ethereum-verification-benchmark`](https://github.com/lfglabs-dev/ethereum-verification-benchmark) commit `2b27270b66a1fc248e4ff594ba323698648ef02c`:

- `1inch/xycswap_curve_safety/quote_exact_in_curve_safety`
- `openzeppelin/erc4626_virtual_offset_deposit/deposit_redeem_round_trip_bound`
- `uniswap_v2/pair_fee_adjusted_swap/swap_enforces_fee_adjusted_invariant`

Prepare isolated worktrees:

```bash
python3 scripts/prepare_benchmark_workspaces.py
```

Then, once hosted authentication works:

```bash
./scripts/run_vibe_task.sh 1inch
./scripts/run_vibe_task.sh erc4626
./scripts/run_vibe_task.sh uniswap-v2
```

The exact prompts and sanitized observed model messages are under `examples/`. Full sanitized evidence is published on branch [`evidence/2026-07-19`](https://github.com/Th0rgal/mistral-vibe-leanstral-repro/tree/evidence/2026-07-19/artifacts).

## Local model used for the interoperability traces

- Base: [`mistralai/Leanstral-1.5-119B-A6B`](https://huggingface.co/mistralai/Leanstral-1.5-119B-A6B)
- Runtime quant: [`Frosty40/Leanstral-1.5-119B-A6B-GGUF-NVFP4`](https://huggingface.co/Frosty40/Leanstral-1.5-119B-A6B-GGUF-NVFP4)
- Format: GGUF, NVFP4 4-bit, 67,135,119,264-byte local file
- Runtime: llama.cpp, context 131,072, one parallel slot

The public model card recommends vLLM with `--tool-call-parser mistral` and `--enable-auto-tool-choice`. That is not the runtime used for these local traces, so quantization and tool-template handling are explicit confounders.
