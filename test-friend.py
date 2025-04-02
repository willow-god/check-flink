import json
import requests
import warnings
import time
import os
import concurrent.futures
from datetime import datetime
from queue import Queue

warnings.filterwarnings("ignore", message="Unverified HTTPS request is being made.*")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
HEADERS = {"User-Agent": USER_AGENT}

if os.getenv("LIJIANGAPI_TOKEN") is None:
    print("本地运行，从环境变量中加载并获取环境变量")
    from dotenv import load_dotenv
    load_dotenv()

env_loaded = os.getenv("LIJIANGAPI_TOKEN")
print("本地运行，从环境变量中加载 API Key" if not env_loaded else "在服务器上运行，从环境变量中获取 API Key")

API_KEY = os.getenv("LIJIANGAPI_TOKEN")
API_URL_TEMPLATE = f"https://api.nsmao.net/api/web/query?key={API_KEY}&url={{}}" if API_KEY else None
PROXY_URL_TEMPLATE = f"{os.getenv('PROXY_URL')}{{}}" if os.getenv("PROXY_URL") else None
print("代理 URL 获取成功" if PROXY_URL_TEMPLATE else "未提供代理 URL")

api_request_queue = Queue()
RESULT_FILE = './result.json'


def load_previous_results():
    """加载上次检查结果"""
    if os.path.exists(RESULT_FILE):
        with open(RESULT_FILE, 'r', encoding='utf-8') as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                print("JSON 解析错误，使用空数据")
                return {}
    return {}


def save_results(data):
    """保存检测结果"""
    with open(RESULT_FILE, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def fetch_json_data(url):
    """获取 JSON 数据"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"无法获取 JSON 数据: {e}")
        return None

def is_likely_garbled(text):
    return any(ord(char) > 127 for char in text) if text else False

def check_link(item):
    """检查友链可访问性"""
    link = item['link']

    for method, url in [("直接访问", link), ("代理访问", PROXY_URL_TEMPLATE.format(link) if PROXY_URL_TEMPLATE else None)]:
        if not url:
            continue
        try:
            start_time = time.time()
            response = requests.get(url, headers=HEADERS, timeout=15, verify=True)
            latency = round(time.time() - start_time, 2)

            if response.status_code == 200:
                print(f"成功通过 {method} 访问 {link}, 延迟 {latency} 秒")
                return item, latency
        except requests.RequestException:
            print(f"{method} 失败: {link}")

    api_request_queue.put(item)
    return item, -1


def handle_api_requests():
    """处理 API 请求"""
    updated_results = []
    while not api_request_queue.empty():
        time.sleep(0.2)
        item = api_request_queue.get()
        link = item['link']

        if not API_URL_TEMPLATE:
            print("API Key 未提供，无法通过 API 访问")
            continue

        try:
            response = requests.get(API_URL_TEMPLATE.format(link), headers=HEADERS, timeout=30)
            response_data = response.json()

            if (response_data.get('code') == 200 and
                response_data.get('data') and (
                    (response_data.get('data').get('title') not in ["", None] and not is_likely_garbled(response_data['data']['title'])) or
                    (response_data.get('data').get('keywords') not in ["", None] and not is_likely_garbled(response_data['data']['title'])) or
                    (response_data.get('data').get('description') not in ["", None] and not is_likely_garbled(response_data['data']['title']))
                )):
                latency = round(response_data.get('exec_time', -1), 2)
                print(f"成功通过 API 访问 {link}, 延迟 {latency} 秒")
                print(f"API 返回数据: {response_data.get('data')}")
                print(f"API 返回标题: {response_data.get('data').get('title')}")
                print(f"API 返回关键词: {response_data.get('data').get('keywords')}")
                print(f"API 返回描述: {response_data.get('data').get('description')}")
                item['latency'] = latency
            else:
                print(f"API 访问失败: {link}，错误代码 {response_data.get('code')}")
                item['latency'] = -1
        except requests.RequestException:
            print(f"API 请求失败: {link}")
            item['latency'] = -1

        updated_results.append(item)  # 记录更新后的结果
        time.sleep(0.2)

    return updated_results


def main():
    json_url = 'https://blog.liushen.fun/flink_count.json'
    data = fetch_json_data(json_url)
    if not data:
        return

    link_list = data.get('link_list', [])
    previous_results = load_previous_results()

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(check_link, link_list))

    # 处理 API 请求，并获取更新后的结果
    updated_api_results = handle_api_requests()

    # 用 API 结果覆盖原来的结果
    for updated_item in updated_api_results:
        for idx, (item, latency) in enumerate(results):
            if item['link'] == updated_item['link']:
                results[idx] = (item, updated_item['latency'])  # 更新 latency
                break

    # 获取当前的友链列表（去重）
    current_links = {item['link'] for item in link_list}

    link_status = []
    for item, latency in results:
        name, link = item['name'], item['link']
        prev_entry = next((x for x in previous_results.get('link_status', []) if x['link'] == link), None)

        if latency == -1:
            failed_days = (prev_entry['failed_days'] + 1) if prev_entry and 'failed_days' in prev_entry else 1
        else:
            failed_days = 0

        link_status.append({'name': name, 'link': link, 'latency': latency, 'failed_days': failed_days})

    # **删除已被移除的友链**
    link_status = [entry for entry in link_status if entry['link'] in current_links]

    accessible_count = sum(1 for s in link_status if s['latency'] != -1)
    total_count = len(link_status)
    inaccessible_count = total_count - accessible_count

    output_data = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'accessible_count': accessible_count,
        'inaccessible_count': inaccessible_count,
        'total_count': total_count,
        'link_status': link_status
    }

    save_results(output_data)
    print(f"共检查 {total_count} 个链接，其中 {accessible_count} 个可访问，{inaccessible_count} 个不可访问。")
    print(f"检查完成，结果已保存至 '{RESULT_FILE}'。")


if __name__ == "__main__":
    main()
