---
description: Add a new memory from text
allowed-tools: ["add_memories"]
argument-hint: "<text to remember>" [--user <user_id>]
---

# Add Memory

Store new information as a memory in Mem0.

## Process

1. **Parse the input text** into messages format:
   ```
   add_memories({
     messages: [{"role": "user", "content": "<text>"}],
     user_id: "<user_id if provided>",
     infer: true
   })
   ```

2. **Display result** with the created memory ID.

3. **Verify storage** (optional):
   ```
   search_memories({ query: "<text snippet>", user_id: "<user_id>" })
   ```

## Example Usage
```
/add-memory The project uses PostgreSQL 15 with pgvector extension
/add-memory Meeting notes: decided to migrate to microservices --user project-alpha
```
