from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import os

# --- 1. НАСТРОЙКИ ---
URL = "https://docs.google.com/forms/d/e/1FAIpQLSf1iRmPbEsG29p7qNGVGrfKd8AiyKEHdm8LYg-JRscb5wLsdQ/viewform?usp=publish-editor"
PASSPORT_FILE = r"C:\Users\11-Kompyuter\Desktop\passport.jpg" 

# --- Данные для заполнения ---
NAME = "Azamat"
SURNAME = "Komilov"
# !!! ДАТУ ОСТАВЛЯЕМ С ТОЧКАМИ, НО СКРИПТ АВТОМАТИЧЕСКИ ИХ УБЕРЕТ ПЕРЕД ВВОДОМ !!!
BIRTH = "01.01.2006" 
PHONE = "+998901234567"
CITY_OR_REGION = "Farg'ona" 
GENDER = "Erkak"
MODULE = "Computing Fundamentals"
LANG = "In English"
FIRST_TIME = "birinchi" 

# --- 2. ФУНКЦИИ СТАБИЛИЗАЦИИ ---

def scroll_to(driver, element):
    """Плавная прокрутка к элементу."""
    try:
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
        time.sleep(0.3) 
    except:
        pass

def safe_click(driver, element):
    """Надежный клик: обычный или через JS."""
    try:
        element.click()
    except:
        try:
            driver.execute_script("arguments[0].click();", element)
        except:
            return False
    return True

# --- 3. ОСНОВНЫЕ ФУНКЦИИ ---

def find_blocks(driver):
    return driver.find_elements(By.CLASS_NAME, "Qr7Oae")

def fill_text_or_date(driver, block, value):
    """Заполняет текстовое поле или поле даты."""
    try:
        scroll_to(driver, block)
        
        # 1. Поиск поля ввода. Поле ввода текста/даты в Google Forms часто имеет тег <input>
        # или находится внутри элементов с определенными классами.
        # Ищем основной input для текста.
        input_field = block.find_element(By.TAG_NAME, 'input')
        
        # 2. Очищаем значение, если оно есть
        input_field.clear()
        
        # 3. Подготовка значения
        # Если это дата (проверяем по наличию точек), убираем их
        if "." in value and value.replace(".", "").isdigit():
            # Это может быть поле даты. Вводим значение без точек.
            processed_value = value.replace(".", "")
            print(f"   ✍️ Ввод даты: {value} -> {processed_value}")
        else:
            # Обычное текстовое поле
            processed_value = value
            print(f"   ✍️ Ввод текста: {processed_value}")

        # 4. Ввод значения
        input_field.send_keys(processed_value)
        return True
    except Exception as e:
        print(f"   ⚠️ Ошибка ввода текста/даты: {e}")
        return False

def click_by_text(driver, block, keyword):
    try:
        scroll_to(driver, block)
        options = block.find_elements(By.CSS_SELECTOR, "div[role='radio'], div[role='checkbox']")
        for o in options:
            label = (o.get_attribute("aria-label") or o.text or "").strip()
            if keyword.lower() in label.lower():
                safe_click(driver, o)
                return True
        return False
    except:
        return False

def fill_dropdown(driver, block, value, wait: WebDriverWait):
    try:
        scroll_to(driver, block)
        dropdown_trigger = wait.until(
            EC.element_to_be_clickable((block.find_element(By.CSS_SELECTOR, 'div[role="listbox"]')))
        )
        dropdown_trigger.click()
        
        options_container = wait.until(
            EC.presence_of_element_located((By.XPATH, '//div[@role="listbox"]'))
        )
        time.sleep(0.5) 
        
        options = options_container.find_elements(By.XPATH, './div/div[@role="option"]')
        for option in options:
            if value.lower() == option.text.strip().lower():
                safe_click(driver, option)
                return True
        
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        return False
    except:
        try:
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except:
            pass
        return False

def upload_file(driver, block, path, wait: WebDriverWait):
    """Стабильная загрузка с переключением на IFRAME."""
    if not os.path.exists(path):
        print(f"❌ Файл не найден: {path}")
        return False

    try:
        scroll_to(driver, block)
        
        # 1. Клик "Добавить файл"
        add_btn = wait.until(EC.element_to_be_clickable((block.find_element(By.XPATH, ".//span[contains(text(), 'Добавить файл') or contains(text(), 'Add file') or contains(text(), 'Fayl qo‘shish')]"))))
        safe_click(driver, add_btn)
        
        # 2. IFRAME
        iframe = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "iframe.picker-frame, iframe[src*='picker']")))
        driver.switch_to.frame(iframe)
        
        # 3. Input и отправка
        inp = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']")))
        inp.send_keys(path)
        
        # 4. Выход и ожидание закрытия окна
        driver.switch_to.default_content()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "iframe.picker-frame")))
        time.sleep(0.5) 
        
        print(f"✅ Файл загружен.")
        return True
    except Exception as e:
        print(f"⚠️ Ошибка загрузки: {e}")
        driver.switch_to.default_content()
        try: driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except: pass
        return False

# --- 4. ЗАПУСК ---

# --- НАСТРОЙКА ПРОФИЛЯ ---
profile_dir = r"C:\form_profile"
os.makedirs(profile_dir, exist_ok=True) 
print(f"ℹ️ Используется Chrome профиль: {profile_dir}")

options = Options()
options.add_argument(f"--user-data-dir={profile_dir}") 
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

try:
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
except:
    print("Ошибка драйвера. Закройте все окна Chrome.")
    exit()

wait = WebDriverWait(driver, 15) 
driver.get(URL)
time.sleep(3) 

blocks = find_blocks(driver)

for i, b in enumerate(blocks):
    time.sleep(0.3) 
    print(f"Обработка блока {i+1}...") 
    
    t = b.text.lower()

    if "ismingiz" in t or "имя" in t:
        fill_text_or_date(driver, b, NAME)
    elif "familiyangiz" in t or "фамилия" in t:
        fill_text_or_date(driver, b, SURNAME)
    elif "tug'il" in t or "дата" in t:
        fill_text_or_date(driver, b, BIRTH)
    elif "telefon" in t or "telegram" in t or "номер" in t:
        fill_text_or_date(driver, b, PHONE)
    elif "qayerda" in t or "проживаете" in t or "viloyat" in t:
        if not fill_dropdown(driver, b, CITY_OR_REGION, wait):
            fill_text_or_date(driver, b, CITY_OR_REGION)
    elif "jinsingiz" in t or "ваш пол" in t:
        click_by_text(driver, b, GENDER)
    elif "modul" in t or "модуль" in t:
        click_by_text(driver, b, MODULE)
    elif "til" in t or "язык" in t:
        click_by_text(driver, b, LANG)
    elif "oldin" in t or "ранее" in t:
        click_by_text(driver, b, FIRST_TIME)
    elif "roziman" in t or "соглас" in t:
        click_by_text(driver, b, "Roziman")
    elif "passport" in t or "id" in t or "rasmini" in t:
        upload_file(driver, b, PASSPORT_FILE, wait) 

time.sleep(1)

print("Нажимаю 'Отправить'...")
try:
    submit_btn = driver.find_element(By.XPATH, "//span[contains(text(), 'Отправить') or contains(text(), 'Submit') or contains(text(), 'Yuborish')]")
    scroll_to(driver, submit_btn) 
    safe_click(driver, submit_btn)
    print("✅ ГОТОВО!")
except Exception as e:
    print(f"❌ Не нажал: {e}")
    
input("Нажми Enter для выхода...")
driver.quit()
