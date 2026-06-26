---
mode: interrogate
---
# Grill Me — Plan Interrogation

Interrogate the developer's plan before implementation begins. Surface hidden assumptions, unresolved decision branches, and missing requirements.

Based on Matt Pocock's Grill Me technique: https://agentpatterns.ai/agent-design/grill-me-technique/

## Instructions

### 1. Enter Interrogation Mode

You are NOT implementing anything. Your job is to challenge the plan relentlessly until every decision branch is resolved.

Core rules:
- **Ask one question at a time.** Do not send a list of questions.
- **Provide your recommended answer** for each question. The developer confirms, corrects, or expands.
- **If a question can be answered by exploring the codebase, explore the codebase instead of asking.** Only ask about genuine unknowns.

### 2. Walk the Decision Tree

For each aspect of the plan, probe:

**Scope & Boundaries:**
- What exactly is in scope? What is explicitly out of scope?
- Which repos are affected? Follow the dependency graph
- Are there cross-repo implications?

**Architecture & Design:**
- Where does this logic live? (Service layer, controller, new module?)
- Does similar functionality already exist in the codebase? (Search before asking.)
- What patterns should this follow? (Check existing implementations first.)
- For proyectate-back: Does this involve AI/LLM? If so — prompts in English, user-facing fields in Spanish.

**Data & State:**
- What data model changes are needed? (New fields, new collections, migrations?)
- What happens to existing data?
- Are there validation rules that need updating?

**Edge Cases & Failure Modes:**
- What happens when [X] fails? What's the fallback?
- What about empty states, null values, concurrent access?
- Are there rate limits, size limits, or performance concerns?

**Dependencies & Blockers:**
- Does this depend on other PRs being merged first?
- Are there secrets, env vars, or external services needed?
- Does the team need to do anything before or after?

**Acceptance Criteria:**
- How do we know this is done?
- What should a reviewer check?
- Are there specific test scenarios that must pass?

### 3. Resolve Branches Sequentially

- Tackle one decision branch at a time.
- Don't move to the next branch until the current one is resolved.
- If a branch reveals sub-branches, walk those too.
- Keep track of resolved decisions.

### 4. Produce the Output

Once all branches are resolved, compile the findings into a **structured spec** that includes:

```
## Initiative: [Name]

**Objective:** [One sentence]

**Repos involved:** [List]

**Resolved decisions:**
- [Decision 1]: [Resolution]
- [Decision 2]: [Resolution]
- ...

**Acceptance criteria:**
- [ ] [Criterion 1]
- [ ] [Criterion 2]
- ...

**Implementation order:**
1. [First change]
2. [Second change]

**Out of scope:**
- [Explicitly excluded items]

**Open questions (if any):**
- [Questions that couldn't be resolved in this session]
```

Send this as an attachment (.md file) to the developer for final confirmation before any implementation begins.

### 5. Transition to Implementation

After the developer confirms the spec:
- Save the spec as context for the implementation session
- If the developer wants to proceed immediately, switch to the appropriate playbook (`!feature`, `!bugfix`, `!refactor`, `!security`) based on the nature of the work
- If the developer wants a separate session, the spec serves as the input for that session

## When to Use This Playbook

- Before non-trivial features where wrong assumptions are expensive to reverse
- When the spec feels underspecified — you sense there are branches you haven't walked
- Before delegating a large initiative to unattended execution
- When a design review is needed but no human reviewer is available

## When NOT to Use This Playbook

- Single-step tasks or bug fixes with clear scope
- Reversible experiments where implementation reveals gaps faster than interrogation
- Changes fully constrained by external requirements (API contracts, regulatory rules)
