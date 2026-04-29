# Security Policy

LoanPilot is a demonstration project and must not be treated as production banking software.

## Supported Versions

Security fixes are handled on the `main` branch unless a maintainer announces a release branch.

## Reporting a Vulnerability

Please do not disclose vulnerabilities publicly before maintainers have had a chance to assess them.

If you find a vulnerability, privately contact the repository owner through GitHub or a maintainer-provided contact channel. Include:

- Affected component.
- Steps to reproduce.
- Potential impact.
- Suggested mitigation, if available.

## Sensitive Data Rules

Never commit:

- API keys, tokens, passwords, private keys, certificates, or OAuth secrets.
- Production database URLs or banking credentials.
- Real customer PII, loan documents, account numbers, or audit logs.
- Local `.env` files, SQLite databases, or runtime logs.

## Production Warning

Before connecting LoanPilot to real financial systems, add a full security review covering authentication, authorization, audit logging, rate limiting, data retention, encryption, model governance, and regulatory controls.
