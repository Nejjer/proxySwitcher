import tkinter as tk
from tkinter import ttk
import winreg
import ctypes
import subprocess
import os

def get_password_from_file(app, filename='pass.txt'):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            # Читаем первую строку и удаляем пробельные символы по краям
            password = file.readline().strip()
            return password if password else None
    except FileNotFoundError:
        app.log_message(f"Файл {filename} не найден")
        return None
    except Exception as e:
        app.log_message(f"Ошибка при чтении файла: {e}")
        return None


def refresh_system_settings():
    """Обновление системных настроек интернета"""
    INTERNET_OPTION_SETTINGS_CHANGED = 39
    INTERNET_OPTION_REFRESH = 37
    ctypes.windll.Wininet.InternetSetOptionW(0, INTERNET_OPTION_SETTINGS_CHANGED, 0, 0)
    ctypes.windll.Wininet.InternetSetOptionW(0, INTERNET_OPTION_REFRESH, 0, 0)

def set_proxy_state(enable, app):
    """Установка состояния прокси в реестре Windows"""
    try:
        registry_key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r'Software\Microsoft\Windows\CurrentVersion\Internet Settings',
            0, 
            winreg.KEY_WRITE
        )
        
        winreg.SetValueEx(registry_key, 'ProxyEnable', 0, winreg.REG_DWORD, 1 if enable else 0)
        winreg.CloseKey(registry_key)
        
        refresh_system_settings()
        return True
    except Exception as e:
        app.log_message(f"Ошибка при изменении настроек: {e}")
        return False

def get_current_proxy_state(app):
    """Получение текущего состояния прокси из реестра"""
    try:
        registry_key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r'Software\Microsoft\Windows\CurrentVersion\Internet Settings'
        )
        value, _ = winreg.QueryValueEx(registry_key, 'ProxyEnable')
        winreg.CloseKey(registry_key)
        return bool(value)
    except Exception as e:
        app.log_message(f"Ошибка при чтении настроек: {e}")
        return False

class ProxySwitcherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Управление прокси")
        self.proxy_process = None
        
        self.proxy_state = tk.BooleanVar(value=get_current_proxy_state(self))
        
        # Создание основного контейнера
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Элементы управления
        self.label = ttk.Label(main_frame, text="Состояние прокси:")
        self.label.pack(pady=10)
        
        self.switch = ttk.Checkbutton(
            main_frame, 
            text="Включить прокси", 
            variable=self.proxy_state,
            command=self.toggle_proxy,
            style='Switch.TCheckbutton'
        )
        self.switch.pack(pady=10)
        
        # Текстовый блок для логов
        self.log_text = tk.Text(
            main_frame, 
            height=8, 
            state='disabled',
            wrap=tk.WORD
        )
        scrollbar = ttk.Scrollbar(
            main_frame, 
            orient=tk.VERTICAL, 
            command=self.log_text.yview
        )
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        # Упаковка элементов логов
        self.log_text.pack(
            side=tk.LEFT, 
            fill=tk.BOTH, 
            expand=True, 
            pady=(20,0)
        )
        scrollbar.pack(
            side=tk.RIGHT, 
            fill=tk.Y, 
            pady=(20,0)
        )

        # Обработка закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Стиль для переключателя
        style = ttk.Style()
        style.configure('Switch.TCheckbutton', font=('Arial', 12))
        
        # Первое сообщение в лог
        self.log_message("Приложение запущено")

    def log_message(self, message):
        """Метод для записи сообщений в лог"""
        self.log_text.configure(state='normal')  # Включаем редактирование
        self.log_text.insert(tk.END, message + "\n")  # Добавляем сообщение
        self.log_text.see(tk.END)  # Автопрокрутка к последнему сообщению
        self.log_text.configure(state='disabled')  # Отключаем редактирование

    def start_proxy_server(self):
        """Запуск прокси-сервера glider.exe"""
        try:
            if os.path.exists("glider/glider.exe"):
                self.proxy_process = subprocess.Popen([
                    "glider/glider.exe", 
                    "-listen", ":7777", 
                    "-forward", f"trojan://{get_password_from_file(self)}@arasaka.didns.ru:443"
                ])
                self.log_message("Прокси-сервер успешно запущен")
                return True
            else:
                self.log_message("Ошибка: glider.exe не найден в текущей директории")
                return False
        except Exception as e:
            self.log_message(f"Ошибка запуска прокси-сервера: {e}")
            return False

    def stop_proxy_server(self):
        """Остановка прокси-сервера"""
        if self.proxy_process:
            try:
                self.proxy_process.terminate()
                self.proxy_process.wait(timeout=5)
                self.log_message("Прокси-сервер остановлен")
            except Exception as e:
                self.log_message(f"Ошибка при остановке прокси-сервера: {e}")
            finally:
                self.proxy_process = None

    def toggle_proxy(self):
        """Обработчик переключения состояния"""
        if self.proxy_state.get():
            if set_proxy_state(True, self) and self.start_proxy_server():
                self.log_message("Прокси активирован")
            else:
                self.proxy_state.set(False)
        else:
            set_proxy_state(False, self)
            self.stop_proxy_server()
            self.log_message("Прокси деактивирован")

    def on_close(self):
        """Обработчик закрытия окна"""
        set_proxy_state(False, self)
        self.stop_proxy_server()
        self.root.destroy()

if __name__ == "__main__":
    try:
        if ctypes.windll.shell32.IsUserAnAdmin():
            root = tk.Tk()
            root.title("Прокси-Switcher")
            root.geometry("400x200")
            app = ProxySwitcherApp(root)
            root.mainloop()
        else:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", "python", __file__, None, 1)
    except Exception as e:
        print(f"Ошибка: {e}")