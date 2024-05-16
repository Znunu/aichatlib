import asyncio
import base64
import json
from enum import Enum
import util
from PIL import Image
from io import BytesIO
import httpx
from collections import namedtuple


async def convert(msg, model: util.Model_Class):
    if isinstance(msg, Message):
        return await msg.convert_to(model)
    elif isinstance(msg, dict):
        return msg
    else:
        return msg


class Role(Enum):
    SYSTEM = "system"
    ASSISTANT = "assistant"
    USER = "user"
    TOOL = "tool"


class Message:
    text: str
    role: Role

    def __init__(self, role, text=None):
        self.role = role
        self.text = text

    async def convert_to(self, model):
        return await self.convert_to_openai()

    async def convert_to_openai(self):
        return {"role": self.role.value, "content": self.text}

    @classmethod
    def convert_from(cls, self_as_dict):
        return cls(self_as_dict["role"], self_as_dict["content"])

    def count_tokens(self):
        return util.words_to_tokens(self.text)


class PictureMessage(Message):
    picture: str

    def __init__(self, role, picture, text=None):
        super().__init__(role, text)
        self.picture = picture

    async def convert_to(self, model):
        if model == util.weak_gpt_version:
            return await Message(self.role, self.text).convert_to(model)
        elif model == util.strong_gpt_version:
            return await self.convert_to_openai()
        elif model in (util.weak_claude_version, util.strong_claude_version):
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

    @classmethod
    def convert_from(cls, self_as_dict):
        contents = self_as_dict["content"]
        text = next(c["text"] for c in contents if c["type"] == "text")
        picture = next(c["image_url"]["url"] for c in contents if c["type"] == "image_url")
        return cls(role=self_as_dict["role"], picture=picture, text=text)


class ToolCallMessage(Message):
    Call = namedtuple("Call", ["fun", "id", "args"])
    calls: [Call]

    def __init__(self, calls, text=""):
        super().__init__(Role.ASSISTANT, text)
        self.calls = calls

    async def convert_to(self, model: util.Model_Class):
        return await self.convert_openai()

    async def convert_openai(self):
        return {
            "content": self.text,
            "role": "assistant",
            "tool_calls": [{
                "id": call.id,
                "type": "function",
                "function": {
                    "name": call.fun.__name__,
                    "arguments": json.dumps(call.args)
                }
            }
                for call in self.calls]
        }

    async def get_responses(self, convo):
        tasks = (asyncio.create_task(call.fun(**call.args, convo=convo)) for call in self.calls)
        responses = await asyncio.gather(*tasks)
        return [ToolResponseMessage(ToolResponseMessage.Response(call.fun, call.id, res)) for res, call in zip(responses, self.calls)]


class ToolResponseMessage(Message):
    Response = namedtuple("Response", ["fun", "id", "response"])
    response: Response

    def __init__(self, response):
        super().__init__(Role.TOOL, None)
        self.response = response

    async def convert_to(self, model: util.Model_Class):
        return await self.convert_to_openai()

    async def convert_to_openai(self):
        return {
            "role": "tool",
            "tool_call_id": self.response.id,
            "content": self.response.response,
            "name": self.response.fun.__name__
        }
