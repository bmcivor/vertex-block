# REST API Design

This document defines the REST API endpoints for Vertex Block management.

## Overview

The API runs on port 8080 and provides endpoints for:
- Blocklist catalog and subscription management
- Statistics and monitoring
- Health checks

## Base URL

```
http://<host>:8080/api/v1
```

## Authentication

No authentication initially. API is intended for local network access only.

Future consideration: API key or basic auth for remote access.

## Endpoints

### Health

#### GET /health

Health check endpoint.

**Response:**

```json
{
  "status": "healthy",
  "dns_server": "running",
  "uptime_seconds": 3600
}
```

### Catalog

#### GET /catalog

List all available blocklists in the catalog.

**Response:**

```json
{
  "lists": [
    {
      "id": "stevenblack-unified",
      "name": "Steven Black Unified",
      "url": "https://...",
      "category": "ads",
      "description": "Unified hosts file with base extensions",
      "format": "hosts",
      "subscribed": true
    }
  ]
}
```

#### GET /catalog/{id}

Get details for a specific catalog entry.

**Response:**

```json
{
  "id": "stevenblack-unified",
  "name": "Steven Black Unified",
  "url": "https://...",
  "category": "ads",
  "description": "Unified hosts file with base extensions",
  "format": "hosts",
  "subscribed": true,
  "domain_count": 85000,
  "last_updated": "2026-01-14T10:00:00Z"
}
```

### Subscriptions

#### GET /subscriptions

List currently subscribed blocklists.

**Response:**

```json
{
  "subscriptions": [
    {
      "id": "stevenblack-unified",
      "name": "Steven Black Unified",
      "domain_count": 85000,
      "last_updated": "2026-01-14T10:00:00Z"
    }
  ],
  "total_domains": 125000
}
```

#### POST /subscriptions

Subscribe to a blocklist.

**Request:**

```json
{
  "list_id": "stevenblack-unified"
}
```

**Response:**

```json
{
  "status": "subscribed",
  "list_id": "stevenblack-unified"
}
```

#### DELETE /subscriptions/{id}

Unsubscribe from a blocklist.

**Response:**

```json
{
  "status": "unsubscribed",
  "list_id": "stevenblack-unified"
}
```

### Custom Lists

#### POST /subscriptions/custom

Subscribe to a custom blocklist URL.

**Request:**

```json
{
  "url": "https://example.com/my-blocklist.txt",
  "name": "My Custom List",
  "format": "domains"
}
```

`name` and `format` are optional. Format auto-detects if not specified.

**Response:**

```json
{
  "status": "subscribed",
  "id": "custom-abc123",
  "name": "My Custom List"
}
```

### Updates

#### POST /update

Trigger a manual update of all subscribed lists.

**Response:**

```json
{
  "status": "completed",
  "updated": ["stevenblack-unified", "custom-abc123"],
  "failed": [],
  "total_domains": 125000,
  "duration_ms": 3400
}
```

#### POST /update/{id}

Update a specific subscribed list.

**Response:**

```json
{
  "status": "completed",
  "list_id": "stevenblack-unified",
  "domain_count": 85000,
  "duration_ms": 1200
}
```

### Statistics

#### GET /stats

Get overall statistics.

**Response:**

```json
{
  "queries": {
    "total": 150000,
    "blocked": 45000,
    "allowed": 105000,
    "block_percentage": 30.0
  },
  "blocklist": {
    "total_domains": 125000,
    "subscribed_lists": 3
  },
  "uptime_seconds": 86400
}
```

#### GET /stats/queries

Get recent query statistics.

**Query Parameters:**

| Param | Description | Default |
|-------|-------------|---------|
| period | Time period (hour, day, week) | day |

**Response:**

```json
{
  "period": "day",
  "total": 50000,
  "blocked": 15000,
  "allowed": 35000,
  "top_blocked": [
    {"domain": "ads.example.com", "count": 500},
    {"domain": "tracker.example.com", "count": 300}
  ],
  "top_allowed": [
    {"domain": "google.com", "count": 1000},
    {"domain": "github.com", "count": 800}
  ]
}
```

### Query Lookup

#### GET /lookup/{domain}

Check if a domain would be blocked.

**Response:**

```json
{
  "domain": "ads.example.com",
  "blocked": true,
  "matched_by": "stevenblack-unified",
  "matched_rule": "ads.example.com"
}
```

### Allowlist

#### GET /allowlist

Get user-defined allowed domains (overrides blocklist).

**Response:**

```json
{
  "domains": [
    "allowed.example.com",
    "another.example.com"
  ]
}
```

#### POST /allowlist

Add domain to allowlist.

**Request:**

```json
{
  "domain": "allowed.example.com"
}
```

**Response:**

```json
{
  "status": "added",
  "domain": "allowed.example.com"
}
```

#### DELETE /allowlist/{domain}

Remove domain from allowlist.

**Response:**

```json
{
  "status": "removed",
  "domain": "allowed.example.com"
}
```

## Error Responses

All errors follow this format:

```json
{
  "error": "not_found",
  "message": "List 'invalid-id' not found in catalog"
}
```

### Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | bad_request | Invalid request format |
| 404 | not_found | Resource not found |
| 409 | conflict | Already subscribed/exists |
| 500 | internal_error | Server error |

## Rate Limiting

No rate limiting initially. Consider adding if exposed to wider network.
