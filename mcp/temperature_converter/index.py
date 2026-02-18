def handler(event, context):
    tool_name = event.get("tool_name") or event.get("name", "")
    params = event.get("parameters") or event.get("input") or {}

    if tool_name == "celsius_to_fahrenheit":
        celsius = float(params.get("celsius", 0))
        return {"fahrenheit": round((celsius * 9 / 5) + 32, 4)}
    elif tool_name == "fahrenheit_to_celsius":
        fahrenheit = float(params.get("fahrenheit", 0))
        return {"celsius": round((fahrenheit - 32) * 5 / 9, 4)}
    else:
        return {"error": f"Unknown tool: {tool_name}"}
