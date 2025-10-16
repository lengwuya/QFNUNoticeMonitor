#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OneBot v11 协议消息发送组件
支持向指定群组发送消息
"""

import requests
import json
import os
import logging
from typing import List, Dict, Any, Union
from dotenv import load_dotenv

load_dotenv()


class OneBotSender:
    """OneBot v11 协议消息发送器"""

    def __init__(self):
        """
        初始化OneBot发送器
        从环境变量读取配置信息
        """
        self.onebot_url = os.environ.get("ONEBOT_HTTP_URL")
        self.access_token = os.environ.get("ONEBOT_ACCESS_TOKEN")
        self.target_groups = self._parse_target_groups()

        # 验证配置
        if not self.onebot_url:
            logging.error("OneBot HTTP URL 未配置，请设置环境变量 ONEBOT_HTTP_URL")
            raise ValueError("OneBot HTTP URL 未配置")

        if not self.target_groups:
            logging.warning("未配置目标群组，请设置环境变量 ONEBOT_TARGET_GROUPS")

    def _parse_target_groups(self) -> List[str]:
        """
        解析目标群组ID列表
        从环境变量 ONEBOT_TARGET_GROUPS 中读取，支持逗号分隔

        Returns:
            List[str]: 群组ID列表
        """
        groups_str = os.environ.get("ONEBOT_TARGET_GROUPS", "")
        if not groups_str:
            return []

        # 支持逗号分隔的群组ID
        groups = [group.strip() for group in groups_str.split(",") if group.strip()]
        return groups

    def _build_headers(self) -> Dict[str, str]:
        """
        构建请求头

        Returns:
            Dict[str, str]: 请求头字典
        """
        headers = {"Content-Type": "application/json", "User-Agent": "QFNU-Monitor/1.0"}

        # 如果配置了access token，添加到请求头
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        return headers

    def send_group_message(
        self, group_id: str, message: Union[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        向指定群组发送消息

        Args:
            group_id (str): 群组ID
            message (Union[str, List[Dict[str, Any]]]): 要发送的消息内容
                - 可以是简单字符串（向后兼容）
                - 也可以是消息段数组，格式如: [{"type": "text", "data": {"text": "内容"}}]

        Returns:
            Dict[str, Any]: API响应结果
        """
        if not self.onebot_url:
            return {"error": "OneBot URL 未配置"}

        # 构建API端点
        api_url = f"{self.onebot_url.rstrip('/')}/send_group_msg"

        # 处理消息格式
        if isinstance(message, str):
            # 字符串格式：转换为消息段格式
            formatted_message = [{"type": "text", "data": {"text": message}}]
        else:
            # 已经是消息段格式
            formatted_message = message

        # 构建请求数据（group_id 保持字符串格式以匹配示例）
        data = {"group_id": group_id, "message": formatted_message}

        headers = self._build_headers()

        try:
            response = requests.post(
                api_url, headers=headers, data=json.dumps(data), timeout=10
            )
            logging.info(f"OneBot消息发送响应: {response.text}")
            result = response.json()

            if result.get("status") == "ok":
                logging.info(f"OneBot消息发送成功 - 群组: {group_id}")
                return result
            else:
                error_msg = result.get("message", "未知错误")
                logging.error(
                    f"OneBot消息发送失败 - 群组: {group_id}, 错误: {error_msg}，响应内容: {result}"
                )
                return {"error": error_msg}

        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求失败: {str(e)}"
            logging.error(
                f"OneBot消息发送失败 - 群组: {group_id}, {error_msg}，响应内容: {result}"
            )
            return {"error": error_msg}
        except json.JSONDecodeError as e:
            error_msg = f"响应解析失败: {str(e)}"
            logging.error(
                f"OneBot消息发送失败 - 群组: {group_id}, {error_msg}，响应内容: {result}"
            )
            return {"error": error_msg}
        except Exception as e:
            error_msg = f"未知错误: {str(e)}"
            logging.error(
                f"OneBot消息发送失败 - 群组: {group_id}, {error_msg}，响应内容: {result}"
            )
            return {"error": error_msg}

    def send_to_all_groups(
        self, message: Union[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        向所有配置的群组发送消息

        Args:
            message (Union[str, List[Dict[str, Any]]]): 要发送的消息内容
                - 可以是简单字符串（向后兼容）
                - 也可以是消息段数组，格式如: [{"type": "text", "data": {"text": "内容"}}]

        Returns:
            Dict[str, Any]: 发送结果汇总
        """
        if not self.target_groups:
            logging.warning("没有配置目标群组")
            return {"error": "没有配置目标群组"}

        results = {}
        success_count = 0

        for group_id in self.target_groups:
            result = self.send_group_message(group_id, message)
            results[group_id] = result

            if "error" not in result:
                success_count += 1

        summary = {
            "total_groups": len(self.target_groups),
            "success_count": success_count,
            "failed_count": len(self.target_groups) - success_count,
            "results": results,
        }

        if success_count > 0:
            logging.info(
                f"OneBot批量发送完成: {success_count}/{len(self.target_groups)} 个群组发送成功"
            )
        else:
            logging.error("OneBot批量发送失败: 所有群组发送均失败")

        return summary

    def send_to_specific_groups(
        self, group_ids: List[str], message: Union[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        向指定的群组列表发送消息

        Args:
            group_ids (List[str]): 群组ID列表
            message (Union[str, List[Dict[str, Any]]]): 要发送的消息内容
                - 可以是简单字符串（向后兼容）
                - 也可以是消息段数组，格式如: [{"type": "text", "data": {"text": "内容"}}]

        Returns:
            Dict[str, Any]: 发送结果汇总
        """
        if not group_ids:
            return {"error": "群组列表为空"}

        results = {}
        success_count = 0

        for group_id in group_ids:
            result = self.send_group_message(group_id, message)
            results[group_id] = result

            if "error" not in result:
                success_count += 1

        summary = {
            "total_groups": len(group_ids),
            "success_count": success_count,
            "failed_count": len(group_ids) - success_count,
            "results": results,
        }

        logging.info(
            f"OneBot指定群组发送完成: {success_count}/{len(group_ids)} 个群组发送成功"
        )
        return summary


# 便捷函数，保持与feishu模块相似的接口
def onebot_send_all(message: Union[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    向所有配置的群组发送消息的便捷函数

    Args:
        message (Union[str, List[Dict[str, Any]]]): 要发送的消息内容
            - 可以是简单字符串（向后兼容）
            - 也可以是消息段数组，格式如: [{"type": "text", "data": {"text": "内容"}}]

    Returns:
        Dict[str, Any]: 发送结果
    """
    try:
        sender = OneBotSender()
        return sender.send_to_all_groups(message)
    except Exception as e:
        error_msg = f"OneBot发送失败: {str(e)}"
        logging.error(error_msg)
        return {"error": error_msg}


def onebot_send_groups(
    group_ids: List[str], message: Union[str, List[Dict[str, Any]]]
) -> Dict[str, Any]:
    """
    向指定群组发送消息的便捷函数

    Args:
        group_ids (List[str]): 群组ID列表
        message (Union[str, List[Dict[str, Any]]]): 要发送的消息内容
            - 可以是简单字符串（向后兼容）
            - 也可以是消息段数组，格式如: [{"type": "text", "data": {"text": "内容"}}]

    Returns:
        Dict[str, Any]: 发送结果
    """
    try:
        sender = OneBotSender()
        return sender.send_to_specific_groups(group_ids, message)
    except Exception as e:
        error_msg = f"OneBot发送失败: {str(e)}"
        logging.error(error_msg)
        return {"error": error_msg}
