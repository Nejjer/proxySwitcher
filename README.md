## Setup
Создать файл pass.txt и записать в него пароль. 



### Dev заметки
Glider запускается с командой `glider.exe -listen :7777 -forward trojan://PASSWORD@arasaka.didns.ru:443`

Сборка `pyinstaller --onefile --windowed --distpath . --clean --name proxy main.py`