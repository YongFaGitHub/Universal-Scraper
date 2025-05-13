#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知脚本 - 发送分析结果通知
支持多种通知渠道：钉钉、飞书、企业微信
"""

import os
import sys
import json
import yaml
import argparse
import logging
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('notify')

class Notifier:
    """通知发送器类，支持多种通知渠道"""
    
    def __init__(self, file_path, site_id, settings_path=None):
        """
        初始化通知发送器
        
        Args:
            file_path (str): 分析结果文件路径
            site_id (str): 网站ID
            settings_path (str, optional): 设置文件路径
        """
        self.file_path = file_path
        self.site_id = site_id
        
        # 设置路径
        self.base_dir = Path(__file__).parent.parent
        self.settings_path = settings_path or self.base_dir / "config" / "settings.yaml"
        
        # 加载设置
        self.settings = self._load_settings()
        
        # 验证通知设置
        self._validate_notification_settings()
        
        # 加载分析结果
        self.result_data = None
        self.load_result()
    
    def _load_settings(self):
        """加载设置文件"""
        try:
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                settings = yaml.safe_load(f)
            logger.info(f"成功加载设置文件: {self.settings_path}")
            return settings
        except Exception as e:
            logger.error(f"加载设置文件失败: {e}")
            raise
    
    def _validate_notification_settings(self):
        """验证通知设置"""
        notification_settings = self.settings.get('notification', {})
        if not notification_settings.get('enabled', False):
            logger.warning("通知功能未启用")
            return False
        
        # 检查各通知渠道
        dingtalk_enabled = notification_settings.get('dingtalk', {}).get('enabled', False)
        feishu_enabled = notification_settings.get('feishu', {}).get('enabled', False)
        wechat_enabled = notification_settings.get('wechat', {}).get('enabled', False)
        
        if not (dingtalk_enabled or feishu_enabled or wechat_enabled):
            logger.warning("未启用任何通知渠道")
            return False
        
        logger.info("通知设置验证通过")
        return True
    
    def load_result(self):
        """加载分析结果"""
        try:
            # 获取文件扩展名
            file_ext = self.file_path.split('.')[-1].lower()
            
            if file_ext == 'json':
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self.result_data = json.load(f)
            elif file_ext == 'csv':
                self.result_data = pd.read_csv(self.file_path)
            elif file_ext == 'tsv':
                self.result_data = pd.read_csv(self.file_path, sep='\t')
            elif file_ext == 'txt' or file_ext == 'md':
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                # 尝试解析为TSV
                try:
                    import io
                    self.result_data = pd.read_csv(io.StringIO(content), sep='\t')
                except:
                    # 如果解析失败，则作为纯文本保存
                    self.result_data = content
            else:
                logger.error(f"不支持的文件格式: {file_ext}")
                raise ValueError(f"不支持的文件格式: {file_ext}")
                
            logger.info(f"成功加载分析结果文件: {self.file_path}")
            return True
        except Exception as e:
            logger.error(f"加载分析结果文件失败: {e}")
            return False
    
    def prepare_message(self):
        """准备通知消息内容"""
        notification_settings = self.settings.get('notification', {})
        template = notification_settings.get('template', '分析完成，共有{count}条记录')
        
        # 获取统计信息
        if isinstance(self.result_data, pd.DataFrame):
            record_count = len(self.result_data)
            top_records = self.result_data.head(5)
            
            # 尝试获取不同类别的统计
            category_field = notification_settings.get('category_field', '类别')
            category_stats = None
            if category_field in self.result_data.columns:
                category_stats = self.result_data[category_field].value_counts().to_dict()
            
            # 格式化消息
            message = template.format(
                site=self.site_id,
                count=record_count,
                date=datetime.now().strftime('%Y-%m-%d'),
                time=datetime.now().strftime('%H:%M:%S')
            )
            
            # 添加类别统计
            if category_stats:
                message += "\n\n类别统计:\n"
                for category, count in category_stats.items():
                    message += f"- {category}: {count}条\n"
            
            # 添加前5条记录
            message += "\n\n前5条记录预览:\n"
            for idx, row in top_records.iterrows():
                message += f"{idx+1}. "
                for col, val in row.items():
                    message += f"{col}: {val}, "
                message = message[:-2] + "\n"
            
        elif isinstance(self.result_data, list) and self.result_data:
            record_count = len(self.result_data)
            top_records = self.result_data[:5]
            
            # 格式化消息
            message = template.format(
                site=self.site_id,
                count=record_count,
                date=datetime.now().strftime('%Y-%m-%d'),
                time=datetime.now().strftime('%H:%M:%S')
            )
            
            # 添加前5条记录
            message += "\n\n前5条记录预览:\n"
            for idx, record in enumerate(top_records):
                message += f"{idx+1}. "
                for key, val in record.items():
                    message += f"{key}: {val}, "
                message = message[:-2] + "\n"
                
        else:
            # 纯文本结果
            if isinstance(self.result_data, str):
                # 获取行数
                lines = self.result_data.strip().split('\n')
                record_count = len(lines) - 1 if len(lines) > 1 else 0  # 减去表头
                
                # 格式化消息
                message = template.format(
                    site=self.site_id,
                    count=record_count,
                    date=datetime.now().strftime('%Y-%m-%d'),
                    time=datetime.now().strftime('%H:%M:%S')
                )
                
                # 添加前5行预览
                message += "\n\n结果预览:\n"
                preview_lines = lines[:6]  # 包含表头和前5条数据
                for line in preview_lines:
                    message += line + "\n"
            else:
                message = f"分析完成 - {self.site_id} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return message
    
    def send_dingtalk(self, message):
        """发送钉钉通知"""
        dingtalk_settings = self.settings.get('notification', {}).get('dingtalk', {})
        if not dingtalk_settings.get('enabled', False):
            logger.info("钉钉通知未启用")
            return False
        
        webhook_url = dingtalk_settings.get('webhook_url')
        secret = dingtalk_settings.get('secret')
        
        if not webhook_url:
            logger.error("钉钉Webhook URL未设置")
            return False
        
        try:
            # 添加签名（如果有密钥）
            if secret:
                import hmac
                import hashlib
                import base64
                import urllib.parse
                import time
                
                timestamp = str(round(time.time() * 1000))
                string_to_sign = f"{timestamp}\n{secret}"
                hmac_code = hmac.new(
                    secret.encode(), string_to_sign.encode(), digestmod=hashlib.sha256
                ).digest()
                sign = urllib.parse.quote_plus(base64.b64encode(hmac_code).decode())
                
                webhook_url = f"{webhook_url}&timestamp={timestamp}&sign={sign}"
            
            # 构造请求数据
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": f"{self.site_id}分析结果",
                    "text": message
                }
            }
            
            # 发送请求
            response = requests.post(
                webhook_url,
                json=data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200 and response.json().get('errcode') == 0:
                logger.info("钉钉通知发送成功")
                return True
            else:
                logger.error(f"钉钉通知发送失败: {response.text}")
                return False
        except Exception as e:
            logger.error(f"钉钉通知发送异常: {e}")
            return False
    
    def send_feishu(self, message):
        """发送飞书通知"""
        feishu_settings = self.settings.get('notification', {}).get('feishu', {})
        if not feishu_settings.get('enabled', False):
            logger.info("飞书通知未启用")
            return False
        
        webhook_url = feishu_settings.get('webhook_url')
        
        if not webhook_url:
            logger.error("飞书Webhook URL未设置")
            return False
        
        try:
            # 构造请求数据
            data = {
                "msg_type": "text",
                "content": {
                    "text": message
                }
            }
            
            # 发送请求
            response = requests.post(
                webhook_url,
                json=data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200 and response.json().get('code') == 0:
                logger.info("飞书通知发送成功")
                return True
            else:
                logger.error(f"飞书通知发送失败: {response.text}")
                return False
        except Exception as e:
            logger.error(f"飞书通知发送异常: {e}")
            return False
    
    def send_wechat(self, message):
        """发送企业微信通知"""
        wechat_settings = self.settings.get('notification', {}).get('wechat', {})
        if not wechat_settings.get('enabled', False):
            logger.info("企业微信通知未启用")
            return False
        
        webhook_url = wechat_settings.get('webhook_url')
        
        if not webhook_url:
            logger.error("企业微信Webhook URL未设置")
            return False
        
        try:
            # 构造请求数据
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "content": message
                }
            }
            
            # 发送请求
            response = requests.post(
                webhook_url,
                json=data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200 and response.json().get('errcode') == 0:
                logger.info("企业微信通知发送成功")
                return True
            else:
                logger.error(f"企业微信通知发送失败: {response.text}")
                return False
        except Exception as e:
            logger.error(f"企业微信通知发送异常: {e}")
            return False
    
    def send_notifications(self):
        """发送所有通知"""
        if not self.result_data:
            logger.error("没有分析结果可通知")
            return False
        
        # 准备消息内容
        message = self.prepare_message()
        
        # 发送各渠道通知
        success_count = 0
        
        # 钉钉通知
        if self.settings.get('notification', {}).get('dingtalk', {}).get('enabled', False):
            if self.send_dingtalk(message):
                success_count += 1
        
        # 飞书通知
        if self.settings.get('notification', {}).get('feishu', {}).get('enabled', False):
            if self.send_feishu(message):
                success_count += 1
        
        # 企业微信通知
        if self.settings.get('notification', {}).get('wechat', {}).get('enabled', False):
            if self.send_wechat(message):
                success_count += 1
        
        # 判断是否有成功的通知
        if success_count > 0:
            logger.info(f"通知发送完成，成功发送 {success_count} 个渠道")
            return True
        else:
            logger.warning("所有通知渠道均发送失败")
            return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='通知脚本 - 发送分析结果通知')
    parser.add_argument('--file', '-f', required=True, help='分析结果文件路径')
    parser.add_argument('--site', '-s', required=True, help='网站ID')
    parser.add_argument('--settings', help='设置文件路径')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # 创建通知发送器实例
        notifier = Notifier(
            file_path=args.file,
            site_id=args.site,
            settings_path=args.settings
        )
        
        # 发送通知
        if notifier.send_notifications():
            logger.info("通知任务完成")
            return 0
        else:
            logger.error("发送通知失败")
            return 1
    except Exception as e:
        logger.exception(f"通知过程中发生错误: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 