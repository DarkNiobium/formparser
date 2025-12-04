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
from tkinter import filedialog, messagebox

# --- CTK SOZLAMALARI ---
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# --- 1. O'ZGARUVCHILAR VA SOZLAMALAR ---
# Standart URL (dastlabki qiymat)
DEFAULT_URL = "https://docs.google.com/forms/d/e/1FAIpQLSf1iRmPbEsG29p7qNGVGrfKd8AiyKEHdm8LYg-JRscb5wLsdQ/viewform?usp=publish-editor"
PASSPORT_FILE = "" 
PROFILE_DIR = r"C:\form_profile"

EXPLICIT_WAIT_TIME = 10 

# Variantlar
GENDERS = ["Erkak", "Ayol"]
MODULES = ["Computing Fundamentals", "Object Oriented Programming (OOP)", "Web Development"]
LANGS = ["In English", "На Русском", "O'zbek tilida"]
FIRST_TIME_OPTIONS = ["birinchi", "takroriy"]
CITIES = ["Toshkent", "Samarqand", "Buxoro", "Farg'ona", "Andijon", "Namangan", "Qashqadaryo", "Surxondaryo", "Jizzax", "Sirdaryo", "Xorazm", "Navoiy", "Qoraqalpog'iston Respublikasi"]

# --- 2. SELENIUM FUNKSIYALARI ---

def scroll_to(driver, element):
    """Elementga tezkor skroll qilish."""
    try:
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});", element)
        time.sleep(0.1)
    except:
        pass

def safe_click(driver, element):
    """Xavfsiz klik: oddiy yoki JS orqali."""
    try:
        element.click()
    except:
        try:
            driver.execute_script("arguments[0].click();", element)
        except:
            return False
    return True

# --- 3. ASOSIY SELENIUM FUNKSIYALARI ---

def find_blocks(driver):
    """Savol bloklarini topadi."""
    return driver.find_elements(By.CLASS_NAME, "Qr7Oae")

def fill_text_or_date(driver, block, value):
    """Matn yoki sana maydonini to'ldiradi."""
    try:
        scroll_to(driver, block)
        input_field = block.find_element(By.CSS_SELECTOR, 'input[type="text"], input[type="date"], input[type="tel"]')
        input_field.clear()
        
        if "." in value and value.replace(".", "").isdigit():
            processed_value = value.replace(".", "")
        else:
            processed_value = value

        input_field.send_keys(processed_value)
        return True
    except Exception as e:
        return False

def click_by_text(driver, block, keyword):
    """Kalit so'zga mos keladigan radio/checkbox tugmasini bosadi."""
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
    """Ochilgan ro'yxatni (dropdown) to'ldiradi."""
    try:
        scroll_to(driver, block)
        dropdown_trigger = wait.until(
            EC.element_to_be_clickable((block.find_element(By.CSS_SELECTOR, 'div[role="listbox"]')))
        )
        dropdown_trigger.click()
        
        options_container = wait.until(
            EC.presence_of_element_located((By.XPATH, '//div[@role="listbox"]'))
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

def upload_file(driver, block, path, wait: WebDriverWait):
    """IFRAME orqali fayl yuklash."""
    if not os.path.exists(path):
        return False

    try:
        scroll_to(driver, block)
        
        add_btn = wait.until(EC.element_to_be_clickable((block.find_element(By.XPATH, ".//*[contains(text(), 'Добавить файл') or contains(text(), 'Add file') or contains(text(), 'Fayl qo‘shish')]"))))
        safe_click(driver, add_btn)
        
        iframe = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "iframe.picker-frame, iframe[src*='picker']")))
        driver.switch_to.frame(iframe)
        
        inp = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']")))
        inp.send_keys(path)
        
        driver.switch_to.default_content()
        wait.until(EC.element_to_be_clickable(add_btn)) 
        
        return True
    except Exception as e:
        driver.switch_to.default_content()
        try: driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except: pass
        return False

# --- 4. AVTOMATLASHTIRISHNI ISHGA TUSHIRISH FUNKSIYASI ---

def run_automation(data, log_callback, headless_mode):
    """Seleniumni ishga tushirish funksiyasi."""
    start_time = time.time()
    url = data['url'] # Yangi: URL ni data dan olish
    log_callback("Avtomatlashtirish boshlandi...")
    
    if not url.startswith('http'):
        log_callback("❌ Xato: URL noto'g'ri kiritilgan.")
        messagebox.showerror("Xato", "URL manzilini tekshiring.")
        return

    if not data['passport_file'] or not os.path.exists(data['passport_file']):
        log_callback(f"❌ Xato: Pasport fayli topilmadi: {data['passport_file']}")
        messagebox.showerror("Xato", "Pasport fayli topilmadi.")
        return

    # 1. Chrome sozlamalari (Headless Mode)
    os.makedirs(PROFILE_DIR, exist_ok=True)
    options = Options()
    options.add_argument(f"--user-data-dir={PROFILE_DIR}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    if headless_mode:
        options.add_argument("--headless=new")
        log_callback("🚀 Maksimal tezlik uchun Headless rejimda ishga tushirildi.")
    else:
        log_callback("⚠️ Oddiy rejimda ishga tushirildi.")

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.implicitly_wait(2) 
    except Exception as e:
        log_callback(f"❌ Driver xatosi: {e}")
        messagebox.showerror("Xato", "Chrome ishga tushirish xatosi.")
        return

    wait = WebDriverWait(driver, EXPLICIT_WAIT_TIME)

    if not headless_mode:
        driver.maximize_window() 

    driver.get(url)
    
    try:
        wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "Qr7Oae")))
        log_callback("Sahifa yuklandi va savol elementlari topildi.")
    except:
        log_callback("❌ Savollar topilmadi. Kutish vaqti tugagan bo'lishi mumkin.")
        driver.quit()
        return

    # 2. Formani to'ldirish
    blocks = find_blocks(driver)
    
    for i, b in enumerate(blocks):
        status = False
        t = b.text.lower()
        
        if "ismingiz" in t or "имя" in t:
            status = fill_text_or_date(driver, b, data['name'])
        elif "familiyangiz" in t or "фамилия" in t:
            status = fill_text_or_date(driver, b, data['surname'])
        elif "tug'il" in t or "дата" in t:
            status = fill_text_or_date(driver, b, data['birth'])
        elif "telefon" in t or "telegram" in t or "номер" in t:
            status = fill_text_or_date(driver, b, data['phone'])
        elif "qayerda" in t or "проживаете" in t or "viloyat" in t:
            status = fill_dropdown(driver, b, data['city_or_region'], wait)
            if not status:
                 status = fill_text_or_date(driver, b, data['city_or_region'])
        elif "jinsingiz" in t or "ваш пол" in t:
            status = click_by_text(driver, b, data['gender'])
        elif "modul" in t or "модуль" in t:
            status = click_by_text(driver, b, data['module'])
        elif "til" in t or "язык" in t:
            status = click_by_text(driver, b, data['lang'])
        elif "oldin" in t or "ранее" in t:
            status = click_by_text(driver, b, data['first_time'])
        elif "roziman" in t or "соглас" in t:
            status = click_by_text(driver, b, "Roziman")
        elif "passport" in t or "id" in t or "rasmini" in t:
            status = upload_file(driver, b, data['passport_file'], wait)
            
        log_callback(f"  Blok {i+1}: {'✅ Muvaffaqiyatli' if status else '❌ Xato'}")


    # 3. Formani yuborish va xatolarni e'tiborsiz qoldirish
    log_callback(" 'Yuborish' tugmasi bosilmoqda...")
    try:
        submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Отправить') or contains(text(), 'Submit') or contains(text(), 'Yuborish')]")))
        scroll_to(driver, submit_btn)
        safe_click(driver, submit_btn)
        
        # !!! ESKI TASDIQLASH BLOKI OLIB TASHLANDI !!!
        # wait.until(EC.presence_of_element_located((By.XPATH, confirmation_xpath)))
        
        end_time = time.time()
        duration = end_time - start_time
        log_callback(f"✅ TUGADI! Forma {duration:.2f} sekundda YUBORILDI (Tasdiqlash kutilmadi).")
        messagebox.showinfo("Muvaffaqiyat", f"Forma {duration:.2f} sekundda to'ldirildi va yuborildi.")
    except Exception as e:
        # Xatoni logga yozamiz, ammo brauzerni yopib jarayonni yakunlaymiz.
        log_callback(f"⚠️ YUBORISHDA XATO (tugma topilmadi yoki bosilmadi): {e}")
        messagebox.showwarning("Ogohlantirish", "Formani yuborishda xatolik yuz berdi. Tugmani topishda muammo bo'lishi mumkin.")
        
    driver.quit()
    log_callback("Brauzer yopildi.")

# --- 5. INTERFEYS KLASSI (CTK) ---

class FormApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🚀 Tezlashtirilgan Google Forma Avtomatik To'ldirgich")
        self.geometry("1920x1080")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.passport_file_path = ctk.StringVar(value="")
        self.url_var = ctk.StringVar(value=DEFAULT_URL) # Yangi o'zgaruvchi

        self.create_sidebar()
        self.create_main_frame()
        self.create_log_frame()

    def create_sidebar(self):
        """Sozlamalar paneli (URL kiritish maydoni bilan)."""
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(11, weight=1)

        ctk.CTkLabel(self.sidebar_frame, text="⚙️ SOZLAMALAR", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 10))

        # --- YANGI URL KIRITISH MAYDONI ---
        ctk.CTkLabel(self.sidebar_frame, text="Forma URL manzili:").grid(row=1, column=0, padx=20, pady=(10, 0), sticky="w")
        self.url_entry = ctk.CTkEntry(self.sidebar_frame, textvariable=self.url_var, placeholder_text="https://docs.google.com/forms/...")
        self.url_entry.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")
        # ----------------------------------
        
        self.headless_var = ctk.BooleanVar(value=True)
        self.headless_check = ctk.CTkCheckBox(self.sidebar_frame, text="✅ Headless Mode (MAKS. TEZLIK)", variable=self.headless_var)
        self.headless_check.grid(row=3, column=0, padx=20, pady=(10, 10), sticky="w")
        
        # Modul
        ctk.CTkLabel(self.sidebar_frame, text="Modul:").grid(row=4, column=0, padx=20, pady=(10, 0), sticky="w")
        self.module_select = ctk.CTkOptionMenu(self.sidebar_frame, values=MODULES)
        self.module_select.set(MODULES[0])
        self.module_select.grid(row=5, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Til
        ctk.CTkLabel(self.sidebar_frame, text="Til:").grid(row=6, column=0, padx=20, pady=(10, 0), sticky="w")
        self.lang_select = ctk.CTkOptionMenu(self.sidebar_frame, values=LANGS)
        self.lang_select.set(LANGS[0])
        self.lang_select.grid(row=7, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Tajriba
        ctk.CTkLabel(self.sidebar_frame, text="Tajriba (birinchi/takroriy):").grid(row=8, column=0, padx=20, pady=(10, 0), sticky="w")
        self.first_time_select = ctk.CTkOptionMenu(self.sidebar_frame, values=FIRST_TIME_OPTIONS)
        self.first_time_select.set(FIRST_TIME_OPTIONS[0])
        self.first_time_select.grid(row=9, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Ishga tushirish tugmasi
        self.start_button = ctk.CTkButton(self.sidebar_frame, text="▶️ AVTOMATLASHTIRISHNI ISHGA TUSHIRISH", command=self.start_fill)
        self.start_button.grid(row=12, column=0, padx=20, pady=20, sticky="s")


    def create_main_frame(self):
        """Asosiy ma'lumot kiritish paneli."""
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, padx=(20, 20), pady=(20, 10), sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self.main_frame, text="👤 SHAXSIY MA'LUMOTLAR", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        fields = [
            ("Ism:", "name_entry"),
            ("Familiya:", "surname_entry"),
            ("Tug'ilgan sana (KK.OO.YYYY):", "birth_entry"),
            ("Telefon/Telegram:", "phone_entry"),
        ]

        # Matn kiritish maydonlari
        for i, (label_text, attr_name) in enumerate(fields):
            ctk.CTkLabel(self.main_frame, text=label_text).grid(row=i*2+1, column=0, padx=20, pady=(10, 0), sticky="w")
            entry = ctk.CTkEntry(self.main_frame, placeholder_text=label_text.split(':')[0])
            setattr(self, attr_name, entry)
            entry.grid(row=i*2+2, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Shahar/Viloyat (OptionMenu)
        ctk.CTkLabel(self.main_frame, text="Shahar/Viloyat:").grid(row=len(fields)*2+1, column=0, padx=20, pady=(10, 0), sticky="w")
        self.city_select = ctk.CTkOptionMenu(self.main_frame, values=CITIES)
        self.city_select.set("Farg'ona")
        self.city_select.grid(row=len(fields)*2+2, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Jins (OptionMenu)
        ctk.CTkLabel(self.main_frame, text="Jins:").grid(row=len(fields)*2+3, column=0, padx=20, pady=(10, 0), sticky="w")
        self.gender_select = ctk.CTkOptionMenu(self.main_frame, values=GENDERS)
        self.gender_select.set(GENDERS[0])
        self.gender_select.grid(row=len(fields)*2+4, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Pasport faylini tanlash
        ctk.CTkLabel(self.main_frame, text="Pasport/ID fayli (jpg/png):").grid(row=len(fields)*2+5, column=0, padx=20, pady=(10, 0), sticky="w")
        
        file_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        file_frame.grid(row=len(fields)*2+6, column=0, padx=20, pady=(0, 20), sticky="ew")
        file_frame.grid_columnconfigure(0, weight=1)

        self.file_path_label = ctk.CTkLabel(file_frame, textvariable=self.passport_file_path, fg_color="gray", corner_radius=5)
        self.file_path_label.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.file_select_button = ctk.CTkButton(file_frame, text="Faylni tanlash", command=self.select_file)
        self.file_select_button.grid(row=0, column=1, sticky="e")

        # Boshlang'ich qiymatlar
        self.name_entry.insert(0, "Azamat")
        self.surname_entry.insert(0, "Komilov")
        self.birth_entry.insert(0, "01.01.2006")
        self.phone_entry.insert(0, "+998901234567")


    def create_log_frame(self):
        """Loglar uchun panel."""
        self.log_frame = ctk.CTkFrame(self, corner_radius=0)
        self.log_frame.grid(row=1, column=1, padx=(20, 20), pady=(0, 20), sticky="nsew")
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self.log_frame, text="📋 BAJARISH LOGI", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, padx=20, pady=(10, 0), sticky="w")
        
        self.log_text = ctk.CTkTextbox(self.log_frame, width=400, height=150)
        self.log_text.grid(row=1, column=0, padx=20, pady=(10, 20), sticky="nsew")
        self.log_text.configure(state="disabled")

    # --- UI METODLARI ---

    def log_message(self, message):
        """Log xabarini matn maydoniga chiqarish."""
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        self.update_idletasks()

    def select_file(self):
        """Pasport faylini tanlash dialogi."""
        filepath = filedialog.askopenfilename(
            title="Pasport faylini tanlang (JPG/PNG)",
            filetypes=(("Rasm fayllari", "*.jpg *.jpeg *.png"), ("Barcha fayllar", "*.*"))
        )
        if filepath:
            self.passport_file_path.set(filepath)
            global PASSPORT_FILE
            PASSPORT_FILE = filepath

    def start_fill(self):
        """Ma'lumotlarni yig'ish va avtomatlashtirishni ishga tushirish."""
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

        # UI dan ma'lumotlarni yig'ish (URL ham qo'shildi)
        data = {
            'url': self.url_var.get(), # Yangi: URL ni olamiz
            'name': self.name_entry.get(),
            'surname': self.surname_entry.get(),
            'birth': self.birth_entry.get(),
            'phone': self.phone_entry.get(),
            'city_or_region': self.city_select.get(),
            'gender': self.gender_select.get(),
            'module': self.module_select.get(),
            'lang': self.lang_select.get(),
            'first_time': self.first_time_select.get(),
            'passport_file': self.passport_file_path.get()
        }
        headless_mode = self.headless_var.get()

        if not all(data[k] for k in ['url', 'name', 'surname', 'birth', 'phone', 'passport_file']):
            messagebox.showwarning("Ogohlantirish", "Iltimos, barcha maydonlarni (shu jumladan URL) to'ldiring va faylni tanlang.")
            return

        self.start_button.configure(state="disabled", text="Bajarilmoqda...")
        self.update_idletasks()

        try:
            # Avtomatlashtirish funksiyasini chaqirish
            run_automation(data, self.log_message, headless_mode)
        finally:
            self.start_button.configure(state="normal", text="▶️ AVTOMATLASHTIRISHNI ISHGA TUSHIRISH")

if __name__ == "__main__":
    app = FormApp()
    app.mainloop()
