FROM python:3.11-slim

# Install dependencies needed for Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    gnupg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv for Python package management
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy only what's needed for installation
COPY pyproject.toml .

# Install Python dependencies using uv and pyproject.toml
RUN uv pip install . --system

# Install Playwright browsers
RUN playwright install --with-deps chromium

# Copy only the app directory
COPY app/ ./

# Set environment variable for headless browser
ENV BROWSER_HEADLESS=true

# Start the MCP server
CMD ["python", "-m", "main"] 