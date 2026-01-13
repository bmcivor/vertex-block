# Configuration

This document defines the configuration options for Vertex Block.

## Overview

Configuration is loaded from environment variables and/or a config file. Environment variables take precedence over config file values.

## Configuration Sources

| Source | Priority | Use Case |
|--------|----------|----------|
| Environment variables | 1 (highest) | Docker/container deployment |
| Config file (YAML) | 2 | Local development, persistent settings |
| Defaults | 3 (lowest) | Fallback values |

## Environment Variables

### DNS Server

| Variable | Description | Default |
|----------|-------------|---------|
| `VB_DNS_PORT` | Port for DNS server | `53` |
| `VB_DNS_UPSTREAM` | Upstream DNS servers (comma-separated) | `1.1.1.1,8.8.8.8` |
| `VB_DNS_TIMEOUT` | Upstream query timeout (seconds) | `5` |
| `VB_DNS_BLOCK_RESPONSE` | Response for blocked domains: `nxdomain` or `zero` | `nxdomain` |

### API Server

| Variable | Description | Default |
|----------|-------------|---------|
| `VB_API_PORT` | Port for REST API | `8080` |
| `VB_API_HOST` | Bind address for API | `0.0.0.0` |

### Blocklists

| Variable | Description | Default |
|----------|-------------|---------|
| `VB_BLOCKLIST_DIR` | Directory for blocklist files | `./blocklists` |
| `VB_CATALOG_FILE` | Path to catalog JSON | `./catalog.json` |
| `VB_UPDATE_SCHEDULE` | Cron expression for auto-updates | (disabled) |

### Logging

| Variable | Description | Default |
|----------|-------------|---------|
| `VB_LOG_LEVEL` | Log level: debug, info, warning, error | `info` |
| `VB_LOG_QUERIES` | Log all DNS queries | `false` |

### Storage

| Variable | Description | Default |
|----------|-------------|---------|
| `VB_DATA_DIR` | Directory for persistent data | `./data` |
| `VB_STATS_RETENTION` | Days to retain query stats | `7` |

## Config File

Optional YAML config file at `config.yaml` or path specified by `VB_CONFIG_FILE`.

```yaml
dns:
  port: 53
  upstream:
    - 1.1.1.1
    - 8.8.8.8
  timeout: 5
  block_response: nxdomain

api:
  port: 8080
  host: 0.0.0.0

blocklist:
  directory: ./blocklists
  catalog: ./catalog.json
  update_schedule: "0 4 * * *"  # 4am daily

logging:
  level: info
  queries: false

storage:
  data_dir: ./data
  stats_retention: 7
```

## Docker Compose Example

```yaml
services:
  vertex-block:
    image: vertex-block:latest
    ports:
      - "53:53/udp"
      - "53:53/tcp"
      - "8080:8080"
    environment:
      - VB_DNS_UPSTREAM=1.1.1.1,8.8.8.8
      - VB_LOG_LEVEL=info
      - VB_UPDATE_SCHEDULE=0 4 * * *
    volumes:
      - ./blocklists:/app/blocklists
      - ./data:/app/data
```

## Upstream DNS Servers

Configurable list of upstream DNS servers for forwarding non-blocked queries.

| Provider | Primary | Secondary |
|----------|---------|-----------|
| Cloudflare | 1.1.1.1 | 1.0.0.1 |
| Google | 8.8.8.8 | 8.8.4.4 |
| Quad9 | 9.9.9.9 | 149.112.112.112 |

Default uses Cloudflare primary, Google primary as fallback.

## Block Response Modes

| Mode | Response | Use Case |
|------|----------|----------|
| `nxdomain` | NXDOMAIN status | Preferred - domain doesn't exist |
| `zero` | 0.0.0.0 / :: | Compatibility - some clients prefer this |

## Update Schedule

Uses cron expression format:

```
┌───────────── minute (0-59)
│ ┌───────────── hour (0-23)
│ │ ┌───────────── day of month (1-31)
│ │ │ ┌───────────── month (1-12)
│ │ │ │ ┌───────────── day of week (0-6, Sun=0)
│ │ │ │ │
* * * * *
```

Examples:
- `0 4 * * *` - Daily at 4am
- `0 */6 * * *` - Every 6 hours
- `0 0 * * 0` - Weekly on Sunday midnight

Set to empty string or omit to disable scheduled updates.

## Query Logging

When `VB_LOG_QUERIES=true`, all DNS queries are logged:

```
2026-01-14 10:00:00 INFO  query domain=ads.example.com result=blocked
2026-01-14 10:00:01 INFO  query domain=github.com result=allowed
```

Disabled by default for privacy and performance.

## Data Persistence

| Directory | Contents |
|-----------|----------|
| `blocklists/` | Downloaded blocklist files |
| `data/` | Subscriptions, custom lists, stats |

Mount these as volumes for persistence across container restarts.
