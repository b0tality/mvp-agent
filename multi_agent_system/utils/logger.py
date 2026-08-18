"""
日志工具
提供统一的日志管理
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
from loguru import logger


class Logger:
    """日志管理器"""
    
    _instance: Optional["Logger"] = None
    _initialized: bool = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(
        self,
        log_file: str = "./logs/system.log",
        log_level: str = "INFO",
        rotation: str = "10 MB",
        retention: str = "7 days"
    ):
        if self._initialized:
            return
        
        self._initialized = True
        self.log_file = log_file
        self.log_level = log_level
        
        # 创建日志目录
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 配置loguru
        logger.remove()  # 移除默认处理器
        
        # 添加控制台处理器
        logger.add(
            sys.stdout,
            level=log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            colorize=True
        )
        
        # 添加文件处理器
        logger.add(
            log_file,
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation=rotation,
            retention=retention,
            encoding="utf-8"
        )
        
        self.logger = logger
    
    def get_logger(self):
        """获取logger实例"""
        return self.logger
    
    def info(self, message: str, **kwargs) -> None:
        """记录信息日志"""
        self.logger.info(message, **kwargs)
    
    def debug(self, message: str, **kwargs) -> None:
        """记录调试日志"""
        self.logger.debug(message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """记录警告日志"""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """记录错误日志"""
        self.logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """记录严重错误日志"""
        self.logger.critical(message, **kwargs)
    
    def exception(self, message: str, **kwargs) -> None:
        """记录异常日志"""
        self.logger.exception(message, **kwargs)
    
    def log_agent_action(self, agent_name: str, action: str, details: str = "") -> None:
        """记录智能体操作"""
        self.info(f"[{agent_name}] {action} {details}".strip())
    
    def log_state_change(self, key: str, old_value: any, new_value: any) -> None:
        """记录状态变更"""
        self.debug(f"状态变更: {key} = {old_value} -> {new_value}")
    
    def log_error(self, agent_name: str, error: Exception) -> None:
        """记录错误"""
        self.error(f"[{agent_name}] 错误: {type(error).__name__}: {error}")
    
    def log_performance(self, operation: str, duration: float) -> None:
        """记录性能"""
        self.info(f"性能: {operation} 耗时 {duration:.2f}秒")


def get_logger(
    log_file: str = "./logs/system.log",
    log_level: str = "INFO"
) -> Logger:
    """获取日志管理器实例"""
    return Logger(log_file=log_file, log_level=log_level)
