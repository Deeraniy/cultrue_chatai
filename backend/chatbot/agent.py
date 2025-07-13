# 导入所需的第三方库和标准库
import requests  # 用于发送HTTP请求（本文件暂未直接用到）
from langchain_openai import ChatOpenAI  # LangChain对OpenAI/DeepSeekChat模型的封装
from langchain.agents import initialize_agent, AgentType, Tool  # 智能体相关工具
from langchain.memory import ConversationBufferWindowMemory  # 对话记忆窗口
import datetime  # 处理日期时间
import json  # 处理JSON数据

# DeepSeekChat API的基础信息（API地址和密钥）
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_API_KEY = ""

# ========== 1. 阅读计划生成工具函数 ==========
def generate_plan_tool_func(goal: str) -> str:
    """
    根据用户目标生成详细的阅读计划，输出为JSON结构。
    该函数会构造prompt并调用llm_plan（低temperature，结构化输出更稳定）。
    goal: 用户的阅读目标或兴趣描述
    返回：模型生成的JSON格式阅读计划
    """
    plan_prompt = f"""
你是一名阅读规划师。请根据用户的目标或兴趣，为其制定一个详细的阅读计划，包括推荐书目、章节划分、建议完成天数和每日阅读任务。请用JSON格式输出，例如：
{{
  "book": "书名",
  "total_days": 7,
  "daily_plan": [
    {{"day": 1, "task": "阅读第1-2章"}},
    ...
  ]
}}
用户目标：{goal}
"""
    try:
        # 使用结构化任务专用的llm_plan（temperature=0.3，输出更规范）
        plan_content = llm_plan.invoke(plan_prompt)
        # 兼容不同返回类型，优先取content属性
        return plan_content.content if hasattr(plan_content, 'content') else str(plan_content)
    except Exception as e:
        return f"计划生成失败: {str(e)}"

# 将上述函数封装为LangChain工具，便于agent调用
# 这样agent可以在对话中自动调用该工具生成计划
generate_plan_tool = Tool(
    name="GenerateReadingPlan",
    func=generate_plan_tool_func,
    description="根据用户目标生成详细的阅读计划"
)

# ========== 2. 大语言模型实例化 ==========
# 对话/日记等自然语言任务，使用较高temperature，提升表达多样性
llm_chat = ChatOpenAI(
    openai_api_key=DEEPSEEK_API_KEY,  # API密钥
    openai_api_base="https://api.deepseek.com/v1",  # API地址
    model="deepseek-chat",  # 指定使用DeepSeekChat模型
    temperature=0.7,      # 对话场景，生成更灵活
    max_tokens=1024       # 控制生成内容长度
)

# 结构化任务（如阅读计划生成），使用较低temperature，保证输出稳定
llm_plan = ChatOpenAI(
    openai_api_key=DEEPSEEK_API_KEY,
    openai_api_base="https://api.deepseek.com/v1",
    model="deepseek-chat",
    temperature=0.3,      # 结构化场景，输出更规范
    max_tokens=1024
)

# ========== 3. 多用户对话记忆管理 ==========
# 用于存储每个用户的对话历史，实现多用户并发和上下文记忆
user_memories = {}

def get_agent_with_memory(user_id, current_book=None, current_plan=None):
    """
    为每个用户维护独立的对话记忆（窗口大小k=5），并动态生成system prompt。
    支持结合当前阅读计划，主动引导用户打卡和反思。
    user_id: 用户唯一标识
    current_book: 当前阅读的书名
    current_plan: 当前阅读计划（JSON字符串）
    返回：配置好记忆和工具的LangChain智能体
    """
    # 如果该用户还没有记忆，则新建一个窗口记忆（只保留最近5轮）
    if user_id not in user_memories:
        user_memories[user_id] = ConversationBufferWindowMemory(
            memory_key="chat_history",
            k=5,  # 只保留最近5轮对话
            return_messages=True
        )
    memory = user_memories[user_id]

    # 构造system prompt，包含计划信息和今日任务
    today = datetime.date.today().strftime('%Y-%m-%d')
    plan_info = ""
    today_task = ""
    if current_book and current_plan:
        try:
            plan_json = json.loads(current_plan)
            plan_info = f"当前阅读书籍：《{current_book}》，计划如下：{current_plan}"
            # 查找今日任务
            if 'daily_plan' in plan_json:
                start_date = plan_json.get('start_date')
                if start_date:
                    start_dt = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
                    today_dt = datetime.date.today()
                    day_num = (today_dt - start_dt).days + 1
                else:
                    day_num = None
                if day_num:
                    for d in plan_json['daily_plan']:
                        if d.get('day') == day_num:
                            today_task = f"今天是第{day_num}天，任务：{d.get('task')}"
                            break
                if not today_task:
                    today_task = "请确认你的计划起始日期，以便我为你匹配今日任务。"
        except Exception as e:
            plan_info = f"计划解析失败: {str(e)}"
    else:
        plan_info = "你还没有选择当前书籍或计划。"

    # 生成system prompt，指导AI主动关心用户计划进展
    system_prompt = f"""
你是用户的智能阅读助理。{plan_info}\n{today_task}\n今天日期是{today}。请结合计划内容主动询问用户今天的任务完成情况，并引导用户分享感悟。
"""

    # 初始化LangChain智能体
    # - tools: 可用工具（如生成阅读计划）
    # - llm: 对话/日记等任务用llm_chat（temperature=0.7）
    # - memory: 用户独立对话记忆
    # - agent类型: CONVERSATIONAL_REACT_DESCRIPTION，支持工具调用和多轮对话
    # - agent_kwargs: 注入system prompt
    agent = initialize_agent(
        tools=[generate_plan_tool],
        llm=llm_chat,  # 对话/日记等任务用llm_chat（temperature=0.7）
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        memory=memory,
        verbose=True,  # 输出详细日志，便于调试
        handle_parsing_errors=True,  # 自动处理解析异常
        agent_kwargs={
            "input_variables": ["input", "chat_history"],
            "system_message": system_prompt
        }
    )
    return agent

# ========== 4. 示例主程序 ==========
# 演示如何用agent进行多轮对话，记忆用户偏好
if __name__ == "__main__":
    test_user = "test_user"
    agent = get_agent_with_memory(test_user)
    print(agent.run("你好，我喜欢简短的诗歌"))  # 第一次对话，输入偏好
    print(agent.run("帮我推荐一首诗"))        # 第二次对话，AI应结合记忆推荐
    print(agent.run("你还记得我喜欢什么吗？")) # 第三次对话，测试记忆能力 