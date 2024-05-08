# aichatlib
This project is in development. I am working on this out of frustration of the python openAI and Antropic libraries. They are very thin wrappers with an overreliance on dicts for everything. Especially when pictures and tools are brought into the mix, this leads to very buggy and unworkable code. This library will wrap those libraries. For now, this is made to work with the openAI library, however it can also work for antrophic or any other LLM by using the litellm library instead of the openAI one!

# Install
- install python module "parse_doc"
- copy all the python files in this repo and place into your project

# tools.py example
BaseTools in tools.py lets you easily add tool functions for the LLM to use.

First define the function that you want the llm to use. Instead of later creating a dict with your documentation, just document it how you normaly would with a python docstring. For the example I will use google style documentation. Always add an extra undocumented "ctx" parameter. This won't be provided by the LLM and contains the context of where the function was called, e.g. what user requested this.
```python
def get_current_weather(ctx, location, unit="fahrenheit"):
    """
    Get the current weather in a given location

    args:
      location (string): The city and state, e.g. San Francisco, CA
      unit (string, optional): enum, either "celsius" or "fahrenheit"
    """

    if "tokyo" in location.lower():
        return json.dumps({"location": "Tokyo", "temperature": "10", "unit": unit})
    elif "san francisco" in location.lower():
        return json.dumps({"location": "San Francisco", "temperature": "72", "unit": unit})
    elif "paris" in location.lower():
        return json.dumps({"location": "Paris", "temperature": "22", "unit": unit})
    else:
        return json.dumps({"location": location, "temperature": "unknown"})
```

Next create a BaseTools object with all your tools, in this case just get_current_weather. Get the docs for the LLM from this object.
```python
from tools import BaseTools

tools = BaseTools([get_current_weather])

response = completions.create(
        model="your_model_here",
        messages=messages,
        tools=tools.get_all_json_docs(),
    )
```
Say the response contains multiple tool calls. The tools object will take in a tool call and return the response, ready to be appended to your messages. Just don't forget to provide the ctx yourself!
```python
responses = []
for call in response["message"]["tools_calls]:
    response.append(tools.execute_tool_call(ctx, call))
messages.extend(responses)
```
That's it! You can now request the next completion.

# message.py example

Add some messages
```python
from message import *

log = []
log.append(Message(Role.USER, "hello there!"))
log.append(PictureMessage(Message(Role.USER, yourImageUrl, "Hello!!")))
```

Call convert_to on every message, to prep them to be sent to the API
```python
ready_log = [convert_to(Model.GPT) for msg in log]
completion = (...
```

# What's next?
If this receives any attention, I will keep expanding on this, to handle everything else for you.




