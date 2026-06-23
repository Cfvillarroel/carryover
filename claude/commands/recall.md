---
description: Recall what carryover already knows about a topic
---

Recall stored knowledge for the user. Run via Bash:

```bash
bash ~/.carryover/recall.sh $ARGUMENTS
```

Present the matches clearly (grouped by repo if helpful). If `$ARGUMENTS` is empty, ask the
user what they want to recall. By default it searches only the current repo's memories; pass
`--all` as the first argument to search every repo. This is a fast keyword lookup over the
knowledge store; for the full live view use the `co-dash` dashboard.
