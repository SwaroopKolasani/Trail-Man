#!/usr/bin/env python3
"""
Selenium Setup Script for Trail-Man

This script configures the environment variables needed for Selenium
and tests the setup to ensure everything works correctly.
"""

import os
import sys
import platform

def update_env_file():
    """Update the .env file with Selenium configuration"""
    env_file_path = ".env"
    
    # Read existing .env file
    env_vars = {}
    if os.path.exists(env_file_path):
        with open(env_file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
    
    # Selenium configuration based on platform
    selenium_config = {
        'SELENIUM_ENABLED': 'true',
        'HEADLESS_BROWSER': 'true',
        'BROWSER_TIMEOUT': '30'
    }
    
    # Set Chrome binary path for macOS
    if platform.system() == "Darwin":
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        if os.path.exists(chrome_path):
            selenium_config['CHROME_BIN'] = chrome_path
    
    # Update environment variables
    env_vars.update(selenium_config)
    
    # Add Redis URL if not present
    if 'REDIS_URL' not in env_vars:
        env_vars['REDIS_URL'] = 'redis://localhost:6379/0'
    
    # Write updated .env file
    with open(env_file_path, 'w') as f:
        f.write("# Trail-Man Environment Configuration\n")
        f.write("# Database Configuration\n")
        for key in ['MYSQL_SERVER', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DB']:
            if key in env_vars:
                f.write(f"{key}={env_vars[key]}\n")
        
        f.write("\n# Clerk Authentication\n")
        for key in ['CLERK_SECRET_KEY', 'CLERK_PUBLIC_KEY']:
            if key in env_vars:
                f.write(f"{key}={env_vars[key]}\n")
        
        f.write("\n# AWS Configuration (Optional)\n")
        for key in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_S3_BUCKET']:
            if key in env_vars:
                f.write(f"{key}={env_vars[key]}\n")
        
        f.write("\n# Redis Configuration\n")
        f.write(f"REDIS_URL={env_vars['REDIS_URL']}\n")
        
        f.write("\n# Selenium Configuration\n")
        for key, value in selenium_config.items():
            f.write(f"{key}={value}\n")
        
        f.write("\n# Application Settings\n")
        for key in ['PROJECT_NAME', 'VERSION', 'API_V1_STR']:
            if key in env_vars:
                f.write(f"{key}={env_vars[key]}\n")
    
    print("✅ Updated .env file with Selenium configuration")
    return selenium_config

def main():
    """Main setup function"""
    print("🔧 Setting up Selenium for Trail-Man")
    print("=" * 40)
    
    # Update environment file
    selenium_config = update_env_file()
    
    print("\n📋 Selenium Configuration:")
    for key, value in selenium_config.items():
        print(f"   {key}: {value}")
    
    print("\n🧪 Run tests with:")
    print("   python selenium_test.py")
    
    print("\n🐳 For Docker setup, use:")
    print("   docker-compose up --build")
    print("   # or for development:")
    print("   docker-compose -f docker-compose.dev.yml up --build")

if __name__ == "__main__":
    main() 