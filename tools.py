import asyncio
import json
from datetime import datetime
import httpx
import util
from docstring_parser import parse as parse_doc
from litellm import acompletion
import beta.message as message_types


client = httpx.AsyncClient()


class Forget(Exception):
    pass


class BaseTools:
    tool_functions: []
    usage: {}  # = {util.Models.GPT: 300, util.Models.CLAUDE: 850}

    def __init__(self, tool_functions):
        self.tool_functions = tool_functions

    def get_all_json_docs(self):
        return [self.create_json_docstring(fun) for fun in self.tool_functions]

    def new_tool_call_msg(self, msg, extra_args=None):
        calls = []
        for call in msg.tool_calls:
            fun = next(f for f in self.tool_functions if f.__name__ == call.function.name)
            args = json.loads(call.function.arguments)
            if extra_args: args.extend(extra_args)
            calls.append(message_types.ToolCallMessage.Call(fun, call.id, args))
        return message_types.ToolCallMessage(calls)

    @staticmethod
    def create_json_docstring(func):
        docs = parse_doc(func.__doc__)
        json_docs = {"type": "function", "function": {
            "parameters": {"type": "object", "properties": {}},
            "name": func.__name__,
            "description": docs.description}}
        required = []
        for param in docs.params:
            if not param.is_optional: required.append(param.arg_name)
            param_docs = {"description": param.description, "type": param.type_name}
            json_docs["function"]["parameters"]["properties"][param.arg_name] = param_docs
        json_docs["function"]["parameters"]["required"] = required
        return json_docs

    async def token_usage(self, model: util.Model_Class):
        await self.tokens_for_tools()
        return self.usage[model]

    async def tokens_for_tools(self):
        async def run(model, specs):
            response = await asyncio.wait_for(acompletion(
                model=model,
                messages=[{"role": "user", "content": "."}],
                temperature=1,
                max_tokens=200,
                tools=specs
            ), timeout=30)
            return response["usage"]["prompt_tokens"]

        self.usage = {}
        for model in (util.strong_gpt_version, util.strong_claude_version):
            res_without_tools = await run(model, None)
            res_with_tools = await run(model, self.get_all_json_docs())
            delta = res_with_tools - res_without_tools
            print(f"{model}: {delta}")
            self.usage[model] = delta

