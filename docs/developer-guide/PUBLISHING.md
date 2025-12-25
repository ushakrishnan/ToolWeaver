# Publish Docs

This repo uses MkDocs Material for the documentation site.

## Quick Publish (GitHub Pages)

- Ensure Python env and dependencies:
```bash
pip install -r requirements.txt
pip install mkdocs-material
```
- Build and serve locally:
```bash
mkdocs serve
```
- Publish to `gh-pages`:
```bash
mkdocs gh-deploy --no-history --message "Publish docs"
```

## GitHub Actions (CI)

Add a workflow to build and deploy on push to `main`:
```yaml
name: Deploy Docs
on:
  push:
    branches: [ main ]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install mkdocs-material
      - run: mkdocs build --strict
  deploy:
    needs: build
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install mkdocs-material
      - run: mkdocs gh-deploy --no-history --message "Publish docs"
```

## Tips
- Only `docs/` is published; `documentation/` is legacy/non-public.
- Set `site_url`, `repo_url`, and `edit_uri` in `mkdocs.yml`.
- Use `mkdocs build --strict` to catch broken links.
