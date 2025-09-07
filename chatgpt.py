from openai import AsyncOpenAI
from enum import StrEnum
from io import BytesIO
import base64

class GptModel(StrEnum):
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_5_MINI = "gpt-5-mini"
    GPT_5 = "gpt-5"
    GPT_IMAGE = "gpt-image-1"


def get_base64_image(image_data: bytes) -> str:
    return f"data:image/jpeg;base64,{base64.b64encode(image_data).decode('utf-8')}"


async def analyze_image(
    image_data: bytes, prompt: str, api_key: str,
    model: GptModel = GptModel.GPT_4O_MINI
) -> str | None:

    client = AsyncOpenAI(api_key=api_key)
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt},
            {"role": "user", "content": [{"type": "image_url", "image_url": {"url": get_base64_image(image_data)}}]}
        ]
    )
    return response.choices[0].message.content


async def text_prompt(
    prompt: str, api_key: str,
    model: GptModel = GptModel.GPT_4O_MINI
) -> str | None:
    client = AsyncOpenAI(api_key=api_key)
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content


class ImageSize(StrEnum):
    LARGE = "1024x1024"
    HORIZONTAL_LARGE = "1536x1024"
    VERTICAL_LARGE = "1024x1536"



async def generate_image(
    prompt: str,
    api_key: str,
    size: ImageSize,
    model: GptModel = GptModel.GPT_IMAGE,
) -> BytesIO | None:
    """
    Generate an image from a prompt using the GPT-Image model.
    size: 1024x1024, 1024x1792, 1792x1024
    Returns the URL of the generated image.
    """
    client = AsyncOpenAI(api_key=api_key)
    response = await client.images.generate(
        model=model,
        prompt=prompt,
        size=size.value,
    )
    if not response or not response.data or not response.data[0].b64_json:
        return None
    
    image_data = base64.b64decode(response.data[0].b64_json)
    image = BytesIO(image_data)
    return image

