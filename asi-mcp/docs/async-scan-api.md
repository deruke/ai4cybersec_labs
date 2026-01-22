# Async Scan API Documentation

## Overview

The Async Scan API allows long-running security scans to execute in the background without blocking. This solves timeout issues with comprehensive scans like Nuclei vulnerability assessments.

**Key Benefits**:
- Start scans and get immediate response with job ID
- Poll for status updates without blocking
- Retrieve results when complete
- Support for webhook callbacks (optional)
- Persistent result storage in `/tmp/scans/`

---

## API Endpoints

### 1. Start Async Scan

**POST** `/scans/start`

Start a security scan in the background.

**Request Body**:
```json
{
  "tool": "nuclei_scan",
  "target": "https://example.com",
  "arguments": {
    "severity": "high,critical"
  },
  "webhook_url": "https://your-webhook.com/callback"
}
```

**Parameters**:
- `tool` (string, required): Tool name (e.g., "nuclei_scan", "httpx_scan", "nmap_scan")
- `target` (string, required): Target URL, domain, or IP address
- `arguments` (object, optional): Tool-specific arguments
- `webhook_url` (string, optional): URL to POST results when complete

**Response** (200 OK):
```json
{
  "job_id": "3ef5d95c-ec18-451e-b330-9a867f7af483",
  "status": "pending",
  "tool": "nuclei_scan",
  "target": "https://example.com",
  "message": "Scan job created and started",
  "status_url": "/scans/3ef5d95c-ec18-451e-b330-9a867f7af483/status",
  "results_url": "/scans/3ef5d95c-ec18-451e-b330-9a867f7af483/results"
}
```

**Example**:
```bash
curl -X POST http://localhost:3000/scans/start \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "nuclei_scan",
    "target": "https://ginandjuice.shop",
    "arguments": {"severity": "high,critical"}
  }'
```

---

### 2. Get Scan Status

**GET** `/scans/{job_id}/status`

Check the current status of a scan job.

**Response** (200 OK):
```json
{
  "job_id": "3ef5d95c-ec18-451e-b330-9a867f7af483",
  "tool_name": "nuclei_scan",
  "target": "https://example.com",
  "arguments": {
    "target": "https://example.com",
    "severity": "high,critical"
  },
  "status": "running",
  "created_at": "2026-01-14T13:03:36.834549",
  "started_at": "2026-01-14T13:03:36.834894",
  "completed_at": null,
  "duration_seconds": null,
  "error": null
}
```

**Status Values**:
- `pending` - Job created, not yet started
- `running` - Scan in progress
- `completed` - Scan finished successfully
- `failed` - Scan encountered an error
- `cancelled` - Scan was cancelled

**Example**:
```bash
curl http://localhost:3000/scans/3ef5d95c-ec18-451e-b330-9a867f7af483/status
```

---

### 3. Get Scan Results

**GET** `/scans/{job_id}/results`

Retrieve the full results of a completed scan.

**Response** (200 OK - when completed):
```json
{
  "job_id": "3ef5d95c-ec18-451e-b330-9a867f7af483",
  "status": "completed",
  "tool": "nuclei_scan",
  "target": "https://example.com",
  "completed_at": "2026-01-14T13:05:42.123456",
  "duration_seconds": 125.29,
  "results": {
    "tool": "nuclei",
    "target": "https://example.com",
    "success": true,
    "output": "...",
    "findings": [...]
  }
}
```

**Response** (200 OK - when not complete):
```json
{
  "job_id": "3ef5d95c-ec18-451e-b330-9a867f7af483",
  "status": "running",
  "message": "Job not completed yet"
}
```

**Example**:
```bash
curl http://localhost:3000/scans/3ef5d95c-ec18-451e-b330-9a867f7af483/results
```

---

### 4. List All Scans

**GET** `/scans`

List all scan jobs with optional filters.

**Query Parameters**:
- `status` (string, optional): Filter by status (pending, running, completed, failed, cancelled)
- `tool` (string, optional): Filter by tool name
- `limit` (integer, optional): Max results to return (default: 50)

**Response** (200 OK):
```json
{
  "jobs": [
    {
      "job_id": "832e425c-0c66-4de9-a41c-134800363cab",
      "tool_name": "httpx_scan",
      "target": "https://example.com",
      "status": "completed",
      "created_at": "2026-01-14T13:04:03.518916",
      "started_at": "2026-01-14T13:04:03.519503",
      "completed_at": "2026-01-14T13:04:04.470596",
      "duration_seconds": 0.951093,
      "has_results": true,
      "result_size": 1086
    }
  ],
  "count": 1
}
```

**Examples**:
```bash
# List all scans
curl http://localhost:3000/scans

# List only running scans
curl http://localhost:3000/scans?status=running

# List only nuclei scans
curl http://localhost:3000/scans?tool=nuclei_scan

# List last 10 completed scans
curl http://localhost:3000/scans?status=completed&limit=10
```

---

### 5. Cancel Scan

**POST** `/scans/{job_id}/cancel`

Cancel a running or pending scan job.

**Response** (200 OK - success):
```json
{
  "success": true,
  "job_id": "3ef5d95c-ec18-451e-b330-9a867f7af483",
  "message": "Scan job cancelled successfully"
}
```

**Response** (404 Not Found):
```json
{
  "success": false,
  "error": "Job not found"
}
```

**Response** (400 Bad Request):
```json
{
  "success": false,
  "error": "Job cannot be cancelled (already completed/failed)"
}
```

**Example**:
```bash
curl -X POST http://localhost:3000/scans/3ef5d95c-ec18-451e-b330-9a867f7af483/cancel
```

---

## Supported Tools

All 22 security tools support async scanning:

### Network Reconnaissance
- `nmap_scan` - Port scanning
- `masscan_scan` - High-speed scanning
- `rustscan_scan` - Fast port discovery
- `subfinder_scan` - Subdomain enumeration
- `nuclei_scan` - Vulnerability scanning ⚡ **Best for async**
- `theharvester_scan` - OSINT gathering

### Web Application Security
- `gobuster_scan` - Directory brute-forcing ⚡ **Can take time**
- `nikto_scan` - Web server scanning ⚡ **Can take time**
- `sqlmap_scan` - SQL injection testing
- `wpscan_scan` - WordPress security
- `ffuf_scan` - Fast fuzzing ⚡ **Can take time**
- `httpx_scan` - HTTP toolkit (fast)
- `wafw00f_scan` - WAF detection (fast)

### Cloud Security
- `prowler_scan` - AWS security ⚡ **Best for async**
- `scoutsuite_scan` - Multi-cloud audit ⚡ **Best for async**

### Binary Analysis
- `strings_analyze` - String extraction
- `binwalk_analyze` - Firmware analysis
- `radare2_analyze` - Reverse engineering

### Exploitation
- `hydra_bruteforce` - Password attacks ⚡ **Best for async**
- `hashcat_crack` - Hash cracking ⚡ **Best for async**
- `john_crack` - John the Ripper ⚡ **Best for async**
- `crackmapexec_scan` - Network pentesting

⚡ = Recommended for async (long-running scans)

---

## Workflow Pattern

### Typical Usage Flow

```
1. Start scan → Get job_id
2. Poll status → Wait for "completed"
3. Get results → Process findings
4. (Optional) Feed to AI agent for analysis
```

### Complete Example

```bash
#!/bin/bash

# 1. Start comprehensive nuclei scan
JOB_ID=$(curl -s -X POST http://localhost:3000/scans/start \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "nuclei_scan",
    "target": "https://ginandjuice.shop",
    "arguments": {"severity": "high,critical"}
  }' | jq -r '.job_id')

echo "Started scan: $JOB_ID"

# 2. Poll for completion (every 5 seconds)
while true; do
  STATUS=$(curl -s http://localhost:3000/scans/$JOB_ID/status | jq -r '.status')
  echo "Status: $STATUS"

  if [ "$STATUS" = "completed" ]; then
    break
  elif [ "$STATUS" = "failed" ]; then
    echo "Scan failed!"
    exit 1
  fi

  sleep 5
done

# 3. Get full results
curl -s http://localhost:3000/scans/$JOB_ID/results | jq > results.json

echo "Results saved to results.json"
```

---

## n8n Integration

### Method 1: HTTP Request Nodes (Polling)

**Workflow Structure**:
```
[Trigger] → [Start Scan] → [Wait 5s] → [Check Status] → [Loop Until Complete] → [Get Results] → [AI Agent]
```

**1. Start Scan (HTTP Request Node)**
- Method: POST
- URL: `http://mcp-security-server:3000/scans/start`
- Body:
  ```json
  {
    "tool": "nuclei_scan",
    "target": "{{ $json.target }}",
    "arguments": {
      "severity": "high,critical"
    }
  }
  ```
- Output: Save `job_id` to workflow data

**2. Wait Node**
- Wait: 5 seconds

**3. Check Status (HTTP Request Node)**
- Method: GET
- URL: `http://mcp-security-server:3000/scans/{{ $json.job_id }}/status`
- Output: Check if `status === "completed"`

**4. Loop (If Node)**
- Condition: If `status !== "completed"` → Go back to Wait Node
- Else: Continue to Get Results

**5. Get Results (HTTP Request Node)**
- Method: GET
- URL: `http://mcp-security-server:3000/scans/{{ $json.job_id }}/results`

**6. AI Agent Node**
- Feed results to AI for analysis and recommendations

---

### Method 2: Webhook Callback (Recommended)

**Workflow Structure**:
```
[Trigger] → [Start Scan with Webhook] → [Wait for Webhook] → [AI Agent]
```

**1. Webhook Node**
- Create webhook: `https://your-n8n.com/webhook/scan-complete`
- Wait for POST request

**2. Start Scan (HTTP Request Node)**
- Method: POST
- URL: `http://mcp-security-server:3000/scans/start`
- Body:
  ```json
  {
    "tool": "nuclei_scan",
    "target": "{{ $json.target }}",
    "arguments": {
      "severity": "high,critical"
    },
    "webhook_url": "https://your-n8n.com/webhook/scan-complete"
  }
  ```

**3. Webhook Receives Results**
- When scan completes, MCP server POSTs results to webhook
- Workflow continues automatically

**4. AI Agent Node**
- Process webhook payload with scan results

---

## Result Storage

### File System Storage
- Results saved to: `/tmp/scans/{job_id}.json`
- Persistent across container restarts (if `/tmp` is mounted)
- Automatic cleanup of old jobs (configurable)

### Cleanup Policy
- Jobs older than 24 hours are automatically removed
- Configure with `cleanup_old_jobs(max_age_hours=24)`

---

## Error Handling

### Common Errors

**1. Tool Not Found**
```json
{
  "error": "Tool 'invalid_tool' not found",
  "available_tools": ["nmap_scan", "nuclei_scan", ...]
}
```

**2. Invalid Target**
```json
{
  "error": "Target validation failed: IP is blacklisted"
}
```

**3. Job Not Found**
```json
{
  "error": "Scan job not found"
}
```

**4. Scan Failed**
```json
{
  "job_id": "...",
  "status": "failed",
  "error": "Command execution failed: nuclei returned non-zero exit code"
}
```

---

## Performance Considerations

### Typical Scan Durations

| Tool | Small Target | Medium Target | Large Target |
|------|--------------|---------------|--------------|
| httpx_scan | < 1s | 1-5s | 5-10s |
| wafw00f_scan | 1-2s | 2-5s | 5-10s |
| nmap_scan (quick) | 5-10s | 10-30s | 30-60s |
| nuclei_scan (high/critical) | 30-60s | 1-5m | 5-15m |
| nuclei_scan (all) | 2-5m | 5-15m | 15-60m |
| gobuster_scan | 30s-2m | 2-10m | 10-30m |
| nikto_scan | 1-3m | 3-10m | 10-30m |

### Recommendations

**Fast Tools (< 10s)** - Can use synchronous API:
- httpx_scan
- wafw00f_scan
- subfinder_scan

**Medium Tools (10s-2m)** - Consider async for better UX:
- nmap_scan (quick scans)
- nuclei_scan (high/critical only)

**Slow Tools (> 2m)** - Always use async:
- nuclei_scan (comprehensive)
- gobuster_scan
- nikto_scan
- prowler_scan
- hydra_bruteforce

---

## Testing

### Health Check
```bash
curl http://localhost:3000/health
```

### Quick Test (Fast Tool)
```bash
# Start httpx scan
JOB_ID=$(curl -s -X POST http://localhost:3000/scans/start \
  -H "Content-Type: application/json" \
  -d '{"tool":"httpx_scan","target":"https://ginandjuice.shop","arguments":{}}' \
  | jq -r '.job_id')

# Wait 3 seconds
sleep 3

# Get results (should be complete)
curl -s http://localhost:3000/scans/$JOB_ID/results | jq
```

### Full Test (Slow Tool)
```bash
# Start nuclei scan
JOB_ID=$(curl -s -X POST http://localhost:3000/scans/start \
  -H "Content-Type: application/json" \
  -d '{
    "tool":"nuclei_scan",
    "target":"https://ginandjuice.shop",
    "arguments":{"severity":"high,critical"}
  }' | jq -r '.job_id')

# Poll status every 10 seconds
watch -n 10 "curl -s http://localhost:3000/scans/$JOB_ID/status | jq"

# When complete, get results
curl -s http://localhost:3000/scans/$JOB_ID/results | jq > nuclei-results.json
```

---

## Security Considerations

1. **Target Validation**: All targets validated against authorized domains/networks
2. **Rate Limiting**: Consider implementing rate limits for scan creation
3. **Result Access Control**: Job IDs are UUIDs (hard to guess)
4. **Webhook Security**: Validate webhook URLs to prevent SSRF
5. **Result Cleanup**: Old results automatically removed

---

## Migration Guide

### From Synchronous to Async

**Before (Synchronous)**:
```python
# This could timeout with long scans
result = await nuclei_scan(
    target="https://example.com",
    severity="high,critical"
)
```

**After (Async)**:
```python
# 1. Start scan
job_id = create_scan(
    tool="nuclei_scan",
    target="https://example.com",
    arguments={"severity": "high,critical"}
)

# 2. Poll for completion
while True:
    status = get_scan_status(job_id)
    if status["status"] == "completed":
        break
    await asyncio.sleep(5)

# 3. Get results
result = get_scan_results(job_id)
```

---

## Troubleshooting

### Scan Stuck in "running" Status
- Check container logs: `docker logs mcp-security-server`
- Cancel and restart: `curl -X POST http://localhost:3000/scans/{job_id}/cancel`

### Results Not Available
- Verify scan completed: `curl http://localhost:3000/scans/{job_id}/status`
- Check result file exists: `docker exec mcp-security-server ls /tmp/scans/`

### Webhook Not Called
- Verify webhook URL is accessible from container
- Check container logs for webhook errors
- Test webhook manually with curl

---

## API Reference Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/scans/start` | POST | Start async scan |
| `/scans/{job_id}/status` | GET | Check scan status |
| `/scans/{job_id}/results` | GET | Get scan results |
| `/scans` | GET | List all scans |
| `/scans/{job_id}/cancel` | POST | Cancel scan |

---

**Updated**: 2026-01-14
**Version**: 1.0.0
