import customtkinter as ctk
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
import json
from tkinter import filedialog, messagebox

# ================== GLOBAL SOZLAMALAR ==================

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

DEFAULT_URL = ""
PROFILE_DIR = r"C:\form_profile"
EXPLICIT_WAIT_TIME = 12
SETTINGS_FILE = "settings.json"

GENDERS = ["Erkak", "Ayol"]
MODULES = ["Computing Fundamentals", "Key Applications", "Living Online"]
LANGS = ["In English", "На Русском"]
FIRST_TIME_OPTIONS = ["birinchi", "takroriy"]
CITIES = [
    "Toshkent", "Samarqand", "Buxoro", "Farg'ona", "Andijon", "Namangan",
    "Qashqadaryo", "Surxondaryo", "Jizzax", "Sirdaryo", "Xorazm",
    "Navoiy", "Qoraqalpog'iston Respublikasi"
]

# ================== SELENIUM YORDAMCHI FUNKSIYALAR ==================

def scroll_to(driver, element):
    try:
        driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});",
            element
        )
        time.sleep(0.15)
    except:
        pass


def safe_click(driver, element):
    try:
        element.click()
    except:
        try:
            driver.execute_script("arguments[0].click();", element)
        except:
            return False
    return True


def find_blocks(driver):
    return driver.find_elements(By.CLASS_NAME, "Qr7Oae")


def fill_text_or_date(driver, block, value):
    try:
        scroll_to(driver, block)
        input_field = block.find_element(By.CSS_SELECTOR,
                                            'input[type="text"], input[type="date"], input[type="tel"]')
        input_field.clear()

        if "." in value and value.replace(".", "").isdigit():
            value = value.replace(".", "")

        input_field.send_keys(value)
        return True
    except:
        return False


def click_by_text(driver, block, keyword):
    try:
        scroll_to(driver, block)
        options = block.find_elements(By.CSS_SELECTOR,
                                    "div[role='radio'], div[role='checkbox']")

        for o in options:
            label = (o.get_attribute("aria-label") or o.text or "").strip()
            if keyword.lower() in label.lower():
                return safe_click(driver, o)

        return False
    except:
        return False


def fill_dropdown(driver, block, value, wait: WebDriverWait):
    """Исправленная функция выбора dropdown."""
    try:
        scroll_to(driver, block)
        dropdown_trigger = block.find_element(By.CSS_SELECTOR, 'div[role="listbox"]')
        wait.until(EC.element_to_be_clickable(dropdown_trigger)).click()

        # Находим контейнер с опциями
        options_container = wait.until(
            EC.presence_of_element_located((By.XPATH, "//div[@role='listbox']"))
        )

        xpath_option = f'.//div[@role="option"]//span[text()="{value}"]'
        option_element = wait.until(
            EC.element_to_be_clickable((By.XPATH, xpath_option))
        )
        safe_click(driver, option_element)
        return True
    except:
        try:
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except:
            pass
        return False


def upload_file(driver, block, file_path, wait):
    if not os.path.exists(file_path):
        return False

    try:
        scroll_to(driver, block)

        add_btn = block.find_element(
            By.XPATH,
            ".//*[contains(text(),'Добавить') or contains(text(),'Add') or contains(text(),'Fayl')]"
        )

        safe_click(driver, add_btn)

        iframe = wait.until(EC.presence_of_element_located((
            By.CSS_SELECTOR, "iframe[src*='picker'], iframe.picker-frame"
        )))

        driver.switch_to.frame(iframe)
        file_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']")))
        file_input.send_keys(file_path)
        driver.switch_to.default_content()

        time.sleep(1)
        return True
    except:
        driver.switch_to.default_content()
        return False

# ================== SETTINGS ==================

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_settings(data):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except:
        pass

# ================== BRAUZERNI OCHISH UCHUN ASOSIY FUNKSIYA ==================

def open_browser_with_profile(log_callback, initial_url=None):
    os.makedirs(PROFILE_DIR, exist_ok=True)

    options = Options()
    options.add_argument(f"--user-data-dir={PROFILE_DIR}")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        driver.maximize_window()
        driver.get(initial_url or "https://google.com")
        return driver
    except Exception as e:
        log_callback(f"Brauzerni ishga tushirishda xato: {e}")
        messagebox.showerror("XATOLIK", f"Brauzerni ishga tushirishda xato yuz berdi: {e}")
        return None

# ================== GOOGLE LOGIN ==================

def login_google(log_callback):
    log_callback("⚠️ Google'ga kirish oynasi ochilmoqda...")
    log_callback("❗️ Brauzerda Google akkauntingizga kiring va tugmasini bosing.")
    
    driver = open_browser_with_profile(log_callback, "https://accounts.google.com/signin")
    
    if driver:
        start_time = time.time()
        while time.time() - start_time < 3600:
            try:
                driver.title
                time.sleep(1)
            except:
                log_callback("✅ Brauzer yopildi. Google kirish ma'lumotlari saqlandi.")
                return True
        log_callback("⚠️ Kirish uchun juda ko'p vaqt ketdi. Brauzer avtomatik yopilmoqda.")
        try:
            driver.quit()
        except:
            pass
    return False

# ================== AVTOMATLASHTIRISH ==================

def run_automation(data, log_callback):
    url = data['url']

    if not url.startswith("http"):
        messagebox.showerror("XATOLIK", "URL noto‘g‘ri")
        return

    if not os.path.exists(data['passport_file']):
        messagebox.showerror("XATOLIK", "Passport fayli topilmadi")
        return

    log_callback("Brauzer saqlangan profil bilan ochilmoqda...")
    driver = open_browser_with_profile(log_callback, initial_url=url)
    if driver is None:
        log_callback("Brauzerni ochib bo'lmadi. Avval 'Google'ga kirish' tugmasini bosing.")
        return

    wait = WebDriverWait(driver, EXPLICIT_WAIT_TIME)
    log_callback("Google Form ochilmoqda...")

    try:
        wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "Qr7Oae")))
        log_callback("Savollar topildi.")
    except:
        log_callback("Savollar topilmadi yoki Google kirishini talab qildi.")
        try:
            driver.quit()
        except:
            pass
        return

    blocks = find_blocks(driver)

    for i, block in enumerate(blocks):
        status = False
        text = block.text.lower()

        if "ism" in text or "имя" in text:
            status = fill_text_or_date(driver, block, data['name'])
        elif "familiya" in text or "фамилия" in text:
            status = fill_text_or_date(driver, block, data['surname'])
        elif "tug" in text or "дата" in text:
            status = fill_text_or_date(driver, block, data['birth'])
        elif "telefon" in text or "номер" in text:
            status = fill_text_or_date(driver, block, data['phone'])
        elif "viloyat" in text or "shahar" in text or "прожива" in text:
            status = fill_dropdown(driver, block, data['city_or_region'], wait) or fill_text_or_date(driver, block, data['city_or_region'])
        elif "jins" in text or "пол" in text:
            status = click_by_text(driver, block, data['gender'])
        elif "modul" in text or "модуль" in text:
            status = click_by_text(driver, block, data['module'])
        elif "til" in text or "язык" in text:
            status = click_by_text(driver, block, data['lang'])
        elif "oldin" in text or "ранее" in text:
            status = click_by_text(driver, block, data['first_time'])
        elif "roziman" in text or "соглас" in text:
            status = click_by_text(driver, block, "roziman")
        elif "passport" in text or "id" in text or "rasm" in text:
            status = upload_file(driver, block, data['passport_file'], wait)

        log_callback(f"Blok {i + 1}: {'✅ OK' if status else '❌ XATO'}")

    log_callback("---")
    log_callback("✅ Tayyor. Forma avtomatik yuborilmaydi.")
    log_callback("⚠️ Brauzer yopilmaydi – formani tekshiring va 'Yuborish' tugmasini bosing.")
    log_callback("Ish tugagach, brauzerni qo'lda yoping.")

# ================== INTERFACE ==================

class FormApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Google Form Auto Fill")
        self.geometry("1920x1080")

        self.passport_file_path = ctk.StringVar(value="")
        self.url_var = ctk.StringVar(value=DEFAULT_URL)

        self.load_previous_settings()
        self.create_main_ui()
        self.create_log_ui()

    def load_previous_settings(self):
        settings = load_settings()
        self.url_var.set(settings.get("url", DEFAULT_URL))
        self.passport_file_path.set(settings.get("passport_file", ""))
        self.previous_entries = settings.get("entries", {})
        self.previous_options = settings.get("options", {})

    def save_current_settings(self):
        data = {
            "url": self.url_var.get(),
            "passport_file": self.passport_file_path.get(),
            "entries": {k: v.get() for k, v in self.entries.items()},
            "options": {
                "city": self.city_menu.get(),
                "gender": self.gender.get(),
                "module": self.module.get(),
                "lang": self.lang.get(),
                "first_time": self.first.get()
            }
        }
        save_settings(data)

    def create_main_ui(self):
        self.left = ctk.CTkFrame(self, width=400)
        self.left.pack(side="left", fill="y", padx=10, pady=10)

        ctk.CTkLabel(self.left, text="🔑 Google Akkauntiga Kirish", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=10, pady=(10, 0))
        ctk.CTkLabel(self.left, text="Avval bir marta kirish kerak.\nBrauzer ochilgach, Google'ga kiring va yoping.").pack(anchor="w", padx=10, pady=(0, 5))
        ctk.CTkButton(self.left, text="Google'ga kirish 🚪", command=self.start_login).pack(fill="x", padx=10, pady=(5, 15))
        
        ctk.CTkLabel(self.left, text="📝 Forma Ma'lumotlari", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=10, pady=(10, 0))
        ctk.CTkLabel(self.left, text="Forma URL").pack(anchor="w", padx=10, pady=(10, 0))
        self.url_entry = ctk.CTkEntry(self.left, textvariable=self.url_var)
        self.url_entry.pack(fill="x", padx=10, pady=5)
        self.url_entry.bind("<Return>", self.auto_start)

        self.entries = {}
        fields = ["Ism", "Familiya", "Tugilgan sana (M:01.09.2011)", "Telefon (+998XXXXXXXXX)"]
        for f in fields:
            ctk.CTkLabel(self.left, text=f).pack(anchor="w", padx=10)
            e = ctk.CTkEntry(self.left)
            e.pack(fill="x", padx=10, pady=5)
            e.insert(0, self.previous_entries.get(f, ""))
            self.entries[f] = e

        ctk.CTkLabel(self.left, text="Shahar / Viloyat").pack(anchor="w", padx=10)
        self.city_menu = ctk.CTkOptionMenu(self.left, values=CITIES)
        self.city_menu.pack(fill="x", padx=10, pady=5)
        self.city_menu.set(self.previous_options.get("city", CITIES[0]))

        ctk.CTkLabel(self.left, text="Jins").pack(anchor="w", padx=10)
        self.gender = ctk.CTkOptionMenu(self.left, values=GENDERS)
        self.gender.pack(fill="x", padx=10, pady=5)
        self.gender.set(self.previous_options.get("gender", GENDERS[0]))

        ctk.CTkLabel(self.left, text="Modul").pack(anchor="w", padx=10)
        self.module = ctk.CTkOptionMenu(self.left, values=MODULES)
        self.module.pack(fill="x", padx=10, pady=5)
        self.module.set(self.previous_options.get("module", MODULES[0]))

        ctk.CTkLabel(self.left, text="Til").pack(anchor="w", padx=10)
        self.lang = ctk.CTkOptionMenu(self.left, values=LANGS)
        self.lang.pack(fill="x", padx=10, pady=5)
        self.lang.set(self.previous_options.get("lang", LANGS[0]))

        ctk.CTkLabel(self.left, text="Oldin o'qiganmisiz?").pack(anchor="w", padx=10)
        self.first = ctk.CTkOptionMenu(self.left, values=FIRST_TIME_OPTIONS)
        self.first.pack(fill="x", padx=10, pady=5)
        self.first.set(self.previous_options.get("first_time", FIRST_TIME_OPTIONS[0]))

        ctk.CTkButton(self.left, text="Passport fayl tanlash 🖼️", command=self.select_file).pack(fill="x", padx=10, pady=15)
        
        # Улучшенная кнопка
        self.start_button = ctk.CTkButton(self.left, text="🔥 Avtomatik to'ldirishni boshlash", command=self.start_automation_from_button, height=60, font=ctk.CTkFont(size=18, weight="bold"))
        self.start_button.pack(padx=50, pady=30, fill="x")

    def create_log_ui(self):
        self.right = ctk.CTkFrame(self)
        self.right.pack(side="right", expand=True, fill="both", padx=10, pady=10)

        ctk.CTkLabel(self.right, text="LOG JURNALI 📋", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=10)
        self.logbox = ctk.CTkTextbox(self.right)
        self.logbox.pack(expand=True, fill="both", padx=10, pady=10)

    def log_message(self, msg):
        self.logbox.insert("end", msg + "\n")
        self.logbox.see("end")
        self.update()

    def select_file(self):
        file = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if file:
            self.passport_file_path.set(file)
            self.log_message(f"Fayl tanlandi: {os.path.basename(file)}")

    def start_login(self):
        self.logbox.delete("1.0", "end")
        login_google(self.log_message)

    def start_automation_from_button(self):
        self.logbox.delete("1.0", "end")
        self.log_message("🔥 Avtomatik to'ldirish boshlanmoqda...")
        self.run_automation_with_data()
        
    def auto_start(self, event):
        self.logbox.delete("1.0", "end")
        self.log_message("Avtomatik ishga tushirildi (URL bo‘yicha)...")
        self.run_automation_with_data()
    
    def run_automation_with_data(self):
        data = {
            "url": self.url_var.get(),
            "name": self.entries["Ism"].get(),
            "surname": self.entries["Familiya"].get(),
            "birth": self.entries["Tugilgan sana (M:01.09.2011)"].get(),
            "phone": self.entries["Telefon (+998XXXXXXXXX)"].get(),
            "city_or_region": self.city_menu.get(),
            "gender": self.gender.get(),
            "module": self.module.get(),
            "lang": self.lang.get(),
            "first_time": self.first.get(),
            "passport_file": self.passport_file_path.get()
        }
        save_settings(data)
        run_automation(data, self.log_message)


if __name__ == "__main__":
    app = FormApp()
    app.mainloop()
