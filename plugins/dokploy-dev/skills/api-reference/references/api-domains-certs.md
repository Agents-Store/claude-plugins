# API Reference: Domains, Certificates, Security, Redirects, Ports

## Contents
- [Domain (9 endpoints)](#domain-9-endpoints)
- [Certificates (4 endpoints)](#certificates-4-endpoints)
- [Security (4 endpoints)](#security-4-endpoints)
- [Redirects (4 endpoints)](#redirects-4-endpoints)
- [Port (4 endpoints)](#port-4-endpoints)

## Domain (9 endpoints)

Domains map hostnames to applications and compose services via Traefik.

| Method | Path | operationId | Description |
|--------|------|-------------|-------------|
| GET | `/domain.byApplicationId` | domain.byApplicationId | List domains for an application |
| GET | `/domain.byComposeId` | domain.byComposeId | List domains for a compose service |
| GET | `/domain.one` | domain.one | Get a single domain by ID |
| POST | `/domain.create` | domain.create | Create a new domain mapping |
| POST | `/domain.update` | domain.update | Update domain configuration |
| POST | `/domain.delete` | domain.delete | Remove a domain mapping |
| POST | `/domain.validateDomain` | domain.validateDomain | Check if a domain is valid and resolvable |
| POST | `/domain.generateDomain` | domain.generateDomain | Auto-generate a subdomain (traefik.me) |
| GET | `/domain.canGenerateTraefikMeDomains` | domain.canGenerateTraefikMeDomains | Check if traefik.me auto-domains are available |

### Key parameters

**domain.create**
```json
{
  "host": "string (required — e.g. app.example.com)",
  "path": "string (default: /)",
  "port": "number (default: 80 — container port to route to)",
  "https": "boolean (default: true)",
  "certificateType": "letsencrypt | none (default: letsencrypt)",
  "applicationId": "string (one of applicationId or composeId required)",
  "composeId": "string (one of applicationId or composeId required)",
  "serviceName": "string (required for compose — which service in the compose file)"
}
```

**domain.update**
```json
{
  "domainId": "string (required)",
  "host": "string",
  "path": "string",
  "port": "number",
  "https": "boolean",
  "certificateType": "string"
}
```

**domain.byApplicationId**
- Query: `applicationId` (required)

**domain.byComposeId**
- Query: `composeId` (required)

---

## Certificates (4 endpoints)

Manage SSL/TLS certificates for custom domains.

| Method | Path | operationId | Description |
|--------|------|-------------|-------------|
| GET | `/certificates.all` | certificates.all | List all certificates |
| GET | `/certificates.one` | certificates.one | Get a single certificate |
| POST | `/certificates.create` | certificates.create | Upload or create a certificate |
| POST | `/certificates.remove` | certificates.remove | Remove a certificate |

### Key parameters

**certificates.create**
```json
{
  "name": "string (required)",
  "certificateData": "string (PEM certificate content)",
  "privateKey": "string (PEM private key content)",
  "autoRenew": "boolean"
}
```

---

## Security (4 endpoints)

HTTP basic auth rules applied to domains.

| Method | Path | operationId | Description |
|--------|------|-------------|-------------|
| GET | `/security.one` | security.one | Get security config for a resource |
| POST | `/security.create` | security.create | Add basic auth to a domain |
| POST | `/security.delete` | security.delete | Remove basic auth |
| POST | `/security.update` | security.update | Update basic auth credentials |

### Key parameters

**security.create**
```json
{
  "username": "string (required)",
  "password": "string (required)",
  "applicationId": "string (target resource)"
}
```

---

## Redirects (4 endpoints)

HTTP redirect rules configured in Traefik.

| Method | Path | operationId | Description |
|--------|------|-------------|-------------|
| GET | `/redirects.one` | redirects.one | Get a redirect rule |
| POST | `/redirects.create` | redirects.create | Create a redirect rule |
| POST | `/redirects.delete` | redirects.delete | Delete a redirect rule |
| POST | `/redirects.update` | redirects.update | Update a redirect rule |

### Key parameters

**redirects.create**
```json
{
  "regex": "string (required — source URL pattern)",
  "replacement": "string (required — target URL)",
  "permanent": "boolean (default: false — 301 vs 302)",
  "applicationId": "string"
}
```

---

## Port (4 endpoints)

Expose additional container ports beyond the main service port.

| Method | Path | operationId | Description |
|--------|------|-------------|-------------|
| GET | `/port.one` | port.one | Get a port mapping |
| POST | `/port.create` | port.create | Add a port mapping |
| POST | `/port.delete` | port.delete | Remove a port mapping |
| POST | `/port.update` | port.update | Update a port mapping |

### Key parameters

**port.create**
```json
{
  "publishedPort": "number (required — host port)",
  "targetPort": "number (required — container port)",
  "protocol": "tcp | udp (default: tcp)",
  "applicationId": "string"
}
```
