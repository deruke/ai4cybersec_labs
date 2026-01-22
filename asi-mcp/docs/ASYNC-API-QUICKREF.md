# Async Scan API - Quick Reference

## Problem & Solution

**Problem**: Long-running scans (nuclei, gobuster, nikto) timeout after 30 seconds in n8n
**Solution**: Async scan API with polling or webhook patterns

## Endpoints

```bash
# Start scan (returns immediately with job_id)
POST /scans/start
{
  "tool": "nuclei_scan",
  "target": "https://example.com",
  "arguments": {"severity": "high,critical"},
  "webhook_url": "https://your-webhook.com/callback"  # optional
}

# Check status
GET /scans/{job_id}/status

# Get results (when complete)
GET /scans/{job_id}/results

# List all scans
GET /scans?status=completed&limit=10

# Cancel scan
POST /scans/{job_id}/cancel
```

## Usage Pattern

### Option 1: Polling (Simple)
```bash
# 1. Start scan
JOB_ID=$(curl -X POST http://localhost:3000/scans/start \
  -H "Content-Type: application/json" \
  -d '{"tool":"nuclei_scan","target":"https://example.com","arguments":{"severity":"high,critical"}}' \
  | jq -r '.job_id')

# 2. Poll until complete
while true; do
  STATUS=$(curl -s http://localhost:3000/scans/$JOB_ID/status | jq -r '.status')
  echo "Status: $STATUS"
  [ "$STATUS" = "completed" ] && break
  sleep 10
done

# 3. Get results
curl -s http://localhost:3000/scans/$JOB_ID/results | jq
```

### Option 2: Webhook (Production)
```bash
# Start with webhook
curl -X POST http://localhost:3000/scans/start \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "nuclei_scan",
    "target": "https://example.com",
    "arguments": {"severity": "high,critical"},
    "webhook_url": "https://your-n8n.com/webhook/scan-complete"
  }'

# MCP server will POST results to webhook when done
```

## n8n Integration

### Polling Workflow
```
Manual Trigger
  ↓
HTTP Request: Start Scan (save job_id)
  ↓
Wait 10 seconds
  ↓
HTTP Request: Get Status
  ↓
IF status == "completed":
  ↓ YES
  HTTP Request: Get Results
    ↓
  AI Agent (MCP Client)
  ↓ NO (status == "running")
  Loop back to Wait
```

### Webhook Workflow
```
Webhook Node: Create /security-scan-complete
  ↓
Manual Trigger
  ↓
HTTP Request: Start Scan (with webhook_url)
  ↓
[Scan runs in background]
  ↓
Webhook Receives Results
  ↓
AI Agent (MCP Client)
```

## Supported Tools

**Fast (< 5s)** - Optional async:
- httpx_scan
- wafw00f_scan
- subfinder_scan

**Medium (5-30s)** - Recommended async:
- nmap_scan
- nuclei_scan (filtered)

**Slow (> 30s)** - Required async:
- nuclei_scan (comprehensive)
- gobuster_scan
- nikto_scan
- ffuf_scan
- prowler_scan
- hydra_bruteforce

## Performance Tests

| Tool | Target | Duration | Status |
|------|--------|----------|--------|
| httpx_scan | ginandjuice.shop | 0.95s | ✅ Complete |
| nuclei_scan (high/crit) | ginandjuice.shop | 112.96s | ✅ Complete |
| gobuster_scan | ginandjuice.shop | ~120s | ✅ Complete |

**Before**: nuclei_scan would timeout at 30s ❌
**After**: nuclei_scan completes in 112s ✅

## Status Values

- `pending` - Job created, not started
- `running` - Scan in progress
- `completed` - Scan finished successfully
- `failed` - Error occurred
- `cancelled` - Manually cancelled

## Example Response

```json
{
  "job_id": "3ef5d95c-ec18-451e-b330-9a867f7af483",
  "status": "completed",
  "tool": "nuclei_scan",
  "target": "https://ginandjuice.shop",
  "completed_at": "2026-01-14T13:05:29.797611",
  "duration_seconds": 112.96,
  "results": {
    "tool": "nuclei",
    "success": true,
    "output": "...",
    "findings": [...]
  }
}
```

## Troubleshooting

**Scan stuck in "running"**:
```bash
# Check logs
docker logs mcp-security-server --tail 50

# Cancel if needed
curl -X POST http://localhost:3000/scans/{job_id}/cancel
```

**Results not available**:
```bash
# Verify status first
curl http://localhost:3000/scans/{job_id}/status

# Check result files
docker exec mcp-security-server ls -lh /tmp/scans/
```

**Webhook not called**:
- Verify URL is accessible from container
- Check logs for webhook errors
- Test webhook manually with curl

## Documentation

- Full API docs: `docs/async-scan-api.md`
- n8n workflows: `docs/n8n-async-workflow-guide.md`
- Main docs: `ALL-ISSUES-RESOLVED.md`

---

**Version**: 1.0.0
**Updated**: 2026-01-14
**Status**: Production Ready ✅
