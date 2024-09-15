from datetime import datetime, timedelta
from zipfile import ZipFile
import os
from PIL import Image
from transliterate import translit
import re
import openpyxl as xl
from log_settings import log
import shutil
from uuid import UUID
from db import r


class CreatingLinks:

    def __init__(self, filename: str, uuid: UUID):
        self.filename = filename
        if not os.path.exists("./media/zip_files"):
            os.mkdir("./media/zip_files")
        self.filepath = f"./media/zip_files/{self.filename}"
        self.uuid = uuid

    def unzip_archive(self):
        with ZipFile(self.filepath, "r") as zObject:
            filename_cut, ext = os.path.splitext(self.filename)
            unzipped_folder_name = f"{filename_cut}_{self.uuid}"
            path = f"./media/{unzipped_folder_name}"
            zObject.extractall(path=path)
        zObject.close()
        return unzipped_folder_name

    @staticmethod
    def get_size_format(b, factor=1024, suffix="B"):
        """
        Scale bytes to its proper byte format
        e.g:
            1253656 => '1.20MB'
            1253656678 => '1.17GB'
        """
        for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
            if b < factor:
                return f"{b:.2f}{unit}{suffix}"
            b /= factor
        return f"{b:.2f}Y{suffix}"

    @staticmethod
    def make_path(first_part, name):
        return f"./{first_part}/{name}"

    @staticmethod
    def remove_symbols(phrase: str) -> str:
        word = re.sub("[^a-zа-яё-]", "", phrase, flags=re.IGNORECASE)
        word = word.strip("-")
        while " " in word:
            word = word.replace(" ", "")
        return word

    def compress_img(
        self,
        image_name,
        compressed_file_path,
        new_size_ratio=0.9,
        quality=90,
        width=None,
        height=None,
        to_jpg=True,
    ):
        # load the image to memory
        img = Image.open(image_name)
        # print the original image shape
        print("[*] Image shape:", img.size)
        # get the original image size in bytes
        image_size = os.path.getsize(image_name)
        # print the size before compression/resizing
        print("[*] Size before compression:", self.get_size_format(image_size))
        if new_size_ratio < 1.0:
            # if resizing ratio is below 1.0, then multiply width & height with this ratio to reduce image size
            img = img.resize(
                (int(img.size[0] * new_size_ratio), int(img.size[1] * new_size_ratio)),
                Image.LANCZOS,
            )
            # print new image shape
            print("[+] New Image shape:", img.size)
        elif width and height:
            # if width and height are set, resize with them instead
            img = img.resize((width, height), Image.LANCZOS)
            # print new image shape
            print("[+] New Image shape:", img.size)
        try:
            # save the image with the corresponding quality and optimize set to True
            img.save(compressed_file_path, quality=quality, optimize=True)
        except OSError:
            # convert the image to RGB mode first
            img = img.convert("RGB")
            # save the image with the corresponding quality and optimize set to True
            img.save(compressed_file_path, quality=quality, optimize=True)
        print("[+] New file saved:", compressed_file_path)
        # get the new image size in bytes
        new_image_size = os.path.getsize(compressed_file_path)
        # print the new size in a good format
        print("[+] Size after compression:", self.get_size_format(new_image_size))
        if new_image_size <= 200000:
            img = Image.open(image_name)
            img = img.resize(
                (int(img.size[0] * 0.9), int(img.size[1] * 0.9)), Image.LANCZOS
            )
            # print new image shape
            print("[+] New Image shape:", img.size)
            try:
                # save the image with the corresponding quality and optimize set to True
                img.save(compressed_file_path, quality=quality, optimize=True)
            except OSError:
                # convert the image to RGB mode first
                img = img.convert("RGB")
                # save the image with the corresponding quality and optimize set to True
                img.save(compressed_file_path, quality=quality, optimize=True)
            new_image_size = os.path.getsize(compressed_file_path)

            print("[+] Size after compression:", self.get_size_format(new_image_size))

        # calculate the saving bytes
        saving_diff = new_image_size - image_size
        # print the saving percentage
        print(
            f"[+] Image size change: {saving_diff / image_size * 100:.2f}% of the original image size."
        )

    def secure_filepaths(self, unzipped_folder_name, photo):
        photo_path = f"./media/{unzipped_folder_name}/{photo}"
        phrase, ext = os.path.splitext(photo)
        secure_name = translit(phrase, "ru", True)
        secure_name = self.remove_symbols(secure_name)
        compressed_filepath = (
            f"./media_compressed/{unzipped_folder_name}/{secure_name}.jpg"
        )
        return phrase, photo_path, compressed_filepath, secure_name

    @staticmethod
    def links_to_xlsx(phrase_list, unzipped_folder_name):
        wb = xl.Workbook()
        ws = wb.active
        for row in phrase_list:
            ws.append(row)
        path = f"./xlsx_files/{unzipped_folder_name}.xlsx"
        wb.save(path)
        return path

    def compress_photos(self, unzipped_folder_name):

        phrase_list = []
        errors_list = []

        tree = os.walk(f"./media/{unzipped_folder_name}")
        photos_list = list(tree)[-1][-1]
        print(photos_list)
        for photo in photos_list:
            phrase, photo_path, compressed_filepath, secure_name = (
                self.secure_filepaths(unzipped_folder_name, photo)
            )
            if not os.path.exists(f"./media_compressed/{unzipped_folder_name}"):
                os.mkdir(f"./media_compressed/{unzipped_folder_name}")
            try:
                self.compress_img(
                    photo_path, compressed_filepath, new_size_ratio=0.6, to_jpg=False
                )
            except Exception as exc:
                log.error("Error while compressing photos, %s", exc)
                errors_list.append(phrase)
                continue
            link = f"{os.getenv('BACKEND_URL')}/get_photo_compressed/{unzipped_folder_name}/{secure_name}"
            link_tuple = (phrase, link)
            phrase_list.append(link_tuple)
        return phrase_list

    @staticmethod
    def save_date_to_redis(folder_name: str):
        expire_date = datetime.now() + timedelta(hours=24)
        expire_date_str = expire_date.isoformat()
        try:
            r.set(folder_name, expire_date_str)
            log.info(f"Successfully saved {expire_date_str} to redis")
        except Exception as exc:
            log.exception("Error while saving date to redis exc=%s", exc)

    def run(self):
        unzipped_folder_name = self.unzip_archive()
        os.remove(self.filepath)
        phrase_list = self.compress_photos(unzipped_folder_name)
        shutil.rmtree(f"./media/{unzipped_folder_name}")
        self.save_date_to_redis(unzipped_folder_name)
        xlsx_path = self.links_to_xlsx(phrase_list, unzipped_folder_name)
        return xlsx_path
