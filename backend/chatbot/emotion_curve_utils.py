from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import UserEmotionHistory
from datetime import timedelta, date as dt_date

@api_view(['GET'])
def emotion_curve(request):
    user_id = request.GET.get('user_id')
    plan_id = request.GET.get('plan_id')
    if not user_id or not plan_id:
        return Response({'error': 'user_id and plan_id required'}, status=400)
    qs = UserEmotionHistory.objects.filter(user_id=user_id, plan_id=plan_id).order_by('date')
    if not qs.exists():
        return Response({'dates': [], 'scores': []})
    records = list(qs.values('date', 'sentiment_score'))
    date_score = {str(r['date']): r['sentiment_score'] for r in records}
    start = records[0]['date']
    end = records[-1]['date']
    d = start
    dates, scores = [], []
    prev_score = date_score.get(str(start), 0)
    next_known = None
    known_dates = sorted(date_score.keys())
    idx = 0
    while d <= end:
        ds = str(d)
        if ds in date_score:
            score = date_score[ds]
            prev_score = score
            idx = known_dates.index(ds)
        else:
            # 线性插值：找下一个有分数的日期
            if not next_known or d > next_known['date']:
                # 找下一个
                next_score = None
                for future_ds in known_dates[idx+1:]:
                    if future_ds > ds:
                        next_score = date_score[future_ds]
                        next_date = dt_date.fromisoformat(future_ds)
                        break
                if next_score is not None:
                    days_gap = (next_date - d).days
                    days_total = (next_date - dt_date.fromisoformat(known_dates[idx])).days
                    if days_total > 0:
                        score = prev_score + (next_score - prev_score) * ((d - dt_date.fromisoformat(known_dates[idx])).days / days_total)
                    else:
                        score = prev_score
                else:
                    score = prev_score
            else:
                score = prev_score
        dates.append(ds)
        scores.append(round(score, 4) if score is not None else 0)
        d += timedelta(days=1)
    return Response({'dates': dates, 'scores': scores})
