import os
import shutil
import tarfile
import tempfile
import zipfile
import zlib

from PIL import Image, UnidentifiedImageError

from django.core.files import File
from django.db.transaction import atomic

from oscar.core.loading import get_model
from oscar.apps.catalogue.exceptions import InvalidImageArchive
from oscar.utils.image_processor import ImageProcessor

Product = get_model("catalogue", "Product")
ProductImage = get_model("catalogue", "ProductImage")


class ProductImporter(ImageProcessor):

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
                    new_path, new_filename = self._process_image(
                        image_dir, filename, lookup_value
                    )
                    self._save_image_to_db(new_path, lookup_value, new_filename)
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

    def _process_image(self, dirname, filename, lookup_value):
        file_path = os.path.join(dirname, filename)

        try:
            # Проверяем, что файл является изображением
            trial_image = Image.open(file_path)
            trial_image.verify()  # Проверка целостности файла
        except (UnidentifiedImageError, IOError):
            raise ValueError("Загруженный файл не является изображением или поврежден.")

        image = Image.open(file_path)
        image = self.optimize_image(image)
        new_filename = f"{lookup_value}.{self.preferred_format.lower()}"
        new_path = os.path.join(dirname, new_filename)

        with open(new_path, "wb") as f:
            image.save(f, self.preferred_format, optimize=True)

        return new_path, new_filename

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
