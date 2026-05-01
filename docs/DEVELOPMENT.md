# Development

## Local checks

Install the lightweight development tools:

```bash
python -m pip install -r requirements-dev.txt
```

Run the same checks as CI:

```bash
ruff check .
pytest -q
```

For the Home Assistant panel JavaScript, run a syntax check with Node.js when the panel changes:

```bash
node --check custom_components/ha_context_explorer_next/www/app.js
```

## Git on Windows

The repository uses `.gitattributes` to keep text files normalized as LF. On Windows, this repo-local configuration avoids repeated CRLF warnings:

```bash
git config core.autocrlf false
git config core.eol lf
```

If files were already checked out with CRLF, re-checkout the branch after changing the config or let Git normalize them on the next touched file.
