FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including LaTeX for resume compilation
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    gnupg \
    unzip \
    curl \
    texlive-latex-base \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    texlive-latex-extra \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Chromium browser for ARM64 compatibility
# Chromium is available for both x86_64 and ARM64, unlike Google Chrome
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# ChromeDriver is installed via chromium-driver package
# webdriver-manager will be used as fallback in Python code

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables for Chromium/Selenium and LaTeX
ENV CHROME_BIN="/usr/bin/chromium"
ENV DISPLAY=:99
ENV TEXMFHOME="/tmp/texmf"
ENV TEXMFVAR="/tmp/texmf-var"
ENV TEXMFCONFIG="/tmp/texmf-config"

# Create directories for static files and LaTeX
RUN mkdir -p /app/static/resumes /app/uploads /tmp/texmf /tmp/texmf-var /tmp/texmf-config

# Create a non-root user for security but give permissions for LaTeX compilation
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app /tmp/texmf /tmp/texmf-var /tmp/texmf-config

# Switch to non-root user
USER app

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 