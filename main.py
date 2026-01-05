import requests
import json
import os
from tqdm import tqdm
from urllib.parse import quote
import datetime


# ==============================
# 1. ПОЛУЧЕНИЕ КАРТИНКИ С КОТОМ
# ==============================
def get_cat_image(text):
    """
    Получаем картинку с котом и текстом
    """
    try:
        # Кодируем текст для URL (иначе сломается на русском)
        encoded_text = quote(text)

        # Формируем URL как в документации
        url = f"https://cataas.com/cat/says/{encoded_text}"

        # Получаем картинку
        print("🔄 Загружаю картинку с котом...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()  # Проверяем ошибки

        print("✅ Картинка получена")
        return response.content  # Возвращаем данные картинки

    except Exception as e:
        print(f"❌ Ошибка при загрузке картинки: {e}")
        return None


# ==============================
# 2. РАБОТА С ЯНДЕКС.ДИСКОМ
# ==============================
def create_yandex_folder(token, folder_name):
    """
    Создаем папку на Яндекс.Диске
    """
    try:
        url = "https://cloud-api.yandex.net/v1/disk/resources"
        headers = {"Authorization": f"OAuth {token}"}
        params = {"path": folder_name}

        response = requests.put(url, headers=headers, params=params)

        # Если папка уже существует (код 409) - это нормально
        if response.status_code in [201, 409]:
            print(f"✅ Папка '{folder_name}' создана/уже существует")
            return True
        else:
            print(f"❌ Ошибка создания папки: {response.json()}")
            return False

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def upload_to_yandex(token, folder_name, file_name, image_data):
    """
    Загружаем картинку на Яндекс.Диск
    """
    try:
        # 1. Получаем ссылку для загрузки
        print("🔄 Получаю ссылку для загрузки...")
        upload_url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
        headers = {"Authorization": f"OAuth {token}"}

        # Полный путь к файлу на диске
        full_path = f"{folder_name}/{file_name}.jpg"
        params = {"path": full_path, "overwrite": "true"}

        response = requests.get(upload_url, headers=headers, params=params)
        response.raise_for_status()

        upload_href = response.json()["href"]

        # 2. Загружаем с прогресс-баром
        print(f"⬆️ Загружаю файл {file_name}.jpg...")
        with tqdm(total=len(image_data), unit='B', unit_scale=True, desc=file_name) as pbar:
            # Создаем кастомный адаптер для отслеживания прогресса
            response = requests.put(upload_href, data=image_data)
            pbar.update(len(image_data))

        print(f"✅ Файл загружен на Яндекс.Диск")
        return True, full_path

    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")
        return False, None


# ==============================
# 3. СОХРАНЕНИЕ В JSON
# ==============================
def save_to_json(data, filename="result.json"):
    """
    Сохраняем информацию о загрузке в JSON файл
    """
    try:
        # Если файл уже существует - читаем старые данные
        existing_data = []
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)

        # Добавляем новые данные
        existing_data.append(data)

        # Сохраняем обратно
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)

        print(f"✅ Информация сохранена в {filename}")

    except Exception as e:
        print(f"❌ Ошибка сохранения JSON: {e}")


# ==============================
# 4. ОСНОВНАЯ ПРОГРАММА
# ==============================
def main():
    print("=" * 50)
    print("🚀 ПРОГРАММА ДЛЯ ЗАГРУЗКИ КОТИКОВ НА ЯНДЕКС.ДИСК")
    print("=" * 50)

    # 1. Получаем данные от пользователя
    user_text = input("✏️  Введите текст для картинки (на русском или английском): ").strip()
    yandex_token = input("🔑 Введите токен Яндекс.Диска: ").strip()
    group_name = input("🏷️  Введите название вашей группы в Нетологии: ").strip()

    # Проверяем, что все поля заполнены
    if not user_text or not yandex_token or not group_name:
        print("❌ Ошибка: Все поля должны быть заполнены!")
        return

    # 2. Получаем картинку с котом
    image_data = get_cat_image(user_text)
    if not image_data:
        print("❌ Не удалось получить картинку. Программа завершена.")
        return

    # 3. Создаем папку на Яндекс.Диске
    if not create_yandex_folder(yandex_token, group_name):
        print("❌ Не удалось создать папку. Программа завершена.")
        return

    # 4. Подготавливаем имя файла
    # Заменяем пробелы на подчеркивания и убираем спецсимволы
    file_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in user_text)
    file_name = file_name.replace(" ", "_")

    # 5. Загружаем на Яндекс.Диск
    success, file_path = upload_to_yandex(yandex_token, group_name, file_name, image_data)

    if success:
        # 6. Сохраняем информацию в JSON
        file_info = {
            "date": datetime.datetime.now().isoformat(),
            "text": user_text,
            "file_name": f"{file_name}.jpg",
            "file_size_bytes": len(image_data),
            "file_size_mb": round(len(image_data) / (1024 * 1024), 2),
            "folder": group_name,
            "yandex_path": file_path,
            "status": "uploaded"
        }

        save_to_json(file_info)

    print("\n" + "=" * 50)
    print("🎉 ПРОГРАММА ЗАВЕРШЕНА!")
    print("=" * 50)
    print("Что проверить:")
    print("1. На Яндекс.Диске должна быть папка с названием вашей группы")
    print("2. В папке - картинка с вашим текстом")
    print("3. В папке с программой появился файл result.json с информацией")


# Запускаем программу
if __name__ == "__main__":
    main()