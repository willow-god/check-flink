![](/images/cover.png)

---

# 友情链接自动检查项目

[示例页面](https://check.zeabur.app) | [详细教程](https://blog.qyliu.top/posts/c2262998/)

这个项目旨在自动检查从互联网上托管的 JSON 文件中的链接的可访问性。它利用 GitHub Actions 来定期调度检查，并将结果输出为 JSON 文件，可以部署到如 Vercel 等平台以便于访问。该项目基于并改进了 [butterfly-check-links](https://github.com/shangskr/butterfly-check-links.git) 项目。

## 功能

- 使用 GitHub Actions 进行自动链接检查
- 支持使用 `HEAD` 和 `GET` 请求进行链接验证
- 并发处理以提高链接检查效率
- 结果输出为 JSON 格式，便于与 Web 应用集成
- 使用 cron 作业进行定时执行

## 项目结构

```plaintext
.
├── .github
│   └── workflows
│       └── check_links.yml
├── test-friend.py
├── test-friend-in-txt.py
├── result.json
├── link.txt
└── README.md
```

## 文件说明

- `.github/workflows/check_links.yml`: GitHub Actions 的工作流配置文件，用于定时执行链接检查脚本。
- `test-friend.py`: 主链接检查脚本，负责检查 JSON 数据中的链接可访问性并生成结果。
- `test-friend-in-txt.py`: 从 `link.txt` 文件中读取链接并进行可访问性检查，生成结果。
- `result.json`: 链接检查结果的输出文件。
- `link.txt`: 存放待检查链接的文本文件。
- `README.md`: 项目说明文件。

## 使用说明

### 配置 GitHub Actions

在项目的 GitHub 仓库中，创建一个 GitHub Actions 工作流配置文件（`.github/workflows/check_links.yml`），内容如下：

```yaml
name: Check Links and Generate JSON

on:
  push:
    branches:
      - main
  schedule:
    - cron: '0 1 * * *'  # 每天凌晨一点执行一次
  workflow_dispatch:

jobs:
  check_links:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout Repository
      uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.x'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install requests

    - name: Run Python script to check links from JSON and generate JSON
      run: python test-friend.py

    - name: Run Python script to check links from TXT and generate JSON
      run: python test-friend-in-txt.py

    - name: Ensure file is updated
      run: touch result.json

    - name: Configure Git
      run: |
        git config --global user.email "actions@github.com"
        git config --global user.name "GitHub Actions"

    - name: Commit and push generated JSON file
      env:
        PAT_TOKEN: ${{ secrets.PAT_TOKEN }}
      run: |
        git add .
        git commit -m "每日更新"
        git push https://x-access-token:${{ secrets.PAT_TOKEN }}@github.com/${{ github.repository }}.git main
```

以上action为从Json文件中获取，除此之外还有通用方式，从txt获取，具体请看顶部详细教程介绍。

### 添加 GitHub Secrets

在 GitHub 仓库的设置中，添加一个名为 `PAT_TOKEN` 的秘密，步骤如下：

1. 打开你的 GitHub 仓库，点击右上角的“Settings”。
2. 在左侧栏中找到并点击“Secrets and variables”，然后选择“Actions”。
3. 点击“New repository secret”按钮。
4. 在“Name”字段中输入 `PAT_TOKEN`。
5. 在“Secret”字段中粘贴你的 Personal Access Token（个人访问令牌）。
6. 点击“Add secret”按钮保存。

其中 `PAT_TOKEN` 请在右上角设置，开发者选项自行生成：

![](/images/PAT.png)

### 配置仓库权限

在 GitHub 仓库的设置中，确保 Actions 有写权限，步骤如下：

1. 打开你的 GitHub 仓库，点击右上角的“Settings”。
2. 在左侧栏中找到并点击“Actions”。
3. 选择“General”。
4. 在“Workflow permissions”部分，选择“Read and write permissions”。
5. 点击“Save”按钮保存设置。

### 部署到 Vercel 或 Zeabur

在 Vercel 或 Zeabur 选择对应仓库，按照以下步骤进行操作：

1. **登录 Vercel 或 Zeabur**：
   - 如果还没有账户，请先注册一个 Vercel 或 Zeabur 账户。
   - 登录后进入仪表板。

2. **导入 GitHub 仓库**：
   - 点击“New Project”或“Import Project”按钮。
   - 选择“Import Git Repository”。
   - 连接到您的 GitHub 账户，并选择该链接检查项目的仓库。

3. **配置项目**：
   - 确保选择正确的分支（如 `main`）。
   - 对于 Vercel，在“Build and Output Settings”中，确保 `output.json` 文件在构建输出目录中。

4. **部署项目**：
   - 点击“Deploy”按钮开始部署。
   - 部署完成后，Vercel 或 Zeabur 会生成一个 URL，您可以使用这个 URL 访问部署的网页。

使用zeabur或者vercel部署的目的是加快国内访问，并且可以跟随仓库更新实时同步内容，配合上前台的缓存和异步加载，可以得到最佳体验。

### 通过 API 获取数据

该项目还生成了一个 JSON 文件，通过该文件可以获取最新的链接检查结果。您可以使用任何支持 HTTP 请求的编程语言或工具来获取此 JSON 数据。

API 地址如下（用本站部署的作为示例）：

```txt
https://check.zeabur.app/result.json
```

以下是通过 `Javascript` 获取无法访问链接数据的简单页面示例，具体请自行编写：

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>友链检测</title>
</head>
<body>
    <h1>不可访问的链接</h1>
    <div id="inaccessibleLinksContainer"></div>

    <script>
        async function fetchInaccessibleLinks() {
            const jsonUrl = 'https://your-deployed-url.com/result.json';
            try {
                const response = await fetch(jsonUrl);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                displayInaccessibleLinks(data.inaccessible_links);
            } catch (error) {
                console.error("Fetch error: ", error);
            }
        }

        function displayInaccessibleLinks(links) {
            const container = document.getElementById('inaccessibleLinksContainer');
            container.innerHTML = ''; // 清空容器
            links.forEach(link => {
                const linkElement = document.createElement('p');
                linkElement.innerHTML = `<strong>${link.name}:</strong> <a href="${link.link}" target="_blank">${link.link}</a>`;
                container.appendChild(linkElement);
            });
        }

        fetchInaccessibleLinks();
    </script>
</body>
</html>
```

### JSON 结构介绍

链接检查结果以 JSON 格式存储，主要包含以下字段：

- `accessible_links`: 可访问的链接列表。
- `inaccessible_links`: 不可访问的链接列表。
- `timestamp`: 生成检查结果的时间戳。

以下是一个示例 JSON 文件结构：

```json
{
    "accessible_links": [
        {
            "name": "清羽飞扬",
            "link": "https://blog.qyliu.top/"
        },
        {
            "name": "ChrisKim",
            "link": "https://www.zouht.com/"
        }
    ],
    "inaccessible_links": [
        {
            "name": "JackieZhu",
            "link": "https://blog.zhfan.top/"
        },
        {
            "name": "青桔气球",
            "link": "https://blog.qjqq.cn/"
        }
    ],
    "accessible_count": 2,
    "inaccessible_count": 2,
    "timestamp": "2024-06-20T23:40:15"
}
```

**不管是txt获取数据或者从json获取数据，最终得到的结果均一致，不会影响到最终结果的结构！**

### `test-friend.py`

该脚本主要执行以下步骤：

1. 忽略 HTTPS 请求的警告信息。
2. 发送 HTTP 请求获取目标 JSON 数据，并解析其中的链接列表。
3. 使用 `ThreadPoolExecutor` 并发检查多个链接的可访问性。
4. 将可达和不可达的链接分开，并将结果写入 `result.json` 文件。

```python
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

# 目标JSON数据的URL
json_url = 'https://blog.qyliu.top/flink_count.json'

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
```

### `test-friend-in-txt.py`

该脚本主要执行以下步骤：

1. 忽略 HTTPS 请求的警告信息。
2. 从 `link.txt` 文件中读取链接列表。
3. 使用 `ThreadPoolExecutor` 并发检查多个链接的可访问性。
4. 将可达和不可达的链接分开，并将结果写入 `result.json` 文件。

```python
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
```

这个项目提供了一种自动化的方式来定期检查链接的可访问性，并将结果以 JSON 格式输出，便于集成到前端页面。通过使用 GitHub Actions，整个流程实现了自动化和可视化，极大地方便了用户对链接的管理和监控。
