---
name: codemap-explain
description: >
  This skill should be used when the user asks to "explain this code", "what does this file do", "how does this work",
  "walk me through this function", "explain this module", "what is this for",
  "help me understand this", or needs a beginner-friendly step-by-step explanation
  of code, files, functions, or modules. Also triggers when the user points at code
  and asks "why" or "how" questions.
---

# Code Explanation for Beginners

## Step 0: Execution Mode (MANDATORY)

Before doing ANY work, ask the user:

> "Want me to delegate this to the **architect-explainer** agent (guided explanation with diagrams), or proceed inline in this chat?"

- If user chooses agent → launch the **architect-explainer** agent with the target and context. STOP here — do not continue with the steps below.
- If user chooses inline → proceed with the methodology below.
- If user doesn't respond clearly → default to agent.

---

Explain code using the 4-layer model: Context, Data Flow, Details, Pitfalls. Adjust depth based on scope (file vs function vs module).

## Explanation Process

1. **Detect scope** — is the user asking about a file, function, module/directory, or symbol?
2. **Read the target** and its immediate dependencies (imports, related files)
3. **Apply the 4-layer model** at appropriate depth
4. **Decide on mini-diagram** — if 3+ components interact, generate a diagram using the `codemap-diagram` skill at `${CLAUDE_PLUGIN_ROOT}/skills/codemap-diagram/SKILL.md`

## The 4-Layer Explanation Model

### Layer 1: Context (always start here)

Answer: **What problem does this solve? Where does it fit in the project?**

- One sentence: what this code does in plain language
- Where it sits in the architecture (data layer? route handler? utility?)
- Who calls it / what triggers it (incoming request, cron job, user action, another module)
- What would break if this didn't exist

Example: "This file handles user authentication — login, registration, and logout. It's a Flask blueprint that gets called when users visit /login, /register, or /logout."

### Layer 2: Data Flow

Answer: **What goes in, what comes out, what happens in between?**

- Inputs: what data this code receives (parameters, request data, database queries)
- Processing: the main transformations, validations, or decisions
- Outputs: what it returns or produces (response, database write, side effect)
- Dependencies: what external services or modules it relies on

Example: "Login flow: form data (email, password) comes in → password is checked against hash in DB → if valid, Flask-Login creates a session → user is redirected to dashboard."

### Layer 3: Details

Answer: **How does each part work?**

- Walk through key sections of the code (not every line — focus on logic, not boilerplate)
- Explain non-obvious patterns or framework-specific conventions
- Define technical terms on first use
- Show connections: "this function is called by X on line Y in file Z"

### Layer 4: Pitfalls

Answer: **What can go wrong? What's non-obvious?**

- Edge cases the code handles (or doesn't)
- Common mistakes when modifying this code
- Framework gotchas relevant to this code
- Performance considerations if applicable
- Security implications if applicable

## Scope-Specific Adjustments

### For a single function
- Layer 1: 1-2 sentences
- Layer 2: parameter → return value trace
- Layer 3: line-by-line for key logic
- Layer 4: edge cases and error paths

### For a file
- Layer 1: file's role in the project
- Layer 2: list public API (exports, route handlers, model definitions)
- Layer 3: explain each key function/class
- Layer 4: common modification mistakes

### For a module/directory
- Layer 1: module's purpose and boundaries
- Layer 2: file listing with one-line role descriptions
- Layer 3: key files explained, internal dependency graph
- Layer 4: architectural decisions and their tradeoffs

## Mini-Diagram Decision

Generate a mini-diagram (via `codemap-diagram` skill) when:
- 3+ components interact in the explanation
- Data flows through multiple files/services
- The user is confused about how pieces connect
- A visual would save 200+ words of text

Do NOT generate a diagram for:
- Single-function explanations
- Simple CRUD with obvious flow
- When the user just wants a quick answer

## Tone Rules

- **Define terms on first use** — "Blueprint (Flask's way of organizing related routes into a module)"
- **Use concrete examples** — show actual values flowing through, not abstract descriptions
- **Relate to familiar concepts** — "like a Python dictionary, but persisted to disk"
- **Progressive complexity** — start simple, add nuance layer by layer
- **Honest about complexity** — "this part is genuinely tricky because..." is better than oversimplifying

## Error Handling

- **File not found** → ask the user to verify the path or provide the correct one
- **Symbol not found** → grep broader patterns, ask user for clarification if still not found
- **Module too large (>20 files)** → explain top-level structure first, offer to drill into submodules