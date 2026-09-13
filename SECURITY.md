# Security Policy

## Reporting a vulnerability

Please **do not** open a public issue for security problems.

Report privately through either channel:

- **GitHub private vulnerability reporting** — on this repository, go to
  **Security → Report a vulnerability**.
- **Email** — security@obilabs.dev

Please include what you found, how to reproduce it, and the version or commit affected.
We aim to acknowledge reports within a few business days and will keep you updated while
we work on a fix. We are happy to credit reporters once a fix ships, unless you prefer
to stay anonymous.

## Scope

Rubric is a parser, a CLI, and a static browser playground. Relevant reports include,
for example: a crafted question file or manifest that causes code execution, path
traversal outside a bundle, or script injection in the playground when rendering a bank.

The optional authoring scripts in `scripts/` call third-party model APIs with keys you
supply; keep those keys in your environment or a local `.env` file (gitignored), never in
a committed file.

## Supported versions

Rubric is pre-1.0. Security fixes land on `main` and in the next release.
