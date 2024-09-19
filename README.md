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

### 1. 复刻仓库

首先，复刻这个仓库到你的 GitHub 账户，命名随意。

### 2. 环境配置

#### （1）添加密钥

在 GitHub 仓库的设置中，添加一个名为 `PAT_TOKEN` 的秘密，步骤如下：

1. 打开你的 GitHub 仓库，点击右上角的“Settings”。
2. 在左侧栏中找到并点击“Secrets and variables”，然后选择“Actions”。
3. 点击“New repository secret”按钮。
4. 在“Name”字段中输入 `PAT_TOKEN`。
5. 在“Secret”字段中粘贴你的 Personal Access Token（个人访问令牌）。
6. 点击“Add secret”按钮保存。

其中 `PAT_TOKEN` 请在右上角设置，开发者选项自行生成：

![](/images/PAT.png)

#### （2）配置仓库权限

在 GitHub 仓库的设置中，确保 Actions 有写权限，步骤如下：

1. 打开你的 GitHub 仓库，点击右上角的“Settings”。
2. 在左侧栏中找到并点击“Actions”。
3. 选择“General”。
4. 在“Workflow permissions”部分，选择“Read and write permissions”。
5. 点击“Save”按钮保存设置。

### 3. 选择抓取方式

#### （1）JSON（比较复杂，butterfly 及类 butterfly 以外主题不推荐）

- 修改 `test-friend.py` 文件内的 JSON 文件地址。

  ```python
  # 目标JSON数据的URL
  json_url = 'https://blog.example.com/flink_count.json'
  ```
- 具体所需JSON文件格式示例：

  ```json
  {
    "link_list": [
      {
        "name": "String",
        "link": "String",
        "avatar": "String",
        "descr": "String",
        "siteshot": "String"
      },{
        "name": "String",
        "link": "String",
        "avatar": "String",
        "descr": "String",
        "siteshot": "String"
      },
    ],
    "length": 100
  }
  ```

- JSON 具体生成教程请看[详细教程](https://blog.qyliu.top/posts/c2262998/)。

#### （2）TXT（简单，推荐，全适用）

- 修改 `link.txt` 中的内容，格式如下，请修改为你自己的数据：
  ```plaintext
  清羽飞扬,https://blog.qyliu.top/
  ChrisKim,https://www.zouht.com/
  Akilar,https://akilar.top/
  张洪Heo,https://blog.zhheo.com/
  ```

- 修改 Action 任务中，运行 Python 脚本部分，改为运行 TXT 脚本文件：

  ```yaml
   - name: Run Python script to check frined-links
     run: python test-friend-in-txt.py
  ```

**注**：两种抓取方式最终获得结果相同，所以不影响后面的操作。

### 4. 部署前端页面

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

使用zeabur或者vercel部署的目的是加快结果文件国内访问并且展示最终结果， Vercel 或 Zeabur 平台可以跟随仓库更新实时同步内容，配合上前端的缓存和异步加载，可以得到较好体验。

### 5. 进阶操作

该项目最终文件结果为 JSON 格式，通过该文件可以获取最新的链接检查结果。您可以使用任何支持 HTTP(S) 请求的编程语言或工具来获取此 JSON 数据，API 地址如下（用本站部署的作为示例）：

```txt
https://check.zeabur.app/result.json
```

#### `result.json` 格式：

```json
{
    "timestamp": "2024-09-19 09:18:49",
    "accessible_count": 64,
    "inaccessible_count": 12,
    "total_count": 76,
    "link_status": [
        {
            "name": "清羽飞扬",
            "link": "https://blog.qyliu.top/",
            "latency": -1,
            "ssl_status": false
        },
        {
            "name": "ChrisKim",
            "link": "https://www.zouht.com/",
            "latency": 0.76,
            "ssl_status": true
        },
        {
            "name": "Akilar",
            "link": "https://akilar.top/",
            "latency": 3.31,
            "ssl_status": true
        }
    ]
}
```

#### 展示到HTML：

通过 `Javascript` 获取无法访问链接数据的简单页面示例：

```javascript
    fetch('./result.json')
        .then(response => response.json())
        .then(data => {
            // 提取整体统计信息
            const summary = `总数: ${data.total_count} | 可访问: ${data.accessible_count} | 不可访问: ${data.inaccessible_count}`;
            document.getElementById('summary').textContent = summary + ` | 检测时间: ${data.timestamp}`;

            // 动态生成表格数据
            const tbody = document.getElementById('link-table-body');
            data.link_status.forEach(item => {
                const row = document.createElement('tr');

                // 名称列
                const nameCell = document.createElement('td');
                nameCell.textContent = item.name;
                row.appendChild(nameCell);

                // 链接列
                const linkCell = document.createElement('td');
                const linkElement = document.createElement('a');
                linkElement.href = item.link;
                linkElement.target = "_blank";
                linkElement.textContent = item.link;
                linkCell.appendChild(linkElement);
                row.appendChild(linkCell);

                // 时延列
                const latencyCell = document.createElement('td');
                latencyCell.textContent = item.latency >= 0 ? item.latency.toFixed(2) : '不可达';
                row.appendChild(latencyCell);

                // SSL 状态列
                const sslCell = document.createElement('td');
                sslCell.textContent = item.ssl_status ? '✔️' : '❌';
                row.appendChild(sslCell);

                tbody.appendChild(row);
            });
        })
        .catch(error => {
            console.error('Error loading JSON data:', error);
            const tbody = document.getElementById('link-table-body');
            const row = document.createElement('tr');
            const cell = document.createElement('td');
            cell.colSpan = 4;
            cell.textContent = '无法加载数据';
            cell.style.textAlign = 'center';
            row.appendChild(cell);
            tbody.appendChild(row);
        });
```

#### 展示到友链卡片

除以上展示为单独页面之外，还可以通过JavaScript对比友链结果，生成友链卡片小标签，大致效果可以看[清羽飞扬の友链页面](https://blog.qyliu.top/link/)，示例代码如下：

```html
<style>
    .status-tag {
        position: absolute;
        top: 0px;
        left: 0px;
        padding: 3px 8px;
        border-radius: 12px 0px 12px 0px;
        font-size: 12px;
        color: white;
        font-weight: bold;
        transition: font-size 0.3s ease-out, width 0.3s ease-out, opacity 0.3s ease-out;
    }
    .flink-list-item:hover .status-tag {
        font-size: 0px;
        opacity: 0;
    }
    /* 固态颜色 */
    .status-tag-green {
        background-color: #005E00; /* 绿色 */
    }
    .status-tag-light-yellow {
        background-color: #FED101; /* 浅黄色 */
    }
    .status-tag-dark-yellow {
        background-color: #F0B606; /* 深黄色 */
    }
    .status-tag-red {
        background-color: #B90000; /* 红色 */
    }
</style>
<script>
function addStatusTagsWithCache(jsonUrl) {
    const cacheKey = "statusTagsData";
    const cacheExpirationTime = 30 * 60 * 1000; // 半小时
    function applyStatusTags(data) {
        const linkStatus = data.link_status;
        document.querySelectorAll('.flink-list-item').forEach(card => {
            if (!card.href) return;
            const link = card.href.replace(/\/$/, '');
            const statusTag = document.createElement('div');
            statusTag.classList.add('status-tag');
            let matched = false;
            // 查找链接状态
            const status = linkStatus.find(item => item.link.replace(/\/$/, '') === link);
            if (status) {
                let latencyText = '未知';
                let className = 'status-tag-red'; // 默认红色
                if (status.latency === -1) {
                    latencyText = '未知';
                } else {
                    latencyText = status.latency.toFixed(2) + ' s';
                    if (status.latency <= 2) {
                        className = 'status-tag-green';
                    } else if (status.latency <= 5) {
                        className = 'status-tag-light-yellow';
                    } else if (status.latency <= 10) {
                        className = 'status-tag-dark-yellow';
                    }
                }
                statusTag.textContent = latencyText;
                statusTag.classList.add(className);
                matched = true;
            }
            if (matched) {
                card.style.position = 'relative';
                card.appendChild(statusTag);
            }
        });
    }
    function fetchDataAndUpdateUI() {
        fetch(jsonUrl)
            .then(response => response.json())
            .then(data => {
                applyStatusTags(data);
                const cacheData = {
                    data: data,
                    timestamp: Date.now()
                };
                localStorage.setItem(cacheKey, JSON.stringify(cacheData));
            })
            .catch(error => console.error('Error fetching test-flink result.json:', error));
    }
    const cachedData = localStorage.getItem(cacheKey);
    if (cachedData) {
        const { data, timestamp } = JSON.parse(cachedData);
        if (Date.now() - timestamp < cacheExpirationTime) {
            applyStatusTags(data);
            return;
        }
    }
    fetchDataAndUpdateUI();
}
setTimeout(() => {
    addStatusTagsWithCache('https://check.zeabur.app/result.json');
}, 0);
</script>
```

### 6. 联系作者

如果有疑问可通过[个人主页](https://www.qyliu.top)或者提 issue 进行联系，非常欢迎。
