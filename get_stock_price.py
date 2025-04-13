import os
import httpx
import logging
import yfinance as yf
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

mcp = FastMCP(
    name="Stock Price & News Server",
)

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
TAVILY_API_URL = os.getenv("TAVILY_API_URL")

@mcp.tool()
async def get_article(query: str) -> str:
    """
    Use tools when user ask for news about a specific topic.
    Get the latest news article for the given query.
    Returns the summarize article.
    """
    payload = {
        "query": query,
        "topic": "news",  # "general"
        "search_depth": "advanced",
        "chunks_per_source": 3,
        "max_results": 3,
        "days": 7,
        "include_answer": True,
        "include_raw_content": False,
        "include_images": False,
        "include_image_descriptions": False,
        "include_domains": [
            "https://arstechnica.com",
            "https://techcrunch.com",
        ],
    }
    headers = {
        "Authorization": f"Bearer {TAVILY_API_KEY}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(TAVILY_API_URL, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()
            logger.info("Status code: %s", response.status_code)
            return response.text
        except httpx.RequestError as exc:
            logger.error("Request error: %s", exc)
            return None
        except httpx.HTTPStatusError as exc:
            logger.error("HTTP error: %s - %s", exc.response.status_code, exc.response.text)
            return None


@mcp.tool()
def get_stock_price(symbol: str) -> float:
    """
    Retrieve the current stock price for the given ticker symbol.
    Returns the latest closing price as a float.
    """
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period="1d") #["Close"][0]
        if not data.empty:
            price = data['Close'].iloc[-1]
            return float(price)
        else:
            info = stock.info
            price = info.get('regularMarketPrice', None)
            if price is not None:
                return float(price)
            else:
                return f"No price data available for {symbol}"
    except Exception as e:
        return f"Error fetching stock price for {symbol}: {e}"

@mcp.resource("stock://{symbol}")
def get_stock_resource(symbol: str):
    """
    Expose stock price data as a resource.
    Returns a formatted string with the current stock price for the given symbol.
    """
    price = get_stock_price(symbol)
    if price is None:
        return f"No price data available for {symbol}"
    return f"The current stock price for {symbol} is ${price:.2f}"

@mcp.tool()
async def get_stock_price_history(symbol: str, period: str = "1d"):
    """
    Retrieve historical data for a stock given a ticker symbol and a period.
    Returns the historical data as a CSV formatted string.
    
    Parameters:
        symbol: The stock ticker symbol.
        period: The period over which to retrieve historical data (e.g., '1mo', '3mo', '1y').
    """
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period=period)
        if not data.empty:
            return data.to_csv()
        else:
            return f"No historical data available for {symbol}"
    except Exception as e:
        return f"Error fetching historical data for {symbol}: {e}"

@mcp.tool()
def compare_stocks(symbol1: str, symbol2: str):
    """
    Compare the current stock prices of two ticker symbols.
    Returns a formatted message comparing the two stock prices.
    
    Parameters:
        symbol1: The first stock ticker symbol.
        symbol2: The second stock ticker symbol.
    """
    
    price1 = get_stock_price(symbol1)
    price2 = get_stock_price(symbol2)
    if price1 < 0 or price2 < 0:
        return f"Error: Could not retrieve data for comparison of '{symbol1}' and '{symbol2}'."
    if price1 > price2:
        result = f"{symbol1} ${price1:.2f} is higher than {symbol2} ${price2:.2f}."
    elif price1 < price2:
        result = f"{symbol1} ${price1:.2f} is lower than {symbol2} ${price2:.2f}."
    else:
        result = f"Both {symbol1} and {symbol2} have the same price ${price1:.2f}."
    return result

if __name__ == "__main__":
    mcp.run(transport="stdio")