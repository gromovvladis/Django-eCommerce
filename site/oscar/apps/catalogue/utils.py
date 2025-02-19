import os
import shutil
import tarfile
import tempfile
import zipfile
import zlib

from io import BytesIO
from PIL import Image, UnidentifiedImageError
from PIL import Image

from django.core.files import File
from django.db.transaction import atomic

from oscar.core.loading import get_model
from oscar.apps.catalogue.exceptions import InvalidImageArchive


Product = get_model("catalogue", "product")
ProductImage = get_model("catalogue", "productimage")


class Importer(object):

    allowed_extensions = {".jpeg", ".jpg", ".png", ".webp", ".gif", ".tiff", ".bmp"}
    preferred_format = "WEBP"  # Используем WEBP для эффективности

    def __init__(self, logger, field):
        self.logger = logger
        self._field = field

    @atomic
    def handle(self, dirname):
        stats = {"num_processed": 0, "num_skipped": 0, "num_invalid": 0}
        image_dir, filenames = self._get_image_files(dirname)
        if image_dir:
            for filename in filenames:
                try:
                    lookup_value = self._get_lookup_value_from_filename(filename)
                    self._process_image(image_dir, filename, lookup_value)
                    stats["num_processed"] += 1
                except (Product.MultipleObjectsReturned, Product.DoesNotExist):
                    self.logger.warning(f"Skipping {filename}, no matching product.")
                    stats["num_skipped"] += 1
                except (IOError, UnidentifiedImageError) as e:
                    stats["num_invalid"] += 1
                    self.logger.error(f"Invalid image {filename}: {e}")
                except Exception as e:
                    stats["num_invalid"] += 1
                    self.logger.error(f"Unexpected error with {filename}: {e}")
            shutil.rmtree(image_dir)
        else:
            self.logger.error(f"Invalid image archive: {dirname}")
            raise InvalidImageArchive(("%s некорректное изображение архива") % dirname)
        self.logger.info(
            "Файл импортирован: %(num_processed)d,"
            " %(num_skipped)d пропустить" % stats
        )

    def _get_image_files(self, dirname):
        filenames = []
        image_dir = self._extract_images(dirname)
        if image_dir:
            filenames = [
                f
                for f in os.listdir(image_dir)
                if os.path.splitext(f)[1].lower() in self.allowed_extensions
            ]
        return image_dir, filenames

    def _extract_images(self, dirname):
        if os.path.isdir(dirname):
            return dirname
        ext = os.path.splitext(dirname)[1].lower()
        temp_dir = tempfile.mkdtemp()
        try:
            if ext in [".gz", ".tar"]:
                with tarfile.open(dirname) as tar:
                    tar.extractall(temp_dir)
            elif ext == ".zip":
                with zipfile.ZipFile(dirname) as zipf:
                    zipf.extractall(temp_dir)
            else:
                return ""
            return temp_dir
        except (tarfile.TarError, zipfile.BadZipFile, zlib.error):
            return ""

    def _process_image(self, dirname, filename, lookup_value):
        file_path = os.path.join(dirname, filename)
        trial_image = Image.open(file_path)
        trial_image.verify()
        image = Image.open(file_path)
        image = self._optimize_image(image)
        new_filename = f"{lookup_value}.{self.preferred_format.lower()}"
        new_path = os.path.join(dirname, new_filename)
        image.save(new_path, self.preferred_format, quality=85, optimize=True)
        self._save_image_to_db(new_path, lookup_value, new_filename)

    def _optimize_image(self, image):
        # Конвертация в RGB (если изображение имеет альфа-канал)
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")

        # Ограничение разрешения (с сохранением пропорций)
        max_size = (1080, 1080)
        image.thumbnail(max_size, Image.LANCZOS)

        # Ограничение размера файла (2MB)
        quality = 100
        output = BytesIO()

        while True:
            output.seek(0)
            output.truncate()
            image.save(output, format=self.preferred_format, quality=quality)

            # Проверяем размер в байтах
            if output.tell() <= 2 * 1080 * 1080 or quality <= 50:
                break

            quality -= 5  # Уменьшаем качество

        output.seek(0)
        optimized_image = Image.open(output).copy()
        output.close()

        return optimized_image

    def _save_image_to_db(self, file_path, lookup_value, filename):
        product = Product._default_manager.get(**{self._field: lookup_value})
        new_file = File(open(file_path, "rb"))
        im = ProductImage(product=product, display_order=product.images.count())
        im.original.save(filename, new_file, save=False)
        im.save()
        self.logger.debug(f"Image added to {product}")

    def _fetch_item(self, filename):
        kwargs = {self._field: self._get_lookup_value_from_filename(filename)}
        return Product._default_manager.get(**kwargs)

    def _get_lookup_value_from_filename(self, filename):
        return os.path.splitext(filename)[0]
