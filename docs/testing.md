# Testing Strategy

## Test Levels

### Unit Tests

Test individual components in isolation.

- Mock external dependencies (DNS resolution, file I/O)
- Fast, run on every commit
- Located in `tests/unit/`

### Integration Tests

Test components working together.

- Use fake/mock upstream DNS server
- Test full query flow (receive → check → forward/block → respond)
- Located in `tests/integration/`

## Tools

| Tool | Purpose |
|------|---------|
| pytest | Test runner |
| pytest-asyncio | Async test support |
| httpx | API testing (FastAPI TestClient) |

### Consider if needed

| Tool | Purpose |
|------|---------|
| factory_boy | Test data generation (if using relational data) |
| pytest-mock | Simplified mocking interface |

## Running Tests

```bash
make test
```

## Test Structure

```
tests/
  unit/
    test_blocklist.py
    test_dns_handler.py
  integration/
    test_query_flow.py
    test_api.py
```

## Mocking Approach

**DNS resolution:** Mock dnspython resolver to return controlled responses.

**Upstream DNS:** For integration tests, use a mock DNS service that returns predetermined responses.

**API:** FastAPI's TestClient handles request/response without network.
