import base64
from enum import Enum
from PIL import Image
from io import BytesIO
import httpx


def convert(msg, model: util.Models):
    if isinstance(msg, Message):
        return msg.convert_to(model)
    else:
        return msg


class Role(Enum):
    SYSTEM = "system"
    ASSISTANT = "assistant"
    USER = "user"
    TOOL = "tool"
    
class Models(Enum):
    GPT = 1
    CLAUDE = 2

class Message:
    text: str
    role: Role

    def __init__(self, role, text=None):
        self.role = role
        self.text = text

    async def convert_to(self, model: Models):
        return await self.convert_to_openai()

    async def convert_to_openai(self):
        return {"role": self.role.value, "content": self.text}


class PictureMessage(Message):
    picture: str

    def __init__(self, role, picture, text=None):
        super().__init__(role, text)
        self.picture = picture

    async def convert_to(self, model: Models):
        if model is Models.GPT:
            return await self.convert_to_openai()
        elif model is Models.CLAUDE:
            return await self.convert_to_anthropic()

    async def convert_to_openai(self):
        return {"role": self.role.value, "content": [
            {"type": "text", "text": self.text},
            {"type": "image_url", "image_url":{"url":self.picture, "detail":"low"}}
        ]}

    async def convert_to_anthropic(self):
        async with httpx.AsyncClient() as client:
            res = await client.get(self.picture)
            image_bytes_file = BytesIO(res.content)
            image = Image.open(image_bytes_file)
            image.thumbnail((300, 300))
            with BytesIO() as buffer:
                image.save(buffer, format="png")
                image_bytes = buffer.getvalue()
            base64_encoded_image = base64.b64encode(image_bytes).decode("utf-8")
            return {"role": self.role.value, "content": [
                {"type": "text", "text": self.text},
                {"type": "image_url", "image_url": {"url":f"data:image/png;base64,{base64_encoded_image}"}}
            ]}
