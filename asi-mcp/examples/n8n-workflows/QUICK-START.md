# Quick Start: Import n8n Workflows in 5 Minutes

Get up and running with MCP Security Server n8n workflows in 5 minutes.

---

## Prerequisites

Before you begin, ensure:
- ✅ MCP Security Server is running (`docker ps | grep mcp-security-server`)
- ✅ n8n instance is running and accessible
- ✅ Both containers can communicate (same network or accessible URLs)

---

## Step 1: Test MCP Server (30 seconds)

Verify the MCP server is working:

```bash
# Test health endpoint
curl http://localhost:3000/health

# Expected output:
# {"status":"healthy","service":"mcp-security-server","version":"1.0.0"}

# Test async scan API
curl -X POST http://localhost:3000/scans/start \
  -H "Content-Type: application/json" \
  -d '{"tool":"httpx_scan","target":"https://example.com","arguments":{}}'

# Expected output:
# {"job_id":"...","status":"pending",...}
```

✅ If both commands succeed, proceed to Step 2.

❌ If they fail:
- Check container: `docker logs mcp-security-server`
- Verify port 3000 is accessible
- Ensure container is running: `docker-compose up -d`

---

## Step 2: Import Your First Workflow (2 minutes)

### Option A: Start with Polling Pattern (Easiest)

**Recommended for**: First-time users, learning, debugging

1. **Download the workflow file**
   ```bash
   # If you have the repo
   cd mcp-security-server/examples/n8n-workflows/

   # Open async-security-scan-polling.json
   ```

2. **Import into n8n**
   - Open n8n in your browser
   - Click **"+"** → **"Import from File"** (or use Ctrl+O / Cmd+O)
   - Select `async-security-scan-polling.json`
   - Click **"Import"**

3. **You should see**:
   - 16 nodes in a workflow
   - Starts with "Manual Trigger"
   - Ends with "Final Report"

---

## Step 3: Configure the Workflow (1 minute)

### Update MCP Server URL

If your MCP server is **not** at `http://mcp-security-server:3000`:

1. **Find these nodes** (use Ctrl+F to search):
   - "Start Async Scan"
   - "Check Scan Status"
   - "Get Scan Results"

2. **Update URL in each node**:
   - Click node → Parameters tab
   - Change URL from `http://mcp-security-server:3000/...`
   - To your URL: `http://localhost:3000/...` (or your actual URL)

### Configure Target (Optional)

1. Click **"Set Target Config"** node
2. Update these values:
   ```
   target:   https://ginandjuice.shop  (change to your authorized target)
   tool:     nuclei_scan               (or any other tool)
   severity: high,critical             (or adjust as needed)
   ```

---

## Step 4: Test the Workflow (1 minute)

### Execute Test Run

1. Click **"Execute Workflow"** button (top right)
2. Watch the nodes light up in sequence
3. Monitor progress in real-time

### What You Should See

```
✓ Manual Trigger          (instant)
✓ Set Target Config       (instant)
✓ Start Async Scan        (1 second)
✓ Save Job Info           (instant)
⏳ Wait 10 Seconds         (10 seconds)
⏳ Check Scan Status       (polling...)
⏳ Wait 10 Seconds         (10 seconds)
⏳ Check Scan Status       (polling...)
  ... (repeats until complete)
✓ Get Scan Results        (1 second)
✓ Format Results          (instant)
✓ Prepare AI Input        (instant)
⏳ AI Security Analysis    (10-30 seconds) *requires Anthropic API
✓ Final Report            (instant)
```

### Check Results

1. Click the **"Final Report"** node
2. View the **Output** tab
3. You should see:
   ```json
   {
     "job_id": "...",
     "tool": "nuclei_scan",
     "target": "https://...",
     "duration": 112.96,
     "scan_results": {...},
     "ai_analysis": "..."
   }
   ```

---

## Step 5: Next Steps (Optional)

### Set Up Anthropic API (for AI Analysis)

If AI nodes show "Missing credentials" error:

1. Get Anthropic API key from https://console.anthropic.com/
2. In n8n: **Settings** → **Credentials** → **Add Credential**
3. Select **"Anthropic API"**
4. Paste API key
5. Save
6. Click **"AI Security Analysis"** node → **Credential to connect with** → Select your credential

### Try Other Workflows

Once polling works, try:

**Webhook Pattern** (more efficient):
- Import `async-security-scan-webhook.json`
- Automatically gets results when complete
- No polling needed

**Multi-Tool Assessment** (comprehensive):
- Import `comprehensive-security-assessment.json`
- Runs 4 tools concurrently
- Integrated AI analysis

---

## Common Issues

### Issue: "Cannot connect to mcp-security-server:3000"

**Solution**:
```bash
# Test from n8n container
docker exec n8n curl http://mcp-security-server:3000/health

# If fails, check if containers on same network
docker network inspect bridge | grep mcp-security-server
docker network inspect bridge | grep n8n

# Connect them to same network if needed
docker network create security-network
docker network connect security-network mcp-security-server
docker network connect security-network n8n
```

### Issue: "Scan times out"

**Solution**:
- Increase `max_retries` in "Save Job Info" node
- Or use webhook pattern (no timeout)
- Check scan status manually:
  ```bash
  curl http://localhost:3000/scans/{job_id}/status
  ```

### Issue: "AI node error"

**Solution**:
- Skip AI nodes for testing (disconnect them)
- Or configure Anthropic credentials (see Step 5)
- AI analysis is optional

---

## Quick Reference Card

```
╔══════════════════════════════════════════════════════════════════╗
║                   QUICK COMMAND REFERENCE                        ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  Check MCP Health:                                               ║
║  curl http://localhost:3000/health                               ║
║                                                                  ║
║  Start Test Scan:                                                ║
║  curl -X POST http://localhost:3000/scans/start \                ║
║    -H "Content-Type: application/json" \                         ║
║    -d '{"tool":"httpx_scan","target":"https://example.com",\     ║
║         "arguments":{}}'                                         ║
║                                                                  ║
║  Check Scan Status:                                              ║
║  curl http://localhost:3000/scans/{job_id}/status                ║
║                                                                  ║
║  Get Scan Results:                                               ║
║  curl http://localhost:3000/scans/{job_id}/results               ║
║                                                                  ║
║  List All Scans:                                                 ║
║  curl http://localhost:3000/scans                                ║
║                                                                  ║
║  View Container Logs:                                            ║
║  docker logs mcp-security-server --tail 50                       ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## Available Tools

All 22 security tools work with async scans:

**Fast (< 5s)** - Test with these first:
- `httpx_scan` - HTTP probing
- `wafw00f_scan` - WAF detection
- `subfinder_scan` - Subdomain enum

**Medium (5s-2m)** - Good for learning:
- `nmap_scan` - Port scanning
- `nuclei_scan` (filtered) - Vuln scanning

**Slow (> 2m)** - Use async pattern:
- `nuclei_scan` (comprehensive)
- `gobuster_scan` - Directory enum
- `nikto_scan` - Web server scan

See `docs/async-scan-api.md` for complete tool reference.

---

## Success Checklist

Before going to production, verify:

- [ ] MCP server health endpoint responds
- [ ] Can start async scan and get job_id
- [ ] Can poll status and see "running" → "completed"
- [ ] Can retrieve full results
- [ ] Polling workflow executes successfully
- [ ] (Optional) Webhook workflow receives callbacks
- [ ] (Optional) AI analysis nodes configured

---

## Help and Support

### Documentation
- Full guide: `README.md` (in this directory)
- API reference: `../../docs/async-scan-api.md`
- Visual diagrams: `WORKFLOW-DIAGRAMS.md`

### Testing
```bash
# Run comprehensive test
./test-async-scans.sh

# Test specific tool
curl -X POST http://localhost:3000/scans/start \
  -d '{"tool":"YOUR_TOOL","target":"YOUR_TARGET","arguments":{}}'
```

### Debugging
```bash
# Check what's running
curl http://localhost:3000/scans?status=running

# View logs
docker logs mcp-security-server --tail 100 -f

# Cancel stuck scan
curl -X POST http://localhost:3000/scans/{job_id}/cancel
```

---

## What's Next?

### After Your First Successful Run

1. **Customize the workflow**
   - Change target to your authorized systems
   - Add more security tools
   - Customize AI prompts

2. **Set up scheduled scans**
   - Add Schedule Trigger node
   - Run daily security checks
   - Email reports automatically

3. **Try advanced patterns**
   - Import webhook workflow (more efficient)
   - Import multi-tool workflow (comprehensive)
   - Build custom workflows

4. **Production deployment**
   - Set up proper authentication
   - Configure webhook callbacks
   - Implement result storage
   - Add monitoring alerts

---

## Success! 🎉

You now have a working security scanning workflow in n8n!

**What you've accomplished**:
- ✅ Imported n8n workflow
- ✅ Configured MCP server connection
- ✅ Executed first async security scan
- ✅ Retrieved and viewed results

**Next**: Explore the other workflows in this directory!

---

**Time to Complete**: ~5 minutes
**Difficulty**: Easy ⭐
**Status**: Production Ready ✅
