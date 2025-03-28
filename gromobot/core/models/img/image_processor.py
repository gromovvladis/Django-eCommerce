import os
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image, UnidentifiedImageError


class ImageProcessor(object):

    allowed_extensions = {".jpeg", ".jpg", ".png", ".webp", ".gif", ".tiff", ".bmp"}
    preferred_format = "WEBP"

    def optimize_image(self, image_file):
        try:
            image = Image.open(image_file)
            if not self._needs_optimization(image, image_file):
                return image_file

            image = self._convert_to_rgb(image)
            image = self._resize_image(image)
            return self._compress_image(image, image_file)
        except (UnidentifiedImageError, IOError):
            raise ValueError("Загруженный файл не является изображением или поврежден.")

    def _needs_optimization(self, image, image_file):
        """Проверяет, нужно ли оптимизировать изображение"""
        # Проверяем формат
        if image.format == self.preferred_format:
            # Проверяем размер файла
            if image_file.size <= 2 * 1024 * 1024:
                # Проверяем разрешение
                if image.width <= 1080 and image.height <= 1080:
                    return False  # Изображение уже в нужном формате и параметрах

        return True  # Нужно оптимизировать

    def _convert_to_rgb(self, image):
        """Конвертация в RGB (если изображение имеет альфа-канал)"""
        if image.mode in ("RGBA", "LA", "P"):
            image = image.convert("RGB")
        return image

    def _resize_image(self, image, max_size=(1080, 1080)):
        """Ограничение разрешения (с сохранением пропорций)"""
        image.thumbnail(max_size, Image.LANCZOS)
        return image

    def _compress_image(self, image, image_file):
        """Сжимает изображение и сохраняет в формате WEBP"""

        # Сжатие до 2MB
        quality = 100
        output = BytesIO()

        while True:
            output.seek(0)
            output.truncate()
            image.save(output, format="WEBP", quality=quality, optimize=True)

            if output.tell() <= 2 * 1024 * 1024 or quality <= 50:
                break

            quality -= 5  # Уменьшаем качество

        output.seek(0)

        # Получаем имя файла или задаем дефолтное
        original_name = getattr(image_file, "name", "image.jpg")
        name, _ = os.path.splitext(original_name)

        return ContentFile(output.read(), name=f"{name}.webp")
