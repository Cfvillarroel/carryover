---
description: Enable carryover's auto-wiki in the current repo
---

Enable the auto-wiki in the current repository. Run via Bash:

```bash
bash ~/.headroom/install-wiki.sh "$(git rev-parse --show-toplevel)"
```

Then briefly tell the user what it set up: a `pre-push` hook that, on push to master/main,
regenerates the `wiki/` folder (Home, Architecture, Flows with mermaid, Changelog) using
`claude -p`; and that the repo is registered so it shows up in `co-dash`.
