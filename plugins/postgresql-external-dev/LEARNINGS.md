# LEARNINGS.md — postgresql-external-dev

## 2026-04-14 — relations: One relation type per table pair

**Problem:** When designing a schema with both a direct FK column (`workflows.software_instance_id` -> `software_instances.id`) and a M2M junction table (`nc_m2m_workflows_software_instances`) between the same two tables, NocoDB and NocoBase auto-detect both relations independently, creating duplicate link columns in the UI.
**Fix:** Added "One Relation Per Table Pair" section to `relations/SKILL.md` with rule: use either a direct FK or a M2M junction between any two tables, never both. Added it as the first item in the Relation Checklist.
**Root cause:** The skill documented FK and M2M patterns separately without warning about combining them on the same table pair.
**Severity:** Major
