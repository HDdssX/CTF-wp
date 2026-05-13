from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

async def py_eval(code: str):
    try:
        local_vars = {}
        exec(code, {}, local_vars)
        return {"result": str(local_vars), "status": "success"}
    except Exception as e:
        return {"error": str(e), "status": "failed"}

def check_url(url: str) -> bool:
    if (url.startswith("http") == False): return True
    return False

async def py_request(url: str):
    if (check_url(url)):
        return {"error": "Unsafe URL"}
    from playwright.async_api import async_playwright
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox",
                      "--disable-dev-shm-usage",
                      "--disable-web-security"]
            )

            context = await browser.new_context()
            page = await context.new_page()

            response = await page.goto(url, timeout = 10000, wait_until = "networkidle")
            content = await page.content()

            result = {
                "status_code": response.status if response else None,
                "content": content[:300]
            }

            await browser.close()

            return result

    except Exception as e:
        return {"error": str(e)}

TOOLS = {"py_eval": py_eval, "py_request": py_request}

@app.post("/mcp")
async def mcp_handler(request: Request):
    data = await request.json()
    params = data.get("params", {})
    name = params.get("name")
    args = params.get("arguments", {})

    if name in TOOLS:
        result = await TOOLS[name](**args)
        return {
            "jsonrpc": "2.0",
            "id": data.get("id"),
            "result": {"content": [{"type": "text", "text": json.dumps(result)}]}
        }
    return {"error": "Tool not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)