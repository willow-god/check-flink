import os
import csv
import json
import time
import logging
import requests
import warnings
from queue import Queue
from datetime import datetime
from urllib.parse import urlparse
import concurrent.futures

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="😎 %(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

warnings.filterwarnings("ignore", message="Unverified HTTPS request is being made.*")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
HEADERS = {"User-Agent": USER_AGENT}
PROXY_URL_TEMPLATE = f"{os.getenv('PROXY_URL')}{{}}" if os.getenv("PROXY_URL") else None
SOURCE_URL = os.getenv("SOURCE_URL", "./link.csv")  # 默认本地文件
RESULT_FILE = "./result.json"
api_request_queue = Queue()

if PROXY_URL_TEMPLATE:
    logging.info("代理 URL 获取成功，代理协议: %s", PROXY_URL_TEMPLATE.split(":")[0])
else:
    logging.info("未提供代理 URL")

def load_previous_results():
    if os.path.exists(RESULT_FILE):
        try:
            with open(RESULT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logging.warning("JSON 解析错误，使用空数据")
    return {}

def save_results(data):
    with open(RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def is_url(path):
    return urlparse(path).scheme in ("http", "https")

def fetch_origin_data(origin_path):
    try:
        if is_url(origin_path):
            response = requests.get(origin_path, headers=HEADERS, timeout=15)
            response.raise_for_status()
            content = response.text
        else:
            with open(origin_path, "r", encoding="utf-8") as f:
                content = f.read()
    except Exception as e:
        logging.error(f"读取数据失败: {e}")
        return []

    try:
        data = json.loads(content)
        if isinstance(data, dict) and 'link_list' in data:
            logging.info("成功解析 JSON 格式数据")
            return data['link_list']
        elif isinstance(data, list):
            logging.info("成功解析 CSV 格式数据")
            return data
    except json.JSONDecodeError:
        pass

    try:
        rows = list(csv.reader(content.splitlines()))
        logging.info("成功解析 CSV 格式数据")
        return [{'name': row[0], 'link': row[1]} for row in rows if len(row) == 2]
    except Exception as e:
        logging.error(f"CSV 解析失败: {e}")
        return []

def check_link(item):
    link = item['link']
    for method, url in [("直接访问", link), ("代理访问", PROXY_URL_TEMPLATE.format(link) if PROXY_URL_TEMPLATE else None)]:
        if not url:
            logging.warning(f"[{method}] 无效链接: {link}")
            continue
        try:
            start_time = time.time()
            response = requests.get(url, headers=HEADERS, timeout=15, verify=True)
            latency = round(time.time() - start_time, 2)

            if response.status_code == 200:
                logging.info(f"[{method}] 成功访问: {link} ，延迟 {latency} 秒")
                return item, latency
            else:
                logging.warning(f"[{method}] 返回异常状态码: {link} -> {response.status_code}")
        except requests.RequestException:
            logging.warning(f"[{method}] 访问失败: {link}")

    api_request_queue.put(item)
    return item, -1

def handle_api_requests():
    results = []
    while not api_request_queue.empty():
        time.sleep(0.2)
        item = api_request_queue.get()
        link = item['link']
        api_url = f"https://v2.xxapi.cn/api/status?url={link}"
        try:
            response = requests.get(api_url, headers=HEADERS, timeout=30)
            res_json = response.json()
            if res_json.get("code") == 200 and res_json.get("data") == 200:
                logging.info(f"[API] 成功访问: {link} ，状态码 200")
                item['latency'] = -2
            else:
                if res_json.get("data") != 200:
                    result_data = res_json.get("data") if res_json.get("data") else "无数据"
                    logging.warning(f"[API] 返回异常数据: {link} -> {result_data}")
                else:
                    logging.warning(f"[API] 返回异常状态码: {link} -> {res_json.get('code')}")
                item['latency'] = -1
        except requests.RequestException as e:
            logging.error(f"[API] 请求失败: {link} ，错误: {e}")
            item['latency'] = -1
        results.append(item)
    return results

def main():
    try:
        link_list = fetch_origin_data(SOURCE_URL)
        if not link_list:
            logging.error("数据源为空或解析失败")
            return

        previous_results = load_previous_results()

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(check_link, link_list))

        updated_api_results = handle_api_requests()
        for updated_item in updated_api_results:
            for idx, (item, latency) in enumerate(results):
                if item['link'] == updated_item['link']:
                    results[idx] = (item, updated_item['latency'])
                    break

        current_links = {item['link'] for item in link_list}
        link_status = []

        for item, latency in results:
            try:
                name = item.get('name', '未知')
                link = item.get('link')
                if not link:
                    logging.warning(f"跳过无效项: {item}")
                    continue

                prev_entry = next((x for x in previous_results.get("link_status", []) if x.get("link") == link), {})
                prev_fail_count = prev_entry.get("fail_count", 0)

                fail_count = prev_fail_count + 1 if latency == -1 else 0

                link_status.append({
                    'name': name,
                    'link': link,
                    'latency': latency,
                    'fail_count': fail_count
                })
            except Exception as e:
                logging.error(f"处理链接时发生错误: {item}, 错误: {e}")

        # 保留在当前数据源中的链接
        link_status = [entry for entry in link_status if entry["link"] in current_links]

        accessible = sum(1 for x in link_status if x["latency"] != -1)
        total = len(link_status)
        output = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "accessible_count": accessible,
            "inaccessible_count": total - accessible,
            "total_count": total,
            "link_status": link_status
        }

        save_results(output)
        logging.info(f"共检查 {total} 个链接，成功 {accessible} 个，失败 {total - accessible} 个")
        logging.info(f"结果已保存至: {RESULT_FILE}")
    except Exception as e:
        logging.exception(f"运行主程序失败: {e}")

if __name__ == "__main__":
    main()
