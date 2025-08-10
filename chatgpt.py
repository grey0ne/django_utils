from openai import AsyncOpenAI
import base64


def get_base64_image(image_data: bytes) -> str:
    return f"data:image/jpeg;base64,{base64.b64encode(image_data).decode('utf-8')}"


async def analyze_image(image_data: bytes, prompt: str, api_key: str) -> str | None:

    client = AsyncOpenAI(api_key=api_key)
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt},
            {"role": "user", "content": [{"type": "image_url", "image_url": {"url": get_base64_image(image_data)}}]}
        ]
    )
    return response.choices[0].message.content