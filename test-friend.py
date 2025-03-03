import json
import requests
import warnings
import time
import os
import concurrent.futures
from datetime import datetime
from queue import Queue


# 忽略 HTTPS 证书警告
warnings.filterwarnings("ignore", message="Unverified HTTPS request is being made.*")

# 用户代理
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
HEADERS = {"User-Agent": USER_AGENT}

# 加载环境变量
if os.getenv("LIJIANGAPI_TOKEN") is None:
    print("本地运行，从环境变量中加载并获取环境变量")
    from dotenv import load_dotenv
    load_dotenv()

env_loaded = os.getenv("LIJIANGAPI_TOKEN")
print("本地运行，从环境变量中加载 API Key" if not env_loaded else "在服务器上运行，从环境变量中获取 API Key")

# API Key 和 URL 模板
API_KEY = os.getenv("LIJIANGAPI_TOKEN")
API_URL_TEMPLATE = "https://api.nsmao.net/api/web/query?key={}&url={}" if API_KEY else None

# 代理配置
PROXY_URL_TEMPLATE = os.getenv("PROXY_URL") + "{}" if os.getenv("PROXY_URL") else None
print("代理 URL 获取成功" if PROXY_URL_TEMPLATE else "未提供代理 URL")

# API 请求队列
api_request_queue = Queue()

def fetch_json_data(url):
    """获取 JSON 数据"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"无法获取 JSON 数据: {e}")
        return None

def check_link(item):
    """检查链接可访问性"""
    link = item['link']
    
    for method, url in [("直接访问", link), ("代理访问", PROXY_URL_TEMPLATE.format(link) if PROXY_URL_TEMPLATE else None)]:
        if not url:
            continue
        
        try:
            start_time = time.time()
            response = requests.get(url, headers=HEADERS, timeout=15, verify=True)
            latency = round(time.time() - start_time, 2)
            
            if response.status_code == 200:
                print(f"成功通过 {method} {link}, 延迟 {latency} 秒")
                return item, latency
        except requests.RequestException:
            print(f"{method} 失败: {link}")
    
    # 直接访问和代理都失败，加入 API 请求队列
    api_request_queue.put(item)
    return item, -1

def handle_api_requests():
    """处理 API 请求队列"""
    while not api_request_queue.empty():
        time.sleep(0.2)  # 控制 API 请求速率
        item = api_request_queue.get()
        link = item['link']
        
        if not API_URL_TEMPLATE:
            print("API Key 未提供，无法通过 API 访问")
            continue
        
        try:
            response = requests.get(API_URL_TEMPLATE.format(API_KEY, link), headers=HEADERS, timeout=30)
            response_data = response.json()
            
            if response_data.get('code') == 200:
                latency = round(response_data.get('exec_time', -1), 2)
                print(f"成功通过 API 访问 {link}, 延迟 {latency} 秒")
                item['latency'] = latency
            else:
                print(f"API 访问失败: {link}，错误代码 {response_data.get('code')}")
                item['latency'] = -1
        except requests.RequestException:
            print(f"API 请求失败: {link}")
            item['latency'] = -1
        
        time.sleep(0.2)  # 控制 API 请求速率

def main():
    """主逻辑"""
    json_url = 'https://blog.liushen.fun/flink_count.json'
    data = fetch_json_data(json_url)
    if not data:
        return
    
    link_list = data.get('link_list', [])
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(check_link, link_list))
    
    handle_api_requests()
    
    # 处理最终结果
    link_status = [
        {'name': item['name'], 'link': item['link'], 'latency': item.get('latency', latency)}
        for item, latency in results
    ]
    
    # 统计数据
    accessible_count = sum(1 for s in link_status if s['latency'] != -1)
    total_count = len(link_status)
    inaccessible_count = total_count - accessible_count
    
    # 生成输出 JSON
    output_data = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'accessible_count': accessible_count,
        'inaccessible_count': inaccessible_count,
        'total_count': total_count,
        'link_status': link_status
    }
    
    output_path = './result.json'
    with open(output_path, 'w', encoding='utf-8') as file:
        json.dump(output_data, file, ensure_ascii=False, indent=4)
    
    print(f"共检查 {total_count} 个链接，其中 {accessible_count} 个可访问，{inaccessible_count} 个不可访问。")
    print(f"检查完成，结果已保存至 '{output_path}'。")

if __name__ == "__main__":
    main()
