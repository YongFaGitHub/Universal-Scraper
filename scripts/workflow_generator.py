#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流生成器 - 根据配置生成GitHub Actions工作流文件
"""

import os
import sys
import yaml
import logging
import argparse
from pathlib import Path
from jinja2 import Template, Environment, FileSystemLoader

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('workflow_generator')

class WorkflowGenerator:
    """工作流生成器类，用于生成GitHub Actions工作流文件"""
    
    def __init__(self, settings_path=None, sites_dir=None, output_dir=None):
        """
        初始化工作流生成器
        
        Args:
            settings_path (str, optional): 设置文件路径
            sites_dir (str, optional): 站点配置目录
            output_dir (str, optional): 输出目录
        """
        # 设置路径
        self.base_dir = Path(__file__).parent.parent
        self.settings_path = settings_path or self.base_dir / "config" / "settings.yaml"
        self.sites_dir = sites_dir or self.base_dir / "config" / "sites"
        self.templates_dir = self.base_dir / "config" / "workflow"
        self.output_dir = output_dir or self.base_dir / ".github" / "workflows"
        
        # 加载设置
        self.settings = self._load_settings()
        
        # 设置Jinja2环境
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
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
    
    def _load_site_config(self, site_id):
        """加载站点配置"""
        site_config_path = self.sites_dir / f"{site_id}.yaml"
        try:
            with open(site_config_path, 'r', encoding='utf-8') as f:
                site_config = yaml.safe_load(f)
            logger.info(f"成功加载站点配置: {site_config_path}")
            return site_config
        except Exception as e:
            logger.error(f"加载站点配置失败: {e}")
            return None
    
    def _load_workflow_template(self, template_name):
        """加载工作流模板"""
        try:
            return self.jinja_env.get_template(f"{template_name}.yml.template")
        except Exception as e:
            logger.error(f"加载工作流模板失败: {e}")
            return None
    
    def generate_workflow(self, site_id, workflow_type="crawler"):
        """
        生成工作流文件
        
        Args:
            site_id (str): 站点ID
            workflow_type (str, optional): 工作流类型，"crawler"或"analyzer"
        
        Returns:
            bool: 是否成功生成
        """
        # 加载站点配置
        site_config = self._load_site_config(site_id)
        if not site_config:
            return False
        
        # 加载工作流模板
        template = self._load_workflow_template(workflow_type)
        if not template:
            return False
        
        # 准备渲染变量
        render_vars = {
            # 全局设置
            "site_id": site_id,
            "site_name": site_config.get('site_info', {}).get('name', site_id),
            "python_version": self.settings.get('python_version', '3.10'),
            
            # 目录设置
            "data_dir": self.settings.get('data_dir', 'data'),
            "analysis_dir": self.settings.get('analysis_dir', 'analysis'),
            "status_dir": self.settings.get('status_dir', 'status'),
            
            # 爬虫设置
            "scraper_script": site_config.get('scraping', {}).get('script_path', 'scripts/scraper.py'),
            "output_filename": site_config.get('output', {}).get('filename', f"{site_id}_data.json"),
            
            # 分析设置
            "analyzer_script": self.settings.get('ai_analysis', {}).get('script_path', 'scripts/ai_analyzer.py'),
            "output_file": self.settings.get('ai_analysis', {}).get('output_file', 'analysis_result.tsv'),
            "output_extension": self.settings.get('ai_analysis', {}).get('output_format', 'tsv'),
            
            # 通知设置
            "notification_script": self.settings.get('notification', {}).get('script_path', 'scripts/notify.py'),
            "send_notification": self.settings.get('notification', {}).get('enabled', False),
            
            # 环境变量
            "env_vars": [
                {"name": "OPENAI_API_KEY", "secret": "OPENAI_API_KEY"},
                {"name": "GEMINI_API_KEY", "secret": "GEMINI_API_KEY"}
            ],
            
            # 依赖设置
            "scraper_dependencies": "requests beautifulsoup4 pandas pyyaml",
            "analysis_dependencies": "requests pandas pyyaml google-generativeai openai"
        }
        
        # 附加站点特定变量
        if workflow_type == "crawler":
            render_vars.update({
                "cron_schedule": site_config.get('scraping', {}).get('schedule', '0 0 * * *'),
                "max_retries": site_config.get('network', {}).get('max_retries', 3),
                "timeout": site_config.get('network', {}).get('timeout', 30),
                "run_analysis": site_config.get('output', {}).get('run_analysis', True)
            })
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 生成工作流文件
        output_filename = f"{workflow_type}_{site_id}.yml"
        output_path = self.output_dir / output_filename
        
        try:
            # 渲染模板
            workflow_content = template.render(**render_vars)
            
            # 写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(workflow_content)
            
            logger.info(f"成功生成工作流文件: {output_path}")
            return True
        except Exception as e:
            logger.error(f"生成工作流文件失败: {e}")
            return False
    
    def generate_all_workflows(self):
        """为所有站点生成工作流文件"""
        # 获取所有站点ID
        site_files = list(self.sites_dir.glob("*.yaml"))
        site_ids = [site_file.stem for site_file in site_files]
        
        if not site_ids:
            logger.warning("未找到任何站点配置文件")
            return False
        
        success_count = 0
        total_count = len(site_ids) * 2  # 每个站点生成两个工作流（爬虫和分析）
        
        for site_id in site_ids:
            # 跳过示例配置
            if site_id == "example":
                logger.info(f"跳过示例配置: {site_id}")
                continue
                
            # 生成爬虫工作流
            if self.generate_workflow(site_id, "crawler"):
                success_count += 1
            
            # 生成分析工作流
            if self.generate_workflow(site_id, "analyzer"):
                success_count += 1
        
        logger.info(f"工作流生成完成，成功: {success_count}/{total_count}")
        return success_count > 0
    
    def update_workflows(self, sites=None):
        """更新指定站点的工作流文件，如果未指定则更新所有站点"""
        if sites:
            site_ids = sites.split(',')
            total_count = len(site_ids) * 2  # 每个站点生成两个工作流
            
            success_count = 0
            for site_id in site_ids:
                # 生成爬虫工作流
                if self.generate_workflow(site_id, "crawler"):
                    success_count += 1
                
                # 生成分析工作流
                if self.generate_workflow(site_id, "analyzer"):
                    success_count += 1
            
            logger.info(f"工作流更新完成，成功: {success_count}/{total_count}")
            return success_count > 0
        else:
            # 更新所有站点
            return self.generate_all_workflows()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='工作流生成器 - 生成GitHub Actions工作流')
    parser.add_argument('--settings', help='设置文件路径')
    parser.add_argument('--sites-dir', help='站点配置目录')
    parser.add_argument('--output-dir', help='输出目录')
    parser.add_argument('--site', help='指定站点ID，多个站点用逗号分隔')
    parser.add_argument('--all', action='store_true', help='生成所有站点的工作流')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # 创建工作流生成器实例
        generator = WorkflowGenerator(
            settings_path=args.settings,
            sites_dir=args.sites_dir,
            output_dir=args.output_dir
        )
        
        # 根据参数执行不同操作
        if args.all:
            if generator.generate_all_workflows():
                logger.info("所有工作流生成成功")
                return 0
            else:
                logger.error("部分或全部工作流生成失败")
                return 1
        elif args.site:
            if generator.update_workflows(args.site):
                logger.info(f"指定站点的工作流更新成功: {args.site}")
                return 0
            else:
                logger.error(f"指定站点的工作流更新失败: {args.site}")
                return 1
        else:
            logger.warning("未指定操作，请使用--all或--site参数")
            parser.print_help()
            return 1
    except Exception as e:
        logger.exception(f"工作流生成过程中发生错误: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 