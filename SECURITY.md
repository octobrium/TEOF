# Security Policy

TEOF treats prompt injection, private-data leakage, unsafe automation, and supply-chain changes as security issues.

## Report A Concern

Open a GitHub issue if the concern can be described publicly without exposing secrets or private data. If the report requires sensitive details, contact the repository owner privately before posting.

## Security-Relevant Changes

The following changes require extra review:

- executable scripts or tools
- dependencies
- GitHub Actions
- agent instructions
- prompt templates
- migrations
- private-sync behavior
- anything that can read or write user data

## Private Data

Do not include real private memory, credentials, tokens, medical records, financial records, email contents, message exports, or relationship records in this repository.

Use synthetic examples and clearly mark them as synthetic.

## Prompt Injection

Public repo content should be treated as untrusted input by private TEOF instances until reviewed. No public file may require a private instance or agent to reveal secrets, override local authority, execute code without approval, or mutate private state automatically.

If a public contribution attempts to bypass these limits, treat it as malicious or unsafe even if it is phrased as helpful automation.
