import requests
import string
from concurrent.futures import ThreadPoolExecutor, as_completed

# 定义URL和POST数据
url = "http://10.1.99.210:7860/chat"

c = string.printable
visited_combinations = set()

def send_request(combination):
    if combination in visited_combinations:
        return
    visited_combinations.add(combination)
    
    response = requests.post(url, json={"message": combination})
    print(f"Sent: {combination}, Response: {response.text}")
    
    if "accepted" in response.text:
        print(f"Combination accepted: {combination}")

def f(ch):
    if len(ch) > 4:
        return
    
    for i in c:
        send_request(ch + i)
        f(ch + i)

if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = []
        futures.append(executor.submit(f, ""))
        
        # 等待所有任务完成
        for future in as_completed(futures):
            future.result()
