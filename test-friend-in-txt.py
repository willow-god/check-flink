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
    try:
        # 发送HEAD请求
        response = requests.head(link, headers=headers, timeout=5)
        if response.status_code == 200:
            return [item, 1]  # 如果链接可访问，返回链接
    except requests.RequestException:
        pass  # 如果出现请求异常，不执行任何操作
    
    try:
        # 如果HEAD请求失败，尝试发送GET请求
        response = requests.get(link, headers=headers, timeout=5)
        if response.status_code == 200:
            return [item, 1]  # 如果GET请求成功，返回链接
    except requests.RequestException:
        pass  # 如果出现请求异常，不执行任何操作
    
    return [item, -1]  # 如果所有请求都失败，返回-1

# 从link.txt中读取链接和名称
link_list = []
with open('./link.txt', 'r', encoding='utf-8') as file:
    for line in file:
        if line.strip():
            name, link = line.strip().split(',', 1)
            link_list.append({'name': name, 'link': link})

# 使用ThreadPoolExecutor并发检查多个链接
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(check_link_accessibility, link_list))

# 分割可达和不可达的链接
accessible_results = [{'name': result[0]['name'], 'link': result[0]['link']} for result in results if result[1] == 1]
inaccessible_results = [{'name': result[0]['name'], 'link': result[0]['link']} for result in results if result[1] == -1]

# 获取当前时间
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 统计可访问和不可访问的链接数
accessible_count = len(accessible_results)
inaccessible_count = len(inaccessible_results)

# 将结果写入JSON文件
output_json_path = './result.json'
with open(output_json_path, 'w', encoding='utf-8') as file:
    json.dump({
        'timestamp': current_time,
        'accessible_links': accessible_results,
        'inaccessible_links': inaccessible_results,
        'accessible_count': accessible_count,
        'inaccessible_count': inaccessible_count
    }, file, ensure_ascii=False, indent=4)

print(f"检查完成，结果已保存至 '{output_json_path}' 文件。")
