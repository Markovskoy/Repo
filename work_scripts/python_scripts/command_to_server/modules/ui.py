# modules/ui.py

import os

def choose_yaml_file(folder: str) -> str:
    files = [f for f in os.listdir(folder) if f.endswith('.yaml')]
    if not files:
        print("Нет доступных файлов для выбора.")
        raise SystemExit(1)
    for i, f in enumerate(files):
        print(f"{i+1}: {f}")
    while True:
        try:
            idx = int(input("Выберите файл: ")) - 1
            if 0 <= idx < len(files):
                return os.path.join(folder, files[idx])
        except ValueError:
            pass
        print("Некорректный ввод. Попробуйте снова.")

def parse_selection(input_str: str, count: int) -> list:
    result = set()
    tokens = input_str.split()
    for token in tokens:
        if '-' in token:
            try:
                start, end = map(int, token.split('-'))
                result.update(range(start, end + 1))
            except ValueError:
                continue
        elif token.isdigit():
            result.add(int(token))
    return [i - 1 for i in sorted(result) if 1 <= i <= count]

def select_files_from_folder(folder: str) -> list:
    if not os.path.isdir(folder):
        print("Папка не найдена:", folder)
        return []
    entries = os.listdir(folder)
    if not entries:
        print("Папка пуста.")
        return []
    print("Содержимое папки:")
    for i, name in enumerate(entries):
        icon = "📁" if os.path.isdir(os.path.join(folder, name)) else "📄"
        print(f"{i+1}: {icon} {name}")

    selected = input("Введите номера файлов через пробел или диапазоны (например: 1 3 5-7): ").strip()
    indices = parse_selection(selected, len(entries))
    return [os.path.join(folder, entries[i]) for i in indices]