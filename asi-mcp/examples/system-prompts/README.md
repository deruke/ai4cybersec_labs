# System Prompts for MCP Security AI Agent

This directory contains optimized system prompts for different use cases.

## Available Prompts

### 1. **security-agent-prompt.md** (Comprehensive)
**Use Case**: Professional penetration testing training
**Audience**: Security professionals, advanced students
**Length**: ~2500 words
**Features**:
- Complete methodology breakdown
- Detailed tool usage guidelines
- Response templates
- Example workflows
- Comprehensive reporting format

**Best For**: Self-hosted LLMs with large context windows, detailed training scenarios

---

### 2. **n8n-short-prompt.txt** (Recommended for n8n) ⭐
**Use Case**: Production n8n workflows
**Audience**: General security testing
**Length**: ~500 words
**Features**:
- Concise methodology
- Quick tool selection guide
- Clear communication style
- Practical examples
- Optimized for token efficiency

**Best For**: Most n8n AI agent implementations, balanced detail/brevity

---

### 3. **student-friendly-prompt.txt** (Educational)
**Use Case**: Beginner cybersecurity training
**Audience**: Students, newcomers to pentesting
**Length**: ~1200 words
**Features**:
- Step-by-step explanations
- Simple terminology
- Educational analogies
- Beginner-friendly examples
- Concept teaching built-in

**Best For**: Training classes, CTF workshops, educational labs

---

## How to Use in n8n

### Method 1: Direct Copy-Paste (Recommended)

1. Open your n8n workflow
2. Find the **AI Agent** node
3. In the **System Message** field, copy and paste your chosen prompt
4. Save the workflow

**For most users, use `n8n-short-prompt.txt`**

### Method 2: File Reference

If your n8n instance can read files:

```javascript
{{ $filesystem.readFile('/path/to/n8n-short-prompt.txt') }}
```

### Example n8n Configuration

```yaml
AI Agent Node:
  System Message: [Paste content from n8n-short-prompt.txt]
  Model: Your preferred model (GPT-4, Claude, Ollama, etc.)
  Temperature: 0.3 (for consistent, focused responses)
  Max Tokens: 2000 (adjust based on your needs)

MCP Client Node:
  Endpoint URL: http://mcp-security-server:3000/sse
  Server Transport: sse
```

---

## Customization Tips

### Adjust Tone
Add to the beginning of any prompt:
- **Strict Professional**: "Use formal technical language. Be precise and concise."
- **Conversational**: "Be friendly and approachable while maintaining technical accuracy."
- **Detailed**: "Provide extensive explanations for every action and finding."

### Add Specific Focus
Append to any prompt:
- **Web-Only**: "Focus primarily on web application testing tools."
- **Network-Heavy**: "Prioritize network reconnaissance and enumeration."
- **OWASP Top 10**: "Frame findings in terms of OWASP Top 10 categories."

### Modify for Your Network
Replace IP ranges in prompts with your specific training environment:
```
Old: "10.x, 172.16.x, 192.168.x"
New: "172.20.0.0/24, 10.50.0.0/16"
```

---

## Testing Your Prompt

After configuring, test with these queries:

### Basic Functionality
```
"What security tools do you have available?"
```
Expected: Categorized list with brief descriptions

### Methodology Check
```
"How would you scan 192.168.1.100?"
```
Expected: Step-by-step approach with tool selection rationale

### Interpretation Test
```
"Scan 192.168.1.50 for vulnerabilities"
```
Expected: Execution of tools + interpretation of results + recommendations

### Educational Test (for student prompt)
```
"What is port scanning and why do we do it?"
```
Expected: Simple explanation with analogies

---

## Prompt Performance Comparison

| Prompt | Tokens | Response Quality | Speed | Best For |
|--------|--------|-----------------|-------|----------|
| Comprehensive | ~3500 | Excellent | Slower | Documentation, training |
| n8n-short | ~700 | Very Good | Fast | Production workflows |
| Student-friendly | ~1800 | Good (Educational) | Medium | Beginner training |

---

## Common Issues & Solutions

### Issue: Agent not using tools
**Solution**: Ensure this is in your prompt:
```
"You have access to security tools via MCP. Always use the appropriate tool when asked to scan or test targets."
```

### Issue: Too verbose
**Solution**: Add:
```
"Be concise. Summarize findings. Don't show full raw output unless requested."
```

### Issue: Not explaining actions
**Solution**: Add:
```
"Always explain what tool you're using and why before executing it."
```

### Issue: Skipping steps
**Solution**: Add:
```
"Follow the methodology systematically. Complete each phase before moving to the next."
```

---

## Advanced: Custom Prompts

### Creating Your Own

Structure your custom prompt with these sections:

```
1. ROLE DEFINITION
   - Who the agent is
   - What environment it's in
   - Core purpose

2. METHODOLOGY
   - Step-by-step approach
   - Tool selection logic

3. TOOL REFERENCE
   - Quick tool descriptions
   - When to use each

4. COMMUNICATION STYLE
   - How to present findings
   - Formatting preferences

5. EXAMPLES
   - Sample interactions
   - Expected outputs

6. CONSTRAINTS
   - What NOT to do
   - Safety reminders
```

### Template
```
You are a [ROLE] for [PURPOSE] in [ENVIRONMENT].

METHODOLOGY:
1. [Phase 1]: [Description]
2. [Phase 2]: [Description]
...

TOOLS:
- [tool_name]: [when to use]
...

STYLE:
[Communication preferences]

EXAMPLE:
User: [query]
You: [response structure]

REMEMBER:
- [Key constraint 1]
- [Key constraint 2]
```

---

## Updating Prompts

When updating prompts in active workflows:

1. **Test in development** first
2. **Compare outputs** with old vs new prompt
3. **Document changes** in your workflow
4. **Monitor first few runs** for unexpected behavior
5. **Gather feedback** from users

---

## Feedback & Iteration

Track these metrics to improve your prompts:
- **Tool Usage Rate**: Are tools being used appropriately?
- **Accuracy**: Are findings correctly interpreted?
- **Efficiency**: Are unnecessary tools being avoided?
- **User Satisfaction**: Are responses helpful?

---

## License & Attribution

These prompts are provided for educational cybersecurity training purposes.
Feel free to modify and adapt for your specific training environment.

**Attribution**: MCP Security Training Server - Black Hills InfoSec

---

## Support

For questions or improvements:
- Review examples in `/examples/n8n-workflows/`
- Check main README.md for troubleshooting
- Test prompts with different models to find best fit
