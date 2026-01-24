# n8n Workflow Visual Diagrams

Visual representations of the security assessment workflows.

---

## 1. Async Polling Pattern Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ASYNC SECURITY SCAN - POLLING PATTERN                     │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────┐
    │   Manual    │
    │  Trigger    │
    └──────┬──────┘
           │
           v
    ┌─────────────┐
    │ Set Target  │
    │   Config    │
    │             │
    │ • target    │
    │ • tool      │
    │ • severity  │
    └──────┬──────┘
           │
           v
    ┌─────────────┐
    │ Start Async │
    │    Scan     │◄─────────┐
    │             │          │
    │ POST /scans/│          │
    │    start    │          │
    └──────┬──────┘          │
           │                 │
           │ Returns job_id  │
           v                 │
    ┌─────────────┐          │
    │ Save Job    │          │
    │    Info     │          │
    │             │          │
    │ • job_id    │          │
    │ • retry=0   │          │
    │ • max=60    │          │
    └──────┬──────┘          │
           │                 │
           v                 │
    ┌─────────────┐          │
    │ Wait 10s    │          │
    └──────┬──────┘          │
           │                 │
           v                 │
    ┌─────────────┐          │
    │ Check Scan  │          │
    │   Status    │          │
    │             │          │
    │ GET /scans/ │          │
    │  {id}/status│          │
    └──────┬──────┘          │
           │                 │
           v                 │
      ┌────────┐             │
      │  Is    │             │
      │Complete│             │
      │   ?    │             │
      └───┬─┬──┘             │
          │ │                │
    YES   │ │   NO           │
          │ │                │
          │ └───────────┐    │
          │             │    │
          │             v    │
          │      ┌──────────┐│
          │      │ Is Failed││
          │      │    ?     ││
          │      └───┬───┬──┘│
          │          │   │   │
          │    YES   │   │NO │
          │          │   │   │
          │          v   v   │
          │      ┌─────────┐ │
          │      │Can Retry│ │
          │      │   ?     │ │
          │      └───┬───┬─┘ │
          │          │   │   │
          │     YES  │   │NO │
          │          │   │   │
          │          │   v   │
          │          │ ┌───────┐
          │          │ │Timeout│
          │          │ │ Error │
          │          │ └───────┘
          │          │
          │          v
          │   ┌──────────────┐
          │   │  Increment   │
          │   │    Retry     │
          │   └──────┬───────┘
          │          │
          │          └────────────┘
          │
          v
    ┌─────────────┐
    │ Get Scan    │
    │  Results    │
    │             │
    │ GET /scans/ │
    │ {id}/results│
    └──────┬──────┘
           │
           v
    ┌─────────────┐
    │   Format    │
    │  Results    │
    └──────┬──────┘
           │
           v
    ┌─────────────┐
    │  Prepare    │
    │  AI Input   │
    └──────┬──────┘
           │
           v
    ┌─────────────┐
    │     AI      │
    │  Security   │
    │  Analysis   │
    │             │
    │ • Summary   │
    │ • Risk      │
    │ • Recommend │
    └──────┬──────┘
           │
           v
    ┌─────────────┐
    │   Final     │
    │   Report    │
    │             │
    │ • Job ID    │
    │ • Results   │
    │ • AI Output │
    └─────────────┘

KEY:
  ┌─────┐
  │ Box │  = Workflow Node
  └─────┘

  ───►    = Data Flow

  ◄────   = Loop Back

EXECUTION TIME: 2-10 minutes (depends on scan complexity)
API CALLS: ~60 (1 per retry attempt)
```

---

## 2. Async Webhook Pattern Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   ASYNC SECURITY SCAN - WEBHOOK PATTERN                      │
└─────────────────────────────────────────────────────────────────────────────┘

PART 1: START SCAN
═══════════════════

    ┌─────────────┐
    │   Manual    │
    │  Trigger    │
    └──────┬──────┘
           │
           v
    ┌─────────────┐
    │ Configure   │
    │    Scan     │
    │             │
    │ • target    │
    │ • tool      │
    │ • webhook   │
    │   URL       │
    └──────┬──────┘
           │
           v
    ┌─────────────┐
    │ Start Scan  │
    │    With     │
    │  Webhook    │
    │             │
    │ POST /scans/│
    │    start    │
    └──────┬──────┘
           │
           │ Returns confirmation
           v
    ┌─────────────┐
    │    Scan     │
    │   Started   │
    │  (message)  │
    └─────────────┘

           ║
           ║ Workflow waits...
           ║ Scan runs in background...
           ║


PART 2: RECEIVE RESULTS (Triggered by MCP Server)
═══════════════════════════════════════════════

    ┌─────────────┐
    │  Webhook    │◄───────┐
    │   Receives  │        │
    │  POST from  │        │
    │     MCP     │        │ MCP Server POSTs
    └──────┬──────┘        │ results when
           │               │ scan completes
           v               │
      ┌────────┐           │
      │   Is   │           │
      │Success?│           │
      └───┬─┬──┘           │
          │ │              │
    YES   │ │   NO         │
          │ │              │
          │ └──────┐       │
          │        │       │
          v        v       │
    ┌─────────┐ ┌────────┐│
    │ Extract │ │ Handle ││
    │ Results │ │ Error  ││
    └────┬────┘ └────────┘│
         │                 │
         v                 │
    ┌─────────┐            │
    │ Prepare │            │
    │ For AI  │            │
    └────┬────┘            │
         │                 │
         v                 │
    ┌─────────┐            │
    │   AI    │            │
    │Security │            │
    │Assess.  │            │
    │         │            │
    │• Exec   │            │
    │ Summary │            │
    │• Findings│           │
    │• Risk   │            │
    │• Actions│            │
    └────┬────┘            │
         │                 │
         v                 │
    ┌─────────┐            │
    │Security │            │
    │ Report  │            │
    │         │            │
    │Complete │            │
    └────┬────┘            │
         │                 │
         v                 │
    ┌─────────┐            │
    │  Send   │            │
    │Response │            │
    │ (200 OK)│────────────┘
    └─────────┘

KEY:
  ═══════  = Major workflow sections
  ║        = Waiting/async gap
  ◄─────   = Callback/webhook

EXECUTION TIME: 2-10 minutes (same as polling, but no polling overhead)
API CALLS: 2 (start + webhook callback)
EFFICIENCY: ~97% fewer API calls than polling
```

---

## 3. Comprehensive Multi-Tool Assessment Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│            COMPREHENSIVE SECURITY ASSESSMENT - MULTI-TOOL                    │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────┐
    │   Manual    │
    │  Trigger    │
    └──────┬──────┘
           │
           v
    ┌─────────────┐
    │ Set Target  │
    │             │
    │ target URL  │
    └──────┬──────┘
           │
           ├───────────────┬───────────────┬───────────────┐
           │               │               │               │
           v               v               v               v
    ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐
    │  Start:   │   │  Start:   │   │  Start:   │   │  Start:   │
    │   httpx   │   │  wafw00f  │   │  nuclei   │   │ gobuster  │
    │           │   │           │   │           │   │           │
    │Tech Stack │   │    WAF    │   │   Vulns   │   │   Dirs    │
    │ Detection │   │ Detection │   │  Scanning │   │   Enum    │
    └─────┬─────┘   └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
          │               │               │               │
          │   All scans run concurrently  │               │
          │    (parallel execution)       │               │
          │               │               │               │
          └───────┬───────┴───────┬───────┴───────┬───────┘
                  │               │               │
                  v               v               v
           ┌──────────────────────────────────────────┐
           │          Merge Job IDs                   │
           │                                          │
           │  job_ids = [httpx_id, waf_id,          │
           │             nuclei_id, gobuster_id]     │
           └──────────────────┬───────────────────────┘
                              │
                              v
                       ┌──────────────┐
                       │  Wait 30s    │
                       │              │
                       │ Allows time  │
                       │ for scans to │
                       │  complete    │
                       └──────┬───────┘
                              │
                              v
                       ┌──────────────┐
                       │  Get All     │
                       │  Completed   │
                       │   Scans      │
                       │              │
                       │ GET /scans?  │
                       │status=done   │
                       └──────┬───────┘
                              │
                              v
                       ┌──────────────┐
                       │  Split Jobs  │
                       │              │
                       │ Separate     │
                       │ into array   │
                       └──────┬───────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
                v             v             v
         ┌───────────┐ ┌───────────┐ ┌───────────┐
         │Get Result │ │Get Result │ │Get Result │
         │    #1     │ │    #2     │ │    #N     │
         └─────┬─────┘ └─────┬─────┘ └─────┬─────┘
               │             │             │
               └─────────────┼─────────────┘
                             │
                             v
                      ┌──────────────┐
                      │  Aggregate   │
                      │ All Results  │
                      │              │
                      │  Combine     │
                      │  into one    │
                      │  dataset     │
                      └──────┬───────┘
                             │
                             v
                      ┌──────────────┐
                      │   Format     │
                      │Comprehensive │
                      │   Report     │
                      │              │
                      │ • httpx      │
                      │ • wafw00f    │
                      │ • nuclei     │
                      │ • gobuster   │
                      └──────┬───────┘
                             │
                             v
                      ┌──────────────┐
                      │      AI      │
                      │Comprehensive │
                      │  Analysis    │
                      │              │
                      │ Analyzes ALL │
                      │ tools together│
                      │ for integrated│
                      │ assessment   │
                      └──────┬───────┘
                             │
                             v
                      ┌──────────────┐
                      │    Final     │
                      │  Assessment  │
                      │    Report    │
                      │              │
                      │ • All results│
                      │ • AI analysis│
                      │ • Exec summary│
                      │ • Priorities │
                      └──────────────┘

PARALLEL EXECUTION BENEFIT:
  Sequential: 1s + 2s + 120s + 120s = 243s (4 min)
  Parallel:   max(1s, 2s, 120s, 120s) = 120s (2 min)
  Speedup:    2x faster ✨

SCAN SUMMARY:
  httpx:    < 1s  (tech stack, CDN, headers)
  wafw00f:  1-2s  (WAF type and vendor)
  nuclei:   60-120s (vulnerabilities)
  gobuster: 60-120s (hidden directories)

TOTAL TIME: ~2-3 minutes for typical website
API CALLS: ~10 (4 start + 1 list + 4 results + 1 aggregate)
```

---

## Comparison Matrix

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        WORKFLOW COMPARISON MATRIX                          │
└────────────────────────────────────────────────────────────────────────────┘

╔═══════════════╦═══════════════╦═══════════════╦═══════════════════════════╗
║   Feature     ║   Polling     ║   Webhook     ║   Multi-Tool              ║
╠═══════════════╬═══════════════╬═══════════════╬═══════════════════════════╣
║ Complexity    ║ Low ⭐        ║ Medium ⭐⭐    ║ Medium ⭐⭐                ║
║               ║ Easy to debug ║ Need webhooks ║ Multiple scans            ║
╠═══════════════╬═══════════════╬═══════════════╬═══════════════════════════╣
║ API Calls     ║ ~60 calls     ║ 2 calls       ║ ~10 calls                 ║
║               ║ (inefficient) ║ (efficient)   ║ (moderate)                ║
╠═══════════════╬═══════════════╬═══════════════╬═══════════════════════════╣
║ Setup Time    ║ 5 minutes     ║ 10 minutes    ║ 15 minutes                ║
║               ║ (simple)      ║ (webhooks)    ║ (multiple tools)          ║
╠═══════════════╬═══════════════╬═══════════════╬═══════════════════════════╣
║ Best For      ║ • Learning    ║ • Production  ║ • Complete audits         ║
║               ║ • Development ║ • Scheduled   ║ • Pen testing             ║
║               ║ • Debugging   ║ • Long scans  ║ • Executive reports       ║
╠═══════════════╬═══════════════╬═══════════════╬═══════════════════════════╣
║ Scan Types    ║ Single tool   ║ Single tool   ║ 4+ tools                  ║
║               ║ (nuclei)      ║ (any)         ║ (concurrent)              ║
╠═══════════════╬═══════════════╬═══════════════╬═══════════════════════════╣
║ Output        ║ Basic report  ║ Basic report  ║ Comprehensive             ║
║               ║               ║               ║ integrated report         ║
╠═══════════════╬═══════════════╬═══════════════╬═══════════════════════════╣
║ Timeout Risk  ║ Low           ║ None          ║ Low                       ║
║               ║ (configurable)║ (webhook)     ║ (async)                   ║
╠═══════════════╬═══════════════╬═══════════════╬═══════════════════════════╣
║ Production    ║ ⭐⭐⭐        ║ ⭐⭐⭐⭐⭐      ║ ⭐⭐⭐⭐                   ║
║ Ready         ║ Good          ║ Excellent     ║ Very Good                 ║
╚═══════════════╩═══════════════╩═══════════════╩═══════════════════════════╝
```

---

## Decision Tree: Which Workflow Should I Use?

```
                    START
                      │
                      v
           ┌──────────────────────┐
           │ Do you need webhooks │
           │    or polling?       │
           └────────┬──────┬──────┘
                    │      │
            Webhooks│      │Polling
                    │      │
                    v      v
         ┌─────────────────────────────┐
         │ How many tools do you need? │
         └──────┬──────────────┬───────┘
                │              │
        1 tool  │              │ Multiple
                │              │
                v              v
       ┌──────────────┐  ┌─────────────┐
       │   Webhook    │  │ Multi-Tool  │
       │   Pattern    │  │Comprehensive│
       └──────────────┘  └─────────────┘
                |
                |
       1 tool   |
                v
       ┌──────────────┐
       │   Polling    │
       │   Pattern    │
       └──────────────┘


RECOMMENDATION BY USE CASE:
═══════════════════════════

┌─ Learning / Development ─────────────┐
│ Use: Polling Pattern                 │
│ Why: Easier to debug and understand  │
└──────────────────────────────────────┘

┌─ Production / Scheduled Scans ───────┐
│ Use: Webhook Pattern                 │
│ Why: Most efficient, no polling      │
└──────────────────────────────────────┘

┌─ Security Audits / Pen Tests ────────┐
│ Use: Multi-Tool Comprehensive        │
│ Why: Complete coverage, all tools    │
└──────────────────────────────────────┘

┌─ Quick Bug Bounty Recon ─────────────┐
│ Use: Multi-Tool (with fast tools)    │
│ Why: Parallel execution = speed      │
└──────────────────────────────────────┘
```

---

## Data Flow Diagrams

### Polling Pattern Data Flow

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│  User   │────►│   n8n   │────►│   MCP   │────►│  Tool   │
│ Browser │     │Workflow │     │ Server  │     │ (nuclei)│
└─────────┘     └────┬────┘     └────┬────┘     └────┬────┘
                     │               │               │
                     │ 1. POST start │               │
                     ├──────────────►│               │
                     │               │ 2. Execute    │
                     │               ├──────────────►│
                     │               │               │
                     │◄──────────────┤               │
                     │ job_id        │               │
                     │               │               │
  ┌──────────────────┘               │               │
  │ Loop every 10s                   │               │
  │                                  │               │
  │ 3. GET status                    │               │
  ├──────────────────────────────────►│               │
  │                                  │               │
  │◄──────────────────────────────────┤               │
  │ status: running                   │◄──────────────┤
  │                                  │ 4. Results    │
  │ 5. GET status                    │               │
  ├──────────────────────────────────►│               │
  │                                  │               │
  │◄──────────────────────────────────┤               │
  └─ status: completed                │               │
                     │               │               │
                     │ 6. GET results│               │
                     ├──────────────►│               │
                     │               │               │
                     │◄──────────────┤               │
                     │ Full results  │               │
                     │               │               │
                     v               v               v
```

### Webhook Pattern Data Flow

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│  User   │────►│   n8n   │────►│   MCP   │────►│  Tool   │
│ Browser │     │Workflow │     │ Server  │     │ (nuclei)│
└─────────┘     └────┬────┘     └────┬────┘     └────┬────┘
                     │               │               │
                     │ 1. POST start │               │
                     │  +webhook_url │               │
                     ├──────────────►│               │
                     │               │ 2. Execute    │
                     │               ├──────────────►│
                     │◄──────────────┤               │
                     │ confirmation  │               │
                     │               │               │
                     │ [n8n waits]   │ [scan runs]   │
                     │               │               │
                     │               │◄──────────────┤
                     │               │ 3. Results    │
                     │               │               │
                     │ 4. POST       │               │
                     │  results to   │               │
                     │  webhook      │               │
                     │◄──────────────┤               │
                     │ Full results  │               │
                     │               │               │
                     │ 5. Process &  │               │
                     │    Respond    │               │
                     ├──────────────►│               │
                     │ 200 OK        │               │
                     │               │               │
                     v               v               v

KEY BENEFIT: Only 2 HTTP requests (vs ~60 for polling)
```

---

## Timing Diagrams

### Polling vs Webhook Comparison

```
TIME ────────────────────────────────────────────────────────────────►

POLLING PATTERN:
0s    10s   20s   30s   40s   50s   60s   70s   80s   90s   100s  110s  120s
│     │     │     │     │     │     │     │     │     │     │     │     │
▼     ▼     ▼     ▼     ▼     ▼     ▼     ▼     ▼     ▼     ▼     ▼     ▼
START check check check check check check check check check check check DONE
  │     X     X     X     X     X     X     X     X     X     X     X     ✓
  └───────────────────────────────────────────────────────────────────────┘
         12 status checks (12 API calls) before completion


WEBHOOK PATTERN:
0s    10s   20s   30s   40s   50s   60s   70s   80s   90s   100s  110s  120s
│                                                                         │
▼                                                                         ▼
START                      [n8n waits silently]                        WEBHOOK
  │                                                                         ✓
  └─────────────────────────────────────────────────────────────────────────┘
         1 callback (1 API call) when complete

EFFICIENCY: Webhook uses 92% fewer API calls (1 vs 12)
```

---

## Error Handling Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ERROR HANDLING PATHS                                │
└─────────────────────────────────────────────────────────────────────────────┘

                         ┌───────────┐
                         │Check Status│
                         └─────┬─────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              v                v                v
        ┌──────────┐     ┌──────────┐    ┌──────────┐
        │completed │     │ running  │    │  failed  │
        └────┬─────┘     └────┬─────┘    └────┬─────┘
             │                │                │
             │                │                │
             v                v                v
       ┌──────────┐     ┌──────────┐    ┌──────────┐
       │Get Results│    │Can Retry?│    │  Handle  │
       └────┬─────┘     └────┬──┬──┘    │  Error   │
            │                │  │        └────┬─────┘
            │           YES  │  │ NO          │
            │                │  │             │
            │                v  v             │
            │         ┌──────────┐      ┌─────────┐
            │         │Increment │      │Timeout  │
            │         │ & Loop   │      │ Error   │
            │         └────┬─────┘      └────┬────┘
            │              │                  │
            │              └──────────┐       │
            │                         │       │
            v                         v       v
       ┌─────────────────────────────────────────┐
       │          FINAL OUTPUT                   │
       │                                         │
       │ • Success Report                        │
       │ • Error Message                         │
       │ • Timeout Notice                        │
       └─────────────────────────────────────────┘
```

---

## n8n Node Anatomy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TYPICAL HTTP REQUEST NODE                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│  HTTP Request: Start Async Scan                               │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  Method:         POST                                         │
│  URL:            http://mcp-security-server:3000/scans/start  │
│  Authentication: None                                         │
│                                                               │
│  ┌─ Body ────────────────────────────────────────────────┐   │
│  │ {                                                     │   │
│  │   "tool": "nuclei_scan",                             │   │
│  │   "target": "={{ $json.target }}",                   │   │
│  │   "arguments": {                                     │   │
│  │     "severity": "high,critical"                      │   │
│  │   }                                                  │   │
│  │ }                                                     │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌─ Output ──────────────────────────────────────────────┐   │
│  │ {                                                     │   │
│  │   "job_id": "3ef5d95c-...",                          │   │
│  │   "status": "pending",                               │   │
│  │   "tool": "nuclei_scan",                             │   │
│  │   "target": "https://...",                           │   │
│  │   "message": "Scan job created and started",         │   │
│  │   "status_url": "/scans/.../status",                 │   │
│  │   "results_url": "/scans/.../results"                │   │
│  │ }                                                     │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                               │
│  [Execute]  [Test]  [Add Note]                               │
└───────────────────────────────────────────────────────────────┘
```

---

## Summary Statistics

```
╔══════════════════════════════════════════════════════════════════════════╗
║                         WORKFLOW STATISTICS                              ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  POLLING WORKFLOW                                                        ║
║  • Nodes: 16                                                             ║
║  • Connections: 20                                                       ║
║  • Average execution: 2-10 minutes                                       ║
║  • API calls: ~60 (varies by scan duration)                              ║
║                                                                          ║
║  WEBHOOK WORKFLOW                                                        ║
║  • Nodes: 11                                                             ║
║  • Connections: 10                                                       ║
║  • Average execution: 2-10 minutes                                       ║
║  • API calls: 2 (start + callback)                                       ║
║                                                                          ║
║  MULTI-TOOL WORKFLOW                                                     ║
║  • Nodes: 14                                                             ║
║  • Connections: 17                                                       ║
║  • Average execution: 2-3 minutes                                        ║
║  • API calls: ~10 (4 starts + list + 4 results)                          ║
║  • Concurrent scans: 4                                                   ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
```

---

**Generated**: 2026-01-14
**For**: MCP Security Server v1.0.0
