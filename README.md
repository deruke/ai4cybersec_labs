# AI for Cybersecurity Professionals - Lab Environment

This repository contains a complete lab environment for learning about AI in cybersecurity, including:

- **Prompt Injection CTF**: 5 challenges teaching LLM security concepts
- **Jupyter Notebooks**: Hands-on labs for phishing detection with ML/AI
- **Open WebUI**: Chat interface for interacting with LLM challenges
- **n8n**: n8n security automation workflows
- **asi-mcp**: Custom MCP server with cyber security tools that work with n8n

Note that this repository was made to run locally in a training and testing environment. Do not use for production or expose to directly to the internet.

## Prerequisites

Before starting, ensure you have the following installed:

### Required Software

| Software | Minimum Version | Download |
|----------|-----------------|----------|
| Docker Desktop | 4.0+ | [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/) |
| Git | 2.0+ | [git-scm.com](https://git-scm.com/) |

### System Requirements

- **RAM**: 8GB minimum (16GB recommended)
- **Disk Space**: 70GB free space
- **OS**: macOS, Linux, or Windows with WSL2

### OpenAI API Key

You'll need an OpenAI API key for the lab exercises:

1. Go to [platform.openai.com](https://platform.openai.com/)
2. Sign up or log in
3. Navigate to **API Keys** in the left sidebar
4. Click **Create new secret key**
5. Copy the key (starts with `sk-`)

> **Note**: OpenAI offers free credits for new accounts. The labs use `gpt-4.1-mini` or `gpt-5.1-mini` which is cost-effective.

You can do *most* labs without an OpenAI API key, but the CTF will be very slow as is will use a Llama model on the CPU instead of a GPU.

---

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/deruke/ai4cybersec_labs.git
cd ai4cybersec_labs
```

### Step 2: Configure Your OpenAI API Key

Create a file called `.openai_key` in the project root and paste your API key:

```bash
# On macOS/Linux:
echo "sk-your-api-key-here" > .openai_key

# Or use a text editor to create the file
```

> **Security Note**: The `.openai_key` file is in `.gitignore` and will not be committed to version control.

### Step 3: Start the Environment

```bash
# Build and start all services (This can take 15+ minutes)
docker compose up -d

# Wait for services to initialize (this takes 4-5 minutes on first run, but could take longer)
docker compose logs -f ctf-setup
```

Watch for the message: `Setup completed successfully!`

Press `Ctrl+C` to stop following logs once setup is complete.

Now restart all the containers:

```bash
docker compose down
docker compose up -d
```

### Step 4: Verify Installation

Check that all services are running:

```bash
docker compose ps
```

You should see these services with status "Up" or "running":

| Service | Port | URL |
|---------|------|-----|
| Open WebUI | 4242 | http://localhost:4242 |
| Jupyter | 8888 | http://localhost:8888 |
| Ollama | 11435 | http://localhost:11435 |
| n8n | 5678 | http://localhost:5678 |

Note there will be other containers running as well.

---

## Accessing the Labs

### Prompt Injection CTF (Open WebUI)

1. Open http://localhost:4242 in your browser
2. Log in with the student credentials:
   - **Email**: `ctf@ctf.local`
   - **Password**: `Hellollmworld!`
3. Select a challenge from the model dropdown (Challenge 1-5)
4. Try to extract the secret flag using prompt injection techniques!

### Jupyter Notebooks

1. Open http://localhost:8888 in your browser
2. Enter the token: `AntiSyphonBlackHillsTrainingFtw!`
3. Navigate to `work/notebooks` to find the lab notebooks:
   - **Lab01**: Traditional ML for phishing detection
   - **Lab02**: Testing a pre-trained BERT model
   - **Lab03**: LLM-generated phishing detection
   - **Optional**: Neural Networks for phishing detection
   - **Optional**: Deepfake audio detection

> **Tip**: The notebooks in `work/notebooks` are read-only templates. To make changes, right-click a notebook and select "Copy", then paste it into `work/` where you can edit and save freely.

If the notebooks do not appead in the work/ folder then can be manually uploaded from the cloned repository into Jupyter lab.

---

## Quick Reference

### Starting/Stopping the Environment

```bash
# Start all services
docker compose up -d

# Stop all services (keeps data)
docker compose down

# Stop and remove all data (fresh start)
docker compose down -v
```

### Viewing Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f open-webui
docker compose logs -f jupyter
```

### Re-running CTF Setup

If you need to reset the CTF challenges:

```bash
docker compose down open-webui
docker volume rm ai4cybersec_labs_dev_open-webui
docker compose up -d
```

---

## Troubleshooting

### "Cannot connect to Docker daemon"

Make sure Docker Desktop is running. On macOS/Windows, look for the Docker icon in your system tray.

### "Port already in use"

Another application is using the port. Either stop that application or change the port in `.env`:

```bash
# Edit .env and change the port, for example:
OPENWEBUI_PORT=4243
JUPYTER_PORT=8889
```

Then restart: `docker compose down && docker compose up -d`

### "Model not found" error in Open WebUI

The OpenAI API key may not be configured correctly. Verify:

```bash
# Check if .openai_key exists and has content
cat .openai_key

# Re-run the setup
docker compose build ctf-setup
docker compose run --rm ctf-setup
```

### Jupyter notebooks won't load

Try restarting the Jupyter container:

```bash
docker compose restart jupyter
```

### Out of disk space

Docker images can consume significant space. Clean up unused images:

```bash
docker system prune -a
```

---

## Lab Overview

### Lab 01: Phishing Detection with Traditional ML

Learn how to build phishing email classifiers using:
- Logistic Regression
- Support Vector Machines (SVM)
- Naive Bayes
- Decision Trees
- Random Forests

### Lab 02: Testing a Pre-trained BERT Model

Evaluate a pre-trained transformer model for phishing detection:
- Load the `ealvaradob/bert-finetuned-phishing` model
- Test against real phishing email samples
- Analyze model accuracy and confidence scores

### Lab 03: LLM-Generated Phishing Detection

Explore the intersection of generative AI and cybersecurity:
- Use GPT-4.1-mini to generate phishing emails
- Test if AI-generated phishing can evade detection
- Understand the arms race between offensive and defensive AI

### Optional: Neural Networks for Phishing Detection

Deep dive into neural network architectures:
- Build and train custom neural networks
- Compare performance with traditional ML methods
- Understand overfitting and model optimization

### Optional: Deepfake Audio Detection

Learn to detect AI-generated audio:
- Analyze audio spectrograms
- Train models to identify synthetic speech
- Understand the challenges of deepfake detection

### CTF Challenges

Practice prompt injection techniques with increasing difficulty:

| Challenge | Protection Level | Hint |
|-----------|-----------------|------|
| 1 | None | Just ask for the flag! |
| 2 | System prompt instructions | Try to override instructions |
| 3 | Input filtering | Bypass the filter |
| 4 | Output filtering | The flag is there, but hidden |
| 5 | ML-based prompt guard | Advanced evasion required |

---

## Getting Help

- **Lab Issues**: Ask your instructor
- **Technical Problems**: Check the troubleshooting section above
- **Bug Reports**: [GitHub Issues](https://github.com/RiverGumSecurity/ai4cybersec_labs/issues)

---

## Credits

Developed for AI for Cybersecurity Professionals training by:
- [River Gum Security](https://rivergum.security)
- [Black Hills Information Security](https://blackhillsinfosec.com)
- [Antisyphon Training](https://antisyphontraining.com)
