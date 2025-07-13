from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import datetime
import json
from .models import DailyStatus, ReadingPlan
from .diary_service import generate_diary_summary
import re

# 用户历史对话缓存
user_direct_memories = {}
# 新增：每个用户最近一次AI建议的新计划缓存
user_pending_plan = {}
# 用户提醒状态缓存（全局）
user_plan_remind_status = {}

@csrf_exempt
@api_view(['POST'])
def direct_chat_with_diary(request):
    auto_diary = None  # 保证所有分支都能引用
    plan_text = ''  # 初始化，防止未定义
    user_id = request.data.get('user_id')
    message = request.data.get('message')
    current_book = request.data.get('current_book')
    current_plan = request.data.get('current_plan')
    if not user_id or not message:
        return JsonResponse({'error': 'user_id和message为必填项'}, status=400)
    # 取历史对话
    if user_id not in user_direct_memories:
        user_direct_memories[user_id] = []
    history = user_direct_memories[user_id]
    # 打印调试信息
    print(f"[direct_chat_with_diary] user_id={user_id}, message={message}")
    print(f"[direct_chat_with_diary] 历史对话: {history}")
    # 解析计划和进度
    plan_info = ""
    today_task = ""
    progress_info = ""
    today = datetime.date.today().strftime('%Y-%m-%d')
    need_check_progress = False
    today_task_obj = None
    if current_book and current_plan:
        try:
            plan_json = json.loads(current_plan)
            plan_info = f"当前书籍：《{current_book}》，计划如下：{current_plan}"
            start_date = plan_json.get('start_date')
            total_days = plan_json.get('total_days')
            daily_plan = plan_json.get('daily_plan', [])
            # 计划终止日期
            end_date = None
            if start_date and total_days:
                start_dt = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
                end_dt = start_dt + datetime.timedelta(days=total_days-1)
                end_date = end_dt.strftime('%Y-%m-%d')
                today_dt = datetime.date.today()
                planned_day = (today_dt - start_dt).days + 1
                # 查询所有打卡记录
                from .models import DailyStatus
                daily_status_list = list(DailyStatus.objects.filter(
                    user_id=user_id, book=current_book
                ).order_by('date').values('date', 'actual_progress', 'remark'))
                checked_status = [d for d in daily_status_list if d['actual_progress']]
                checked_days_count = len(checked_status)
                checked_days_list = [str(d['date']) for d in checked_status]
                # 今日任务
                if daily_plan and planned_day > 0:
                    for d in daily_plan:
                        if d.get('day') == planned_day:
                            today_task_obj = d
                            break
                missed_days = planned_day - checked_days_count
                if checked_days_count == 0 and planned_day > 1:
                    progress_info = f"你已经开始第{planned_day}天的计划，但前{planned_day-1}天还没有打卡。需要帮你调整计划吗？"
                elif checked_days_count < planned_day:
                    progress_info = f"你目前已打卡{checked_days_count}天，计划进度是第{planned_day}天，落后了{missed_days}天。"
                elif checked_days_count > planned_day:
                    progress_info = f"你目前已打卡{checked_days_count}天，计划进度是第{planned_day}天，你进度超前！"
                else:
                    progress_info = f"你目前已打卡{checked_days_count}天，进度和计划一致。"
                # 结构化进度信息
                progress_info += f"\n今天日期：{today_dt.strftime('%Y-%m-%d')}，计划起始日期：{start_date}，计划终止日期：{end_date}。"
                progress_info += f"\n今天是计划的第{planned_day}天。你已打卡的天数有：{checked_days_count}天，分别是：{checked_days_list}。今日任务：{today_task_obj['task'] if today_task_obj and 'task' in today_task_obj else '无'}。"
                progress_info += f"\n本书的所有打卡记录（date, actual_progress, remark）：{daily_status_list}"
                # 判断是否进度落后
                need_check_progress = checked_days_count < planned_day
        except Exception as e:
            plan_info = f"计划解析失败: {str(e)}"
    else:
        plan_info = "你还没有选择当前书籍或计划。"

    # 判断用户是否同意生成新计划
    agree_keywords = ['同意', '好的', '调整吧', '请帮我调整', '可以', '没问题', '行', 'ok', 'yes']
    user_agree = any(k in message for k in agree_keywords)
    # 判断历史对话是否有AI主动建议调整计划
    last_ai_reply = user_direct_memories[user_id][-1] if user_direct_memories[user_id] else ''
    plan_change_suggested = any(kw in last_ai_reply for kw in ['建议调整计划', '调整你的计划', '重新规划', '延长计划', '分成多天', '调计划', '修改计划'])

    from .agent import llm
    import re
    new_plan = None
    reply_text_clean = ""

    if user_agree and user_id in user_pending_plan:
        # 用户同意，保存新计划
        try:
            plan_json = json.loads(user_pending_plan[user_id])
            # 标准化
            original_plan = None
            if current_plan:
                try:
                    original_plan = json.loads(current_plan)
                except Exception:
                    original_plan = None
            plan_json = standardize_plan_json(plan_json, original_plan)
            # 补全关键字段
            if not plan_json.get('book') and current_book:
                plan_json['book'] = current_book
            if not plan_json.get('start_date') and original_plan:
                plan_json['start_date'] = original_plan.get('start_date')
            if not plan_json.get('end_date') and original_plan:
                plan_json['end_date'] = original_plan.get('end_date')
            if not plan_json.get('total_days') and plan_json.get('daily_plan'):
                plan_json['total_days'] = len(plan_json['daily_plan'])
            if not plan_json.get('daily_plan'):
                plan_json['daily_plan'] = []
            new_plan_content = json.dumps(plan_json, ensure_ascii=False)
            from .models import ReadingPlan
            # 查找是否已有同书计划
            plan = ReadingPlan.objects.filter(user_id=user_id, book=plan_json.get('book', current_book)).first()
            if plan:
                # 更新内容
                plan.plan_content = new_plan_content
                plan.start_date = plan_json.get('start_date')
                plan.end_date = plan_json.get('end_date')
                plan.is_active = True
                plan.save()
            else:
                # 新建
                plan = ReadingPlan.objects.create(
                    user_id=user_id,
                    book=plan_json.get('book', current_book),
                    start_date=plan_json.get('start_date'),
                    end_date=plan_json.get('end_date'),
                    plan_content=new_plan_content,
                    current_progress="未开始",
                    is_active=True
                )
            # 其他计划设为非激活
            ReadingPlan.objects.filter(user_id=user_id).exclude(id=plan.id).update(is_active=False)
            # 清除缓存
            del user_pending_plan[user_id]
            # 祝贺语
            reply_text_clean = "计划已更新！(๑•̀ㅂ•́)و✧ 新目标加油鸭！"
            return JsonResponse({'reply': reply_text_clean, 'auto_diary': auto_diary, 'next_suggestion': '', 'new_plan': None, 'plan_ai_raw': new_plan_content, 'new_plan_id': plan.id, 'new_plan_content': new_plan_content})
        except Exception as e:
            return JsonResponse({'reply': f'计划保存失败：{e}', 'auto_diary': auto_diary, 'next_suggestion': '', 'new_plan': None})

    # 判断用户是否主动要求调整计划
    adjust_keywords = ['调整计划', '修改计划', '重新规划', '压缩', '延长', '合并', '细化', '调计划']
    user_request_adjustment = any(k in message for k in adjust_keywords)
    # 判断用户是否拒绝调整
    reject_keywords = ['不用', '先聊聊', '不需要', '不用调整', '以后再说', '暂时不用', '先这样']
    user_reject_adjustment = any(k in message for k in reject_keywords)
    if user_reject_adjustment:
        user_plan_remind_status[user_id] = 'rejected'

    # 1. 只有用户主动要求调整计划时才弹窗生成新计划
    if user_request_adjustment and user_id not in user_pending_plan:
        # 用户主动要求调整，清除拒绝标记
        user_plan_remind_status[user_id] = None
        # 构建进度信息
        progress_detail = f"用户当前阅读进度：已打卡 {checked_days_count} 天，当前是第 {planned_day} 天。"
        if today_task_obj and 'task' in today_task_obj:
            progress_detail += f" 今日任务：{today_task_obj['task']}"
        prompt = (
            f"你是用户的智能阅读助理。请根据用户需求调整阅读计划。\n"
            f"原计划：{current_plan}\n"
            f"用户进度：已打卡{checked_days_count}天，当前第{planned_day}天\n"
            f"用户需求：{message}\n"
            f"请智能调整原计划（压缩/延长/合并/细化），输出标准JSON格式：\n"
            "```json\n"
            "{\n"
            '  "book": "书名",\n'
            '  "total_days": 天数,\n'
            '  "daily_plan": [\n'
            '    {"day": 1, "task": "任务描述"},\n'
            '    {"day": 2, "task": "任务描述"}\n'
            "  ]\n"
            "}\n"
            "```\n"
            "只输出JSON，不要任何其他文字。"
        )
        reply = llm.invoke(prompt)
        reply_text = reply.content if hasattr(reply, 'content') else str(reply)
        print(f"[direct_chat_with_diary] AI原始回复内容: {reply_text}")
        # 匹配 JSON
        match = re.search(r'```json([\s\S]+?)```', reply_text)
        json_candidate = None
        if match:
            json_candidate = match.group(1).strip()
            print(f"[direct_chat_with_diary] 匹配到的JSON代码块: {json_candidate}")
        else:
            match2 = re.search(r'({[\s\S]+})', reply_text)
            if match2:
                json_candidate = match2.group(1).strip()
                print(f"[direct_chat_with_diary] 匹配到的大括号JSON: {json_candidate}")
        if json_candidate:
            try:
                plan_obj = json.loads(json_candidate)
                print(f"[direct_chat_with_diary] JSON解析成功: {plan_obj}")
                # 去重检测：如果和current_plan内容完全一样，提示失败
                try:
                    prev_plan = json.loads(current_plan) if current_plan else None
                    if prev_plan and plan_obj == prev_plan:
                        print(f"[DEBUG] AI生成计划与原计划相同，返回失败")
                        return JsonResponse({
                            'reply': 'AI未能生成有变化的新计划，请重试或换个说法。',
                            'auto_diary': auto_diary,
                            'next_suggestion': '',
                            'new_plan': None,
                            'plan_ai_raw': '',
                            'new_plan_id': None,
                            'new_plan_content': None
                        })
                except Exception:
                    pass
                user_pending_plan[user_id] = json_candidate
                print(f"[direct_chat_with_diary] AI成功生成新计划，返回给前端: {json_candidate}")
                return JsonResponse({
                    'reply': '检测到你的阅读进度落后了，我为你生成了一个调整后的计划，是否同意？',
                    'auto_diary': auto_diary,
                    'next_suggestion': '',
                    'new_plan': json_candidate,
                    'plan_ai_raw': json_candidate,
                    'new_plan_id': None,
                    'new_plan_content': json_candidate
                })
            except Exception as e:
                print(f"[AI计划生成失败] JSON解析失败: {e}")

    # 2. 只在未提醒过且未被拒绝时提醒
    if need_check_progress and missed_days > 0 and user_plan_remind_status.get(user_id) != 'rejected' and user_plan_remind_status.get(user_id) != 'reminded':
        user_plan_remind_status[user_id] = 'reminded'
        # 用AI生成温和提醒
        remind_prompt = (
            f"你是用户的智能阅读助理。用户的阅读进度有点落后，请用温柔、幽默、鼓励的语气提醒用户可以调整计划，但不要强迫。"
            f"可以用轻松的方式说“如果需要帮忙调整计划，随时告诉我哦！”也可以用俏皮、共情的表达。"
            f"当前计划进度：{progress_info}\n用户最新输入：{message}"
        )
        remind_reply = llm.invoke(remind_prompt)
        remind_text = remind_reply.content if hasattr(remind_reply, 'content') else str(remind_reply)
        return JsonResponse({
            'reply': remind_text,
            'auto_diary': auto_diary,
            'next_suggestion': '',
            'new_plan': None,
            'plan_ai_raw': '',
            'new_plan_id': None,
            'new_plan_content': None
        })

    # 判断是否为“对话式打卡”
    complete_keywords = ['完成', '打卡', '已读', '已完成', '做完', '搞定', 'ok', 'done', '看完了', '读完了']
    is_complete = any(k in message for k in complete_keywords)
    diary_text = ''
    next_suggestion = ''
    if is_complete and current_plan:
        # 自动更新计划状态
        try:
            plan_obj = json.loads(current_plan)
            start_date = plan_obj.get('start_date')
            if not start_date:
                start_date = datetime.date.today().strftime('%Y-%m-%d')
            today = datetime.date.today().strftime('%Y-%m-%d')
            from .models import DailyStatus
            DailyStatus.objects.update_or_create(
                user_id=user_id, book=current_book, date=today,
                defaults={'actual_progress': '对话打卡'}
            )
            # 自动生成学习笔记摘要
            from .diary_service import generate_diary_summary
            history = ''
            try:
                history_list = user_direct_memories.get(user_id, [])
                history = '\n'.join(history_list)
            except Exception:
                history = ''
            # 获取今日任务
            today_task = ''
            try:
                plan_json = plan_obj
                start_dt = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
                today_dt = datetime.date.today()
                day_num = (today_dt - start_dt).days + 1
                if day_num and 'daily_plan' in plan_json:
                    for d in plan_json['daily_plan']:
                        if d.get('day') == day_num:
                            today_task = d.get('task', '')
                            break
            except Exception:
                today_task = ''
            diary_text = generate_diary_summary(history, message, current_plan, today_task)
            DailyStatus.objects.filter(user_id=user_id, book=current_book, date=today).update(remark=diary_text)
            # 生成下一步建议或小测验
            suggestion_prompt = f"用户今天的输入：{message}\n请为用户生成下一步学习建议或一个小测验。"
            suggestion_reply = llm.invoke(suggestion_prompt)
            next_suggestion = suggestion_reply.content if hasattr(suggestion_reply, 'content') else str(suggestion_reply)
        except Exception as e:
            print(f"[对话式打卡自动笔记异常] {e}")

    # 默认日常鼓励/普通对话
    prompt = (
        f"你是用户的智能阅读助理，风格要简洁、直接、清晰，但要有趣、俏皮、共情。"
        f"{plan_info}\n"
        f"{progress_info}\n"
        f"历史对话：{history}\n用户：{message}\n"
        "请用有趣、俏皮、共情的语气和用户互动，鼓励用户分享阅读感受，也可以主动发起轻松话题。"
    )
    reply = llm.invoke(prompt)
    reply_text_clean = reply.content if hasattr(reply, 'content') else str(reply)
    user_direct_memories[user_id].append(f"用户：{message}")
    user_direct_memories[user_id].append(f"助手：{reply_text_clean}")

    # 每次对话都自动生成/刷新AI学习日记
    from .diary_service import generate_diary_summary
    diary_history = '\n'.join(user_direct_memories.get(user_id, []))
    today_task = ''
    try:
        plan_obj = json.loads(current_plan) if current_plan else None
        start_date = plan_obj.get('start_date') if plan_obj else None
        if start_date:
            start_dt = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
            today_dt = datetime.date.today()
            day_num = (today_dt - start_dt).days + 1
            if day_num and 'daily_plan' in plan_obj:
                for d in plan_obj['daily_plan']:
                    if d.get('day') == day_num:
                        today_task = d.get('task', '')
                        break
    except Exception:
        today_task = ''
    diary_text = generate_diary_summary(diary_history, message, current_plan or '', today_task)
    # 写入DailyStatus
    try:
        from .models import DailyStatus
        today = datetime.date.today().strftime('%Y-%m-%d')
        plan_id_val = None
        try:
            plan_id_val = int(request.data.get('plan_id') or (selectedPlanObj['id'] if 'selectedPlanObj' in locals() else None))
        except Exception:
            plan_id_val = None
        DailyStatus.objects.update_or_create(
            user_id=user_id,
            plan_id=plan_id_val,
            book=current_book,
            date=today,
            defaults={'remark': diary_text, 'actual_progress': '对话自动日记'}
        )
    except Exception as e:
        print(f"[自动日记写入异常] {e}")

    return JsonResponse({'reply': reply_text_clean, 'auto_diary': diary_text, 'next_suggestion': next_suggestion, 'new_plan': None, 'plan_ai_raw': '', 'new_plan_id': None, 'new_plan_content': None})

def standardize_plan_json(plan_json, original_plan=None):
    # 补全必需字段
    if not plan_json.get('book') and original_plan:
        plan_json['book'] = original_plan.get('book')
    if not plan_json.get('start_date') and original_plan:
        plan_json['start_date'] = original_plan.get('start_date')
    if not plan_json.get('end_date'):
        if plan_json.get('start_date') and plan_json.get('total_days'):
            from datetime import datetime, timedelta
            start_dt = datetime.strptime(plan_json['start_date'], '%Y-%m-%d')
            plan_json['end_date'] = (start_dt + timedelta(days=plan_json['total_days']-1)).strftime('%Y-%m-%d')
        elif original_plan:
            plan_json['end_date'] = original_plan.get('end_date')
    if not plan_json.get('total_days') and plan_json.get('daily_plan'):
        plan_json['total_days'] = len(plan_json['daily_plan'])
    # daily_plan 必须是数组且每项有 day/task
    if not isinstance(plan_json.get('daily_plan'), list):
        plan_json['daily_plan'] = []
    for idx, item in enumerate(plan_json['daily_plan']):
        if 'day' not in item:
            item['day'] = idx + 1
        if 'task' not in item:
            item['task'] = ''
    return plan_json

def contains_json_block(text):
    import re
    return bool(re.search(r'```json[\s\S]+?```', text)) or bool(re.search(r'({[\s\S]+})', text)) 