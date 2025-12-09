import customtkinter as ctk
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PWTimeout
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

# ================== PLAYWRIGHT HELPERS (ASYNC, HEAD-FULL) ==================

async def _ensure_profile_dir():
    os.makedirs(PROFILE_DIR, exist_ok=True)

async def open_persistent_context(initial_url=None, headless=False, log_callback=lambda m: None):
    """
    Opens Playwright persistent context using PROFILE_DIR so Chrome/Chromium profile is reused.
    Returns (playwright, context, page) or (None, None, None) on failure.
    """
    await _ensure_profile_dir()
    try:
        pw = await async_playwright().start()
        context = await pw.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-default-browser-check",
                "--disable-extensions",
                "--start-fullscreen"
            ],
            accept_downloads=True
        )
        # Get a page (existing or new)
        if context.pages:
            page = context.pages[0]
        else:
            page = await context.new_page()
        if initial_url:
            try:
                await page.goto(initial_url, timeout=30000)
            except Exception:
                pass
        #await page.set_viewport_size({"width": 1920, "height": 1080})
        return pw, context, page
    except Exception as e:
        log_callback(f"Brauzerni ishga tushirishda xato: {e}")
        try:
            await pw.stop()
        except:
            pass
        return None, None, None

async def close_context(pw, context):
    try:
        if context:
            await context.close()
    except:
        pass
    try:
        if pw:
            await pw.stop()
    except:
        pass

async def scroll_to_element(page, handle):
    try:
        await page.evaluate("el => el.scrollIntoView({behavior: 'instant', block: 'center'})", handle)
        #await asyncio.sleep(0.06)
    except:
        pass

async def safe_click_handle(handle):
    try:
        await handle.click()
        return True
    except:
        try:
            await handle.evaluate("el => el.click()")
            return True
        except:
            return False

# ================== FORM FILL HELPERS ==================

async def find_blocks(page):
    return await page.query_selector_all(".Qr7Oae")

async def fill_text_or_date_handle(page, block, value):
    try:
        # Прокрутка
        await page.evaluate("(el) => el.scrollIntoView({behavior: 'instant', block: 'center'})", block)

        input_field = await block.query_selector('input[type="text"], input[type="date"], input[type="tel"]')
        if not input_field:
            return False

        # Очистка
        try:
            await input_field.fill("")  # быстрый вариант
        except:
            await input_field.evaluate("el => el.value = ''")

        # Если поле дата, конвертируем DD.MM.YYYY → YYYY-MM-DD
        input_type = await input_field.get_attribute("type")
        if input_type == "date" and "." in value:
            parts = value.split(".")
            if len(parts) == 3:
                value = f"{parts[2]}-{parts[1]}-{parts[0]}"

        # Отправка символов (как send_keys)
        await input_field.type(value, delay=10)  # delay=10ms между символами
        return True
    except Exception as e:
        print(f"fill_text_or_date_handle error: {e}")
        return False


async def click_by_text_handle(page, block, keyword):
    try:
        await scroll_to_element(page, block)
        options = await block.query_selector_all("div[role='radio'], div[role='checkbox']")
        for o in options:
            label = (await o.get_attribute("aria-label") or await o.inner_text() or "").strip()
            if keyword.lower() in label.lower():
                return await safe_click_handle(o)
        return False
    except:
        return False

async def fill_dropdown_handle(page, block, value):
    try:
        await scroll_to_element(page, block)
        dropdown_trigger = await block.query_selector('div[role="listbox"]')
        if dropdown_trigger:
            await dropdown_trigger.click()
            try:
                opt = page.locator(f"//div[@role='option']//span[text()=\"{value}\"]")
                await opt.first.click(timeout=200)
                return True
            except:
                try:
                    opt2 = page.locator(f"//div[@role='option']//span[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), \"{value.lower()}\")]")
                    await opt2.first.click(timeout=200)
                    return True
                except:
                    try:
                        await page.keyboard.press('Escape')
                    except:
                        pass
                    return False
        else:
            return False
    except:
        try:
            await page.keyboard.press('Escape')
        except:
            pass
        return False

async def upload_file_handle(page, block, file_path, timeout_ms=10000):
    if not os.path.exists(file_path):
        return False
    try:
        await scroll_to_element(page, block)
        file_input = await block.query_selector('input[type="file"]')
        if file_input:
            await file_input.set_input_files(file_path)
            return True
        add_btn = await block.query_selector(".appsMaterialWizButtonPaperbuttonContent, button, span:has-text('Добавить'), span:has-text('Add'), span:has-text('Fayl')")
        if add_btn:
            try:
                await add_btn.click()
            except:
                try:
                    await add_btn.evaluate('el=>el.click()')
                except:
                    pass
        start = time.time()
        while time.time() - start < (timeout_ms / 1000.0):
            frames = page.frames
            found = False
            for f in frames:
                try:
                    input_f = await f.query_selector('input[type="file"]')
                    if input_f:
                        await input_f.set_input_files(file_path)
                        found = True
                        break
                except:
                    continue
            if found:
                return True
            await asyncio.sleep(0.2)
        return False
    except:
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

# ================== GOOGLE LOGIN ==================

async def login_google(log_callback):
    log_callback("⚠️ Google'ga kirish oynasi ochilmoqda...")
    log_callback("❗️ Brauzerda Google akkauntingizga kiring va oynani yoping yoki brauzer oynasini qoldiring. (Ko'rinadi)")

    pw, context, page = await open_persistent_context("https://accounts.google.com/signin", headless=False, log_callback=log_callback)
    if page is None:
        log_callback("Brauzerni ochib bo'lmadi.")
        return False

    start = time.time()
    timeout = 3600
    signed = False
    while time.time() - start < timeout:
        try:
            if 'signin' not in page.url.lower():
                signed = True
                break
        except:
            pass
        await asyncio.sleep(1)
    return signed

# ================== AUTOMATION ==================

async def run_automation_async(data, log_callback):
    start_time = time.time()  # старт
    url = data['url']
    if not url.startswith("http"):
        messagebox.showerror("XATOLIK", "URL noto‘g‘ri")
        return
    if not os.path.exists(data['passport_file']):
        messagebox.showerror("XATOLIK", "Passport fayli topilmadi")
        return

    log_callback("Brauzer saqlangan profil bilan ochilmoqda...")
    pw, context, page = await open_persistent_context(initial_url=url, headless=False, log_callback=log_callback)
    if page is None:
        log_callback("Brauzerni ochib bo'lmadi. Avval 'Google'ga kirish' tugmasini bosing va profilingizni saqlang.")
        return

    try:
        try:
            await page.wait_for_selector('.Qr7Oae', timeout=EXPLICIT_WAIT_TIME * 1000)
            log_callback('Savollar topildi.')
        except PWTimeout:
            log_callback('Savollar topilmadi yoki Google kirishni talab qildi.')
            return

        blocks = await find_blocks(page)
        for i, block in enumerate(blocks):
            status = False
            try:
                text = (await block.inner_text() or "").lower()
            except:
                text = ""
            if any(k in text for k in ["ism", "имя"]):
                status = await fill_text_or_date_handle(page, block, data['name'])
            elif any(k in text for k in ["familiya", "фамилия"]):
                status = await fill_text_or_date_handle(page, block, data['surname'])
            elif any(k in text for k in ["tug", "дата"]):
                status = await fill_text_or_date_handle(page, block, data['birth'])
            elif any(k in text for k in ["telefon", "номер"]):
                status = await fill_text_or_date_handle(page, block, data['phone'])
            elif any(k in text for k in ["viloyat", "shahar", "прож", "region"]):
                city_value = data['city_or_region']
                if city_value and "far" in city_value.lower():
                    city_value = "Farg'ona"
                status = await fill_dropdown_handle(page, block, city_value) or await fill_text_or_date_handle(page, block, city_value)
            elif any(k in text for k in ["jins", "пол"]):
                status = await click_by_text_handle(page, block, data['gender'])
            elif any(k in text for k in ["modul", "модуль"]):
                status = await click_by_text_handle(page, block, data['module'])
            elif any(k in text for k in ["til", "язык"]):
                status = await click_by_text_handle(page, block, data['lang'])
            elif any(k in text for k in ["oldin", "ранее"]):
                status = await click_by_text_handle(page, block, data['first_time'])
            elif any(k in text for k in ["roziman", "соглас"]):
                status = await click_by_text_handle(page, block, "roziman")
            elif any(k in text for k in ["passport", "id", "rasm", "file"]):
                status = await upload_file_handle(page, block, data['passport_file'])
            log_callback(f"Blok {i + 1}: {'✅ OK' if status else '❌ XATO'}")

        # Auto-submit
        try:
            submit = None
            for t in ['Отправить', 'Submit', 'Yuborish']:
                try:
                    submit = page.locator(f"//span[contains(normalize-space(.), '{t}')]").first
                    if submit:
                        await submit.click(timeout=3000)
                        log_callback('📤 Forma avtomatik yuborildi!')
                        break
                except:
                    submit = None
            if not submit:
                log_callback("⚠️ 'Отправить' tugmasi topilmadi yoki bosib bo'lmadi.")
        except:
            log_callback("⚠️ 'Отправить' tugmasi topilmadi yoki bosib bo'lmadi.")

    finally:
        log_callback("⚠️ Brauzerni qo'lda yopishingiz mumkin. Profil saqlanadi.")
    elapsed = time.time() - start_time  # прошло секунд
    log_callback(f"⏱️ Forma to‘ldirildi {elapsed:.2f} soniyada.")
# ================== INTERFACE ==================

class FormApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("Google Form Auto Fill")
        self.geometry("1200x800")

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
        ctk.CTkButton(self.left, text="Google'ga kirish 🚪", command=lambda: asyncio.run(self.start_login())).pack(fill="x", padx=10, pady=(5, 15))

        ctk.CTkLabel(self.left, text="📝 Forma Ma'lumotlari", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=10, pady=(10, 0))
        ctk.CTkLabel(self.left, text="Forma URL").pack(anchor="w", padx=10, pady=(10, 0))
        self.url_entry = ctk.CTkEntry(self.left, textvariable=self.url_var)
        self.url_entry.pack(fill="x", padx=10, pady=5)
        self.url_entry.bind("<Return>", lambda e: asyncio.run(self.auto_start(e)))

        self.entries = {}
        fields = ["Ism", "Familiya", "Tugilgan sana (M:01.09.2011)", "Telefon (+998XXXXXXXXX)"]
        for f in fields:
            ctk.CTkLabel(self.left, text=f).pack(anchor="w", padx=10)
            e = ctk.CTkEntry(self.left)
            e.pack(fill="x", padx=10, pady=5)
            e.insert(0, self.previous_entries.get(f, ""))
            self.entries[f] = e

        entry_list = list(self.entries.values())
        for i, entry in enumerate(entry_list):
            def make_handler(idx):
                return lambda event: entry_list[idx + 1].focus() if idx + 1 < len(entry_list) else self.start_button.focus()
            entry.bind("<Return>", make_handler(i))

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

        self.start_button = ctk.CTkButton(self.left, text="🔥 Avtomatik to'ldirishni boshlash", command=lambda: asyncio.run(self.start_automation_from_button()), height=60, font=ctk.CTkFont(size=18, weight="bold"))
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
        file = filedialog.askopenfilename(filetypes=[
            ("Images/PDF", "*.png *.jpg *.jpeg *.pdf"),
            ("All files", "*.*")
        ])
        if file:
            self.passport_file_path.set(file)
            self.log_message(f"Fayl tanlandi: {os.path.basename(file)}")

    async def start_login(self):
        self.logbox.delete("1.0", "end")
        ok = await login_google(self.log_message)
        if ok:
            self.log_message("✅ Google profilingiz saqlandi.")
        else:
            self.log_message("❌ Google profilingiz saqlanmadi yoki oynani yopdingiz.")

    async def start_automation_from_button(self):
        self.logbox.delete("1.0", "end")
        self.log_message("🔥 Avtomatik to'ldirish boshlanmoqda...")
        await self.run_automation_with_data()

    async def auto_start(self, event):
        self.logbox.delete("1.0", "end")
        self.log_message("Avtomatik ishga tushirildi...")
        await self.run_automation_with_data()

    async def run_automation_with_data(self):
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
        await run_automation_async(data, self.log_message)


if __name__ == "__main__":
    app = FormApp()
    app.mainloop()
