import json
import requests
import warnings
import concurrent.futures
from datetime import datetime
import time

# 忽略警告信息
warnings.filterwarnings("ignore", message="Unverified HTTPS request is being made.*")

# 用户代理字符串，模仿浏览器
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"

# 拼接的备用域名
backup_domain = "https://lius.me/"

# 检查链接是否可访问的函数并测量时延和SSL状态
def check_link_accessibility(item):
    headers = {"User-Agent": user_agent}
    link = item['link']
    ssl_status = False
    latency = -1

    # 尝试使用 HTTPS 访问
    try:
        start_time = time.time()
        response = requests.get(link, headers=headers, timeout=15, verify=True)
        latency = round(time.time() - start_time, 2)
        if response.status_code == 200 and response.url.startswith("https"):
            ssl_status = True
            print(f"成功通过HTTPS访问 {link}")
            return [item, latency, ssl_status]  # 成功通过HTTPS访问
    except requests.RequestException:
        pass

    # 如果 HTTPS 访问失败，尝试备用代理
    backup_link = backup_domain + link
    try:
        start_time = time.time()
        response = requests.get(backup_link, headers=headers, timeout=15, verify=True)
        latency = round(time.time() - start_time, 2)
        if response.status_code == 200:
            ssl_status = response.url.startswith("https")  # 判断是否使用了 HTTPS
            print(f"成功通过备用代理访问 {link}")
            return [item, latency, ssl_status]
    except requests.RequestException:
        pass

    # 如果备用代理也失败，尝试 HTTP 访问
    http_link = link.replace("https://", "http://")
    try:
        start_time = time.time()
        response = requests.get(http_link, headers=headers, timeout=15, verify=False)
        latency = round(time.time() - start_time, 2)
        if response.status_code == 200:
            ssl_status = False  # 使用了 HTTP，SSL 关闭
            print(f"成功通过HTTP访问 {link}")
            return [item, latency, ssl_status]
    except requests.RequestException:
        pass

    print(f"无法访问 {link}")
    return [item, -1, False]  # 如果所有请求都失败，返回不可达状态

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

# 添加时延和SSL状态信息到每个链接项
link_status = [{'name': result[0]['name'], 'link': result[0]['link'], 'latency': result[1], 'ssl_status': result[2]} for result in results]

# 获取当前时间
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 统计可访问和不可访问的链接数
accessible_count = len([result for result in results if result[1] != -1])
inaccessible_count = len([result for result in results if result[1] == -1])
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
