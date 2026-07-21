import requests
import time
import logging
import os
from abc import ABC, abstractmethod

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


AVATAR_MUSETALK_URL = "http://10.2.42.21:8081/generate"



def get_data_dir():
    data_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(data_dir,'data')
    return data_dir


class AvatarClient(ABC):
    @abstractmethod
    def submit_task(self, audio_path: str, video_path: str, rm_bg: bool) -> str:
        pass
    
    @abstractmethod
    def check_status(self, task_id: str) -> tuple:
        pass
    
    @abstractmethod
    def download_result(self, result_url: str, save_path: str = None) -> str:
        pass


class MuseTalkClientImpl(AvatarClient):
    def __init__(self):
        self.base_url = "http://10.2.42.21:8081"
    
    def submit_task(self, audio_path: str, video_path: str, rm_bg: bool = False) -> str:
        client = MuseTalkClient()
        return client.submit_task(audio_path, video_path, rm_bg)
    
    def check_status(self, task_id: str) -> tuple:
        client = MuseTalkClient()
        return client.check_status(task_id)
    
    def download_result(self, result_url: str, save_path: str = None) -> str:
        client = MuseTalkClient()
        return client.download_result(result_url, save_path)


class AvatarGenerator:
    """工厂类 - 使用策略模式"""
    _strategies = {
        'musetalk': MuseTalkClientImpl,
    }
    _instances = {}
    
    @classmethod
    def register_model(cls, model_name: str, client_class: type):
        """注册新的模型"""
        cls._strategies[model_name] = client_class
        logger.info(f"已注册模型: {model_name}")
    
    @classmethod
    def _get_client(cls, model: str) -> AvatarClient:
        """获取客户端实例"""
        if model not in cls._strategies:
            raise ValueError(f"未知的模型: {model}。支持的模型: {list(cls._strategies.keys())}")
        
        if model not in cls._instances:
            cls._instances[model] = cls._strategies[model]()
        
        return cls._instances[model]
    
    @staticmethod
    def submit_task(model: str, audio_path: str, video_path: str, rm_bg: bool = False) -> str:
        """提交任务"""
        client = AvatarGenerator._get_client(model)
        return client.submit_task(audio_path, video_path, rm_bg)

    @staticmethod
    def check_status(model: str, task_id: str) -> tuple:
        """查询任务状态"""
        client = AvatarGenerator._get_client(model)
        return client.check_status(task_id)
    
    @staticmethod
    def download_result(model: str, result_url: str, save_path: str = None) -> str:
        """下载结果"""
        client = AvatarGenerator._get_client(model)
        return client.download_result(result_url, save_path)



class MuseTalkClient:
    def __init__(self):
        """
        初始化客户端
        :param base_url: 服务端地址，例如 "http://10.2.42.21:8081"
        """
        self.base_url = "http://10.2.42.21:8081"
    
    def submit_task(self, audio_path, video_path, rm_bg=False):
        """
        提交生成任务
        :param audio_path: 音频文件路径
        :param video_path: 视频文件路径
        :param rm_bg: 是否去背景
        :return: 任务ID
        """
        files = [
            ('audio', ('audio.wav', open(audio_path, 'rb'), 'audio/wav')),
            ('video', ('video.mp4', open(video_path, 'rb'), 'video/mp4'))
        ]
        payload = {'rm_bg': str(rm_bg)}
        response = requests.post(f"{self.base_url}/generate", files=files, data=payload)
        if response.status_code != 200:
            logger.error(f"任务提交失败: {response.text}")
            raise Exception("任务提交失败")
        
        data = response.json()
        logger.info(f"提交任务 {data}")

        return data['task_id']
    
    def check_status(self, task_id):
        """
        查询任务状态
        :param task_id: 任务ID
        :return: 任务状态
        """
        status_url = f"{self.base_url}/status/{task_id}"
        response = requests.get(status_url)
        if response.status_code != 200:
            logger.error(f"查询任务状态失败: {response.text}")
            raise Exception("查询任务状态失败")
        
        data = response.json()
        logger.info(f"查询任务状态 {data}")

        return data['status'], data.get('result_url'), data.get('message')
    

    def download_result(self, result_url, save_path = None):
        """
        下载生成结果
        :param result_url: 结果下载链接
        :param save_path: 保存路径
        """
        data_dir = get_data_dir()

        if save_path is None:
            save_dir = os.path.join(data_dir,"result_video","avatar_video",)
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, f"{time.strftime('%Y%m%d%H%M%S', time.localtime())}.mp4")
        
        download_url = f"{self.base_url}{result_url}"
        response = requests.get(download_url)
        if response.status_code != 200:
            logger.error(f"下载结果失败: {response.text}")
            raise Exception("下载结果失败")
        with open(save_path, "wb") as f:
            f.write(response.content)
        logger.info(f"结果已保存到 {save_path}")


if __name__ == "__main__":

    ##################################################musetalk接口测试###############################################

    audio_path = r'C:\Users\ddf\Desktop\zzc\code\avatar\test_data\demo1_audio.wav'
    video_path = r'C:\Users\ddf\Desktop\zzc\code\avatar\test_data\demo1_video.mp4'
    # client = MuseTalkClient()
    # task_id = client.submit_task(audio_path, video_path, rm_bg=False)
    # logger.info(f"任务已提交，ID: {task_id}")
    
    # while True:
    #     status, result_url, message = client.check_status(task_id)
    #     logger.info(f"当前状态: {status}")
        
    #     if status == 'success':
    #         client.download_result(result_url)
    #         logger.info("生成成功！结果已下载。")
    #         break
    #     elif status == 'failed':
    #         logger.error(f"生成失败: {message}")  
    #         break
        
    #     time.sleep(5)  

    ##################################################工厂模式进程测试###############################################
    # 使用方案1或方案2都相同
    try:
        # 1. 提交任务
        task_id = AvatarGenerator.submit_task(
            model='musetalk',
            audio_path=audio_path,
            video_path=video_path,
            rm_bg=False
        )
        logger.info(f"任务已提交: {task_id}")
        
        # 2. 轮询查询状态
        while True:
            status, result_url, message = AvatarGenerator.check_status('musetalk', task_id)
            logger.info(f"任务状态: {status}")
            
            if status == 'success':
                # 3. 下载结果
                save_path = AvatarGenerator.download_result('musetalk', result_url)
                logger.info(f"结果已保存: {save_path}")
                break
            elif status == 'failed':
                logger.error(f"任务失败: {message}")
                break
            
            time.sleep(5)

    except Exception as e:
        logger.error(f"处理出错: {str(e)}")

    
        
        
    