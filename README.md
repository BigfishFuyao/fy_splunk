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
from splunk import search, configure

# 配置 Splunk 连接参数
# 你可以通过函数参数配置，或者设置以下环境变量：
# SPLUNK_HOST, SPLUNK_PORT (可选, 默认 8089), SPLUNK_TOKEN
configure(
    host="your_splunk_host",
    token="your_splunk_token", 
    use_env=False
)

# 或者，如果环境变量已设置，可以省略 configure 调用，会自动加载

# 定义你的搜索查询
splunk_query = "search index=_internal | head 5"

try:
    # 执行搜索
    # search() 函数返回一个结果生成器
    results_generator = search(
        search_query=splunk_query,
        earliest_time="-1h",  # 搜索过去1小时的数据
        latest_time="now",
        exec_mode="oneshot"  # 使用 oneshot 模式进行快速查询
    )

    print(f"搜索查询: {splunk_query}")
    print("搜索结果:")
    for result in results_generator:
        print(result)

except Exception as e:
    print(f"执行 Splunk 搜索时出错: {e}")


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