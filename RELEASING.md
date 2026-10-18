# Releasing wowhandy

Releases are built by GitHub Actions (`.github/workflows/release.yml`):

- **Tag `vX.Y.Z` pushed** → tests, build sdist + wheel + `wowhandy.pyz`, publish
  to **PyPI**, then create a **GitHub release** with all files attached
  (`releases/latest/download/wowhandy.pyz` always points to the newest file).
- **"Run workflow" by hand** (Actions tab) → the same build, published to
  **TestPyPI** only – a rehearsal.

No passwords or tokens are stored anywhere: PyPI and TestPyPI trust this
repository through *trusted publishing* (OpenID Connect).

## One-time setup

1. **GitHub environments** (repository → Settings → Environments): create
   `pypi` and `testpypi`. Optionally require your approval for `pypi`.
2. **TestPyPI** (https://test.pypi.org, separate account from PyPI): Account →
   Publishing → *Add a new pending publisher*:
   - PyPI project name: `wowhandy`
   - Owner: `unoctanium`, repository: `wowhandy`
   - Workflow name: `release.yml`
   - Environment name: `testpypi`
3. **PyPI** (https://pypi.org): the same as above with environment `pypi`.

A *pending* publisher reserves nothing; the project is created by the first
successful upload.

## Making a release

1. Update the version in `src/wowhandy/__init__.py` (single source of truth;
   `pyproject.toml` reads it).
2. Note user-visible changes in `STATUS.md` (and the README if needed).
3. Run the tests: `.venv/bin/pytest`
4. Commit, then tag and push:

   ```sh
   git tag v0.1.0
   git push origin main v0.1.0
   ```

5. Watch the Actions tab. The workflow refuses to publish if the tag does not
   match the package version.

## Things to know

- **A version number can be uploaded to PyPI only once** – even after deleting
  a release. If something went wrong, bump the version (e.g. 0.1.1).
- The same applies to TestPyPI: rehearse with a version you will not need, or
  accept that the rehearsal "uses up" that number there (TestPyPI only).
- The single file needs Python ≥ 3.11 on the user's machine; the package has no
  dependencies.
