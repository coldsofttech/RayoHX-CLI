# CLI security

How the `rayohx` command protects secrets and the machine it runs on. To report a vulnerability, see [SECURITY.md](../SECURITY.md). The protections of the download engine itself (redaction, input checks, credentials per host, working folder, file names, FFmpeg, untrusted media) are in the [core security notes](https://github.com/coldsofttech/RayoHX/blob/main/docs/security.md).

## Secrets you give it

- **Read them from a file.** `--header` and `--cookie` accept `@file`, which reads the entries from that file, one per line. The secret then never appears in your shell history or in the process list. Use this for tokens, cookies and `Authorization` headers.
- **Environment variables work too.** Most options can be set with a `RAYOHX_<NAME>` variable, such as `RAYOHX_PROXY`. Treat the variables of a shared shell or CI job like any other secret.
- **The settings file can hold them.** Its keys are option names, so it may contain headers, cookies or a proxy with credentials. Keep it private (permissions to your own account), and prefer `@file` for the secret values.
- **Credentials stay with their host.** Secret headers and cookies go only to the stream's own host and to hosts you list with `--credential-host`, including across redirects.

## What it shows and logs

- **Redaction.** Addresses (user info and the values of keys such as `token`, `sig` and `key`), `Authorization`, `Cookie` and proxy credentials are hidden in messages, errors and log lines, whether they go to the screen or to `--log-file`. The log file records everything down to debug detail, with secrets removed.
- **Errors are short.** A failure prints a message and, where useful, a hint. An unexpected error prints its type and message only.
- **Tracebacks only on request.** `--verbose` adds a traceback, and local variables are never shown, since they can hold secrets.
- **Result and messages are separate.** The saved path goes to stdout and messages go to stderr, so a pipe or a captured result never carries a secret that a message could have contained.
- **A typo in the settings file is an error.** A key that is not an option is refused with a "did you mean" hint, so a setting meant to protect you is never silently ignored.

## Connections

- **Certificates are checked.** `--insecure` turns TLS verification off and the library logs a warning each time it does. Prefer `--ca-bundle` with the right certificate authority.
- **Proxies are explicit.** A proxy is used only when you give `--proxy` (or `RAYOHX_PROXY`). `HTTPS_PROXY` and similar variables are read only with `--env-proxy`.
- **Client certificates.** `--client-cert` is for servers that require mutual TLS. Give the key password through `RAYOHX_CLIENT_KEY_PASSWORD` or a file, not on the command line.
- **Existing files are safe.** An output file is replaced only with `--overwrite`, and a download is written to a `.part` file and renamed when it is complete.

## What you install

- **PyPI releases are published without stored tokens.** `release.yml` uploads through PyPI trusted publishing, after a reviewer approves the `cli` environment. See [packaging and releasing](packaging.md#releasing-to-pypi).
- **The wheels hold compiled code only.** The release checks that a wheel has the compiled command line and no `.py` sources.
- **The Windows setup installs for one user by default.** Setup runs without administrator rights unless the user chooses "all users" (then UAC asks). The uninstaller removes only the files setup installed, so a folder chosen by hand keeps anything else in it, and it never touches settings or data in the user's profile.
- **PATH is edited by a script, not by the installer.** `installer/windows/path.ps1` adds or removes the install folder in the user (or machine) `PATH` in the registry, keeping the value type and `%VARIABLES%`, so a long `PATH` is never cut. Setup can skip it with the `/NOPATH` option.
- **The Linux packages are system-wide and own only their files.** They install under `/usr/lib/rayohx` with a link in `/usr/bin`, and never write to a user's home folder.
- **Releases carry checksums.** The setup, packages, archives and wheels are attached with `SHA256SUMS.txt`. Each setup and package is installed and removed in CI before it is attached.

## Not included

The command runs with your permissions and does not sandbox the media it downloads, so only download from sources you trust and keep FFmpeg, if you use it, up to date. See [Supply chain](#supply-chain) for how dependencies are checked.

## Supply chain

- **Locked dependencies.** `uv.lock` pins every dependency, and CI installs with `--locked`.
- **Weekly audit.** `audit.yml` checks the locked dependencies against known vulnerabilities every week and whenever `uv.lock` changes.
- **Dependency review.** `dependency-review.yml` checks the dependencies a pull request adds or changes.
- **Static analysis.** `security.yml` runs Semgrep on every pull request and every week, and sends the findings to code scanning.
- **Licenses.** The `lint` job in `ci.yml` fails when a dependency has a GPL license.
- **Updates.** Dependabot proposes updates to the Python dependencies and to the GitHub Actions, with a 7-day cooldown.
- **Secret scanning.** The pre-commit hooks run gitleaks before a commit.
