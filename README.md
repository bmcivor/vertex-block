# Vertex Block

A custom DNS-based ad blocker for network-wide blocking across all devices.

## Overview

Vertex Block runs as a DNS server on your network. When devices query for known ad/tracker domains, it returns nothing. Everything else is forwarded to upstream DNS.

**Features (planned):**

- DNS sinkhole for ad/tracker domains
- Aggregated community blocklists
- REST API for stats and management

## How It Works

1. Configure your router to use Vertex Block as the DNS server
2. All devices on the network automatically get ad blocking
3. No client-side software required - works on phones, TVs, IoT, everything

## Status

🚧 **In Development** - Currently in design phase.

## Documentation

Design documentation is available in `docs/design/`:

- [Architecture](docs/design/architecture.md) - System components and how they connect
- [DNS Server](docs/design/dns-server.md) - Query handling and blocking behavior
- [Blocklists](docs/design/blocklists.md) - Sources, formats, and update strategy
- [API](docs/design/api.md) - REST endpoints for management
- [Configuration](docs/design/configuration.md) - Runtime settings

To view docs with live reload:

```bash
make docs
# Open http://localhost:8000
```

## Development

```bash
make build   # Build Docker image (generates lockfile if needed)
make run     # Run DNS server locally (port 5353)
make test    # Run tests
make lock    # Update uv.lock
make docs    # Serve documentation locally (port 8000)
make clean   # Remove containers
```

## Deployment

Deployed to lab via [vertex-studio](../vertex-studio) Ansible playbooks.

## License

See [LICENSE](LICENSE).
