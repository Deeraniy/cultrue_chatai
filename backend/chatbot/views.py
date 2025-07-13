from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
import requests
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import LiteratureEmotionSummary, ReadingPlan, DailyStatus, UserEmotionHistory, Conversation, Message
import os
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import threading
from .agent import get_agent_with_memory, llm  # 导入 agent 和 get_agent_with_memory
import datetime
import json
from .diary_api import standardize_plan_json
from django.db.models import Q
import pandas as pd
import re

# Create your views here.

@api_view(['POST'])
def chatbot_api(request):
    user_message = request.data.get('message', '')
    # mock reply
    reply = f"你说的是：{user_message}，这是智能回复。"
    return Response({"reply": reply})

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_API_KEY = "sk-a853c03e01e64799a3124528efd82441"

# 全局缓存
FAISS_INDEX = None
FAISS_META = None
EMBEDDING_MODEL = None
recommend_cache = {}
cache_lock = threading.Lock()

# 加载FAISS和meta
def load_faiss():
    global FAISS_INDEX, FAISS_META
    if FAISS_INDEX is None or FAISS_META is None:
        faiss_path = os.path.join(os.path.dirname(__file__), '../literature_faiss.index')
        meta_path = os.path.join(os.path.dirname(__file__), '../literature_meta.pkl')
        FAISS_INDEX = faiss.read_index(faiss_path)
        with open(meta_path, 'rb') as f:
            FAISS_META = pickle.load(f)
    return FAISS_INDEX, FAISS_META

# 加载embedding模型
def load_embedding_model():
    global EMBEDDING_MODEL
    if EMBEDDING_MODEL is None:
        # 可替换为更适合中文的模型
        EMBEDDING_MODEL = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    return EMBEDDING_MODEL

# 推荐理由缓存
def get_recommend_reason_cache(user_text, liter_name):
    key = f"{user_text}||{liter_name}"
    with cache_lock:
        return recommend_cache.get(key)

def set_recommend_reason_cache(user_text, liter_name, reason):
    key = f"{user_text}||{liter_name}"
    with cache_lock:
        recommend_cache[key] = reason

def get_recommend_reason(sentiment, liter_type_name):
    if sentiment == 'positive':
        return f"你现在心情不错，推荐这部{liter_type_name}作品，继续保持好心情！"
    elif sentiment == 'negative':
        return f"你现在心情低落，推荐这部{liter_type_name}作品，希望能温暖你。"
    else:
        return f"为你推荐一部经典{liter_type_name}作品，丰富你的阅读体验。"

@csrf_exempt
def recommend_literature(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)
    user_text = request.POST.get('text') or request.GET.get('text')
    if not user_text:
        return JsonResponse({'error': 'No text provided'}, status=400)

    # 1. 情感分析
    prompt = f"请判断下面这句话的情感倾向，只返回positive、neutral或negative三种结果，不要解释：{user_text}"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    try:
        resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        sentiment = resp.json()['choices'][0]['message']['content'].strip().lower()
        if sentiment not in ['positive', 'neutral', 'negative']:
            sentiment = 'neutral'
    except Exception as e:
        return JsonResponse({'error': '情感分析API调用失败', 'detail': str(e)}, status=500)

    # 2. RAG检索（用缓存）
    index, meta = load_faiss()
    model = load_embedding_model()
    user_vec = model.encode([user_text], convert_to_numpy=True)
    D, I = index.search(user_vec, 5)
    rag_results = [meta[i] for i in I[0]]

    # 3. 生成推荐理由（带缓存）
    recommend_list = []
    for item in rag_results:
        liter_name = item['liter_name']
        reason = get_recommend_reason_cache(user_text, liter_name)
        if reason is None:
            rag_prompt = f"用户说：{user_text}\n推荐作品：{liter_name}\n请结合用户心情和作品内容，生成一句推荐理由。"
            rec_payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "user", "content": rag_prompt}
                ]
            }
            try:
                rec_resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=rec_payload, timeout=10)
                rec_resp.raise_for_status()
                reason = rec_resp.json()['choices'][0]['message']['content'].strip()
            except Exception as e:
                reason = f"为你推荐这部作品：{liter_name}。"
            set_recommend_reason_cache(user_text, liter_name, reason)
        recommend_list.append({
            'liter_id': item['liter_id'],
            'liter_name': liter_name,
            'reason': reason
        })
    return JsonResponse({'sentiment': sentiment, 'recommend': recommend_list})

def extract_json_from_text(text):
    match = re.search(r'```json([\s\S]+?)```', text)
    if match:
        return match.group(1).strip()
    match2 = re.search(r'({[\s\S]+})', text)
    if match2:
        return match2.group(1).strip()
    return None

@csrf_exempt
@api_view(['POST'])
def generate_plan(request):
    user_id = request.data.get('user_id')
    user_goal = request.data.get('goal')
    if not user_id or not user_goal:
        return JsonResponse({'error': 'user_id和goal为必填项'}, status=400)

    # 用 LangChain Agent 生成计划
    try:
        plan_content = get_agent_with_memory(user_id).run(f"请为我制定一个阅读计划，目标：{user_goal}")
    except Exception as e:
        return JsonResponse({'error': '生成计划失败', 'detail': str(e)}, status=500)

    # 提取JSON代码块
    json_candidate = extract_json_from_text(plan_content)
    if json_candidate:
        new_plan = json_candidate
    else:
        # 兜底
        plan_json = {
            "book": user_goal or "未知书籍",
            "total_days": 3,
            "daily_plan": [
                {"day": 1, "task": "请自定义第1天任务"},
                {"day": 2, "task": "请自定义第2天任务"},
                {"day": 3, "task": "请自定义第3天任务"}
            ]
        }
        new_plan = json.dumps(plan_json, ensure_ascii=False)

    # 存入数据库
    ReadingPlan.objects.create(
        user_id=user_id,
        plan_content=plan_content,
        current_progress="未开始"
    )
    return JsonResponse({'plan': plan_content, 'new_plan': new_plan})

@csrf_exempt
@api_view(['POST'])
def my_plans(request):
    user_id = request.data.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'user_id为必填项'}, status=400)
    plans = ReadingPlan.objects.filter(user_id=user_id).order_by('-last_update')
    plan_list = []
    for plan in plans:
        plan_list.append({
            'plan_id': plan.id if hasattr(plan, 'id') else None,
            'id': plan.id,
            'plan_content': plan.plan_content,
            'current_progress': plan.current_progress,
            'last_update': plan.last_update,
            'book': plan.book if hasattr(plan, 'book') else '',
            'start_date': plan.start_date if hasattr(plan, 'start_date') else '',
            'end_date': plan.end_date if hasattr(plan, 'end_date') else '',
            'is_active': plan.is_active if hasattr(plan, 'is_active') else True,
        })
    return JsonResponse({'plans': plan_list})

# 情感分析函数
def analyze_sentiment(text):
    """调用 DeepSeek API 返回情感标签和分数"""
    if not text:
        return 'neutral', 0.5
    prompt = f"请判断下面这句话的情感倾向，并给出0-1的分数，1为极其积极，0为极其消极。只返回json：{{\"sentiment\": \"positive/neutral/negative\", \"score\": 0.xx}}，不要解释：{text}"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    try:
        resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        content = resp.json()['choices'][0]['message']['content']
        result = json.loads(content.replace('```json','').replace('```','').strip())
        return result.get('sentiment', 'neutral'), float(result.get('score', 0.5))
    except Exception:
        return 'neutral', 0.5

@csrf_exempt
@api_view(['POST'])
def join_plan(request):
    user_id = request.data.get('user_id')
    book_name = request.data.get('book_name') or request.data.get('liter_name')
    user_text = request.data.get('goal') or request.data.get('text')
    if not user_id or not book_name:
        return JsonResponse({'error': 'user_id和book_name（或liter_name）为必填项'}, status=400)
    # 情感分析
    sentiment, score = analyze_sentiment(user_text)
    # 检查是否已存在同一本书的计划
    existing = ReadingPlan.objects.filter(user_id=user_id, book=book_name, is_active=True).first()
    if existing:
        return JsonResponse({'plan': existing.plan_content, 'message': '该书已在你的阅读计划中'})
    # 1. 调用大模型生成计划
    plan_prompt = f"""
你是一名阅读规划师。请为用户制定《{book_name}》的详细阅读计划，包括章节划分、建议完成天数和每日阅读任务。请用JSON格式输出，例如：
{{
  "book": "{book_name}",
  "total_days": 7,
  "daily_plan": [
    {{"day": 1, "task": "阅读第1-2章"}},
    ...
  ]
}}
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
    except Exception as e:
        return JsonResponse({'error': '生成计划失败', 'detail': str(e)}, status=500)
    # 提取JSON代码块
    json_candidate = extract_json_from_text(plan_content)
    if json_candidate:
        new_plan = json_candidate
    else:
        # 兜底
        plan_json = {
            "book": book_name or "未知书籍",
            "total_days": 3,
            "daily_plan": [
                {"day": 1, "task": "请自定义第1天任务"},
                {"day": 2, "task": "请自定义第2天任务"},
                {"day": 3, "task": "请自定义第3天任务"}
            ]
        }
        new_plan = json.dumps(plan_json, ensure_ascii=False)
    # 2. 解析计划内容，补全必填字段
    try:
        plan_json = json.loads(plan_content.replace('```json', '').replace('```', '').strip())
    except Exception:
        plan_json = {}
    book = plan_json.get('book', book_name)
    start_date = plan_json.get('start_date')
    if not start_date:
        start_date = datetime.date.today().strftime('%Y-%m-%d')
    total_days = plan_json.get('total_days', 7)
    start_dt = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
    end_dt = start_dt + datetime.timedelta(days=total_days-1)
    # 标准化计划内容
    plan_json = standardize_plan_json(plan_json, None)
    plan_content_db = json.dumps(plan_json, ensure_ascii=False)
    # 3. 新建计划
    ReadingPlan.objects.filter(user_id=user_id, book=book, is_active=True).update(is_active=False)
    plan = ReadingPlan.objects.create(
        user_id=user_id,
        book=book,
        start_date=start_date,
        end_date=end_dt,
        plan_content=plan_content_db,
        current_progress="未开始",
        is_active=True,
        initial_emotion=sentiment,
        initial_emotion_score=score
    )
    # 写入用户情绪历史
    UserEmotionHistory.objects.create(
        user_id=user_id,
        date=datetime.date.today(),
        source='加入计划',
        plan=plan,
        book=book,
        emotion=sentiment,
        emotion_score=score,
        raw_text=user_text
    )
    return JsonResponse({'plan': plan_content, 'new_plan': new_plan})

@csrf_exempt
@api_view(['POST'])
def agent_chat(request):
    user_id = request.data.get('user_id')
    message = request.data.get('message')
    current_book = request.data.get('current_book')
    current_plan = request.data.get('current_plan')
    if not user_id or not message:
        return JsonResponse({'error': 'user_id和message为必填项'}, status=400)
    try:
        agent = get_agent_with_memory(user_id, current_book=current_book, current_plan=current_plan)
        reply = agent.run(message)
        return JsonResponse({'reply': reply})
    except Exception as e:
        return JsonResponse({'error': '对话失败', 'detail': str(e)}, status=500)

# 用户历史对话缓存
user_direct_memories = {}

@csrf_exempt
@api_view(['POST'])
def direct_chat(request):
    user_id = request.data.get('user_id')
    message = request.data.get('message')
    current_book = request.data.get('current_book')
    plan_id = request.data.get('plan_id')
    # 情感分析
    sentiment, score = analyze_sentiment(message)
    if not user_id or not message:
        return JsonResponse({'error': 'user_id和message为必填项'}, status=400)
    # 取历史对话
    if user_id not in user_direct_memories:
        user_direct_memories[user_id] = []
    history = user_direct_memories[user_id]
    # 获取当前激活计划
    plan = None
    if plan_id:
        plan = ReadingPlan.objects.filter(id=plan_id, user_id=user_id).first()
    else:
        plan = ReadingPlan.objects.filter(user_id=user_id, book=current_book, is_active=True).first()
    plan_info = ""
    today_task = ""
    today = datetime.date.today().strftime('%Y-%m-%d')
    if plan:
        try:
            plan_json = json.loads(plan.plan_content)
            plan_info = f"当前书籍：《{plan.book}》，计划如下：{plan.plan_content}"
            if 'daily_plan' in plan_json:
                start_date = plan.start_date
                today_dt = datetime.date.today()
                day_num = (today_dt - start_date).days + 1
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
    # 拼prompt
    prompt = f"你是用户的智能阅读助理。{plan_info}\n{today_task}\n今天日期是{today}。历史对话：{history}\n用户：{message}\n请你结合计划内容和日期，主动告诉用户今天的任务，并引导用户反馈感悟。"
    # 发送给LLM
    reply = llm.invoke(prompt)
    reply_text = reply.content if hasattr(reply, 'content') else str(reply)
    # 存历史
    user_direct_memories[user_id].append(f"用户：{message}")
    user_direct_memories[user_id].append(f"助手：{reply_text}")
    # AI自动打卡：简单关键词识别
    complete_keywords = ['完成', '打卡', '已读', '已完成', '做完', '搞定', 'ok', 'done']
    auto_diary = ""
    next_suggestion = ""
    if any(k in message for k in complete_keywords) and plan:
        # 自动打卡
        DailyStatus.objects.update_or_create(
            user_id=user_id, plan=plan, book=plan.book, date=today,
            defaults={'actual_progress': 'AI对话自动打卡', 'remark': '', 'emotion': sentiment, 'emotion_score': score}
        )
        # 写入用户情绪历史
        UserEmotionHistory.objects.create(
            user_id=user_id,
            date=today,
            source='对话打卡',
            plan=plan,
            book=plan.book,
            emotion=sentiment,
            emotion_score=score,
            raw_text=message
        )
        # 生成学习笔记摘要
        diary_prompt = f"用户说：{message}\n请用简洁的方式总结今天的学习内容、进度、遇到的问题，输出一段学习笔记。"
        diary_reply = llm.invoke(diary_prompt)
        auto_diary = diary_reply.content if hasattr(diary_reply, 'content') else str(diary_reply)
        # 生成下一步建议或测验
        suggestion_prompt = f"用户今天完成了：{message}\n请为用户生成下一步学习建议或一个小测验。"
        suggestion_reply = llm.invoke(suggestion_prompt)
        next_suggestion = suggestion_reply.content if hasattr(suggestion_reply, 'content') else str(suggestion_reply)
    # 记录所有对话情绪（不管是否打卡）
    UserEmotionHistory.objects.create(
        user_id=user_id,
        date=datetime.date.today(),
        source='对话',
        plan=plan,
        book=current_book,
        emotion=sentiment,
        emotion_score=score,
        raw_text=message
    )
    return JsonResponse({'reply': reply_text, 'auto_diary': auto_diary, 'next_suggestion': next_suggestion})

@csrf_exempt
@api_view(['POST'])
def mark_day(request):
    user_id = request.data.get('user_id')
    plan_id = request.data.get('plan_id')
    date = request.data.get('date')
    book = request.data.get('book')
    actual_progress = request.data.get('actual_progress', '已完成')
    remark = request.data.get('remark', '')
    # 情感分析
    sentiment, score = analyze_sentiment(remark or actual_progress)
    if not user_id or not date or not book or not plan_id:
        return JsonResponse({'error': 'user_id、date、book、plan_id为必填项'}, status=400)
    plan = ReadingPlan.objects.filter(id=plan_id, user_id=user_id).first()
    if not plan:
        return JsonResponse({'error': '未找到对应计划'}, status=400)
    # 自动生成AI日记（如果remark为空）
    if not remark:
        from .diary_service import generate_diary_summary
        # 获取历史对话和最近一次用户输入
        history = ''
        message_for_diary = actual_progress or ''
        try:
            from .diary_api import user_direct_memories
            history_list = user_direct_memories.get(user_id, [])
            history = '\n'.join(history_list)
            # 尝试获取最近一次用户输入
            last_user_msg = ''
            for h in reversed(history_list):
                if h.startswith('用户：'):
                    last_user_msg = h.replace('用户：', '').strip()
                    break
            if last_user_msg:
                message_for_diary = last_user_msg
        except Exception:
            history = ''
        # 获取今日任务
        today_task = ''
        if plan and hasattr(plan, 'plan_content'):
            import json
            try:
                plan_json = json.loads(plan.plan_content)
                start_date = plan.start_date
                today_dt = date
                if isinstance(today_dt, str):
                    import datetime
                    today_dt = datetime.datetime.strptime(today_dt, '%Y-%m-%d').date()
                day_num = (today_dt - start_date).days + 1 if start_date else None
                if day_num and 'daily_plan' in plan_json:
                    for d in plan_json['daily_plan']:
                        if d.get('day') == day_num:
                            today_task = d.get('task', '')
                            break
            except Exception:
                today_task = ''
        remark = generate_diary_summary(history, message_for_diary, plan.plan_content if plan else '', today_task)
    DailyStatus.objects.update_or_create(
        user_id=user_id, plan=plan, book=book, date=date,
        defaults={'actual_progress': actual_progress, 'remark': remark, 'emotion': sentiment, 'emotion_score': score}
    )
    # 写入用户情绪历史
    UserEmotionHistory.objects.update_or_create(
        user_id=user_id,
        date=date,
        source='打卡',
        plan=plan,
        book=book,
        defaults={
            'emotion': sentiment,
            'emotion_score': score,
            'raw_text': remark or actual_progress
        }
    )
    # 同步更新阅读计划进度
    plan.current_progress = f"已打卡：{date}"
    plan.save()
    return JsonResponse({'success': True})

@csrf_exempt
@api_view(['POST'])
def get_daily_status(request):
    user_id = request.data.get('user_id')
    book = request.data.get('book')
    start_date = request.data.get('start_date')
    end_date = request.data.get('end_date')
    if not user_id or not book or not start_date or not end_date:
        return JsonResponse({'error': 'user_id、book、start_date、end_date为必填项'}, status=400)
    qs = DailyStatus.objects.filter(user_id=user_id, book=book, date__gte=start_date, date__lte=end_date)
    result = {str(d.date): d.actual_progress for d in qs}
    return JsonResponse({'status': result})

@csrf_exempt
@api_view(['POST'])
def get_diary(request):
    user_id = request.data.get('user_id')
    plan_id = request.data.get('plan_id')
    date = request.data.get('date')
    book = request.data.get('book')
    if not user_id or not date or not book or not plan_id:
        return JsonResponse({'error': 'user_id、date、book、plan_id为必填项'}, status=400)
    entry = DailyStatus.objects.filter(user_id=user_id, plan_id=plan_id, date=date, book=book).first()
    # 新增：如果actual_progress为“对话自动日记”，则auto_diary=remark，否则auto_diary为空
    auto_diary = entry.remark if entry and entry.actual_progress == '对话自动日记' else ''
    return JsonResponse({'remark': entry.remark if entry else '', 'auto_diary': auto_diary})

@csrf_exempt
@api_view(['POST'])
def update_plan(request):
    user_id = request.data.get('user_id')
    plan_id = request.data.get('plan_id')
    plan_content = request.data.get('plan_content')
    if not user_id or not plan_id or not plan_content:
        return JsonResponse({'error': 'user_id、plan_id、plan_content为必填项'}, status=400)
    plan = ReadingPlan.objects.filter(id=plan_id, user_id=user_id).first()
    if not plan:
        return JsonResponse({'error': '未找到对应计划'}, status=400)
    plan.plan_content = plan_content
    plan.last_update = datetime.datetime.now()
    plan.save()
    return JsonResponse({'success': True})

@csrf_exempt
def conversation_list(request):
    if request.method == 'GET':
        user_id = request.GET.get('user_id')
        book = request.GET.get('book')
        date = request.GET.get('date')
        qs = Conversation.objects.filter(user_id=user_id)
        if book:
            qs = qs.filter(plan__book=book)
        if date:
            # 用created_at日期过滤
            qs = qs.filter(created_at__date=date)
        qs = qs.order_by('-updated_at')
        data = [
            {
                'id': c.id,
                'title': c.title,
                'created_at': c.created_at,
                'updated_at': c.updated_at,
                'is_active': c.is_active,
            } for c in qs
        ]
        return JsonResponse({'conversations': data})

    if request.method == 'POST':
        body = json.loads(request.body)
        user_id = body['user_id']
        book = body.get('book')
        plan_id = body.get('plan_id')
        title = body.get('title', '新会话')
        date = body.get('date')
        plan = None
        if plan_id:
            plan = ReadingPlan.objects.filter(id=plan_id, user_id=user_id).first()
        if not plan and book:
            plan = ReadingPlan.objects.filter(user_id=user_id, book=book, is_active=True).first()
        if not plan:
            return JsonResponse({'error': '未找到对应计划'}, status=400)
        c = Conversation.objects.create(user_id=user_id, plan=plan, title=title)
        return JsonResponse({'id': c.id, 'title': c.title})

@csrf_exempt
def message_list(request):
    if request.method == 'GET':
        conversation_id = request.GET.get('conversation_id')
        msgs = Message.objects.filter(conversation_id=conversation_id).order_by('created_at')
        data = [
            {
                'id': m.id,
                'role': m.role,
                'content': m.content,
                'created_at': m.created_at,
            } for m in msgs
        ]
        return JsonResponse({'messages': data})

    if request.method == 'POST':
        body = json.loads(request.body)
        conversation_id = body['conversation_id']
        role = body['role']
        content = body['content']
        m = Message.objects.create(conversation_id=conversation_id, role=role, content=content)
        Conversation.objects.filter(id=conversation_id).update(updated_at=m.created_at)
        return JsonResponse({'id': m.id, 'created_at': m.created_at})

@csrf_exempt
@api_view(['GET'])
def emotion_curve(request):
    user_id = request.GET.get('user_id')
    book = request.GET.get('book')
    if not user_id:
        return JsonResponse({'error': 'user_id为必填项'}, status=400)
    # 查询该用户所有每日情绪分数
    qs = DailyStatus.objects.filter(user_id=user_id)
    if book:
        qs = qs.filter(book=book)
    qs = qs.order_by('date')
    data = list(qs.values('date', 'emotion_score'))
    if not data:
        return JsonResponse([], safe=False)
    import pandas as pd
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.dropna(subset=['emotion_score'])
    if df.empty:
        return JsonResponse([], safe=False)
    df = df.groupby('date').agg({'emotion_score': 'mean'}).reset_index()
    # 补全日期
    all_dates = pd.date_range(df['date'].min(), df['date'].max(), freq='D')
    df = df.set_index('date').reindex(all_dates)
    # 标记预测
    df['predicted'] = df['emotion_score'].isna()
    # 线性插值
    df['emotion_score'] = df['emotion_score'].interpolate(method='linear')
    df = df.reset_index().rename(columns={'index': 'date'})
    # 输出格式
    result = [
        {
            'date': d.strftime('%Y-%m-%d'),
            'emotion': round(float(e), 3) if pd.notna(e) else None,
            'predicted': bool(p)
        }
        for d, e, p in zip(df['date'], df['emotion_score'], df['predicted'])
    ]
    return JsonResponse(result, safe=False)

@csrf_exempt
def conversation_detail(request, id):
    if request.method == 'DELETE':
        try:
            conv = Conversation.objects.filter(id=id).first()
            if not conv:
                return JsonResponse({'error': '未找到该会话'}, status=404)
            # 级联删除消息
            Message.objects.filter(conversation_id=id).delete()
            conv.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': '只支持DELETE'}, status=405)
