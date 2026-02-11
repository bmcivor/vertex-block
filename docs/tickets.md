# Vertex Block – Ticket Backlog

Tickets derived from `docs/design/`. Order reflects dependencies; implement in sequence or respect dependency list per ticket. More granular tickets and detailed acceptance criteria for the number of moving parts.

---

## 1. Config: environment variables and defaults

**As a** deployer  
**I want** all options configurable via environment variables with documented defaults  
**So that** I can run the service in Docker or systemd without a config file.

### Acceptance criteria

- Every option in `docs/design/configuration.md` has a corresponding env var and default.
- Env var naming: `VB_` prefix, e.g. `VB_DNS_PORT`, `VB_API_PORT`, `VB_DNS_UPSTREAM`, `VB_DNS_TIMEOUT`, `VB_DNS_BLOCK_RESPONSE`, `VB_API_HOST`, `VB_BLOCKLIST_DIR`, `VB_CATALOG_FILE`, `VB_UPDATE_SCHEDULE`, `VB_LOG_LEVEL`, `VB_LOG_QUERIES`, `VB_DATA_DIR`, `VB_STATS_RETENTION`.
- Defaults match the design doc (e.g. DNS port 53, API port 8080, upstream `1.1.1.1,8.8.8.8`, block_response `nxdomain`, log level `info`, etc.).
- Config is exposed as a single object or namespace to the rest of the application.
- Invalid values (e.g. unknown block_response, non-numeric port) are rejected at load time with a clear error.

### Dependencies

- None

### Priority

- High

---

## 2. Config: YAML file and merge order

**As a** deployer  
**I want** an optional YAML config file that merges with env with defined precedence  
**So that** I can keep persistent settings in a file while overriding with env in CI/Docker.

### Acceptance criteria

- Optional config file path: `config.yaml` in cwd, or path from `VB_CONFIG_FILE`.
- If the file is missing and `VB_CONFIG_FILE` is not set, only env and defaults are used (no error).
- Precedence: env (highest) > YAML > defaults (lowest). Every key can be overridden by env.
- YAML structure matches the example in `docs/design/configuration.md` (sections: dns, api, blocklist, logging, storage).
- Invalid YAML or unknown keys are handled (reject with clear error or ignore unknown keys; document behaviour).

### Dependencies

- 1

### Priority

- High

---

## 3. Blocklist domain matching

**As a** DNS component  
**I want** an in-memory blocklist with exact and parent-domain matching  
**So that** queries can be classified as blocked or allowed without I/O.

### Acceptance criteria

- Blocklist is a set (or equivalent) of domain strings; no file or network I/O in this component.
- `is_blocked(domain: str) -> bool`: returns true if the domain or any parent label chain is in the set.
- Matching order for `ads.tracking.example.com`: check `ads.tracking.example.com`, then `tracker.example.com`, then `example.com`; do not check `com` (stop at TLD). Algorithm matches `docs/design/blocklists.md`.
- Exact match: if `example.com` is in the set, `example.com` is blocked.
- Subdomain match: if `ads.example.com` is in the set, `sub.ads.example.com` is blocked.
- Empty set: no domain is blocked. Idempotent for repeated lookups.
- Domain normalization: strip trailing dot if present; match is case-insensitive (document and implement consistently).

### Dependencies

- None

### Priority

- High

---

## 4. Parser: hosts format

**As a** blocklist loader  
**I want** a parser for hosts-format blocklist content  
**So that** lists like Steven Black’s can be consumed.

### Acceptance criteria

- Parser accepts string content (no HTTP or file I/O in this ticket).
- Recognised lines: `0.0.0.0 domain`, `127.0.0.1 domain`; any other IP used for blocking is also accepted; the parser extracts and returns the domain; the IP is ignored.
- Blank lines and lines that are not valid “IP domain” are skipped (no crash).
- Comments (e.g. `# comment`) are skipped.
- Returns a set of normalized domain strings (lowercased, no trailing dot).
- Empty input returns empty set. Large input (e.g. 100k lines) is handled without loading entire file into a single string if that would be problematic; document any size assumptions.

### Dependencies

- None

### Priority

- High

---

## 5. Parser: domain list format

**As a** blocklist loader  
**I want** a parser for one-domain-per-line list format  
**So that** simple and OISD-style lists can be consumed.

### Acceptance criteria

- Parser accepts string content (no HTTP or file I/O).
- One domain per line; leading/trailing whitespace is trimmed.
- Lines starting with `#` are comments and skipped.
- Blank lines skipped.
- Returns a set of normalized domain strings (lowercased, no trailing dot).
- Empty input returns empty set.

### Dependencies

- None

### Priority

- High

---

## 6. Parser: adblock domain rules

**As a** blocklist loader  
**I want** a parser for a subset of AdBlock-style domain rules  
**So that** EasyList / EasyPrivacy / AdGuard-style lists can be consumed.

### Acceptance criteria

- Parser accepts string content (no HTTP or file I/O).
- Supported: basic domain rules such as `||domain^`; extract the domain part.
- Complex rules (CSS selectors, regex, options, exception rules that are not simple domains) are ignored (skip line or rule); no crash.
- Returns a set of normalized domain strings.
- Empty input returns empty set. Document which AdBlock rule types are supported and which are skipped.

### Dependencies

- None

### Priority

- High

---

## 7. Blocklist store: load and merge

**As a** DNS server and API  
**I want** a store that loads list files from disk and merges them into one set  
**So that** the active blocklist is available for lookups.

### Acceptance criteria

- Store uses parsers from tickets 4, 5, 6 according to each list’s format.
- Loads one or more list files from a configured directory (e.g. `VB_BLOCKLIST_DIR`); which files to load is determined by subscription state (see ticket 8) or by convention (e.g. filenames matching subscribed list IDs).
- All parsed domains are merged into a single set; that set is exposed for blocking (same semantics as ticket 3).
- On startup, if the blocklist directory is empty or missing, the merged set is empty (no crash).
- Read-only view of the merged set is available for the DNS path and for stats/lookup.

### Dependencies

- 3, 4, 5, 6

### Priority

- High

---

## 8. Blocklist store: add/remove lists and recompute

**As a** update flow and API  
**I want** the store to support adding/removing domains from specific lists and recomputing the merged set  
**So that** subscriptions and updates can change the active blocklist without restart.

### Acceptance criteria

- Store can add a named list’s domains (e.g. by list_id or filename) and recompute the merged set.
- Store can remove a named list and recompute the merged set.
- After recompute, the DNS server uses the new set (via shared reference or explicit reload).
- No file I/O in this ticket for “add/remove” — this ticket is about the in-memory merge logic and API; actual fetch/write is in update flow tickets.

### Dependencies

- 7

### Priority

- High

---

## 9. DNS: UDP listener and query handling

**As a** client on the network  
**I want** a DNS server that listens on UDP and dispatches queries to a handler  
**So that** the service can receive DNS queries on port 53.

### Acceptance criteria

- Server listens on configured port (default 53 UDP) using dnspython.
- For each incoming query: parse the request, extract the query domain from the question section, pass to a handler that returns a response message; send the response back to the client.
- Malformed or empty questions are handled (e.g. return FORMERR or drop; document behaviour).
- Handler is pluggable (blocklist check and upstream forward are in later tickets); this ticket only ensures UDP receive → handler → send.

### Dependencies

- 1

### Priority

- High

---

## 10. DNS: block response (NXDOMAIN / zero)

**As a** DNS component  
**I want** to return a configurable response for blocked domains  
**So that** clients get a consistent “blocked” answer.

### Acceptance criteria

- When the handler decides “blocked”, the response is built according to config: `nxdomain` (NXDOMAIN status) or `zero` (A → 0.0.0.0, AAAA → ::) per `docs/design/configuration.md` and `docs/design/dns-server.md`.
- Query ID and question are preserved in the response so the client can match the reply.
- Behaviour is correct for A and AAAA questions; other record types (e.g. MX, TXT) for blocked domains: document and implement (e.g. NXDOMAIN for all, or zero only for A/AAAA).

### Dependencies

- 1, 9

### Priority

- High

---

## 11. DNS: upstream forward and fallback

**As a** DNS component  
**I want** allowed queries to be forwarded to upstream DNS with timeout and fallback  
**So that** non-blocked domains resolve correctly.

### Acceptance criteria

- Upstream servers are taken from config (e.g. list of IP:port); try primary first, then fallback on timeout (e.g. 2–5 s per design).
- Original query ID is preserved in the forwarded query and in the response so the client receives a consistent reply.
- Response from upstream is returned to the client (no caching in this ticket per design).
- On upstream timeout or unreachable: try next upstream; if all fail, return SERVFAIL. Fail-open: if blocklist check fails, allow the query (per `docs/design/dns-server.md`).

### Dependencies

- 1, 9

### Priority

- High

---

## 12. DNS: TCP listener

**As a** client that uses TCP for DNS  
**I want** the DNS server to listen on TCP on the same port as UDP  
**So that** large responses and TCP-only clients work.

### Acceptance criteria

- TCP listener runs on the same port (default 53); same query handling as UDP (block vs forward).
- Truncation / large response behaviour per design (e.g. TCP fallback when UDP would truncate).
- Both UDP and TCP run concurrently (same process or threading model as in `docs/design/dns-server.md`).

### Dependencies

- 9, 10, 11

### Priority

- Medium

---

## 13. Allowlist: storage and DNS path

**As a** user  
**I want** an allowlist that overrides the blocklist for specific domains  
**So that** I can unblock domains that are incorrectly blocked.

### Acceptance criteria

- Allowlist is an in-memory set of domain strings; persistence is file or SQLite per architecture (load on startup, save on change).
- In the DNS path, allowlist is checked before blocklist; if the query domain (or any parent per ticket 3 logic) is in the allowlist, the query is forwarded even if it would otherwise be blocked.
- Domain matching for allowlist uses the same parent-domain logic as blocklist (allowlisting `example.com` allows `sub.example.com`).
- Empty allowlist: no override; blocklist alone determines blocking.

### Dependencies

- 3

### Priority

- High

---

## 14. Catalog: load from JSON and schema

**As a** API and update flow  
**I want** the blocklist catalog loaded from a JSON file with a defined schema  
**So that** we can list and subscribe to known sources.

### Acceptance criteria

- Catalog is loaded from a path in config (e.g. `VB_CATALOG_FILE`, default `./catalog.json`).
- Schema: each entry has at least id, name, url, category, description, format, update_frequency (or equivalent); types and required fields documented.
- If the file is missing or invalid JSON, the application fails at startup with a clear error (or returns an empty catalog and logs; document behaviour).
- Catalog is read-only in this ticket (no add/remove via API).

### Dependencies

- 1

### Priority

- High

---

## 15. Catalog: initial catalog file content

**As a** deployer  
**I want** a shipped catalog file with the initial sources from the design  
**So that** the app works out of the box with known lists.

### Acceptance criteria

- A catalog JSON file exists (in repo or generated at install) with entries for: Steven Black Unified (ads, hosts), AdGuard DNS Filter (ads/trackers, adblock), EasyList (ads, adblock), EasyPrivacy (trackers, adblock), OISD (ads/trackers, domains) per `docs/design/blocklists.md`.
- Each entry has correct url, category, description, format, update_frequency where applicable.
- IDs are stable and referenced in docs (e.g. `stevenblack-unified`).

### Dependencies

- 14

### Priority

- High

---

## 16. Subscriptions: persistence schema and read/write

**As a** system  
**I want** subscription state (which catalog list IDs are subscribed) persisted  
**So that** subscriptions survive restarts.

### Acceptance criteria

- Persist which catalog list IDs are currently subscribed (e.g. list of IDs).
- Storage is file-based or SQLite per architecture; schema is defined and documented.
- Read subscriptions on startup; write on subscribe/unsubscribe (from API or internal).
- Empty state (no subscriptions) is valid; no lists loaded until user subscribes.

### Dependencies

- 1

### Priority

- High

---

## 17. Custom lists: metadata and persistence

**As a** system  
**I want** custom blocklist definitions (URL, name, format) persisted  
**So that** user-added URLs survive restarts and can be updated.

### Acceptance criteria

- Persist custom lists: url, name, format, a stable id (e.g. generated).
- Same storage as subscriptions (file or SQLite); schema documented.
- Read/write on add/remove custom list; list is available for the update flow by id.

### Dependencies

- 1, 16

### Priority

- High

---

## 18. Update flow: fetch from URL and write raw files

**As a** update flow  
**I want** to fetch a blocklist from a URL and optionally use conditional request (etag)  
**So that** we avoid re-downloading unchanged lists and store raw content for parsing.

### Acceptance criteria

- Given a list definition (catalog or custom) with url: fetch the URL (HTTP/HTTPS); support optional etag/last-modified for conditional GET.
- On success: write raw content to the configured blocklist directory (e.g. `blocklists/<list_id>.txt`); store etag (or equivalent) for next conditional request.
- On failure (network, 4xx/5xx): do not overwrite existing file; return error to caller; no crash.
- Timeout and redirect behaviour documented and reasonable (e.g. 30 s timeout).

### Dependencies

- 1, 16, 17

### Priority

- High

---

## 19. Update flow: parse, merge, metadata, reload blocklist

**As a** update flow  
**I want** to parse fetched lists, update metadata, merge into the active blocklist, and reload the DNS view  
**So that** the DNS server uses the new data without restart.

### Acceptance criteria

- For each subscribed list: read the raw file from blocklist dir (from ticket 18), parse with the correct format (tickets 4–6), validate/normalize entries.
- Merge all lists’ domains into a single set and pass to the blocklist store (ticket 7/8); store updates last_updated, domain_count per list.
- After merge, DNS server sees the new blocklist (replace reference or explicit reload).
- Update can be triggered for all subscribed lists or a single list by id; partial failure (one list fails to fetch/parse) does not clear the rest; report which lists updated and which failed.

### Dependencies

- 4, 5, 6, 7, 8, 14, 16, 17, 18

### Priority

- High

---

## 20. Scheduled blocklist updates

**As a** deployer  
**I want** optional scheduled updates of all subscribed blocklists  
**So that** lists stay up to date without manual API calls.

### Acceptance criteria

- A configurable schedule (cron-style, e.g. `VB_UPDATE_SCHEDULE`) triggers the full update flow (ticket 19) for all subscribed lists.
- When schedule is empty or not set, no background scheduler runs.
- Schedule format and examples match `docs/design/configuration.md` (e.g. `0 4 * * *` daily at 4am).

### Dependencies

- 1, 19

### Priority

- Medium

---

## 21. API skeleton and health

**As a** operator  
**I want** an HTTP API with a health endpoint  
**So that** I can check that the service and DNS server are running.

### Acceptance criteria

- FastAPI app (or equivalent) with base path per `docs/design/api.md` (e.g. `/api/v1`).
- GET `/health` returns JSON: `status` (e.g. "healthy"), `dns_server` (e.g. "running"), `uptime_seconds`.
- API listens on configured port and host (default 8080, 0.0.0.0).
- No auth in this ticket.

### Dependencies

- 1, 9

### Priority

- High

---

## 22. Catalog API

**As a** API consumer  
**I want** to list the catalog and get a single catalog entry by id  
**So that** I can discover and inspect lists before subscribing.

### Acceptance criteria

- GET `/catalog` returns JSON: `lists` array; each element has id, name, url, category, description, format, subscribed (boolean from subscription state).
- GET `/catalog/{id}` returns a single entry with same fields plus domain_count, last_updated when available; 404 if id not in catalog.
- Response shapes match `docs/design/api.md`.

### Dependencies

- 14, 16, 17, 21

### Priority

- High

---

## 23. Subscriptions API: GET, POST, DELETE

**As a** user  
**I want** to list subscriptions, subscribe to a catalog list, and unsubscribe  
**So that** I control which lists are active.

### Acceptance criteria

- GET `/subscriptions` returns JSON: `subscriptions` array (id, name, domain_count, last_updated), `total_domains`; matches API design.
- POST `/subscriptions` body `{ "list_id": "..." }`: subscribe to catalog list; persist (ticket 16), trigger update flow for that list (ticket 19), return status and list_id; 404 if list_id not in catalog; 409 if already subscribed (or document behaviour).
- DELETE `/subscriptions/{id}`: unsubscribe; remove from persistence and from blocklist store; return status and list_id; 404 if not subscribed.

### Dependencies

- 16, 19, 21

### Priority

- High

---

## 24. Subscriptions API: custom list POST

**As a** user  
**I want** to add a custom blocklist by URL  
**So that** I can use lists not in the catalog.

### Acceptance criteria

- POST `/subscriptions/custom` body `{ "url": "...", "name": "...", "format": "..." }`; name and format optional (format auto-detect or default).
- Persist custom list (ticket 17), trigger update flow for that list; return status, id, name per API design.
- Response shape matches `docs/design/api.md`; invalid URL or fetch failure returns 4xx with error body.

### Dependencies

- 17, 19, 21

### Priority

- High

---

## 25. Update API

**As a** user  
**I want** to trigger a full or single-list update via the API  
**So that** I can refresh blocklists on demand.

### Acceptance criteria

- POST `/update`: trigger update for all subscribed lists; response includes status, updated, failed, total_domains, duration_ms per API design.
- POST `/update/{id}`: trigger update for one list; response includes status, list_id, domain_count, duration_ms; 404 if id not subscribed.
- Endpoints call the update flow (ticket 19) and return the documented JSON.

### Dependencies

- 19, 21

### Priority

- High

---

## 26. Stats: in-memory counters and DNS integration

**As a** operator  
**I want** query counts (total, blocked, allowed) and optional per-domain or time-window stats  
**So that** the API can report usage.

### Acceptance criteria

- In-memory counters: total queries, blocked, allowed; incremented on each DNS query (block vs allow).
- Optional: retain per-domain counts or time-bucketed stats per design (e.g. `VB_STATS_RETENTION` days); document what is retained and how it is used for top_blocked / top_allowed.
- DNS handler (tickets 9–13) increments counters; no blocking I/O in the hot path.

### Dependencies

- 9, 10, 11, 13

### Priority

- High

---

## 27. Stats API

**As a** user or operator  
**I want** GET /stats and GET /stats/queries with period and top lists  
**So that** I can see what is being blocked and allowed.

### Acceptance criteria

- GET `/stats`: returns queries (total, blocked, allowed, block_percentage), blocklist (total_domains, subscribed_lists), uptime_seconds per API design.
- GET `/stats/queries`: optional query param period (hour, day, week); returns period, totals, top_blocked, top_allowed; response shape matches API design.
- Data comes from ticket 26 (counters), store (7) for total_domains, and subscriptions (16) for subscribed_lists.

### Dependencies

- 7, 16, 21, 26

### Priority

- High

---

## 28. Lookup API

**As a** user  
**I want** GET /lookup/{domain} to check if a domain would be blocked  
**So that** I can debug and verify blocklist behaviour.

### Acceptance criteria

- GET `/lookup/{domain}`: returns JSON domain, blocked (bool), matched_by (list id or null), matched_rule (matched domain or null) per API design.
- Uses the same blocklist and allowlist as the DNS path (allowlist overrides blocklist).
- Invalid or missing domain: 400 or 404 per API design.

### Dependencies

- 7, 13, 21

### Priority

- High

---

## 29. Allowlist API

**As a** user  
**I want** to view, add, and remove allowlist entries via the API  
**So that** I can unblock domains without editing files.

### Acceptance criteria

- GET `/allowlist`: returns JSON list of allowlisted domains.
- POST `/allowlist` body `{ "domain": "..." }`: add domain; persist (ticket 13), return status and domain; idempotent or 409 if already present (document).
- DELETE `/allowlist/{domain}`: remove domain; persist; return status and domain; 404 if not in allowlist.
- Changes are reflected in the DNS allowlist immediately (shared reference or reload).

### Dependencies

- 13, 21

### Priority

- High

---

## 30. API error responses

**As a** API consumer  
**I want** consistent error JSON and HTTP status codes  
**So that** I can handle failures reliably.

### Acceptance criteria

- All API errors return JSON with `error` (code string) and `message` per `docs/design/api.md`.
- HTTP status and error codes: 400 bad_request, 404 not_found, 409 conflict, 500 internal_error.
- Validation errors (e.g. invalid body) use 400 and appropriate message; not-found uses 404; duplicate/subscribe conflict uses 409.

### Dependencies

- 21

### Priority

- Medium

---

## 31. Application bootstrap

**As a** deployer  
**I want** a single entrypoint that wires config, blocklist, allowlist, DNS, and API and runs until shutdown  
**So that** the service can be started with one command.

### Acceptance criteria

- Entrypoint (e.g. `main`) loads config (1, 2), restores subscriptions and custom lists (16, 17), loads or builds blocklist store (7, 8) and allowlist (13), creates DNS server (9–12) and API app (21+).
- DNS and API run concurrently; graceful shutdown on SIGTERM/SIGINT (close listeners, drain, exit).
- Blocklist and allowlist are passed into DNS and into API routes that need them; stats (26) are wired to DNS and API.

### Dependencies

- 1, 2, 7, 8, 9, 10, 11, 12, 13, 16, 17, 19, 21, 26

### Priority

- High

---

## 32. Unit tests: config, matching, parsers

**As a** developer  
**I want** unit tests for config loading, blocklist matching, and all parsers  
**So that** regressions are caught.

### Acceptance criteria

- Tests for config: env only, env + YAML merge order, invalid values.
- Tests for blocklist matching: exact match, parent match, empty set, TLD boundary, case and trailing dot.
- Tests for each parser (hosts, domain list, adblock): valid input, empty input, comments, malformed lines; output set content.
- Tests live under `tests/unit/`; runnable with `make test` or `pytest`; use pytest and pytest-asyncio where needed.

### Dependencies

- 1, 2, 3, 4, 5, 6

### Priority

- High

---

## 33. Unit tests: DNS handler

**As a** developer  
**I want** unit tests for the DNS handler with mocked blocklist and upstream  
**So that** block/forward logic is verified in isolation.

### Acceptance criteria

- Mock blocklist and upstream; test that blocked queries get block response (NXDOMAIN or zero per config), allowed queries get forwarded response; query ID preserved; upstream timeout/fallback behaviour.
- Per `docs/testing.md`; tests under `tests/unit/`.

### Dependencies

- 9, 10, 11

### Priority

- High

---

## 34. Integration tests: DNS query flow

**As a** developer  
**I want** an integration test for the full DNS path with a fake upstream  
**So that** we verify receive → check → block/forward → respond.

### Acceptance criteria

- Test: start DNS server with real blocklist/allowlist and a mock or fake upstream DNS; send queries (blocked and allowed); assert responses match expectations.
- Tests under `tests/integration/`; runnable with project test command.

### Dependencies

- 31

### Priority

- Medium

---

## 35. Integration tests: API

**As a** developer  
**I want** integration tests for API endpoints  
**So that** we verify HTTP behaviour end-to-end.

### Acceptance criteria

- Tests for health, catalog, subscriptions, update, stats, lookup, allowlist using FastAPI TestClient (or equivalent) per `docs/testing.md`.
- Tests under `tests/integration/`; runnable with project test command.

### Dependencies

- 31

### Priority

- Medium

---

## Dependency overview

```
1 Config env/defaults    2 Config YAML
3 Blocklist matching     4 Hosts parser  5 Domain list parser  6 Adblock parser
7 Blocklist store load   8 Blocklist store add/remove
9 DNS UDP                10 Block response  11 Upstream forward  12 DNS TCP
13 Allowlist
14 Catalog load          15 Catalog initial file
16 Subscriptions persist 17 Custom lists persist
18 Update fetch          19 Update parse/merge/reload  20 Schedule
21 API skeleton
22 Catalog API  23 Subscriptions API  24 Custom POST  25 Update API
26 Stats counters  27 Stats API  28 Lookup API  29 Allowlist API  30 API errors
31 Bootstrap
32 Unit: config/matching/parsers  33 Unit: DNS  34 Integration: DNS  35 Integration: API
```
