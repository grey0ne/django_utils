import base64
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.base import File


def base64_to_file(data: str, name: str) -> ContentFile[bytes]:
    splitted = data.split(';base64,')
    if len(splitted) == 2:
        format, imgstr = splitted
        ext = format.split('/')[-1]
        name = name + '.' + ext
    else:
        imgstr = data


    return ContentFile(base64.b64decode(imgstr), name=name)

def open_s3_file(file_name: str) -> File[bytes]:
    # TODO add context manager to close file
    return default_storage.open(file_name, 'rb') # type: ignore