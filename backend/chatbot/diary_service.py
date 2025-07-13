import datetime
from .agent import llm

def generate_diary_summary(history, message, current_plan, today_task):
    """
    基于历史对话、用户输入、计划内容和今日任务，生成AI学习日记摘要。
    输出日记要求自然、具体、有个人色彩，兼具回顾与反思。
    """
    prompt = f"""
你是用户的智能学习日记助手，现在请你帮助用户撰写一篇“真实自然的学习日记”。你需要模仿真实学生的语气，总结今日任务，回顾完成情况，并加入真实感受或思考。

请注意以下要求：
1. 口吻要自然真实，使用第一人称，像用户自己写的；
2. 不要机械地列出任务，而要用生活化、内心化的语言写；
3. 日记内容应包括以下4部分：
   - 今日任务的简单回顾（今日任务：{today_task}）
   - 实际完成了哪些？有没有偏差？（可根据“用户输入”和“历史对话”判断）
   - 今天学习过程中的感受、困惑、启发、想法；
   - 如果发现前面计划有遗漏/错误，请自然地提到并补充或修正；
4. 语言可以适度口语化，有轻微情绪/犹豫/突破都可以体现。

上下文信息如下：

【历史对话】：
{history}

【用户输入】：
{message}

【阅读计划内容】：
{current_plan}

请根据这些信息生成一篇自然、具体、有情绪、有思考的学习日记。
"""
    diary_reply = llm.invoke(prompt)
    return diary_reply.content if hasattr(diary_reply, 'content') else str(diary_reply)
