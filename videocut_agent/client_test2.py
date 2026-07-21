import requests
import json
import sys
import time

# 配置
BASE_URL = "http://localhost:8000"

# 颜色代码，用于美化输出
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'

def print_step(msg):
    print(f"\n{Colors.HEADER}=== {msg} ==={Colors.ENDC}")

def check_server():
    """1. 测试服务健康状态"""
    print_step("1. 检查服务健康状态 (/health)")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print(f"{Colors.GREEN}✅ 服务运行正常: {response.json()}{Colors.ENDC}")
            return True
        else:
            print(f"{Colors.RED}❌ 服务异常: {response.status_code}{Colors.ENDC}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"{Colors.RED}❌ 无法连接到服务器。请确保 main.py 正在运行 (localhost:8000){Colors.ENDC}")
        return False

def get_agents_list():
    """2. 获取可用工具列表"""
    print_step("2. 获取智能体工具列表 (/agents/list)")
    try:
        response = requests.get(f"{BASE_URL}/agents/list")
        if response.status_code == 200:
            data = response.json()
            print(f"成功获取，共 {data.get('count')} 个工具:")
            for agent in data.get('agents', []):
                print(f"  - {Colors.BLUE}{agent['name']}{Colors.ENDC}: {agent['description'][:50]}...")
        else:
            print(f"{Colors.RED}❌ 获取失败: {response.text}{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.RED}❌ 错误: {e}{Colors.ENDC}")

def test_sync_query(query="你好，请介绍一下你自己"):
    """3. 测试同步查询"""
    print_step("3. 测试同步查询接口 (/query)")
    print(f"发送问题: {query}")
    
    payload = {
        "query": query,
        "model": "gemini-2.5-pro",
        "temperature": 0.7
    }
    
    start_time = time.time()
    try:
        response = requests.post(f"{BASE_URL}/query", json=payload)
        duration = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print(f"{Colors.GREEN}✅ 请求成功 ({duration:.2f}s){Colors.ENDC}")
                print(f"回复内容: {result['result']}")
            else:
                print(f"{Colors.RED}❌ 业务逻辑错误: {result.get('error')}{Colors.ENDC}")
        else:
            print(f"{Colors.RED}❌ HTTP错误: {response.status_code} - {response.text}{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.RED}❌ 请求异常: {e}{Colors.ENDC}")

def test_stream_query(query="帮我生成一个关于雨天咖啡馆的视频文案"):
    """4. 测试流式查询"""
    print_step("4. 测试流式查询接口 (/query/stream)")
    print(f"发送问题: {query}")
    print(f"{Colors.YELLOW}正在接收实时流...{Colors.ENDC}\n")

    payload = {
        "query": query,
        "model": "gemini-2.5-pro"
    }

    try:
        # stream=True 开启流式读取
        with requests.post(f"{BASE_URL}/query/stream", json=payload, stream=True) as response:
            if response.status_code != 200:
                print(f"{Colors.RED}❌ 连接失败: {response.status_code}{Colors.ENDC}")
                return

            # 逐行读取 SSE 数据
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('data: '):
                        # 解析 JSON
                        json_str = decoded_line.replace('data: ', '', 1)
                        try:
                            event = json.loads(json_str)
                            event_type = event.get("type")
                            timestamp = event.get("timestamp", "").split("T")[-1][:8]

                            # 根据不同事件类型打印不同颜色
                            if event_type == "tool_start":
                                print(f"{Colors.BLUE}[{timestamp} 工具开始]{Colors.ENDC} 调用 {event.get('tool')}...")
                                print(f"   输入: {event.get('input')[:100]}...")
                            
                            elif event_type == "tool_end":
                                print(f"{Colors.GREEN}[{timestamp} 工具结束]{Colors.ENDC} 耗时: {event.get('duration'):.2f}s")
                                print(f"   输出: {event.get('output')}")
                            
                            elif event_type == "final_result":
                                print(f"\n{Colors.HEADER}=== 最终结果 ==={Colors.ENDC}")
                                print(event.get("result"))
                            
                            elif event_type == "error":
                                print(f"{Colors.RED}[错误] {event.get('error')}{Colors.ENDC}")
                                
                        except json.JSONDecodeError:
                            print(f"无法解析数据: {decoded_line}")
    except Exception as e:
        print(f"{Colors.RED}❌ 流式请求异常: {e}{Colors.ENDC}")

if __name__ == "__main__":
    # 1. 检查服务是否在线
    if not check_server():
        sys.exit(1)
    
    # 2. 获取工具列表
    get_agents_list()
    
    # 3. 简单的同步测试 (快速)
    test_sync_query(query="hi")
    
    # 4. 复杂的流式测试 (模拟工具调用)
    # 注意：这需要你的后端真实连接了 LLM 并且 AgentManager 能正常工作
    # 这里的 query 设计为触发 'videoscript_agent' 或其他工具
    test_stream_query(query="请帮我写一个关于夏天海边的短视频脚本")