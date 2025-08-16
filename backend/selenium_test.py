#!/usr/bin/env python3
"""
Selenium Setup Test Script for Trail-Man

This script tests the Selenium configuration and ChromeDriver setup
across different environments (local, Docker, etc.)
"""

import os
import sys
import platform
import logging
from typing import Dict, Any

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    from app.core.config import settings
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the backend directory with the virtual environment activated")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_chrome_installation() -> Dict[str, Any]:
    """Test Chrome browser installation"""
    result = {"status": "unknown", "path": None, "version": None}
    
    try:
        system = platform.system()
        
        if system == "Darwin":  # macOS
            chrome_paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chrome.app/Contents/MacOS/Chrome"
            ]
        elif system == "Linux":
            chrome_paths = [
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable",
                "/usr/bin/chromium",
                "/usr/bin/chromium-browser"
            ]
        else:  # Windows
            chrome_paths = [
                "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
            ]
        
        for path in chrome_paths:
            if os.path.exists(path):
                result["status"] = "found"
                result["path"] = path
                logger.info(f"✅ Chrome found at: {path}")
                return result
        
        result["status"] = "not_found"
        logger.warning("⚠️ Chrome browser not found in standard locations")
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        logger.error(f"❌ Error checking Chrome installation: {e}")
    
    return result

def test_chromedriver() -> Dict[str, Any]:
    """Test ChromeDriver installation and compatibility"""
    result = {"status": "unknown", "path": None, "version": None}
    
    try:
        # Try webdriver-manager first
        driver_path = ChromeDriverManager().install()
        result["status"] = "found"
        result["path"] = driver_path
        logger.info(f"✅ ChromeDriver installed via webdriver-manager: {driver_path}")
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        logger.error(f"❌ ChromeDriver installation failed: {e}")
    
    return result

def test_selenium_basic() -> Dict[str, Any]:
    """Test basic Selenium functionality"""
    result = {"status": "unknown", "error": None}
    driver = None
    
    try:
        # Configure Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Set Chrome binary if on macOS
        if platform.system() == "Darwin":
            chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            if os.path.exists(chrome_path):
                chrome_options.binary_location = chrome_path
        
        # Create driver
        driver_path = ChromeDriverManager().install()
        
        # Fix webdriver-manager path issue on macOS
        if platform.system() == "Darwin" and "THIRD_PARTY_NOTICES" in driver_path:
            driver_dir = os.path.dirname(driver_path)
            actual_driver_path = os.path.join(driver_dir, "chromedriver")
            if os.path.exists(actual_driver_path):
                driver_path = actual_driver_path
                # Ensure the chromedriver has execute permissions
                import stat
                current_permissions = os.stat(driver_path).st_mode
                os.chmod(driver_path, current_permissions | stat.S_IEXEC)
                logger.info(f"Fixed ChromeDriver path and permissions: {driver_path}")
        
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Test basic navigation
        driver.get("https://httpbin.org/json")
        
        # Wait for page to load and check if we can find content
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        page_source = driver.page_source
        if "slideshow" in page_source.lower():  # httpbin.org/json contains slideshow data
            result["status"] = "success"
            logger.info("✅ Selenium basic test passed")
        else:
            result["status"] = "warning"
            result["error"] = "Page loaded but content verification failed"
            logger.warning("⚠️ Selenium test: page loaded but content unexpected")
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        logger.error(f"❌ Selenium basic test failed: {e}")
    
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
    
    return result

def test_workday_scraper() -> Dict[str, Any]:
    """Test Workday scraper functionality"""
    result = {"status": "unknown", "error": None}
    
    try:
        from app.scrapers.workday import WorkdayScraper
        
        # Test scraper initialization
        config = {
            'careers_url': 'https://jobs.lever.co/github',  # Using a simple test URL
            'wait_timeout': 5
        }
        
        scraper = WorkdayScraper("TestCompany", config)
        result["status"] = "initialized"
        logger.info("✅ WorkdayScraper initialized successfully")
        
        # Note: We don't actually run the scraper here to avoid hitting real sites
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        logger.error(f"❌ WorkdayScraper test failed: {e}")
    
    return result

def test_environment_variables() -> Dict[str, Any]:
    """Test environment variables and configuration"""
    result = {"status": "unknown", "config": {}}
    
    try:
        config_vars = {
            "SELENIUM_ENABLED": settings.SELENIUM_ENABLED,
            "HEADLESS_BROWSER": settings.HEADLESS_BROWSER,
            "BROWSER_TIMEOUT": settings.BROWSER_TIMEOUT,
            "CHROME_BIN": settings.CHROME_BIN,
            "CHROME_DRIVER_PATH": settings.CHROME_DRIVER_PATH,
        }
        
        result["config"] = config_vars
        result["status"] = "success"
        
        logger.info("✅ Environment configuration:")
        for key, value in config_vars.items():
            logger.info(f"   {key}: {value}")
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        logger.error(f"❌ Environment variables test failed: {e}")
    
    return result

def main():
    """Run all Selenium tests"""
    print("🚀 Trail-Man Selenium Setup Test")
    print("=" * 50)
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Chrome Installation", test_chrome_installation),
        ("ChromeDriver", test_chromedriver),
        ("Selenium Basic", test_selenium_basic),
        ("Workday Scraper", test_workday_scraper)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        try:
            results[test_name] = test_func()
        except Exception as e:
            results[test_name] = {"status": "error", "error": str(e)}
            logger.error(f"❌ {test_name} test crashed: {e}")
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    
    success_count = 0
    total_count = len(tests)
    
    for test_name, result in results.items():
        status = result.get("status", "unknown")
        if status == "success" or status == "found" or status == "initialized":
            print(f"✅ {test_name}: PASS")
            success_count += 1
        elif status == "warning":
            print(f"⚠️ {test_name}: WARNING - {result.get('error', 'Unknown warning')}")
            success_count += 0.5
        else:
            print(f"❌ {test_name}: FAIL - {result.get('error', 'Unknown error')}")
    
    print(f"\nResult: {success_count}/{total_count} tests passed")
    
    if success_count == total_count:
        print("🎉 All tests passed! Selenium is ready for use.")
        return 0
    elif success_count >= total_count * 0.7:
        print("⚠️ Most tests passed. Selenium should work but may have issues.")
        return 0
    else:
        print("❌ Multiple tests failed. Selenium setup needs attention.")
        print("\n🔧 Troubleshooting tips:")
        print("1. Make sure Chrome is installed")
        print("2. Check ChromeDriver compatibility")
        print("3. Verify environment variables")
        print("4. Check Docker setup if running in container")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 