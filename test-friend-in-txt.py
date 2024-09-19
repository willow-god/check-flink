import json
import requests
import warnings
import concurrent.futures
from datetime import datetime

# 忽略警告信息
warnings.filterwarnings("ignore", message="Unverified HTTPS request is being made.*")

# 用户代理字符串，模仿浏览器
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"

# 检查链接是否可访问的函数
def check_link_accessibility(item):
    headers = {"User-Agent": user_agent}
    link = item['link']
    latency = None
    ssl_status = None

    # 尝试检查 HTTPS 链接
    try:
        response = requests.head(link, headers=headers, timeout=5, verify=False)
        latency = response.elapsed.total_seconds()
        if response.status_code == 200:
            ssl_status = response.url.startswith('https')
            return [item, latency, ssl_status]
    except requests.RequestException:
        pass

    # 如果 HTTPS 失败，尝试使用代理
    try:
        proxy_link = 'http://' + link  # 转发代理使用 HTTP
        response = requests.get(proxy_link, headers=headers, timeout=5, verify=False)
        latency = response.elapsed.total_seconds()
        if response.status_code == 200:
            ssl_status = response.url.startswith('https')
            return [item, latency, ssl_status]
    except requests.RequestException:
        pass

    # 如果代理也失败，尝试 HTTP 链接
    try:
        http_link = 'http://' + link
        response = requests.get(http_link, headers=headers, timeout=5, verify=False)
        latency = response.elapsed.total_seconds()
        if response.status_code == 200:
            ssl_status = response.url.startswith('https')
            return [item, latency, ssl_status]
    except requests.RequestException:
        pass

    return [item, -1, False]  # 如果所有请求都失败，返回 -1

# 从 link.txt 中读取链接和名称
link_list = []
with open('./link.txt', 'r', encoding='utf-8') as file:
    for line in file:
        if line.strip():
            name, link = line.strip().split(',', 1)
            link_list.append({'name': name, 'link': link})

# 使用 ThreadPoolExecutor 并发检查多个链接
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(check_link_accessibility, link_list))

# 分割可达和不可达的链接
link_status = []
for result in results:
    item, latency, ssl_status = result
    if latency != -1:
        latency = round(latency, 2)  # 保留两位小数
    link_status.append({
        'name': item['name'],
        'link': item['link'],
        'latency': latency,  # 如果 latency 是 -1，则直接保存为 -1
        'ssl_status': ssl_status
    })

# 获取当前时间
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 统计可访问和不可访问的链接数
accessible_count = len([item for item in link_status if item['latency'] != -1])
inaccessible_count = len([item for item in link_status if item['latency'] == -1])
total_count = len(link_status)

# 将结果写入 JSON 文件
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
