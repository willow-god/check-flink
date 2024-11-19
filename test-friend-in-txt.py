import json
import requests
import warnings
import time
import concurrent.futures
from datetime import datetime
from queue import Queue
import os
import csv

# 忽略警告信息
warnings.filterwarnings("ignore", message="Unverified HTTPS request is being made.*")

# 用户代理字符串，模仿浏览器
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"

# API Key 和 请求URL的模板
if os.getenv("LIJIANGAPI_TOKEN") is None:
    print("本地运行，从环境变量中加载并获取API Key")
    from dotenv import load_dotenv
    load_dotenv()
else:
    print("在服务器上运行，从环境变量中获取API Key")

api_key = os.getenv("LIJIANGAPI_TOKEN")
api_url_template = "https://api.nsmao.net/api/web/query?key={}&url={}"

# 代理链接的模板
proxy_url = os.getenv("PROXY_URL")
if proxy_url is not None:
    proxy_url_template = proxy_url + "{}"
else:
    proxy_url_template = None

# 初始化一个队列来处理API请求
api_request_queue = Queue()

# API 请求处理函数
def handle_api_requests():
    while not api_request_queue.empty():
        item = api_request_queue.get()
        headers = {"User-Agent": user_agent}
        link = item['link']
        if api_key is None:
            print("API Key 未提供，无法通过API访问")
            item['latency'] = -1
            break
        api_url = api_url_template.format(api_key, link)

        try:
            response = requests.get(api_url, headers=headers, timeout=15, verify=True)
            response_data = response.json()

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

        time.sleep(0.2)  # 控制API请求速率

# 检查链接是否可访问的函数并测量时延
def check_link_accessibility(item):
    headers = {"User-Agent": user_agent}
    link = item['link']
    latency = -1

    try:
        start_time = time.time()
        response = requests.get(link, headers=headers, timeout=15, verify=True)
        latency = round(time.time() - start_time, 2)
        if response.status_code == 200:
            print(f"成功通过直接访问 {link}, 延迟为 {latency} 秒")
            return [item, latency]
    except requests.RequestException:
        print(f"直接访问失败 {link}")

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

    item['latency'] = -1
    api_request_queue.put(item)
    return [item, latency]

# 从CSV文件获取友链数据
link_list = []
csv_file_path = './link.csv'

with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
    csvreader = csv.reader(csvfile)
    for row in csvreader:
        if len(row) == 2:
            name, link = row
            link_list.append({'name': name, 'link': link})

# 使用ThreadPoolExecutor并发检查多个链接
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(check_link_accessibility, link_list))

# 处理API请求
handle_api_requests()

# 添加时延信息到每个链接项
link_status = [{'name': result[0]['name'], 'link': result[0]['link'], 'latency': result[0].get('latency', result[1])} for result in results]

# 获取当前时间
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 统计可访问和不可访问的链接数
accessible_count = 0
inaccessible_count = 0

for result in results:
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
