import json
import requests
import warnings
import time
import concurrent.futures
from datetime import datetime
from queue import Queue
import os

# 忽略警告信息
warnings.filterwarnings("ignore", message="Unverified HTTPS request is being made.*")

# 用户代理字符串，模仿浏览器
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"

# API Key 和 请求URL的模板
# 判断是否在本地运行，如果是则从环境变量中获取API Key
if os.getenv("LIJIANGAPI_TOKEN") is None:
    print("本地运行，从环境变量中加载并获取API Key")
    from dotenv import load_dotenv
    load_dotenv()
else:
    print("在服务器上运行，从环境变量中获取API Key")

api_key = os.getenv("LIJIANGAPI_TOKEN")
api_url_template = "https://api.nsmao.net/api/web/query?key={}&url={}"

# 代理链接的模板，代理是通过在代理地址后加目标 URL 来请求，代理地址确保以 / 结尾
proxy_url = os.getenv("PROXY_URL")
if proxy_url is not None:
    proxy_url_template = proxy_url + "{}"
else:
    proxy_url_template = None

# 初始化一个队列来处理API请求
api_request_queue = Queue()

# API 请求处理函数，确保每秒不超过5次请求
def handle_api_requests():
    while not api_request_queue.empty():
        time.sleep(0.2)  # 控制API请求速率，确保每秒不超过5次
        item = api_request_queue.get()
        headers = {"User-Agent": user_agent}
        link = item['link']
        if api_key is None:
            print("API Key 未提供，无法通过API访问")
            item['latency'] = -1
            break
        api_url = api_url_template.format(api_key, link)

        try:
            response = requests.get(api_url, headers=headers, timeout=30)
            response_data = response.json()

            # 提取API返回的code和exec_time
            if response_data['code'] == 200:
                latency = round(response_data['exec_time'], 2)
                print(f"成功通过API访问 {link}, 延迟为 {latency} 秒")
                item['latency'] = latency
            else:
                print(f"API返回错误，code: {response_data['code']}，无法访问 {link}")
                item['latency'] = -1
        except requests.RequestException:
            print(f"API请求失败，无法访问 {link}")
            item['latency'] = -1

        time.sleep(0.2)  # 控制API请求速率，确保每秒不超过5次

# 检查链接是否可访问的函数并测量时延
def check_link_accessibility(item):
    headers = {"User-Agent": user_agent}
    link = item['link']
    latency = -1

    # 1. 首先尝试直接访问
    try:
        start_time = time.time()
        response = requests.get(link, headers=headers, timeout=15, verify=True)
        latency = round(time.time() - start_time, 2)
        if response.status_code == 200:
            print(f"成功通过直接访问 {link}, 延迟为 {latency} 秒")
            return [item, latency]
    except requests.RequestException:
        print(f"直接访问失败 {link}")

    # 2. 尝试通过代理访问(可选)
    if proxy_url_template is None:
        print("未提供代理地址，无法通过代理访问")
    else:
        proxy_url = proxy_url_template.format(link)
        try:
            start_time = time.time()
            response = requests.get(proxy_url, headers=headers, timeout=15, verify=True)
            latency = round(time.time() - start_time, 2)
            if response.status_code == 200:
                print(f"成功通过代理访问 {link}, 延迟为 {latency} 秒")
                return [item, latency]
        except requests.RequestException:
            print(f"代理访问失败 {link}")

    # 3. 如果代理也失败，添加到API队列中
    item['latency'] = -1
    api_request_queue.put(item)
    return [item, latency]

# 目标JSON数据的URL
json_url = 'https://blog.liushen.fun/flink_count.json'

# 发送HTTP GET请求获取JSON数据
response = requests.get(json_url)
if response.status_code == 200:
    data = response.json()  # 解析JSON数据
    link_list = data['link_list']  # 提取所有的链接项
else:
    print(f"Failed to retrieve data, status code: {response.status_code}")
    exit()

# 使用ThreadPoolExecutor并发检查多个链接
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(check_link_accessibility, link_list))

# 处理API请求
handle_api_requests()

# 添加时延信息到每个链接项
link_status = [{'name': result[0]['name'], 'link': result[0]['link'], 'latency': result[0].get('latency', result[1])} for result in results]

# 获取当前时间
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 统计可访问和不可访问的链接数，计算 accessible_count 和 inaccessible_count
accessible_count = 0
inaccessible_count = 0

for result in results:
    # print(result[1])
    if result[1] != -1:
        accessible_count += 1
    else:
        inaccessible_count += 1

# 计算 total_count
total_count = len(results)

# 将结果写入JSON文件
output_json_path = './result.json'
with open(output_json_path, 'w', encoding='utf-8') as file:
    json.dump({
        'timestamp': current_time,
        'accessible_count': accessible_count,
        'inaccessible_count': inaccessible_count,
        'total_count': total_count,
        'link_status': link_status
    }, file, ensure_ascii=False, indent=4)

print(f"检查完成，结果已保存至 '{output_json_path}' 文件。")

