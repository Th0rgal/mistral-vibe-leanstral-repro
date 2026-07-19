# Message ready to send to Mistral support

**Subject:** Recurring HTTP 401 from API keys and Mistral Vibe (account `76a1b995-3912-40f0-8ab5-a25ce3341e1f`)

Hello Mistral team,

I repeatedly lose access to both Mistral Vibe and the direct API because an existing API key starts returning HTTP 401. Creating a new key restores access, but the problem later comes back.

Account and organization:

- Account ID: `76a1b995-3912-40f0-8ab5-a25ce3341e1f`
- Organization ID: `f1cd0a1c-0189-4136-b6b2-af4bec85a0bc`
- My Vibe subscription has ended.

I now have a precise reproduction of the key becoming invalid. After rotating `MISTRAL_API_KEY` on 2026-07-19:

- `08:09:12Z`: `GET /v1/models` returned 200.
- `08:09:12Z`: `mistral-small-latest` returned a successful completion.
- `08:09:13Z`: `labs-leanstral-1-5` was authenticated and resolved; my deliberately greedy request reached normal model validation and returned `top_p must be 1 when using greedy sampling`.
- Around `08:22Z`: hosted Leanstral benchmark canaries completed authenticated provider requests.
- `08:28:09Z`: correctly shaped hosted Leanstral requests returned 401.
- `08:28:17Z`: `/models`, `mistral-small-latest`, and both Leanstral IDs all returned the same 401.

The last precisely timestamped successful Vibe session ended at `08:22:13.813777Z`; the first 401 carries the server timestamp `08:28:08Z`. Therefore the transition occurred within a 5-minute-54.186-second observation gap. The Vibe session accounted for 53,276 LLM tokens (52,214 prompt + 1,062 completion), and a subsequent five-request harness preflight accounted for another 696 tokens. The two durable canaries therefore account for at least 53,972 tokens before failure, plus earlier successful direct probes whose usage was not retained.

I cannot conclude that 53,972 tokens triggered the invalidation: there was no probe exactly at the transition, and the API returned a generic authentication 401 rather than a quota/rate-limit error. Please correlate the timestamps and CF-Ray IDs with your internal key event logs.

The final response was:

```text
HTTP 401
{"detail":"Unauthorized"}
```

This is a newly created key changing from valid to rejected in less than 19 minutes, without a local credential configuration change. The `/models` CF-Ray identifiers for the successful and rejected requests are respectively:

```text
a1d83e1c7adff78c-HEL
a1d85a0ef8cdf78c-HEL
```

The model catalog returned during the valid window listed `labs-leanstral-1-5` and `labs-leanstral-1-5-1` as aliases of the same model, with function calling and reasoning enabled. The unprefixed `leanstral-1-5` returned `invalid_model`.

Earlier the same day, I also reproduced the original failure with two separately provisioned credentials:

1. `MISTRAL_API_KEY`
2. a credential associated with my former Vibe subscription, tested separately as the Bearer credential

Both produced the same 401 result for every request below:

- `GET https://api.mistral.ai/v1/models`
- `POST /v1/chat/completions` with `mistral-small-latest`
- `POST /v1/chat/completions` with `leanstral-1-5`
- `POST /v1/chat/completions` with `labs-leanstral-1-5`

Mistral Vibe 2.21.0 also exits with:

```text
Error: API error from mistral-testing (model: labs-leanstral-1-5): Invalid API key. Please check your API key and try again.
```

Its debug log records another 401 on:

```text
https://api.mistral.ai/v1/connectors/bootstrap?include_auth_actionable_connectors=true
```

The general model failed identically, so those captured failures occurred before Leanstral model resolution or Labs entitlement checks.

I published a minimal reproducer, timestamps, CF-Ray IDs, sanitized API artifacts, and Vibe logs here:

- Reproducer: https://github.com/Th0rgal/mistral-vibe-leanstral-repro
- Full report: https://github.com/Th0rgal/mistral-vibe-leanstral-repro/blob/main/REPORT.md
- Sanitized evidence: https://github.com/Th0rgal/mistral-vibe-leanstral-repro/tree/evidence/2026-07-19/artifacts

No credential value, prefix, hash, or length is included.

Could you please check:

1. key creation, revocation, expiry, and organization-membership events for this account, especially between `08:09:12Z` and `08:28:09Z`;
2. why this newly rotated key changed from accepted to 401 in less than 19 minutes;
3. whether ending a Vibe subscription can invalidate API keys or organization access;
4. the intended credential flow for Vibe subscriptions, since Vibe 2.21.0 reads `MISTRAL_API_KEY`;
5. whether `labs-leanstral-1-5` is the intended API ID, since it was listed and resolved while `leanstral-1-5` returned `invalid_model`.

Because this has been difficult to rely on, I moved the Lean workload to a self-hosted Leanstral 1.5 on a DGX Spark. It is an NVFP4 4-bit quant because the machine has 128 GB of unified memory. I would prefer to use the hosted endpoint if the recurring authentication problem can be fixed.

Thanks,
Thomas
