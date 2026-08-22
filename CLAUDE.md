# Cycle Count — Project Instructions

This project follows the global `AGENTS.md` and `SECURITY_BASELINE.md`.
The notes below cover only what's specific to this repository.

## Version identifiers

Three places, in sync at `v1.3.1`:

- `package.json` — the `version` field
- `public/index.html` — the `<title>` and the `APP_VERSION` JS constant
- `api/index.py` — the `APP_VERSION` constant

## Local development

- `node server.js` — Express, serves `public/` and proxies `/api/*` to
  the Flask backend (port 3000 by default, via `PORT` env var)
- The Flask backend (`api/index.py`) has no `if __name__ == '__main__'`
  block. Run it locally with `flask --app api/index.py run --port 5000`
  rather than `python api/index.py`.

Out-of-tolerance count mismatches send a notification through Manhattan
Messenger, authenticated with the same `MANHATTAN_PASSWORD`/
`MANHATTAN_SECRET` credentials as the rest of the API — no separate
messenger credential is needed.
