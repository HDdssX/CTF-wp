from flask import Flask, request, jsonify, render_template
from openai import OpenAI
import httpx, json, uuid

app = Flask(__name__)

API_KEY = "sk-e8a5dc1c273044e3b3be20992e8207c4"
MCP_SERVICE_URL = "http://localhost:8001/mcp"
client = OpenAI(
        api_key = API_KEY,
        base_url="https://api.deepseek.com/v1")

TOOLS_SPEC = [
    {"type": "function", "function": {"name": "py_eval", "description": "运行代码", "parameters": {"type": "object", "properties": {"code": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "py_request", "description": "访问网页,获取前300个字符", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}}}}
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods = ['POST'])
def chat():
    user_input = request.json.get("message")
    # print(user_input)
    messages = [
    {
        "role": "system",
        "content": "你是一名CTF WEB高手,负责理解用户请求。你需要结合信息,自主判断是否需要调用工具来完成用户任务。"
    },
    {
        "role": "user",
        "content": user_input
    }
    ]

    response = client.chat.completions.create(
            model = "deepseek-chat",
            messages=messages,
            tools = TOOLS_SPEC
    )
    # print(response)
    ai_msg = response.choices[0].message

    if ai_msg.tool_calls:
        tool_call = ai_msg.tool_calls[0]
        return jsonify({
            "type": "tool_request",
            "tool_call_id": tool_call.id,
            "tool_name": tool_call.function.name,
            "arguments": json.loads(tool_call.function.arguments),
            "answer": ai_msg.content
        })

    return jsonify({"type": "text", "answer": ai_msg.content})


@app.route('/execute_tool', methods=['POST'])
def execute_tool():
    data = request.json
    tool_name = data.get("name")
    arguments = data.get("arguments")
    if (tool_name == "py_eval"):
        return jsonify({"code": 0, "result": "py_eval被管理员禁用了"})

    with httpx.Client() as sync_http:
        rpc_data = {
            "jsonrpc": "2.0", "id": str(uuid.uuid4()), "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments}
        }
        res = sync_http.post(MCP_SERVICE_URL, json = rpc_data)
        mcp_output = res.json()["result"]["content"][0]["text"]

        if (mcp_output.startswith('{"error":')):
            return jsonify({"code": 2, "result": mcp_output[11:-2]})
        return jsonify({"code": 1, "result": mcp_output})

if __name__ == "__main__":
    app.run(host = "0.0.0.0", port = 5000)