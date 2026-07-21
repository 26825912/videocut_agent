"""
错误处理工具类 - 提供统一的异常处理和验证功能

提供常用的错误处理装饰器和验证方法，提高代码健壮性。
"""

import os
import logging
import functools
from typing import Optional, Callable, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class FileValidationError(Exception):
    """文件验证错误"""
    pass

class NetworkError(Exception):
    """网络请求错误"""
    pass

class VideoProcessingError(Exception):
    """视频处理错误"""
    pass

class ErrorHandler:
    """错误处理工具类"""

    @staticmethod
    def validate_file_exists(file_path: str, description: str = "文件") -> str:
        """
        验证文件是否存在

        Args:
            file_path: 文件路径
            description: 文件描述，用于错误信息

        Returns:
            str: 验证通过的文件路径

        Raises:
            FileValidationError: 文件不存在时抛出
        """
        if not file_path:
            raise FileValidationError(f"{description}路径不能为空")

        path = Path(file_path)
        if not path.exists():
            raise FileValidationError(f"{description}不存在: {file_path}")

        if not path.is_file():
            raise FileValidationError(f"路径不是文件: {file_path}")

        return str(path.absolute())

    @staticmethod
    def validate_directory_exists(dir_path: str, description: str = "目录", create_if_missing: bool = False) -> str:
        """
        验证目录是否存在

        Args:
            dir_path: 目录路径
            description: 目录描述
            create_if_missing: 是否在目录不存在时创建

        Returns:
            str: 验证通过的目录路径

        Raises:
            FileValidationError: 目录不存在且不创建时抛出
        """
        if not dir_path:
            raise FileValidationError(f"{description}路径不能为空")

        path = Path(dir_path)

        if not path.exists():
            if create_if_missing:
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"创建{description}: {dir_path}")
                except OSError as e:
                    raise FileValidationError(f"创建{description}失败: {e}")
            else:
                raise FileValidationError(f"{description}不存在: {dir_path}")

        if path.exists() and not path.is_dir():
            raise FileValidationError(f"路径不是目录: {dir_path}")

        return str(path.absolute())

    @staticmethod
    def safe_file_operation(operation: Callable, file_path: str, description: str = "文件操作", **kwargs) -> Any:
        """
        安全的文件操作

        Args:
            operation: 文件操作函数
            file_path: 文件路径
            description: 操作描述
            **kwargs: 传给操作函数的参数

        Returns:
            操作结果

        Raises:
            FileValidationError: 文件操作失败时抛出
        """
        try:
            return operation(file_path, **kwargs)
        except FileNotFoundError:
            raise FileValidationError(f"{description}失败: 文件不存在 {file_path}")
        except PermissionError:
            raise FileValidationError(f"{description}失败: 权限不足 {file_path}")
        except OSError as e:
            raise FileValidationError(f"{description}失败: {e}")
        except Exception as e:
            logger.error(f"{description}发生未知错误: {e}")
            raise FileValidationError(f"{description}失败: {e}")

def handle_errors(error_types: dict = None, default_return=None, log_errors: bool = True):
    """
    错误处理装饰器

    Args:
        error_types: 错误类型映射 {Exception: return_value}
        default_return: 默认返回值
        log_errors: 是否记录错误日志
    """
    if error_types is None:
        error_types = {}

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.error(f"函数 {func.__name__} 执行错误: {e}")

                # 检查特定错误类型
                for error_type, return_value in error_types.items():
                    if isinstance(e, error_type):
                        return return_value

                # 如果没有匹配的错误类型，返回默认值或重新抛出
                if default_return is not None:
                    return default_return
                else:
                    raise
        return wrapper
    return decorator

def retry_on_failure(max_retries: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)):
    """
    失败重试装饰器

    Args:
        max_retries: 最大重试次数
        delay: 重试间隔（秒）
        exceptions: 需要重试的异常类型
    """
    import time

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败: {e}, {delay}秒后重试")
                        time.sleep(delay)
                    else:
                        logger.error(f"函数 {func.__name__} 重试 {max_retries} 次后仍失败")
                        raise last_exception
                except Exception as e:
                    # 对于不需要重试的异常，直接抛出
                    raise e

            # 理论上不会到达这里
            raise last_exception
        return wrapper
    return decorator