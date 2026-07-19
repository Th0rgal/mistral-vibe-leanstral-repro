# Artifact sanitization

- Credential values, prefixes, suffixes, hashes, and lengths were removed.
- Only response headers useful for support correlation were retained.
- Absolute local workspace and home paths in model traces were replaced with descriptive placeholders.
- Account and organization IDs remain because the account owner explicitly requested support correlation.
- The self-hosted traces retain the user prompt, exact assistant content apart from path normalization, `tool_calls: null`, counters, and verifier outcome.
