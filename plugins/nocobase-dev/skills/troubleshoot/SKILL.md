---
name: troubleshoot
description: This skill should be used when the user encounters "NocoBase errors", "NocoBase not working", "NocoBase API failing", "debug NocoBase", "NocoBase connection issues", or needs to diagnose and fix common problems with the NocoBase API.
---

# Troubleshoot NocoBase

Diagnose and resolve common NocoBase API errors, connection failures, authentication problems, data issues, and performance bottlenecks.

## Quick Diagnostics

Run these four checks in order to isolate the problem category. Stop at the first failure.

### Step 1 -- Health Check

Verify the NocoBase instance is running and responding.

```bash
curl -s -o /dev/null -w "%{http_code}" "${NOCOBASE_URL}/api/app:getInfo"
```

**Expected:** HTTP 200. Any other code or a connection error means the instance is down or unreachable.

```bash
curl -s "${NOCOBASE_URL}/api/app:getInfo"
```

**Expected response:**

```json
{
  "data": {
    "version": "2.0.0",
    "lang": "en-US",
    "name": "nocobase"
  }
}
```

### Step 2 -- Authentication Test

Verify the API key is valid and the user is recognized.

```bash
curl -s -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/auth:check"
```

**Expected:** Returns user object with `id`, `nickname`, and `roles`. Failure here means the API key is invalid, expired, or missing.

### Step 3 -- List Collections

Verify read access to the data model.

```bash
curl -s -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/collections:list?page=1&pageSize=5"
```

**Expected:** Returns a paginated list with `data` array and `meta` object. A 403 means the API key role lacks collection permissions.

### Step 4 -- Check Version

Confirm the NocoBase version to rule out version-specific issues.

```bash
curl -s -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/app:getInfo" | grep -o '"version":"[^"]*"'
```

Record the version number for cross-referencing with known issues.

## Connection Errors

| Error | Likely Cause | Resolution |
|-------|-------------|------------|
| `ECONNREFUSED` | NocoBase service is not running or wrong port | Verify the service is up (`docker ps` or `systemctl status nocobase`). Check that the URL port matches the actual listening port. |
| `ETIMEDOUT` | Network path blocked or instance is unresponsive | Check firewall rules, security groups, and DNS. Test with `curl -v` to see where the connection stalls. If behind a load balancer, verify health checks pass. |
| `ENOTFOUND` | DNS resolution failed for the hostname | Verify the hostname resolves correctly with `nslookup` or `dig`. Check for typos in the URL. Ensure the domain DNS records exist. |
| SSL/TLS errors (`UNABLE_TO_VERIFY_LEAF_SIGNATURE`, `CERT_HAS_EXPIRED`, `DEPTH_ZERO_SELF_SIGNED_CERT`) | Certificate problem | For self-signed certs in development: use `curl -k` to bypass verification. For production: renew or replace the certificate. Check the full chain is served correctly. |
| `ECONNRESET` | Server dropped the connection mid-request | Often caused by a reverse proxy timeout or the NocoBase process restarting. Check Nginx/Caddy error logs. Increase proxy timeout if request takes long. |
| `502 Bad Gateway` | Reverse proxy cannot reach the NocoBase upstream | Verify the proxy upstream URL and port match the running NocoBase instance. Check NocoBase process logs for crashes. |

## Authentication Errors

### 401 Unauthorized -- Invalid Token

```json
{
  "errors": [{ "message": "Unauthorized" }]
}
```

**Causes and fixes:**

1. **Invalid API key** -- The token does not exist or was revoked. Regenerate in Admin Panel > Settings > API keys.
2. **Expired token** -- API keys can have expiration dates. Create a new key with a longer expiration (`"90d"` or `"never"`).
3. **Wrong token format** -- Ensure the header is exactly `Authorization: Bearer <token>` with a space after `Bearer`. Do not include quotes around the token.
4. **Token from wrong instance** -- API keys are instance-specific. Verify you are using the key from the correct NocoBase instance.

### 403 Forbidden -- Insufficient Permissions

```json
{
  "errors": [{ "message": "Forbidden" }]
}
```

**Causes and fixes:**

1. **Role lacks permission** -- The API key user's role does not have access to the requested resource. Check role configuration in Admin Panel > Roles & Permissions.
2. **Resource-level ACL** -- NocoBase has per-collection access control. The role may have general access but be blocked from a specific collection.
3. **Action not allowed** -- Some actions (destroy, update) may be restricted even if list/get are permitted. Check action-level permissions.

### Token Expired Mid-Session

If a previously working token stops working:

```bash
# Check if the token is still valid
curl -s -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/auth:check"
```

If this returns 401, the token has expired. Create a new API key:

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "Content-Type: application/json" \
  "${NOCOBASE_URL}/api/apiKeys:create" \
  -d '{"name": "Replacement Key", "expiresIn": "90d"}'
```

### Wrong X-Authenticator Header

When multiple authenticators are configured, sending the wrong `X-Authenticator` header causes auth failures even with a valid token:

```bash
# Check which authenticators are available
curl -s "${NOCOBASE_URL}/api/authenticators:publicList"
```

Use the correct authenticator name in the header:

```bash
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  -H "X-Authenticator: basic" \
  "${NOCOBASE_URL}/api/{resource}:{action}"
```

## Data Errors

### 422 Unprocessable Entity -- Validation Error

```json
{
  "errors": [{ "message": "Validation error: notNull Violation: orders.title cannot be null" }]
}
```

**Fixes:**

- Check required fields for the collection. List fields with `collections/{name}/fields:list`.
- Verify field types match the data being sent (e.g., sending a string to a number field).
- Check enum values for select/radio fields match the allowed options.
- For association fields, verify the referenced record exists.

### 409 Conflict -- Duplicate Entry

```json
{
  "errors": [{ "message": "Unique constraint violation" }]
}
```

**Fixes:**

- Check for unique constraints on the collection fields.
- Query existing records to find the conflicting value.
- Use `update` instead of `create` if the record already exists.

### 404 Not Found -- Resource Does Not Exist

```json
{
  "errors": [{ "message": "Not Found" }]
}
```

**Fixes:**

- Verify the collection name is correct (case-sensitive).
- Verify the record ID exists: `curl ... /api/{collection}:get?filterByTk={id}`.
- Check that the URL follows the `{resource}:{action}` pattern, not RESTful `/resource/id`.
- For association endpoints, verify both the source record and the association field name exist.

### 400 Bad Request -- Malformed Input

```json
{
  "errors": [{ "message": "Invalid JSON" }]
}
```

**Fixes:**

- Validate JSON syntax (missing commas, unquoted keys, trailing commas).
- Ensure `Content-Type: application/json` header is present for POST requests.
- For filter parameters in URLs, ensure JSON is properly URL-encoded. Use `curl -g` to disable globbing when passing JSON in query strings.
- Check that array parameters use the correct format: `?fields=[id,name]` or `?appends=[association]`.

## Workflow Errors

### Execution Failed

```bash
# Check recent failed executions
curl -s -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/executions:list?filter={\"status\":-1}&sort=[-createdAt]&page=1&pageSize=5"
```

**Common causes:**

1. **Node configuration invalid** -- A node references a field or collection that no longer exists. Get the execution details with `appends=jobs` to identify the failing node.
2. **Expression evaluation error** -- A `{{$context.data.fieldName}}` reference points to a non-existent field. Check the trigger collection's field names.
3. **External request failed** -- A request node failed to reach the target URL. Check the node's URL, headers, and timeout settings.

### Node Config Invalid

```bash
# Get execution details to find the failing node
curl -s -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/executions:get?filterByTk=1&appends=jobs"
```

Look at the `jobs` array. Each job has a `status` field (1 = resolved, -1 = failed). The failing job's `nodeId` identifies the problematic node.

```bash
# Inspect the failing node's configuration
curl -s -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/flow_nodes:get?filterByTk={nodeId}"
```

### Trigger Not Firing

If a workflow does not execute when expected:

1. **Check workflow is enabled:**

```bash
curl -s -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/workflows:get?filterByTk={workflowId}"
```

Verify `"enabled": true`.

2. **Check trigger condition:** The workflow's `config.condition` may filter out the record you created. Remove or broaden the condition to test.

3. **Check trigger mode:** For collection triggers, verify `config.mode` matches the operation (1 = create, 2 = update, 3 = create or update, 4 = delete).

4. **Check the collection name:** The `config.collection` must exactly match the collection's `name` (not `title`).

5. **Check for duplicate workflows:** Multiple workflows on the same collection may interfere. List all workflows filtering by collection name.

## UI Schema Errors

### UID Not Found

```json
{
  "errors": [{ "message": "Schema node not found" }]
}
```

The `x-uid` you are targeting does not exist. UIDs can change when schemas are regenerated.

**Fix:** Fetch the current page schema first:

```bash
curl -s -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/uiSchemas:getJsonSchema/{pageUid}"
```

Search the response for the correct `x-uid` of the component you want to modify.

### Invalid Schema Structure

When `uiSchemas:insert` or `uiSchemas:patch` fails:

- Verify the `type` field is one of: `void`, `object`, `array`, `string`, `number`, `boolean`.
- Ensure `x-component` matches a valid NocoBase component name (e.g., `Grid`, `Grid.Row`, `Grid.Col`, `Form`, `Table`, `Action`).
- Check that `properties` is an object (not an array).
- Verify nested schemas maintain proper parent-child component relationships.

### insertAdjacent Position Error

The `position` parameter must be one of: `beforeBegin`, `afterBegin`, `beforeEnd`, `afterEnd`.

- `beforeBegin` / `afterEnd` -- insert as a sibling (same parent).
- `afterBegin` / `beforeEnd` -- insert as a child.

Choose the correct position based on where you want the new component in the tree. Fetch the parent schema first to understand the hierarchy.

## Performance Issues

### Slow API Responses

**Add pagination** to all list queries. Never request all records without limits:

```bash
# BAD -- fetches everything
curl ... /api/orders:list

# GOOD -- paginated
curl ... /api/orders:list?page=1&pageSize=50
```

**Select only needed fields** to reduce payload size:

```bash
curl ... /api/orders:list?fields=[id,title,status]&page=1&pageSize=50
```

**Be selective with appends** -- only include associations you actually need:

```bash
# BAD -- loads all associations
curl ... /api/orders:list?appends=[customer,items,shipping,payments,history]

# GOOD -- only what you need
curl ... /api/orders:list?appends=[customer]&page=1&pageSize=50
```

### Request Timeouts

- Simplify complex filter expressions. Deeply nested `$and` / `$or` conditions with multiple field comparisons can be slow.
- Avoid sorting by non-indexed fields on large collections.
- For large data exports, use pagination rather than exporting everything at once.
- Increase the client-side timeout if the server responds slowly but correctly.

### Large Exports

For collections with thousands of records:

1. Export in batches using the `page` and `pageSize` parameters.
2. Limit columns in the export to reduce file size.
3. Run exports during low-traffic periods.
4. Consider using a database view for pre-aggregated data.

## NocoBase-Specific Diagnostics

### Check App Status

Get comprehensive application information including version, database type, and installed plugins.

```bash
curl -s -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/app:getInfo"
```

### List Installed Plugins

Verify which plugins are enabled and their versions.

```bash
curl -s -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/app:getPlugins"
```

Check that required plugins (workflow, localization, etc.) are enabled. Missing plugins cause 404 errors on their endpoints.

### Clear Cache

When the UI or API returns stale data, clear the application cache.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/app:clearCache"
```

Use after:
- Manual database changes outside the NocoBase API
- Plugin enable/disable operations
- UI schema modifications that do not reflect in the frontend
- Collection metadata changes that do not appear in the API

### Restart Application

If clearing cache does not resolve the issue, perform a full restart.

```bash
curl -X POST -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
  "${NOCOBASE_URL}/api/app:restart"
```

Wait 5-10 seconds after restart before making new requests. The application needs time to reinitialize.

## When to Escalate

These situations indicate deeper problems that may require direct server access or NocoBase support:

- **500 Internal Server Error** -- Server-side crash. Check application logs (`docker logs`, `pm2 logs`, or the log directory). Look for stack traces pointing to specific plugins or database operations.
- **Data corruption** -- Records with inconsistent relationships, orphaned association data, or records that exist in the database but not through the API. May require direct database inspection and repair.
- **Plugin conflicts** -- Two plugins modifying the same resource or hook. Disable plugins one by one to isolate the conflict. Check plugin compatibility with the current NocoBase version.
- **Database migration failures** -- Errors during `app:restart` after plugin changes. Check migration logs. May need to run migrations manually or revert the plugin change.
- **Memory/CPU exhaustion** -- Application becomes unresponsive under normal load. Check container resource limits, database connection pooling, and Node.js memory settings.
- **Persistent 502/503 after restart** -- The application fails to start. Check environment variables, database connectivity, and port bindings. Review startup logs for the root cause.

## Diagnostic Command Summary

| What to Check | Command |
|---------------|---------|
| Instance health | `GET /api/app:getInfo` |
| Auth validity | `GET /api/auth:check` |
| Collection access | `GET /api/collections:list?page=1&pageSize=5` |
| Failed executions | `GET /api/executions:list?filter={"status":-1}&sort=[-createdAt]` |
| Installed plugins | `GET /api/app:getPlugins` |
| App language | `GET /api/app:getLang` |
| Available actions | `GET /api/availableActions:list` |
| Clear cache | `POST /api/app:clearCache` |
| Restart app | `POST /api/app:restart` |
