import json
from docstring_parser import parse as parse_doc

class BaseTools:
    tool_functions: []

    def __init__(self, tool_functions):
        self.tool_functions = tool_functions

    def get_all_json_docs(self):
        return [self.create_json_docstring(fun) for fun in self.tool_functions]

    async def execute_tool_call(self, ctx, tool_call):
        for tool_function in self.tool_functions:
            if tool_call.function.name == tool_function.__name__:
                params = json.loads(tool_call.function.arguments)
                print(f"Function {tool_call.function.name} called with {params}")
                params["ctx"] = ctx
                response = await tool_function(**params)
                return {"role": "tool", "tool_call_id": tool_call.id, "content": response, "name": tool_call.function.name}

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

