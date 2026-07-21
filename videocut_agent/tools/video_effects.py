"""
Advanced Video Effects Module - Special effects and green screen removal
"""
import os
import cv2
import logging
import numpy as np
from sklearn.cluster import KMeans
from skimage.morphology import disk, dilation
from .error_handler import ErrorHandler, handle_errors

logger = logging.getLogger(__name__)

class RemoveGreenScreen:
    """绿幕去除和高级视频特效处理类"""

    def __init__(self):
        """初始化绿幕去除处理器"""
        self.lower_green = np.array([40, 40, 40])  # HSV 绿色下限
        self.upper_green = np.array([80, 255, 255])  # HSV 绿色上限

    @handle_errors(error_types={Exception: None})
    def remove_green_screen(self, input_path, output_path, background_path=None):
        """
        去除视频中的绿幕背景

        Args:
            input_path (str): 输入视频路径
            output_path (str): 输出视频路径
            background_path (str): 替换背景图片路径（可选）

        Returns:
            str: 输出文件路径，失败则返回None
        """
        # 验证输入文件
        ErrorHandler.validate_file_exists(input_path, "输入视频文件")
        if background_path:
            ErrorHandler.validate_file_exists(background_path, "背景图片文件")

        # 确保输出目录存在
        output_dir = os.path.dirname(os.path.abspath(output_path))
        ErrorHandler.validate_directory_exists(output_dir, "输出目录", create_if_missing=True)

        try:
            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                logger.error(f"无法打开视频文件: {input_path}")
                return None

            # 获取视频属性
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            # 设置输出视频编码器
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

            # 加载背景图片（如果提供）
            background = None
            if background_path:
                background = cv2.imread(background_path)
                background = cv2.resize(background, (width, height))

            logger.info(f"开始处理绿幕去除，总帧数: {total_frames}")

            frame_count = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # 处理当前帧
                processed_frame = self._process_frame(frame, background)
                out.write(processed_frame)

                frame_count += 1
                if frame_count % 100 == 0:
                    logger.info(f"已处理 {frame_count}/{total_frames} 帧")

            cap.release()
            out.release()

            logger.info(f"绿幕去除完成: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"绿幕去除失败: {e}")
            return None

    def _process_frame(self, frame, background=None):
        """
        处理单帧图像，去除绿幕

        Args:
            frame: 输入帧
            background: 背景图片（可选）

        Returns:
            numpy.ndarray: 处理后的帧
        """
        # 转换到HSV色彩空间
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # 创建绿色掩码
        mask = cv2.inRange(hsv, self.lower_green, self.upper_green)

        # 形态学操作去除噪声
        kernel = disk(3)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # 膨胀操作确保边缘平滑
        mask = dilation(mask, disk(2)).astype(np.uint8) * 255

        # 高斯模糊掩码边缘
        mask = cv2.GaussianBlur(mask, (5, 5), 0)

        if background is not None:
            # 使用提供的背景
            # 将掩码转换为三通道
            mask_3channel = cv2.merge([mask, mask, mask]) / 255.0

            # 混合前景和背景
            result = frame * (1 - mask_3channel) + background * mask_3channel
            return result.astype(np.uint8)
        else:
            # 使用透明背景（设置为黑色）
            result = frame.copy()
            result[mask > 0] = [0, 0, 0]
            return result

    @handle_errors(error_types={Exception: None})
    def auto_detect_green_range(self, sample_frame):
        """
        自动检测绿幕的HSV范围

        Args:
            sample_frame: 样本帧图像

        Returns:
            tuple: (lower_bound, upper_bound) HSV范围
        """
        try:
            # 转换到HSV
            hsv = cv2.cvtColor(sample_frame, cv2.COLOR_BGR2HSV)

            # 使用K-means聚类找到主要颜色
            pixels = hsv.reshape(-1, 3)
            kmeans = KMeans(n_clusters=5, random_state=42)
            kmeans.fit(pixels)

            # 找到绿色聚类中心
            centers = kmeans.cluster_centers_
            green_center = None

            for center in centers:
                h, s, v = center
                # 检查是否在绿色范围内
                if 35 <= h <= 85 and s > 50 and v > 50:
                    green_center = center
                    break

            if green_center is not None:
                h, s, v = green_center
                # 根据聚类中心调整范围
                self.lower_green = np.array([max(0, h-15), max(0, s-50), max(0, v-50)])
                self.upper_green = np.array([min(179, h+15), 255, 255])

                logger.info(f"自动检测到绿色范围: {self.lower_green} - {self.upper_green}")
                return self.lower_green, self.upper_green
            else:
                logger.warning("未检测到明显的绿色区域，使用默认范围")
                return self.lower_green, self.upper_green

        except Exception as e:
            logger.error(f"自动检测绿色范围失败: {e}")
            return self.lower_green, self.upper_green

class VideoEffects:
    """视频特效处理类"""

    @staticmethod
    @handle_errors(error_types={Exception: None})
    def apply_blur_effect(input_path, output_path, blur_strength=15):
        """
        应用模糊效果

        Args:
            input_path (str): 输入视频路径
            output_path (str): 输出视频路径
            blur_strength (int): 模糊强度

        Returns:
            str: 输出文件路径，失败则返回None
        """
        ErrorHandler.validate_file_exists(input_path, "输入视频文件")

        output_dir = os.path.dirname(os.path.abspath(output_path))
        ErrorHandler.validate_directory_exists(output_dir, "输出目录", create_if_missing=True)

        try:
            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                return None

            fps = int(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # 应用高斯模糊
                blurred_frame = cv2.GaussianBlur(frame, (blur_strength, blur_strength), 0)
                out.write(blurred_frame)

            cap.release()
            out.release()

            logger.info(f"模糊效果应用完成: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"应用模糊效果失败: {e}")
            return None

    @staticmethod
    @handle_errors(error_types={Exception: None})
    def adjust_brightness_contrast(input_path, output_path, brightness=0, contrast=1.0):
        """
        调整视频亮度和对比度

        Args:
            input_path (str): 输入视频路径
            output_path (str): 输出视频路径
            brightness (int): 亮度调整值 (-100 到 100)
            contrast (float): 对比度调整值 (0.5 到 3.0)

        Returns:
            str: 输出文件路径，失败则返回None
        """
        ErrorHandler.validate_file_exists(input_path, "输入视频文件")

        output_dir = os.path.dirname(os.path.abspath(output_path))
        ErrorHandler.validate_directory_exists(output_dir, "输出目录", create_if_missing=True)

        try:
            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                return None

            fps = int(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # 调整亮度和对比度
                adjusted_frame = cv2.convertScaleAbs(frame, alpha=contrast, beta=brightness)
                out.write(adjusted_frame)

            cap.release()
            out.release()

            logger.info(f"亮度对比度调整完成: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"调整亮度对比度失败: {e}")
            return None