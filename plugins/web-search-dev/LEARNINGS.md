# LEARNINGS.md — web-search-dev

Accumulated fixes and discoveries for the web-search-dev plugin.

## 2026-03-29 — multiple skills: remove deep-research plugin cross-references

**Problem:** Agent, README, and setup skill referenced the `deep-research` plugin, suggesting web-search-dev "complements" it. This made the plugin appear dependent on another plugin rather than standalone.
**Fix:** Removed all cross-references to deep-research plugin from agent system prompt, README, and setup skill. Kept Perplexity API `"deep-research"` preset references (those are legitimate API values, not plugin references).
**Root cause:** During initial creation, the plugin was designed with explicit differentiation from deep-research. The references were meant to help users choose between plugins, but they incorrectly positioned web-search-dev as subordinate.
**Severity:** Minor
