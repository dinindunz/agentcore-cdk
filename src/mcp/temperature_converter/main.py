def handler(event, context):
    if "celsius" in event:
        celsius = float(event["celsius"])
        return {"fahrenheit": round((celsius * 9 / 5) + 32, 4)}
    elif "fahrenheit" in event:
        fahrenheit = float(event["fahrenheit"])
        return {"celsius": round((fahrenheit - 32) * 5 / 9, 4)}
    else:
        return {"error": f"Unknown input: {event}"}
