# aichatlib
This project is in development. I am working on this out of frustration of the python openAI and Antropic libraries. They are very thin wrappers with an overreliance on dicts for everything. Especially when pictures and tools are brought into the mix, this leads to very buggy and unworkable code. This library will wrap those libraries.

# Install
- install python module "parse_doc"
- copy all the python files in this repo and place into your project

# Example
BaseTools in tools.py lets you easily add tool function functionality.

First define the function that you want the llm to use. Instead of later creating a dict with your documentation, just document it how you normaly would with a python docstring. For the example I will use google style documentation.
```python
def get_current_weather(location, unit="fahrenheit"):
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
