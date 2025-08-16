# Docker Troubleshooting Guide

## Issue: Chrome Installation Failure in Docker

### Problem
The Docker build fails when trying to install Google Chrome with errors like:
```
E: Unable to locate package google-chrome-stable
failed to solve: process "/bin/sh -c apt-get update && apt-get install..." did not complete successfully: exit code: 100
```

### Root Cause
**ARM64 Compatibility Issue**: Google Chrome is only available for x86_64 (amd64) architecture, but Apple Silicon Macs use ARM64. The old Dockerfile was trying to install amd64 Chrome on an ARM64 container, which won't work.

### ✅ Fixed Solution (Current)

The Dockerfile has been updated to use **Chromium** instead of Chrome for ARM64 compatibility:

```dockerfile
# Install Chromium browser for ARM64 compatibility
# Chromium is available for both x86_64 and ARM64, unlike Google Chrome
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*
```

**Why Chromium?**
- ✅ Available for both x86_64 and ARM64
- ✅ Same Chromium engine as Chrome
- ✅ Fully compatible with Selenium WebDriver
- ✅ Includes ChromeDriver package
- ✅ No architecture-specific installation needed

### Build Options Comparison

| Option | LaTeX Resume Editor | Web Scraping | Build Time | Architecture Support |
|--------|-------------------|---------------|------------|---------------------|
| `Dockerfile` (Chromium) | ✅ | ✅ | ~3 min | x86_64 + ARM64 |
| `Dockerfile.dev` | ✅ | ❌ | ~2 min | All |
| Local | ✅* | ✅** | ~30 sec | All |

*Requires local LaTeX installation  
**Requires local Chrome/Chromium

## Quick Fixes

### 1. Use the Updated Dockerfile (Recommended)
```bash
# This now works on both Intel and Apple Silicon Macs
docker-compose up --build
```

### 2. Development Setup (Faster)
```bash
# For development without web scraping
docker-compose -f docker-compose.dev.yml up --build
```

### 3. Force Architecture (If Needed)
```bash
# Force x86_64 emulation on Apple Silicon (slower)
docker-compose up --build --platform linux/amd64
```

## Architecture Detection

You can check your system architecture:

```bash
# Check host architecture
uname -m
# arm64 = Apple Silicon
# x86_64 = Intel

# Check Docker architecture
docker info | grep Architecture
```

## Browser Detection in Code

The Workday scraper now automatically detects available browsers:

**macOS**: 
- Google Chrome → `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
- Chromium → `/Applications/Chromium.app/Contents/MacOS/Chromium`

**Linux/Docker**:
- Chromium → `/usr/bin/chromium`
- Chrome → `/usr/bin/google-chrome`

## Environment Variables

Update your `.env` file for Docker:

```bash
# For Docker with Chromium
SELENIUM_ENABLED=true
HEADLESS_BROWSER=true
CHROME_BIN=/usr/bin/chromium

# For local development with Chrome
CHROME_BIN=/Applications/Google Chrome.app/Contents/MacOS/Google Chrome
```

## Common Docker Issues

### 1. Architecture Mismatch
```bash
# Error: "exec format error" or "cannot execute binary file"
# Solution: Use the updated Dockerfile with Chromium
docker-compose down
docker-compose up --build
```

### 2. Build Cache Issues
```bash
# Clear Docker cache and rebuild
docker system prune -a
docker-compose build --no-cache
```

### 3. ChromeDriver Version Mismatch
```bash
# Remove old ChromeDriver cache
docker-compose exec backend rm -rf ~/.wdm/drivers/
# Or rebuild container
docker-compose up --build
```

### 4. Memory Issues
```yaml
# Add to docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

## Testing Docker Setup

```bash
# Test the Docker build
docker-compose up --build backend

# Test Selenium in container
docker-compose exec backend python selenium_test.py

# Check browser installation
docker-compose exec backend which chromium
docker-compose exec backend chromium --version
```

## Platform-Specific Commands

### Apple Silicon Macs
```bash
# Native ARM64 build (fastest)
docker-compose up --build

# Check if using Rosetta emulation
docker info | grep Architecture
# Should show: Architecture: aarch64
```

### Intel Macs
```bash
# Native x86_64 build
docker-compose up --build

# Architecture should show: x86_64
```

### Linux (x86_64)
```bash
# Standard build
docker-compose up --build
```

### Linux (ARM64)
```bash
# ARM64 Linux (e.g., Raspberry Pi, ARM servers)
docker-compose up --build
```

## Deployment Strategies

### 1. Development (Fast)
```bash
# Quick development without web scraping
docker-compose -f docker-compose.dev.yml up --build
```

### 2. Local Testing
```bash
# Full stack with Chromium
docker-compose up --build
```

### 3. Production (Cloud)
```bash
# For cloud deployment (check platform)
docker-compose up --build
```

## Multi-Architecture Support

The updated setup supports:
- ✅ **Apple Silicon** (M1/M2/M3 Macs)
- ✅ **Intel Macs**
- ✅ **Linux x86_64**
- ✅ **Linux ARM64**
- ✅ **Cloud platforms** (AWS, GCP, Azure)

## Verification

After building, verify everything works:

```bash
# Check browser
docker-compose exec backend which chromium
docker-compose exec backend chromium --version

# Check ChromeDriver
docker-compose exec backend which chromedriver
docker-compose exec backend chromedriver --version

# Test Selenium
docker-compose exec backend python -c "
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
options = Options()
options.add_argument('--headless')
options.binary_location = '/usr/bin/chromium'
driver = webdriver.Chrome(options=options)
print('✅ Selenium with Chromium working!')
driver.quit()
"
```

---

**Status**: ✅ **ARM64 COMPATIBILITY FIXED**

The Docker setup now works seamlessly on both Intel and Apple Silicon Macs using Chromium instead of Chrome. 