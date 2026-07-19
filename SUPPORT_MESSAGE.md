# Message ready to send to Mistral support

**Subject:** Recurring HTTP 401 from API keys and Mistral Vibe (account `76a1b995-3912-40f0-8ab5-a25ce3341e1f`)

Hello Mistral team,

I repeatedly lose access to both Mistral Vibe and the direct API because an existing API key starts returning HTTP 401. Creating a new key restores access, but the problem later comes back.

Account and organization:

- Account ID: `76a1b995-3912-40f0-8ab5-a25ce3341e1f`
- Organization ID: `f1cd0a1c-0189-4136-b6b2-af4bec85a0bc`
- My Vibe subscription has ended.

I reproduced the current failure on 2026-07-19 UTC with two separately provisioned credentials:

1. `MISTRAL_API_KEY`
2. a credential associated with my former Vibe subscription, tested separately as the Bearer credential

Both produced the same result for every request below:

- `GET https://api.mistral.ai/v1/models`
- `POST /v1/chat/completions` with `mistral-small-latest`
- `POST /v1/chat/completions` with `leanstral-1-5`
- `POST /v1/chat/completions` with `labs-leanstral-1-5`

Result:

```text
HTTP 401
{"detail":"Unauthorized"}
```

Mistral Vibe 2.21.0 also exits with:

```text
Error: API error from mistral-testing (model: labs-leanstral-1-5): Invalid API key. Please check your API key and try again.
```

Its debug log records another 401 on:

```text
https://api.mistral.ai/v1/connectors/bootstrap?include_auth_actionable_connectors=true
```

The general model fails identically, so the captured failure occurs before Leanstral model resolution or Labs entitlement checks.

I published a minimal reproducer, timestamps, CF-Ray IDs, sanitized API artifacts, and Vibe logs here:

- Reproducer: https://github.com/Th0rgal/mistral-vibe-leanstral-repro
- Full report: https://github.com/Th0rgal/mistral-vibe-leanstral-repro/blob/main/REPORT.md
- Sanitized evidence: https://github.com/Th0rgal/mistral-vibe-leanstral-repro/tree/evidence/2026-07-19/artifacts

No credential value, prefix, hash, or length is included.

Could you please check:

1. key creation, revocation, expiry, and organization-membership events for this account;
2. why keys repeatedly begin returning 401 until I recreate them;
3. whether ending a Vibe subscription can invalidate API keys or organization access;
4. the intended credential flow for Vibe subscriptions, since Vibe 2.21.0 reads `MISTRAL_API_KEY`;
5. whether the `labs-leanstral-1-5` alias hardcoded by Vibe 2.21.0 is still supported now that the public model ID is `leanstral-1-5`.

Because this has been difficult to rely on, I moved the Lean workload to a self-hosted Leanstral 1.5 on a DGX Spark. It is an NVFP4 4-bit quant because the machine has 128 GB of unified memory. I would prefer to use the hosted endpoint if the recurring authentication problem can be fixed.

Thanks,
Thomas
