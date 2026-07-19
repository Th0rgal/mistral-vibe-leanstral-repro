# Mistral Vibe / Leanstral authentication and tool-calling reproductions

Minimal, sanitized reproductions for two separate observations:

1. **Authentication:** two independently provisioned credentials returned the same HTTP 401. A newly rotated `MISTRAL_API_KEY` then authenticated successfully, but the same provisioned key was back to the identical 401 less than 19 minutes later.
2. **Local Leanstral interoperability:** on three public Lean benchmark tasks, a self-hosted NVFP4 Leanstral 1.5 served by llama.cpp emits tool-shaped text but no native `tool_calls`; stock Vibe therefore executes no tool and exits after one assistant turn.

These must not be conflated. The second observation uses a 4-bit local quant and is **not evidence about Mistral's hosted Leanstral endpoint**.

## Identity for Mistral support

- Account ID: `76a1b995-3912-40f0-8ab5-a25ce3341e1f`
- Organization ID: `f1cd0a1c-0189-4136-b6b2-af4bec85a0bc`
- Vibe version: `2.21.0`
- Test date: `2026-07-19` UTC

No API key, subscription secret, token prefix, hash, or credential length is committed.

## Confirmed authentication result

### Newly rotated key: valid, then rejected within 19 minutes

| UTC | Probe | Result |
|---|---|---|
| `08:09:12` | `GET /v1/models` | 200; catalog returned |
| `08:09:12` | `mistral-small-latest` completion | 200; `OK` |
| `08:09:13` | `leanstral-1-5` | 400 `invalid_model` |
| `08:09:13` | `labs-leanstral-1-5` with greedy sampling | 400 `top_p must be 1 when using greedy sampling` — authentication and model resolution succeeded |
| `08:22` | hosted Leanstral Vibe/harness attempts | authenticated provider requests completed |
| `08:28:09` | correctly shaped Leanstral and tool probes | 401 `Unauthorized` |
| `08:28:17` | `/models`, general model, and both Leanstral IDs | 401 `Unauthorized` for all four |

The live catalog identifies `labs-leanstral-1-5` and `labs-leanstral-1-5-1` as aliases of the same hosted model, with function calling and reasoning enabled. `leanstral-1-5` is not a valid API model ID for this account.

This short valid-to-invalid transition is stronger evidence than the original static 401 snapshot: the rotated key was accepted, used for real provider calls, and then rejected without a local configuration change.

### Original simultaneous credential snapshot

| Credential source | `GET /v1/models` | `mistral-small-latest` | `leanstral-1-5` | `labs-leanstral-1-5` |
|---|---:|---:|---:|---:|
| `MISTRAL_API_KEY` | 401 | 401 | 401 | 401 |
| `MISTRAL_VIBE_SECRET` used as Bearer credential | 401 | 401 | 401 | 401 |

Every response body was exactly:

```json
{"detail":"Unauthorized"}
```

Mistral Vibe reports:

```text
Error: API error from mistral-testing (model: labs-leanstral-1-5): Invalid API key. Please check your API key and try again.
```

## Hosted-vs-NVFP4 comparison status

There is **no valid three-task hosted score yet**. Two hosted canaries authenticated before the key failed again:

- Vibe reached the hosted model, but the experiment's 50,000-token session cap was below Vibe's 53,276-token initialized session and stopped before tool execution. This attempt is `INFRA_INVALID`, not a model failure.
- The standalone harness completed five authenticated preflight requests (696 tokens) but its streaming protocol probe did not observe a tool call. A separate correctly shaped direct request did observe one native tool call. The corrected non-streaming retry could not run after the key returned to 401.

The corrected retry configuration is ready: a 200,000-token Vibe session budget and non-streaming standalone preflight. It requires a key that remains valid for the duration of the three-task run.

See [`REPORT.md`](REPORT.md) for timestamps, endpoints, CF-Ray identifiers, caveats, and the support request. [`SUPPORT_MESSAGE.md`](SUPPORT_MESSAGE.md) is a concise message ready to send to Mistral.

## Reproduce the direct API result

```bash
export MISTRAL_API_KEY='replace-locally; never commit'
python3 scripts/probe_api.py --credential-env MISTRAL_API_KEY --output /tmp/mistral-api-key.json

# Optional historical Vibe subscription credential check:
export MISTRAL_VIBE_SECRET='replace-locally; never commit'
python3 scripts/probe_api.py --credential-env MISTRAL_VIBE_SECRET --output /tmp/mistral-vibe-secret.json
```

The probe uses only Python's standard library and never writes the credential. It records a small allow-list of response headers and a sanitized body.

## Reproduce through Vibe 2.21.0

```bash
uv tool install --force 'mistral-vibe==2.21.0'
export MISTRAL_API_KEY='replace-locally; never commit'
./scripts/run_vibe_auth_repro.sh
```

The script uses an isolated `VIBE_HOME`, enables the built-in `lean` profile, disables telemetry/update checks, and writes only sanitized output under `reproduction-logs/`.

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
