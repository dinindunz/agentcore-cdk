from mcp.server.fastmcp import FastMCP

mcp = FastMCP(host="0.0.0.0", stateless_http=True)


@mcp.tool(description="Add two numbers")
def add(a: float, b: float) -> float:
    return a + b


@mcp.tool(description="Subtract b from a")
def subtract(a: float, b: float) -> float:
    return a - b


@mcp.tool(description="Multiply two numbers")
def multiply(a: float, b: float) -> float:
    return a * b


@mcp.tool(description="Divide a by b")
def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
