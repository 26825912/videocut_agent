from pydantic import BaseModel, Field
from typing import Annotated, Literal, TypedDict, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import AnyMessage, ToolMessage
from langgraph.graph.operator import add
from langgraph.graph.state import State




class WorkflowState(TypedDict):
    # 初始输入
    input_url: str
    target_duration: str
    
    # 中间产物 (由节点填充)
    script_data: Optional[dict]  # 函数1的结果
    audio_path: Optional[str]    # 函数2的结果
    final_video_path: Optional[str] # 函数3的结果



workflow = StateGraph(WorkflowState)

# 添加节点
workflow.add_node("extract_info", get_video_info_node)
workflow.add_node("gen_audio", generate_audio_node)
workflow.add_node("make_video", synthesize_video_node)

# 添加边 (定义线性执行顺序)
# 逻辑：开始 -> 提取信息 -> 生成音频 -> 合成视频 -> 结束
workflow.add_edge(START, "extract_info")
workflow.add_edge("extract_info", "gen_audio")
workflow.add_edge("gen_audio", "make_video")
workflow.add_edge("make_video", END)

# 编译应用
app = workflow.compile()