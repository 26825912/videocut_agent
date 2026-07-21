"""
GPT-SoVITS模型下载脚本
自动下载GPT-SoVITS所需的预训练模型
"""

import os
import sys
import shutil
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GPTSoVITSModelManager:
    """GPT-SoVITS模型管理器"""

    def __init__(self, models_dir: Optional[str] = None):
        """
        初始化模型管理器

        Args:
            models_dir: 模型存储目录，默认为gpt-sovits/GPT_SoVITS/pretrained_models
        """
        current_dir = Path(__file__).parent
        self.gpt_sovits_dir = current_dir / "gpt-sovits"
        self.pretrained_dir = self.gpt_sovits_dir / "GPT_SoVITS" / "pretrained_models"
        self.pretrained_dir.mkdir(parents=True, exist_ok=True)

        # 模型配置 - 基础模型
        self.base_models = {
            "chinese-roberta-wwm-ext-large": {
                "hf_model_id": "hfl/chinese-roberta-wwm-ext-large",
                "local_path": "chinese-roberta-wwm-ext-large",
                "description": "Chinese RoBERTa Large模型 (用于文本编码)",
                "size": "~1.3GB",
                "required": True
            },
            "chinese-hubert-base": {
                "hf_model_id": "TencentGameMate/chinese-hubert-base",
                "local_path": "chinese-hubert-base",
                "description": "Chinese HuBERT Base模型 (用于音频特征提取)",
                "size": "~400MB",
                "required": True
            }
        }

        # GPT-SoVITS权重文件 - 不同版本
        self.version_weights = {
            "v2Pro": {
                "gpt_weights": {
                    "url": "https://huggingface.co/lj1995/GPT-SoVITS/resolve/main/s1v3.ckpt",
                    "local_path": "s1v3.ckpt",
                    "size": "~600MB"
                },
                "sovits_weights": {
                    "url": "https://huggingface.co/lj1995/GPT-SoVITS/resolve/main/v2Pro/s2Gv2Pro.pth",
                    "local_path": "v2Pro/s2Gv2Pro.pth",
                    "size": "~300MB"
                },
                "description": "GPT-SoVITS v2 Pro版本 (推荐，音质更好)",
                "required": True
            },
            "v2": {
                "gpt_weights": {
                    "url": "https://huggingface.co/lj1995/GPT-SoVITS/resolve/main/gsv-v2final-pretrained/s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt",
                    "local_path": "gsv-v2final-pretrained/s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt",
                    "size": "~600MB"
                },
                "sovits_weights": {
                    "url": "https://huggingface.co/lj1995/GPT-SoVITS/resolve/main/gsv-v2final-pretrained/s2G2333k.pth",
                    "local_path": "gsv-v2final-pretrained/s2G2333k.pth",
                    "size": "~300MB"
                },
                "description": "GPT-SoVITS v2版本 (基础版)",
                "required": False
            },
            "v3": {
                "gpt_weights": {
                    "url": "https://huggingface.co/lj1995/GPT-SoVITS/resolve/main/s1v3.ckpt",
                    "local_path": "s1v3.ckpt",
                    "size": "~600MB"
                },
                "sovits_weights": {
                    "url": "https://huggingface.co/lj1995/GPT-SoVITS/resolve/main/s2Gv3.pth",
                    "local_path": "s2Gv3.pth",
                    "size": "~300MB"
                },
                "description": "GPT-SoVITS v3版本",
                "required": False
            }
        }

    def is_base_model_downloaded(self, model_name: str) -> bool:
        """检查基础模型是否已下载"""
        model_info = self.base_models.get(model_name)
        if not model_info:
            return False

        local_path = self.pretrained_dir / model_info["local_path"]
        if not local_path.exists():
            return False

        # 检查关键文件
        key_files = ["config.json", "pytorch_model.bin"]
        return any((local_path / f).exists() for f in key_files)

    def is_version_weights_downloaded(self, version: str) -> bool:
        """检查版本权重是否已下载"""
        version_info = self.version_weights.get(version)
        if not version_info:
            return False

        gpt_path = self.pretrained_dir / version_info["gpt_weights"]["local_path"]
        sovits_path = self.pretrained_dir / version_info["sovits_weights"]["local_path"]

        return gpt_path.exists() and sovits_path.exists()

    def download_from_hf(self, hf_model_id: str, local_path: Path) -> bool:
        """从Hugging Face下载模型"""
        try:
            from huggingface_hub import snapshot_download

            logger.info(f"正在下载模型: {hf_model_id}")
            local_path.mkdir(parents=True, exist_ok=True)

            snapshot_download(
                repo_id=hf_model_id,
                local_dir=str(local_path),
                local_dir_use_symlinks=False
            )

            logger.info(f"模型下载完成: {local_path}")
            return True

        except ImportError:
            logger.error("huggingface_hub未安装，请运行: pip install huggingface_hub")
            return False
        except Exception as e:
            logger.error(f"模型下载失败 {hf_model_id}: {e}")
            return False

    def download_file(self, url: str, local_path: Path) -> bool:
        """下载单个文件"""
        try:
            import requests
            from tqdm import tqdm

            logger.info(f"正在下载: {url}")
            local_path.parent.mkdir(parents=True, exist_ok=True)

            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))

            with open(local_path, 'wb') as f, tqdm(
                total=total_size,
                unit='B',
                unit_scale=True,
                desc=local_path.name
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))

            logger.info(f"文件下载完成: {local_path}")
            return True

        except Exception as e:
            logger.error(f"文件下载失败 {url}: {e}")
            if local_path.exists():
                local_path.unlink()
            return False

    def download_base_model(self, model_name: str, force: bool = False) -> bool:
        """下载基础模型"""
        model_info = self.base_models.get(model_name)
        if not model_info:
            logger.error(f"未知的模型: {model_name}")
            return False

        if not force and self.is_base_model_downloaded(model_name):
            logger.info(f"模型已存在: {model_name}")
            return True

        local_path = self.pretrained_dir / model_info["local_path"]
        return self.download_from_hf(model_info["hf_model_id"], local_path)

    def download_version_weights(self, version: str, force: bool = False) -> bool:
        """下载版本权重文件"""
        version_info = self.version_weights.get(version)
        if not version_info:
            logger.error(f"未知的版本: {version}")
            return False

        if not force and self.is_version_weights_downloaded(version):
            logger.info(f"版本权重已存在: {version}")
            return True

        success = True

        # 下载GPT权重
        gpt_url = version_info["gpt_weights"]["url"]
        gpt_path = self.pretrained_dir / version_info["gpt_weights"]["local_path"]
        if not gpt_path.exists() or force:
            if not self.download_file(gpt_url, gpt_path):
                success = False

        # 下载SoVITS权重
        sovits_url = version_info["sovits_weights"]["url"]
        sovits_path = self.pretrained_dir / version_info["sovits_weights"]["local_path"]
        if not sovits_path.exists() or force:
            if not self.download_file(sovits_url, sovits_path):
                success = False

        return success

    def download_required_models(self) -> bool:
        """下载所有必需的模型"""
        success = True

        logger.info("=" * 60)
        logger.info("开始下载GPT-SoVITS必需模型...")
        logger.info("=" * 60)

        # 下载基础模型
        logger.info("\n[1/2] 下载基础模型...")
        for model_name, model_info in self.base_models.items():
            if model_info.get("required", False):
                logger.info(f"\n下载: {model_name} ({model_info['size']})")
                logger.info(f"描述: {model_info['description']}")
                if not self.download_base_model(model_name):
                    logger.error(f"[FAIL] 基础模型下载失败: {model_name}")
                    success = False
                else:
                    logger.info(f"[OK] 下载完成: {model_name}")

        # 下载必需的版本权重
        logger.info("\n[2/2] 下载版本权重...")
        for version, version_info in self.version_weights.items():
            if version_info.get("required", False):
                logger.info(f"\n下载: {version} 版本")
                logger.info(f"描述: {version_info['description']}")
                if not self.download_version_weights(version):
                    logger.error(f"[FAIL] 版本权重下载失败: {version}")
                    success = False
                else:
                    logger.info(f"[OK] 下载完成: {version}")

        logger.info("\n" + "=" * 60)
        if success:
            logger.info("[OK] 所有必需模型下载完成!")
        else:
            logger.error("[!!] 部分模型下载失败，请检查网络连接或手动下载")
        logger.info("=" * 60)

        return success

    def list_models(self):
        """列出所有模型及其状态"""
        print("\n" + "=" * 80)
        print("GPT-SoVITS 模型状态")
        print("=" * 80)

        print("\n基础模型:")
        print("-" * 80)
        for model_name, model_info in self.base_models.items():
            status = "[OK] 已下载" if self.is_base_model_downloaded(model_name) else "[  ] 未下载"
            required = " [必需]" if model_info.get("required") else " [可选]"
            print(f"{status:15} {model_name:40} {model_info['size']:10}{required}")
            print(f"                {model_info['description']}")

        print("\n版本权重:")
        print("-" * 80)
        for version, version_info in self.version_weights.items():
            status = "[OK] 已下载" if self.is_version_weights_downloaded(version) else "[  ] 未下载"
            required = " [必需]" if version_info.get("required") else " [可选]"
            gpt_size = version_info["gpt_weights"]["size"]
            sovits_size = version_info["sovits_weights"]["size"]
            total_size = f"{gpt_size}+{sovits_size}"
            print(f"{status:12} {version:40} {total_size:15}{required}")
            print(f"             {version_info['description']}")

        print("\n" + "=" * 80)
        print(f"模型存储路径: {self.pretrained_dir}")
        print("=" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(description="GPT-SoVITS模型下载工具")
    parser.add_argument("--required", action="store_true", help="只下载必需的模型")
    parser.add_argument("--all", action="store_true", help="下载所有模型")
    parser.add_argument("--version", help="下载指定版本 (v2, v2Pro, v3)")
    parser.add_argument("--base-only", action="store_true", help="只下载基础模型")
    parser.add_argument("--force", action="store_true", help="强制重新下载")
    parser.add_argument("--list", action="store_true", help="列出所有模型状态")

    args = parser.parse_args()

    manager = GPTSoVITSModelManager()

    if args.list:
        manager.list_models()
        return

    if args.base_only:
        logger.info("下载基础模型...")
        success = True
        for model_name in manager.base_models.keys():
            if not manager.download_base_model(model_name, args.force):
                success = False
        sys.exit(0 if success else 1)

    if args.version:
        logger.info(f"下载 {args.version} 版本权重...")
        success = manager.download_version_weights(args.version, args.force)
        sys.exit(0 if success else 1)

    if args.required:
        success = manager.download_required_models()
        sys.exit(0 if success else 1)

    if args.all:
        logger.info("下载所有模型...")
        success = True

        # 下载所有基础模型
        for model_name in manager.base_models.keys():
            if not manager.download_base_model(model_name, args.force):
                success = False

        # 下载所有版本权重
        for version in manager.version_weights.keys():
            if not manager.download_version_weights(version, args.force):
                success = False

        sys.exit(0 if success else 1)

    # 默认显示帮助
    parser.print_help()
    print("\n提示: 运行 'python download_gpt_sovits.py --required' 下载必需的模型")
    print("      运行 'python download_gpt_sovits.py --list' 查看模型状态")


if __name__ == "__main__":
    main()
