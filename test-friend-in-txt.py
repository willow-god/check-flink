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
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"

# API Key 和 请求URL的模板
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("LIJIANGAPI_TOKEN")
API_URL_TEMPLATE = "https://api.nsmao.net/api/web/query?key={}&url={}" if API_KEY else None
print("API Key 未提供" if not API_KEY else "API Key 获取成功")

# 代理链接的模板
PROXY_URL = os.getenv("PROXY_URL")
PROXY_URL_TEMPLATE = f"{PROXY_URL}{{}}" if PROXY_URL else None
print("代理 URL 获取成功" if PROXY_URL_TEMPLATE else "未提供代理 URL")

# API 请求队列
api_request_queue = Queue()

def handle_api_requests():
    while not api_request_queue.empty():
        item = api_request_queue.get()
        link = item['link']
        if not API_KEY:
            print("API Key 未提供，无法通过API访问")
            item['latency'] = -1
            continue
        api_url = API_URL_TEMPLATE.format(API_KEY, link)
        try:
            response = requests.get(api_url, headers={"User-Agent": USER_AGENT}, timeout=15, verify=True)
            response_data = response.json()
            item['latency'] = round(response_data['exec_time'], 2) if response_data.get('code') == 200 else -1
            print(f"成功通过API访问 {link}，延迟为 {item['latency']} 秒")
        except requests.RequestException:
            item['latency'] = -1
            print(f"无法通过任何方式访问 {link}")
        time.sleep(0.2)

def check_link_accessibility(item):
    link = item['link']
    try:
        start_time = time.time()
        response = requests.get(link, headers={"User-Agent": USER_AGENT}, timeout=15, verify=True)
        if response.status_code == 200:
            print(f"成功直接访问 {link}，延迟为 {round(time.time() - start_time, 2)} 秒")
            return item, round(time.time() - start_time, 2)
    except requests.RequestException:
        pass
    
    if PROXY_URL_TEMPLATE:
        try:
            start_time = time.time()
            response = requests.get(PROXY_URL_TEMPLATE.format(link), headers={"User-Agent": USER_AGENT}, timeout=15, verify=True)
            if response.status_code == 200:
                print(f"成功通过代理访问 {link}，延迟为 {round(time.time() - start_time, 2)} 秒")
                return item, round(time.time() - start_time, 2)
        except requests.RequestException:
            pass
    
    item['latency'] = -1
    api_request_queue.put(item)
    return item, -1

def load_links_from_csv(file_path):
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        return [{'name': row[0], 'link': row[1]} for row in csv.reader(csvfile) if len(row) == 2]

def save_results_to_json(file_path, results):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    accessible_count = sum(1 for _, latency in results if latency != -1)
    total_count = len(results)
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump({
            'timestamp': current_time,
            'accessible_count': accessible_count,
            'inaccessible_count': total_count - accessible_count,
            'total_count': total_count,
            'link_status': [{'name': item['name'], 'link': item['link'], 'latency': item.get('latency', latency)} for item, latency in results]
        }, file, ensure_ascii=False, indent=4)

def main():
    link_list = load_links_from_csv('./link.csv')
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(check_link_accessibility, link_list))
    handle_api_requests()
    save_results_to_json('./result.json', results)
    print("检查完成，结果已保存至 'result.json' 文件。")

if __name__ == "__main__":
    main()
