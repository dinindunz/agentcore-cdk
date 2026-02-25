from common.logger import logger


def handler(event, context):
    """Convert temperature between Celsius and Fahrenheit."""
    if "celsius" in event:
        celsius = float(event["celsius"])
        logger.debug(f"[TempConverter] Converting Celsius to Fahrenheit: celsius={celsius}")
        fahrenheit = round((celsius * 9 / 5) + 32, 4)
        logger.info(f"[TempConverter] Conversion result: celsius={celsius} fahrenheit={fahrenheit}")
        return {"fahrenheit": fahrenheit}
    elif "fahrenheit" in event:
        fahrenheit = float(event["fahrenheit"])
        logger.debug(f"[TempConverter] Converting Fahrenheit to Celsius: fahrenheit={fahrenheit}")
        celsius = round((fahrenheit - 32) * 5 / 9, 4)
        logger.info(f"[TempConverter] Conversion result: fahrenheit={fahrenheit} celsius={celsius}")
        return {"celsius": celsius}
    else:
        logger.error(f"[TempConverter] Invalid input received: event={event}")
        return {"error": f"Unknown input: {event}"}
