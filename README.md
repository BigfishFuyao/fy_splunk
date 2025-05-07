# fy-splunk

`fy-splunk` 是一个 Python 包，用于与 Splunk 服务进行交互，主要功能是执行 Splunk 搜索查询并获取结果。

## 安装说明

### 通过 pip 从 Git 安装

你可以使用 pip 直接从 GitHub 仓库安装此包：

```bash
pip install git+https://github.com/BigfishFuyao/fy_splunk.git
```

或者，如果你有 SSH 密钥访问权限：

```bash
pip install git+ssh://git@github.com/BigfishFuyao/fy_splunk.git
```

### 依赖项

该包依赖于以下库：

*   `splunk-sdk`

`pip` 会自动处理这些依赖项的安装。

## 快速开始

以下是如何使用 `fy-splunk` 包连接到 Splunk 并执行搜索的基本示例：

```python
from splunk import search

# 配置 Splunk 连接参数
# 你可以通过函数参数配置，或者设置以下环境变量：
# SPLUNK_HOST, SPLUNK_PORT (可选, 默认 8089), SPLUNK_TOKEN
search.configure(host="your_splunk_host", token="your_splunk_token")

# 或者，如果环境变量已设置，可以省略 configure 调用，会自动加载

# 定义你的搜索查询
splunk_query = "search index=_internal | head 5"

try:
    # 执行搜索
    # search() 函数返回一个结果生成器
    results_generator = search.search(
        search_query=splunk_query,
        earliest_time="-1h",  # 搜索过去1小时的数据
        latest_time="now",
        exec_mode="oneshot"   # 使用 oneshot 模式进行快速查询
    )

    print(f"搜索查询: {splunk_query}")
    print("搜索结果:")
    for result in results_generator:
        print(result)

except Exception as e:
    print(f"执行 Splunk 搜索时出错: {e}")

```
## 使用示例

以下是一些更详细的示例，展示了如何使用 `fy-splunk` 库的不同功能。

### 1. 配置 Splunk 连接

你可以通过两种主要方式配置 Splunk 连接：

**a) 通过函数参数配置：**

```python
from splunk import search
import os

# 显式传递连接参数
search.configure(host="your_splunk_host", port=8089, token="your_splunk_token")

# 后续的 search.search() 调用将使用此配置
# 例如:
# results = search.search(search_query="search index=_internal | head 1")
# for r in results:
#     print(r)
```

**b) 通过环境变量配置：**

确保设置了以下环境变量：
*   `SPLUNK_HOST`: Splunk 服务的主机名或 IP 地址。
*   `SPLUNK_TOKEN`: 用于认证的 Splunk Bearer Token。
*   `SPLUNK_PORT` (可选): Splunk 管理端口，默认为 `8089`。

```python
from splunk import search
import os

# 假设环境变量已设置 (例如 SPLUNK_HOST, SPLUNK_TOKEN)
# search.configure() 会自动尝试加载它们 (use_env=True 是默认行为)
# 或者，如果你想确保只使用环境变量，可以这样调用：
search.configure(use_env=True) # 如果之前有其他配置，这会重置并尝试加载环境变量

# 如果环境变量已设置，你甚至可以不显式调用 search.configure()
# search.search() 在需要时会自动尝试配置

# 例如:
# results = search.search(search_query="search index=_internal | head 1")
# for r in results:
#     print(r)
```

### 2. 执行搜索查询

**a) 执行阻塞式搜索 (`blocking`)**

此模式会等待搜索完成并将所有结果一次性加载（适用于结果集较小的情况）。

```python
from splunk import search

# 确保已配置连接 (见上一节)
# search.configure(host="your_splunk_host", token="your_splunk_token")

splunk_query = "search index=_internal sourcetype=splunkd | head 3"

try:
    print(f"执行阻塞式搜索: {splunk_query}")
    results_generator = search.search(
        search_query=splunk_query,
        exec_mode="blocking",
        earliest_time="-5m",
        latest_time="now"
    )

    for result in results_generator:
        print(result)

except Exception as e:
    print(f"执行阻塞式搜索时出错: {e}")
```

**b) 执行一次性搜索 (`oneshot`)**

此模式适用于快速、轻量级的搜索，结果会立即返回，不会创建持久的搜索作业。

```python
from splunk import search

# 确保已配置连接
# search.configure(host="your_splunk_host", token="your_splunk_token")

splunk_query = "search index=_audit | head 2"

try:
    print(f"执行一次性搜索: {splunk_query}")
    results_generator = search.search(
        search_query=splunk_query,
        exec_mode="oneshot",
        earliest_time="-10m",
        latest_time="now"
    )

    for result in results_generator:
        print(result)

except Exception as e:
    print(f"执行一次性搜索时出错: {e}")
```

**c) 执行标准搜索 (`normal`) 并迭代处理结果**

此模式会创建一个搜索作业，你可以监控其进度，并分批获取结果。这是处理大量数据的推荐方式。

```python
from splunk import search
import time

# 确保已配置连接
# search.configure(host="your_splunk_host", token="your_splunk_token")

splunk_query = "search index=main earliest=-1d latest=now | stats count by sourcetype"

try:
    print(f"执行标准搜索: {splunk_query}")
    # 注意：对于 normal 模式，search() 函数本身不直接返回 job 对象
    # 结果是通过迭代器获取的，内部会处理作业创建和结果拉取
    results_generator = search.search(
        search_query=splunk_query,
        exec_mode="normal", # 'normal' 是默认的 exec_mode
        earliest_time="-1d",
        latest_time="now",
        sleep_time=1 # 检查作业状态的间隔（秒）
    )

    print("开始迭代处理结果...")
    count = 0
    for result in results_generator:
        print(f"结果 {count + 1}: {result}")
        count += 1
        # 你可以在这里添加更复杂的处理逻辑
    print(f"共处理 {count} 条结果。")

except Exception as e:
    print(f"执行标准搜索时出错: {e}")
```

### 3. 使用作业 SID 获取结果 (`job_sid`)

如果你有一个已存在的 Splunk 搜索作业的 SID，你可以使用它来获取结果。

```python
from splunk import search

# 确保已配置连接
# search.configure(host="your_splunk_host", token="your_splunk_token")

# 假设你有一个已知的作业 SID
# (通常这个 SID 是通过其他方式创建或获取的，例如，一个长时间运行的搜索)
known_sid = "scheduler__admin__search__RMD50aa41752c98a95f9_at_1678886400_360" # 示例 SID，请替换为真实的

# 注意：你需要确保这个 SID 对应的作业在 Splunk 中仍然存在且结果可用。
# 通常，作业结果有其生命周期。

try:
    print(f"使用 SID 获取作业结果: {known_sid}")
    results_generator = search.search(
        search_query="", # search_query 在此模式下通常不被使用，但不能为空
        exec_mode="job_sid",
        sid=known_sid
    )

    for result in results_generator:
        print(result)

except Exception as e:
    print(f"使用 SID 获取作业结果时出错: {e}")
```

## 主要功能

*   **灵活的 Splunk 连接配置**：支持通过函数参数或环境变量 (`SPLUNK_HOST`, `SPLUNK_PORT`, `SPLUNK_TOKEN`) 配置连接。
*   **多种搜索执行模式**：
    *   `oneshot`: 用于快速、即时的搜索，结果直接返回。
    *   `blocking`: 阻塞执行直到搜索完成。
    *   `normal`: 创建一个搜索作业，可以监控进度并分批获取结果。
    *   `job_sid`: 获取已存在的搜索作业的结果。
*   **时间范围控制**：可以指定搜索的 `earliest_time` 和 `latest_time`。
*   **结果处理**：以生成器方式返回搜索结果，高效处理大量数据。
*   **搜索进度监控**：对于 `normal` 模式的搜索，可以监控其执行进度。

## 目录结构

```
.
├── .gitignore          # Git 忽略文件配置
├── LICENSE             # 项目许可证 (Apache License 2.0)
├── README.md           # 本文档
├── setup.py            # 包安装和元数据配置文件
├── fy_splunk.egg-info/ # Python egg 构建信息 (自动生成)
└── splunk/             # 主要的 Python 包目录
    ├── __init__.py     # 包初始化文件
    └── search.py       # 包含 Splunk 搜索核心逻辑的模块
```

## 贡献指南

目前，我们欢迎通过 GitHub Issues 报告问题或提出功能请求。如果你希望贡献代码，请先创建一个 Issue 来讨论你的想法。

## 许可证

该项目根据 [Apache License 2.0](/Users/dayujingji/BigfishFuyao/fy_splunk/LICENSE) 授权。详情请参阅 [`LICENSE`](/Users/dayujingji/BigfishFuyao/fy_splunk/LICENSE) 文件。