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
def check_link_accessibility(link):
    headers = {"User-Agent": user_agent}
    try:
        # 发送HEAD请求
        response = requests.head(link, headers=headers, timeout=5)
        if response.status_code == 200:
            return [link, 1]  # 如果链接可访问，返回链接
    except requests.RequestException:
        pass  # 如果出现请求异常，不执行任何操作
    
    try:
        # 如果HEAD请求失败，尝试发送GET请求
        response = requests.get(link, headers=headers, timeout=5)
        if response.status_code == 200:
            return [link, 1]  # 如果GET请求成功，返回链接
    except requests.RequestException:
        pass  # 如果出现请求异常，不执行任何操作
    
    return [link, -1]  # 如果所有请求都失败，返回-1

# 目标JSON数据的URL
json_url = 'https://blog.qyliu.top/flink_count.json'

# 发送HTTP GET请求获取JSON数据
response = requests.get(json_url)
if response.status_code == 200:
    data = response.json()  # 解析JSON数据
    links = [item['link'] for item in data['link_list']]  # 提取所有的链接
else:
    print(f"Failed to retrieve data, status code: {response.status_code}")
    exit()

# 使用ThreadPoolExecutor并发检查多个链接
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(check_link_accessibility, links))

# 分割可达和不可达的链接
accessible_results = [result for result in results if result[1] == 1]
inaccessible_results = [result for result in results if result[1] == -1]
# 从结果列表中提取链接
accessible_links = [result[0] for result in accessible_results]
inaccessible_links = [result[0] for result in inaccessible_results]

# 获取当前时间
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 将结果写入JSON文件
output_json_path = './result.json'
with open(output_json_path, 'w', encoding='utf-8') as file:
    json.dump({
        'timestamp': current_time,
        'accessible_links': accessible_links,
        'inaccessible_links': inaccessible_links
    }, file, ensure_ascii=False, indent=4)

print(f"检查完成，结果已保存至 '{output_json_path}' 文件。")
