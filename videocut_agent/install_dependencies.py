#!/usr/bin/env python3
"""
安装VideoAgent系统所需的依赖包
"""
import subprocess
import sys

def install_package(package):
    """安装单个包"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} 安装成功")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ {package} 安装失败")
        return False

def main():
    """安装所有必需的依赖"""
    print("🚀 开始安装VideoAgent系统依赖...")

    # 核心依赖
    core_packages = [
        "langchain",
        "langchain-core",
        "langchain-openai",
        "fastapi",
        "uvicorn[standard]",
        "pydantic",
        "python-dotenv",
        "streamlit",
        "requests"
    ]

    # 视频处理依赖
    video_packages = [
        "opencv-python",
        "moviepy",
        "pydub",
        "pillow",
        "numpy",
        "scikit-image",
        "scikit-learn"
    ]

    # Azure语音服务
    azure_packages = [
        "azure-cognitiveservices-speech"
    ]

    # 其他工具
    other_packages = [
        "tqdm",
        "pysubs2",
        "pathlib"
    ]

    all_packages = core_packages + video_packages + azure_packages + other_packages

    failed_packages = []

    for package in all_packages:
        if not install_package(package):
            failed_packages.append(package)

    print("\n" + "="*50)
    if failed_packages:
        print(f"❌ 以下包安装失败: {', '.join(failed_packages)}")
        print("请手动安装这些包或检查网络连接")
    else:
        print("✅ 所有依赖安装成功！")
        print("\n现在您可以运行:")
        print("  python server.py        # API 服务器 (支持流式输出)")

if __name__ == "__main__":
    main()