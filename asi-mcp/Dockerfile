# MCP Security Training Server Dockerfile
# Educational security testing tools for authorized training
# Based on Kali Linux for comprehensive tool availability

FROM kalilinux/kali-rolling:latest

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    LOG_LEVEL=INFO \
    PORT=3000 \
    GOPATH=/root/go \
    PATH=$PATH:/root/go/bin

# Update and install base dependencies
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    wget \
    git \
    build-essential \
    golang-go \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Network & Reconnaissance Tools (via apt)
RUN apt-get update && apt-get install -y \
    nmap \
    masscan \
    fierce \
    dnsenum \
    dnsrecon \
    responder \
    && rm -rf /var/lib/apt/lists/*

# Install Go-based reconnaissance tools
RUN go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest && \
    go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest && \
    go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest && \
    go install -v github.com/projectdiscovery/katana/cmd/katana@latest && \
    go install -v github.com/ffuf/ffuf/v2@latest && \
    go install -v github.com/jaeles-project/gospider@latest

# Copy Go binaries to /usr/local/bin for all users
RUN cp /root/go/bin/* /usr/local/bin/ || true

# Install Web Application Security Tools (via apt)
RUN apt-get update && apt-get install -y \
    gobuster \
    dirb \
    nikto \
    sqlmap \
    wpscan \
    wafw00f \
    seclists \
    && rm -rf /var/lib/apt/lists/*

# Verify seclists raft wordlists are installed
RUN if [ ! -f "/usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt" ]; then \
        echo "ERROR: Raft wordlists not found in seclists!" && exit 1; \
    fi && \
    if [ ! -f "/usr/share/seclists/Discovery/Web-Content/raft-large-directories.txt" ]; then \
        echo "ERROR: Raft large wordlist not found!" && exit 1; \
    fi && \
    if [ ! -f "/usr/share/seclists/Discovery/Web-Content/raft-small-directories.txt" ]; then \
        echo "ERROR: Raft small wordlist not found!" && exit 1; \
    fi && \
    echo "✓ Seclists raft wordlists verified: raft-small ($(wc -l < /usr/share/seclists/Discovery/Web-Content/raft-small-directories.txt) entries), raft-medium ($(wc -l < /usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt) entries), raft-large ($(wc -l < /usr/share/seclists/Discovery/Web-Content/raft-large-directories.txt) entries)"

# Install Python-based web tools
RUN pip3 install --no-cache-dir --break-system-packages \
    dirsearch || true

# Install RustScan
RUN wget -q https://github.com/RustScan/RustScan/releases/download/2.1.1/rustscan_2.1.1_amd64.deb && \
    dpkg -i rustscan_2.1.1_amd64.deb || apt-get install -f -y && \
    rm rustscan_2.1.1_amd64.deb || true

# Install Feroxbuster
RUN wget -q https://github.com/epi052/feroxbuster/releases/download/v2.10.1/feroxbuster_amd64.deb.zip && \
    unzip -q feroxbuster_amd64.deb.zip && \
    dpkg -i feroxbuster_*_amd64.deb || apt-get install -f -y && \
    rm -f feroxbuster_* || true

# Install Exploitation & Post-Exploitation Tools
RUN apt-get update && apt-get install -y \
    hydra \
    hashcat \
    john \
    && rm -rf /var/lib/apt/lists/*

# Install netexec (modern crackmapexec)
RUN pip3 install --no-cache-dir --break-system-packages netexec || true

# Install Binary/Reverse Engineering Tools
RUN apt-get update && apt-get install -y \
    radare2 \
    binwalk \
    binutils \
    && rm -rf /var/lib/apt/lists/*

# Install Cloud Security Tools
RUN pip3 install --no-cache-dir --break-system-packages \
    prowler \
    ScoutSuite || true

# Install OSINT tools
RUN pip3 install --no-cache-dir --break-system-packages \
    sherlock-project \
    theHarvester || true

# Install enum4linux-ng
RUN git clone https://github.com/cddmp/enum4linux-ng.git /opt/enum4linux-ng && \
    cd /opt/enum4linux-ng && \
    pip3 install --break-system-packages -r requirements.txt && \
    chmod +x enum4linux-ng.py && \
    ln -s /opt/enum4linux-ng/enum4linux-ng.py /usr/local/bin/enum4linux-ng || true

# Update nuclei templates and verify pentest profile exists
RUN nuclei -update-templates || true && \
    # Verify nuclei templates directory exists
    if [ ! -d "/root/nuclei-templates" ]; then \
        echo "ERROR: Nuclei templates not installed!" && exit 1; \
    fi && \
    # Verify pentest profile exists
    if [ ! -f "/root/nuclei-templates/profiles/pentest.yml" ]; then \
        echo "WARNING: Pentest profile not found, downloading..."; \
        mkdir -p /root/nuclei-templates/profiles && \
        wget -q https://raw.githubusercontent.com/projectdiscovery/nuclei-templates/refs/heads/main/profiles/pentest.yml \
             -O /root/nuclei-templates/profiles/pentest.yml || \
        echo "ERROR: Failed to download pentest profile!" && exit 1; \
    fi && \
    echo "✓ Nuclei templates installed with pentest profile"

# Create application directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Create necessary directories
RUN mkdir -p /app/logs /app/config/wordlists /tmp/scans

# Download common wordlists
RUN mkdir -p /usr/share/wordlists && \
    cd /usr/share/wordlists && \
    wget -q https://github.com/danielmiessler/SecLists/raw/master/Discovery/Web-Content/common.txt -O common.txt || echo "common" > common.txt && \
    wget -q https://github.com/danielmiessler/SecLists/raw/master/Discovery/Web-Content/directory-list-2.3-small.txt -O directory-list-small.txt || echo "admin" > directory-list-small.txt

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash mcpuser && \
    chown -R mcpuser:mcpuser /app /tmp/scans && \
    # Copy nuclei templates to mcpuser home directory
    cp -r /root/nuclei-templates /home/mcpuser/ && \
    chown -R mcpuser:mcpuser /home/mcpuser/nuclei-templates && \
    echo "✓ Nuclei templates copied to mcpuser home directory"

# Switch to non-root user
USER mcpuser

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Set entrypoint
ENTRYPOINT ["python3", "-m", "uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "3000"]
