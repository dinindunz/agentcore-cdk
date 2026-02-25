from common.logger import logger
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(host="0.0.0.0", stateless_http=True)


@mcp.tool(description="Add two numbers")
def add(a: float, b: float) -> float:
    """Add two numbers."""
    logger.debug(f"[Calculator] Add operation: a={a} b={b}")
    result = a + b
    logger.info(f"[Calculator] Add result: a={a} b={b} result={result}")
    return result


@mcp.tool(description="Subtract b from a")
def subtract(a: float, b: float) -> float:
    """Subtract b from a."""
    logger.debug(f"[Calculator] Subtract operation: a={a} b={b}")
    result = a - b
    logger.info(f"[Calculator] Subtract result: a={a} b={b} result={result}")
    return result


@mcp.tool(description="Multiply two numbers")
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    logger.debug(f"[Calculator] Multiply operation: a={a} b={b}")
    result = a * b
    logger.info(f"[Calculator] Multiply result: a={a} b={b} result={result}")
    return result


@mcp.tool(description="Divide a by b")
def divide(a: float, b: float) -> float:
    """Divide a by b."""
    logger.debug(f"[Calculator] Divide operation: a={a} b={b}")
    if b == 0:
        logger.error(f"[Calculator] Division by zero attempted: a={a} b={b}")
        raise ValueError("Cannot divide by zero")
    result = a / b
    logger.info(f"[Calculator] Divide result: a={a} b={b} result={result}")
    return result


if __name__ == "__main__":
    logger.info("[Calculator] Starting MCP server: host=0.0.0.0 transport=streamable-http")
    mcp.run(transport="streamable-http")
