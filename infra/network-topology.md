# SecurePsych — Network Topology

**Purpose:** Auditable record of network isolation requirements for FERPA compliance review.
All services run on a single on-premise server inside the school LAN. No component communicates with the internet during normal operation.

---

## Port Map

| Service            | Port   | Bound to       | Accessible from     |
| ------------------ | ------ | -------------- | ------------------- |
| API Gateway        | `8000` | `0.0.0.0`      | LAN clients (HTTPS) |
| RAG Service        | `8001` | `127.0.0.1`    | Gateway only        |
| Summarizer Service | `8002` | `127.0.0.1`    | Gateway only        |
| Jargon Service     | `8003` | `127.0.0.1`    | Gateway only        |
| Ollama (LLM)       | `11434`| `127.0.0.1`    | Services only       |

**Rule:** Ports 8001–8003 and 11434 must be bound to loopback (`127.0.0.1`) and blocked by the host firewall from all LAN interfaces. Only port 8000 (gateway) is LAN-reachable.

---

## Firewall Requirements (district IT)

Configure `ufw` or `iptables` on the server:

```bash
# Allow LAN access to gateway only
ufw allow in on <lan-interface> to any port 8000

# Deny direct LAN access to microservice ports
ufw deny in on <lan-interface> to any port 8001
ufw deny in on <lan-interface> to any port 8002
ufw deny in on <lan-interface> to any port 8003
ufw deny in on <lan-interface> to any port 11434
```

Replace `<lan-interface>` with the school LAN NIC (e.g. `eth0`, `enp3s0`). Loopback traffic is always allowed by default.

---

## TLS / HTTPS

The API gateway (port 8000) must be served over HTTPS/TLS within the LAN:
- Use a self-signed certificate issued by the school's internal CA, or obtain one from Let's Encrypt if the server has a private DNS entry.
- Recommended: terminate TLS at an nginx reverse proxy in front of the gateway Uvicorn process.
- Uvicorn TLS flags (`--ssl-keyfile`, `--ssl-certfile`) are acceptable for simpler deployments.
- HTTP (plaintext) is not acceptable even on a private LAN — JWT tokens in transit must be protected.

---

## VLAN Isolation

District IT should place the SecurePsych server on an isolated VLAN accessible only to:
- Authorized workstations in the special education department
- School IT administration hosts for maintenance

General student/staff network VLANs must not have routing access to the server.

---

## Outbound Traffic

The server must have **no outbound internet access** during production operation. The only permitted outbound connections are:

| Destination         | Purpose                          | Required? |
| ------------------- | -------------------------------- | --------- |
| None (loopback)     | All LLM inference via Ollama     | Yes       |
| LangSmith (opt-out) | Dev tracing (disabled in prod)   | **No — must be blocked on school hardware** |

Verify: `LANGCHAIN_TRACING_V2=false` must be set in all production `.env` files.
