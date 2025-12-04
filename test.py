import os
import subprocess
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# 1. ЖЁСТКО закрыть все процессы Chrome
subprocess.call("taskkill /F /IM chrome.exe /T", shell=True)
time.sleep(2)

# 2. Путь к User Data — универсально
user_data = os.path.join(os.environ["LOCALAPPDATA"], "Google", "Chrome", "User Data")

options = Options()
options.add_argument(f"--user-data-dir={user_data}")
options.add_argument("--no-first-run")
options.add_argument("--no-default-browser-check")
options.add_argument("--disable-extensions")
options.add_argument("--disable-sync")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

driver = webdriver.Chrome(options=options)

# После запуска появится родной экран выбора профиля
driver.get("https://accounts.google.com")
