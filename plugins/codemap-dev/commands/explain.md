---
description: Step-by-step explanation of a file, function, or module with mini-diagram if appropriate
argument-hint: <file-path|module-path|symbol-name>
---

# Explain Code for Beginners

Provide a structured, beginner-friendly explanation. Target: $ARGUMENTS

## Instructions

1. Read all three codemap skills:
   - `${CLAUDE_PLUGIN_ROOT}/skills/codemap-explain/SKILL.md` — primary skill for explanation methodology
   - `${CLAUDE_PLUGIN_ROOT}/skills/codemap-diagram/SKILL.md` — for generating diagrams when components interact
   - `${CLAUDE_PLUGIN_ROOT}/skills/codemap-review/SKILL.md` — for noting code quality issues encountered during explanation

### Resolve Target

2. Parse `$ARGUMENTS` to determine scope:
   - If it's a file path → explain the entire file
   - If it's a directory → explain the module
   - If it's a symbol (function/class name) → Grep to find its definition, read surrounding context
   - If no argument → ask user what to explain

### Detect Scope and Adjust Depth

3. Based on scope, set explanation depth:
   - **Single function**: signature → purpose → parameters → return value → side effects
   - **Single file**: role in project → public API → key functions → connections to other files
   - **Module/directory**: purpose → file listing with roles → internal dependencies → entry points

### Apply 4-Layer Model

4. **Layer 1: Context** — what problem this solves, where it fits in the project, who calls it
5. **Layer 2: Data Flow** — what goes in, what comes out, what happens in between
6. **Layer 3: Details** — walk through key sections, explain non-obvious patterns, define terms
7. **Layer 4: Pitfalls** — edge cases, common mistakes when modifying, gotchas

### Code Quality Notes

8. While explaining, if you encounter code quality issues (from codemap-review skill), note them briefly — don't turn the explanation into a full review, but mention 1-2 important observations

### Mini-Diagram Decision

9. If 3+ components interact in the explanation:
   - Use the codemap-diagram skill to generate a diagram showing the interaction
   - Save to `docs/codemap/diagrams/` and provide preview URL

### Output

10. Present the explanation following the 4-layer structure
11. Include code snippets for key sections being explained
12. If a diagram was generated, include the file path and preview URL
13. End with: "Related files you might want to explore next: [list 2-3 connected files]"