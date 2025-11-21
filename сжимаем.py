from PIL import Image

def resize_image(input_path, output_path, max_width=1080, max_height=1440):
    # Открываем изображение
    image = Image.open(input_path)

    # Получаем оригинальные размеры
    original_width, original_height = image.size

    # Вычисляем коэффициенты масштабирования
    width_ratio = max_width / original_width
    height_ratio = max_height / original_height
    scaling_factor = min(width_ratio, height_ratio, 1)  # Не увеличивать изображение

    # Новые размеры
    new_width = int(original_width * scaling_factor)
    new_height = int(original_height * scaling_factor)

    # Изменяем размер
    resized_image = image.resize((new_width, new_height), Image.LANCZOS)  # LANCZOS — фильтр высокого качества
    resized_image = remove_transparency(resized_image, bg_color=(255, 255, 255))

    # Сохраняем изображение с высоким качеством
    resized_image.save(output_path, format='JPEG', quality=95, optimize=True)

    print(f"Изображение сохранено: {output_path} ({new_width}x{new_height})")

# Пример использования


def remove_transparency(im, bg_color=(255, 255, 255)):
    if im.mode in ('RGBA', 'LA'):
        background = Image.new('RGB', im.size, bg_color)
        background.paste(im, mask=im.split()[-1])  # альфа-канал как маска
        return background
    else:
        return im.convert('RGB')


resize_image('hoodie_purplered.png', 'products/initial_images/hoodie/purplered.jpg')
