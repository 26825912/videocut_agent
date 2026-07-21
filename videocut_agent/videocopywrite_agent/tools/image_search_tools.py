import os
import requests
import random
from typing import Optional, Dict, Any, List
import os
import sys
import django
import requests
import uuid
from django.conf import settings
from langchain_core.tools import tool

# # 添加项目根目录到系统路径
# sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# 加载 .env 文件
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
print(f"Env file path: {env_path}")
load_dotenv(dotenv_path=env_path)

UNSPLASH_ACCESS_KEYS = os.getenv('UNSPLASH_ACCESS_KEYS', '')


class UnsplashImageSearchClient:
    """用于搜索媒体内容的客户端，支持多种API"""
    
    def __init__(self):
        self.unsplash_access_keys = self._load_unsplash_keys()
        self.unsplash_base_url = 'https://api.unsplash.com'
        
    def _load_unsplash_keys(self) -> List[str]:
        """
        从环境变量加载Unsplash API密钥
        支持单个密钥和多个密钥（逗号分隔）
        
        Returns:
            API密钥列表
        """
        # 首先尝试获取多个密钥（逗号分隔）
        keys_str = UNSPLASH_ACCESS_KEYS#getattr(settings, 'UNSPLASH_ACCESS_KEYS', '')
        if keys_str:
            keys = [key.strip() for key in keys_str.split(',') if key.strip()]
            if keys:
                return keys
        
        # 向后兼容，回退到单个密钥
        single_key = getattr(settings, 'UNSPLASH_ACCESS_KEY', '')
        if single_key:
            return [single_key.strip()]
        
        return []
    
    def _get_random_api_key(self) -> str:
        """
        从可用密钥中随机获取一个API密钥
        
        Returns:
            随机选择的API密钥
            
        Raises:
            ValueError: 如果没有可用的API密钥
        """
        if not self.unsplash_access_keys:
            raise ValueError("未找到Unsplash API密钥。请在环境变量中设置UNSPLASH_ACCESS_KEYS或UNSPLASH_ACCESS_KEY。")
        
        return random.choice(self.unsplash_access_keys)
        
    def search_photos(
        self,
        query: str,
        page: int = 1,
        per_page: int = 10,
        order_by: str = 'relevant',
        collections: Optional[str] = None,
        content_filter: str = 'low',
        color: Optional[str] = None,
        orientation: Optional[str] = None,
        lang: str = 'en',
        size: str = 'full',
        return_full_data: bool = False
    ) -> List[str] | List[Dict[str, str]]:
        """
        使用Unsplash API搜索图片
        
        Args:
            query: 搜索关键词
            page: 要获取的页码（默认：1）
            per_page: 每页项目数量（默认：10，最大：30）
            order_by: 图片排序方式（'latest'或'relevant'，默认：'relevant'）
            collections: 用于缩小搜索范围的收藏集ID（多个用逗号分隔）
            content_filter: 按内容安全性限制结果（'low'或'high'，默认：'low'）
            color: 按颜色过滤结果（'black_and_white', 'black', 'white', 'yellow', 
                   'orange', 'red', 'purple', 'magenta', 'green', 'teal', 'blue'）
            orientation: 按图片方向过滤（'landscape', 'portrait', 'squarish'）
            lang: 查询的语言代码（默认：'en'）
            size: 图片大小（'thumb', 'small', 'regular', 'full', 'raw'，默认：'thumb'）
            return_full_data: 是否返回完整的URLs数据（包含thumb和full，默认：False）
            
        Returns:
            如果return_full_data=False: 图片URL的列表（根据size参数返回对应尺寸的URL）
            如果return_full_data=True: 字典列表，每个字典包含{'thumb': url, 'full': url}
            
        Raises:
            ValueError: 如果API密钥未配置
            requests.RequestException: 如果API请求失败
        """
        # 为此请求获取一个随机API密钥
        api_key = self._get_random_api_key()
        
        # 验证参数
        if per_page > 30:
            per_page = 30
        if per_page < 1:
            per_page = 1
            
        if order_by not in ['latest', 'relevant']:
            order_by = 'relevant'
            
        if content_filter not in ['low', 'high']:
            content_filter = 'low'
            
        valid_colors = ['black_and_white', 'black', 'white', 'yellow', 'orange', 
                       'red', 'purple', 'magenta', 'green', 'teal', 'blue']
        if color and color not in valid_colors:
            color = None
            
        valid_orientations = ['landscape', 'portrait', 'squarish']
        if orientation and orientation not in valid_orientations:
            orientation = None
        
        # 验证 size 参数
        valid_sizes = ['thumb', 'small', 'regular', 'full', 'raw']
        if size not in valid_sizes:
            size = 'thumb'
        
        # 构建请求参数
        params = {
            'query': query,
            'page': page,
            'per_page': per_page,
            'order_by': order_by,
            'content_filter': content_filter,
            'lang': lang
        }
        
        # 添加可选参数
        if collections:
            params['collections'] = collections
        if color:
            params['color'] = color
        if orientation:
            params['orientation'] = orientation
        
        # 使用选定的API密钥设置请求头
        headers = {
            'Authorization': f'Client-ID {api_key}',
            'Accept-Version': 'v1'
        }
        
        # 尝试使用选定的密钥，如果失败则尝试其他密钥
        last_exception = None
        keys_to_try = [api_key] + [k for k in self.unsplash_access_keys if k != api_key]
        
        for key in keys_to_try:
            headers['Authorization'] = f'Client-ID {key}'
            
            try:
                # 发起API请求
                response = requests.get(
                    f'{self.unsplash_base_url}/search/photos',
                    params=params,
                    headers=headers,
                    timeout=30
                )
                response.raise_for_status()
                
                # 获取API响应并提取指定尺寸的URLs
                search_results = response.json()
                
                # 直接提取并返回指定尺寸的URLs列表
                if 'results' not in search_results:
                    return []
                
                if return_full_data:
                    # 返回完整数据：包含 thumb 和 full
                    image_data = []
                    for photo in search_results['results']:
                        urls = photo.get('urls', {})
                        thumb_url = urls.get('thumb')
                        full_url = urls.get('full')
                        if thumb_url and full_url:
                            image_data.append({
                                'thumb': thumb_url,
                                'full': full_url
                            })
                    return image_data
                else:
                    # 返回单一尺寸的URL列表（向后兼容）
                    image_urls = []
                    for photo in search_results['results']:
                        image_url = photo.get('urls', {}).get(size)
                        if image_url:
                            image_urls.append(image_url)
                    return image_urls
                
            except requests.exceptions.RequestException as e:
                last_exception = e
                # 如果是限流错误(429)或认证错误(401/403)，尝试下一个密钥
                if hasattr(e, 'response') and e.response is not None:
                    if e.response.status_code in [401, 403, 429]:
                        continue
                # 对于其他错误，不使用其他密钥重试
                break
        
        # 如果所有密钥都失败了，抛出最后一个异常
        raise requests.RequestException(f"使用所有可用密钥搜索图片都失败了: {str(last_exception)}")
    
    def get_photo_download_url(self, photo_id: str) -> str:
        """
        获取指定图片的下载URL
        
        Args:
            photo_id: 图片的ID
            
        Returns:
            图片的下载URL
        """
        # 为此请求获取一个随机API密钥
        api_key = self._get_random_api_key()
        
        # 尝试使用选定的密钥，如果失败则尝试其他密钥
        last_exception = None
        keys_to_try = [api_key] + [k for k in self.unsplash_access_keys if k != api_key]
        
        for key in keys_to_try:
            headers = {
                'Authorization': f'Client-ID {key}',
                'Accept-Version': 'v1'
            }
            
            try:
                response = requests.get(
                    f'{self.unsplash_base_url}/photos/{photo_id}/download',
                    headers=headers,
                    timeout=30
                )
                response.raise_for_status()
                
                return response.json().get('url', '')
                
            except requests.exceptions.RequestException as e:
                last_exception = e
                # 如果是限流错误(429)或认证错误(401/403)，尝试下一个密钥
                if hasattr(e, 'response') and e.response is not None:
                    if e.response.status_code in [401, 403, 429]:
                        continue
                # 对于其他错误，不使用其他密钥重试
                break
        
        # 如果所有密钥都失败了，抛出最后一个异常
        raise requests.RequestException(f"使用所有可用密钥获取下载URL都失败了: {str(last_exception)}")
    
    
    def get_key_stats(self) -> Dict[str, Any]:
        """
        获取已加载API密钥的统计信息
        
        Returns:
            包含密钥统计信息的字典
        """
        return {
            'total_keys': len(self.unsplash_access_keys),
            'keys_preview': [f"{key[:8]}..." for key in self.unsplash_access_keys] if self.unsplash_access_keys else [],
            'has_keys': len(self.unsplash_access_keys) > 0
        }


def get_data_dir():
    data_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    data_dir = os.path.join(data_dir,'data')
    return data_dir


@tool
def img_search_tool(query: str, 
                    per_page: int = 5, 
                    orientation: str = "landscape",
                    return_full_data: bool = False) -> List[Dict[str, str]]:
    """
    搜索 Unsplash 图片
    Args:
        query: 搜索关键词
        per_page: 每页返回的图片数量 (默认5)
        orientation: 图片方向 (landscape/portrait/square)
        return_full_data: 是否返回完整数据 (包含 thumb 和 full URL)
        
    Returns:
        包含图片URL的列表 (或包含完整数据的字典列表)
    """
    down_images_path = []
    data_dir = get_data_dir()
    down_path = os.path.join(data_dir,'images')

    # 安全创建目录
    try:
        os.makedirs(down_path, exist_ok=True)
    except OSError as e:
        logger.error(f"创建目录失败: {down_path}, 错误: {e}")
        return []

    client = UnsplashImageSearchClient()
    img_urls= client.search_photos(
        query=query,
        per_page=per_page,
        orientation=orientation,
        return_full_data=return_full_data
    )

    for img_url in img_urls:
        img_name = f"{uuid.uuid4()}.jpg"
        img_path = os.path.join(down_path,img_name)

        try:
            # 添加超时和错误处理的网络请求
            response = requests.get(img_url, timeout=30)
            response.raise_for_status()

            # 检查内容类型
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                logger.warning(f"意外的内容类型: {content_type}")
                continue

            # 安全的文件写入
            with open(img_path, 'wb') as f:
                f.write(response.content)

            relative_path = os.path.relpath(img_path, data_dir)
            down_images_path.append(relative_path)

        except requests.exceptions.Timeout:
            logger.error(f"下载图片超时: {img_url}")
            continue
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP错误: {e.response.status_code} - {img_url}")
            continue
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: {e}")
            continue
        except OSError as e:
            logger.error(f"文件写入失败: {e}")
            continue
        except Exception as e:
            logger.error(f"下载图片时发生未知错误: {e}")
            continue

    return down_images_path


@tool
def img_search_tool_v2(queries: List[str], 
                    per_page: int = 5, 
                    orientation: str = "landscape",
                    return_full_data: bool = False) -> List[str]:
    """
    图像素材搜索工具
    inputs:
        queries: 搜索关键词列表 (List[str])
        per_page: 每个关键词检索的候选图片数量，将从中随机选取一张 (默认5)
        orientation: 图片方向 (landscape/portrait/square)
        return_full_data: 是否返回完整数据 (包含 thumb 和 full URL)
        
    Returns:
        下载后的本地图片相对路径列表，顺序与 queries 一一对应。
    """
    down_images_path = []
    data_dir = get_data_dir()
    down_path = os.path.join(data_dir, 'images')

    # 安全创建目录
    try:
        os.makedirs(down_path, exist_ok=True)
    except OSError as e:
        logger.error(f"创建目录失败: {down_path}, 错误: {e}")
        return []
        
    client = UnsplashImageSearchClient()

    print(f"INFO: 开始批量搜索图片，关键词数量: {len(queries)}")

    for query in queries:
        try:
            img_urls = client.search_photos(
                query=query,
                per_page=per_page,
                orientation=orientation,
                return_full_data=return_full_data
            )

            # 2. 检查是否有结果
            if not img_urls:
                print(f"WARNING: 关键词 '{query}' 未搜索到图片，跳过。")
                continue

            # 3. 核心逻辑：从检索结果中随机抽取一张
            selected_img_url = random.choice(img_urls)
            
            if isinstance(selected_img_url, dict):
                pass 
            
            download_url = selected_img_url 
            img_name = f"{uuid.uuid4()}.jpg"
            img_path = os.path.join(down_path, img_name)
            
            response = requests.get(download_url, timeout=15)
            if response.status_code == 200:
                with open(img_path, 'wb') as f:
                    f.write(response.content)
                
                relative_path = os.path.relpath(img_path, data_dir)
                down_images_path.append(relative_path)
                print(f"SUCCESS: 关键词 '{query}' -> 下载完成")
            else:
                print(f"ERROR: 图片下载失败 {download_url}, status: {response.status_code}")

        except Exception as e:
            print(f"ERROR: 处理关键词 '{query}' 时出错: {e}")
            continue

    return {
            "tool_return":[{
                "down_images_path": down_images_path,
                "describe": "下载的图片相对路径列表，顺序与输入关键词一一对应"
            }]
        }


if __name__ == "__main__":
    # client = UnsplashImageSearchClient()
    # # 搜索意大利图片
    # image_urls = client.search_photos(
    #         query="U.S. 93 Road Trip Views",
    #         per_page=5,
    #         orientation="landscape"
    # )
    # # 显示图片URLs

    image_urls = img_search_tool_v2(["U.S. 93 Road Trip Views","cat","dog"])
    print(f"搜索到 {image_urls} 张图片")
    for i, url in enumerate(image_urls, 1):
        print(f"图片 {i}: {url}")
        print("---")
            