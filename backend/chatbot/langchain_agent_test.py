import requests
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType, Tool

# DeepSeek API 配置（与 views.py 保持一致）
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_API_KEY = "sk-a853c03e01e64799a3124528efd82441"

# 计划生成 Tool

def generate_plan_tool_func(goal: str) -> str:
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
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": plan_prompt}
        ]
    }
    try:
        resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        plan_content = resp.json()['choices'][0]['message']['content'].strip()
        return plan_content
    except Exception as e:
        return f"计划生成失败: {str(e)}"

generate_plan_tool = Tool(
    name="GenerateReadingPlan",
    func=generate_plan_tool_func,
    description="根据用户目标生成详细的阅读计划"
)

def hello_tool_func(query: str) -> str:
    return f"你好，你刚才说：{query}"

hello_tool = Tool(
    name="HelloTool",
    func=hello_tool_func,
    description="简单回声工具"
)

llm = ChatOpenAI(
    openai_api_key=DEEPSEEK_API_KEY,
    openai_api_base="https://api.deepseek.com/v1",
    model="deepseek-chat"
)

agent = initialize_agent(
    tools=[generate_plan_tool, hello_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

if __name__ == "__main__":
    print(agent.run("请帮我制定一个关于中国古诗词的7天阅读计划"))
