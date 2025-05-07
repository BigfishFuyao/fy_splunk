#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Splunk搜索工具，提供连接Splunk并执行查询的功能
"""
import logging

logger = logging.getLogger(__name__)

import os
import time
from typing import Optional, Literal, Union, Dict, Any, Generator
from splunklib import client, results

# 全局配置和连接
_splunk_config = {}
_splunk_service = None


def configure(host=None, port=None, token=None, use_env=True):
    """
    配置Splunk连接参数

    Args:
        host: Splunk主机地址
        port: Splunk端口
        token: Splunk认证令牌
        use_env: 是否使用环境变量作为后备配置
    """
    global _splunk_config, _splunk_service

    # 重置连接
    _splunk_service = None

    # 使用环境变量作为后备配置
    if use_env:
        env_config = {
            'host': os.environ.get('SPLUNK_HOST'),
            'port': os.environ.get('SPLUNK_PORT'),
            'bearer_token': os.environ.get('SPLUNK_TOKEN')
        }
        # 只保留有值的配置项
        env_config = {k: v for k, v in env_config.items() if v is not None}
        _splunk_config.update(env_config)

    # 使用显式传入的参数更新配置（优先级更高）
    explicit_config = {}
    if host is not None:
        explicit_config['host'] = host
    if port is not None:
        explicit_config['port'] = port
    if token is not None:
        explicit_config['bearer_token'] = token

    _splunk_config.update(explicit_config)

    if explicit_config:
        logger.info(f"Splunk配置已更新: {', '.join(explicit_config.keys())}")


def get_splunk_service() -> client.Service:
    """获取Splunk服务连接实例，如果不存在则创建新连接"""
    global _splunk_service, _splunk_config

    # 如果配置为空，则尝试自动初始化
    if not _splunk_config:
        logger.info("Splunk配置为空，尝试使用环境变量进行自动配置...")
        configure(use_env=True)

        # 如果配置仍然为空，可能环境变量也没有设置
        if not _splunk_config:
            logger.warning("无法从环境变量获取Splunk配置")

    if _splunk_service is None:
        try:
            # 检查必要的配置是否存在
            required_keys = ['host', 'bearer_token']
            missing_keys = [key for key in required_keys if key not in _splunk_config or not _splunk_config[key]]

            if missing_keys:
                raise ValueError(
                    f"缺少必要的Splunk配置: {', '.join(missing_keys)}。请通过configure()方法或环境变量设置。")

            # 默认端口
            port = _splunk_config.get('port', 8089)

            _splunk_service = client.connect(
                host=_splunk_config['host'],
                port=port,
                splunkToken=_splunk_config['bearer_token']
            )
            logger.info(f"已连接到Splunk服务: {_splunk_config['host']}:{port}")
        except Exception as e:
            logger.error(f"连接Splunk失败: {e}")
            raise

    return _splunk_service


def search(
        search_query: str,
        earliest_time: Optional[Union[str, int]] = "-1d",
        latest_time: Optional[Union[str, int]] = "now",
        exec_mode: Literal["blocking", "oneshot", "normal", "job_sid"] = "normal",
        adhoc_search_level: Literal["smart", "fast", "verbose"] = "smart",
        output_mode: str = "json",
        sleep_time: int = 2,
        sid: Optional[str] = None,
        offset: int = 0,
        count_per_batch: int = 30000,
        **kwargs
) -> Generator[Dict[str, Any], None, None]:
    """
    执行Splunk搜索查询并返回结果

    Args:
        search_query: Splunk搜索查询语句
        earliest_time: 搜索的最早时间，默认为昨天
        latest_time: 搜索的最晚时间，默认为今天
        exec_mode: 执行模式
        adhoc_search_level: 搜索级别
        output_mode: 输出格式
        sleep_time: 查询状态检查间隔(秒)
        sid: 当exec_mode为job_sid时的作业ID
        offset: 结果起始位置
        count_per_batch: 每批获取的结果数量
        **kwargs: 其他Splunk搜索参数

    Yields:
        Dict[str, Any]: 搜索结果字典

    Raises:
        ValueError: 参数无效时抛出
        Exception: 搜索过程中出现错误时抛出
    """
    if not search_query:
        raise ValueError("search_query不能为空")

    # 获取Splunk服务连接
    splunk_service = get_splunk_service()

    # 准备搜索参数
    search_kwargs = {
        "exec_mode": exec_mode,
        "adhoc_search_level": adhoc_search_level,
        "earliest_time": earliest_time,
        "latest_time": latest_time,
        "output_mode": output_mode
    }
    search_kwargs.update(kwargs)

    try:
        # 根据执行模式处理搜索
        if exec_mode == "blocking":
            logger.info(f"执行阻塞式搜索: {search_query}")
            job = splunk_service.jobs.create(search_query, **search_kwargs)
            reader = results.JSONResultsReader(job.results(output_mode='json'))
            yield from _process_results(reader)
            return

        elif exec_mode == "oneshot":
            logger.info(f"执行一次性搜索: {search_query}")
            del search_kwargs["exec_mode"]
            oneshot_results = splunk_service.jobs.oneshot(search_query, **search_kwargs)
            reader = results.JSONResultsReader(oneshot_results)
            yield from _process_results(reader)
            return

        elif exec_mode == "normal":
            logger.info(f"执行标准搜索: {search_query}")
            job = splunk_service.jobs.create(search_query, **search_kwargs)

        elif exec_mode == "job_sid":
            if not sid:
                raise ValueError("exec_mode为job_sid时必须提供sid参数")
            logger.info(f"获取作业结果，SID: {sid}")
            job = splunk_service.jobs[sid]

        else:
            raise ValueError(f"无效的exec_mode: {exec_mode}")

        # 监控搜索进度
        _monitor_search_progress(job, sleep_time)

        # 分批获取结果
        result_count = int(job["resultCount"])
        logger.info(f"搜索完成，共有 {result_count} 条结果")

        current_offset = offset
        while current_offset < result_count:
            logger.debug(f"获取结果批次: offset={current_offset}, count={count_per_batch}")
            reader = results.JSONResultsReader(
                job.results(output_mode='json', count=count_per_batch, offset=current_offset)
            )

            batch_results = list(_process_results(reader))
            for result in batch_results:
                yield result

            if not batch_results:
                break

            current_offset += count_per_batch

    except Exception as e:
        logger.error(f"Splunk搜索过程中出错: {e}", exc_info=True)
        raise


def _process_results(reader):
    """处理JSONResultsReader的结果，只返回字典类型的结果"""
    for result in reader:
        if isinstance(result, dict):
            yield result
        elif isinstance(result, results.Message):
            logger.debug(f"{result.type}: {result.message}")


def _monitor_search_progress(job: client.Job, sleep_time: int) -> None:
    """监控Splunk搜索任务的进度"""
    while True:
        # 等待任务就绪
        while not job.is_ready():
            time.sleep(sleep_time)

        # 获取任务状态
        stats = {
            "isDone": job["isDone"],
            "doneProgress": float(job["doneProgress"]) * 100,
            "scanCount": int(job["scanCount"]),
            "eventCount": int(job["eventCount"]),
            "resultCount": int(job["resultCount"])
        }

        status = (f"进度: {stats['doneProgress']:.1f}%  已扫描: {stats['scanCount']}  "
                  f"匹配: {stats['eventCount']}  结果: {stats['resultCount']}")
        logger.info(status)

        if stats["isDone"] == "1":
            logger.info("Splunk搜索完成！")
            break

        time.sleep(sleep_time)
