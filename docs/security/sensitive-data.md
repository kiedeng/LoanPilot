# Sensitive Data Checklist

Before pushing LoanPilot to a public repository, verify that the commit does not include:

- `.env` or environment-specific config files.
- SQLite databases such as `loanpilot.db`.
- Runtime logs.
- API keys, OAuth secrets, tokens, private keys, certificates, or passwords.
- Production `DATABASE_URL` values.
- Real customer names, identity documents, account numbers, loan contracts, or audit logs.

Recommended scan:

```bash
rg -n --hidden -g '!.git' -g '!node_modules' -g '!dist' \
  "(api[_-]?key|secret|token|password|DATABASE_URL|Bearer |ghp_|github_pat_|sk-|PRIVATE KEY)"
```

Only the demo defaults in `.env.example` should be committed.
