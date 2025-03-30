import base64
from django.core.files.base import ContentFile


def base64_to_file(data: str, name: str) -> ContentFile:
    format, imgstr = data.split(';base64,') 
    ext = format.split('/')[-1] 

    return ContentFile(base64.b64decode(imgstr), name=name + '.' + ext)

