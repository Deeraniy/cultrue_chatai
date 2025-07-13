#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文化聊天AI系统实验数据收集脚本
用于收集系统性能指标、用户行为数据和实验结果
"""

import time
import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
import sqlite3
import os

class ExperimentDataCollector:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.results = defaultdict(list)
        
    def test_recommendation_system(self, test_queries):
        """测试推荐系统性能"""
        print("开始测试推荐系统...")
        
        for i, query in enumerate(test_queries):
            start_time = time.time()
            try:
                response = requests.post(
                    f"{self.base_url}/api/chatbot/recommend/",
                    data={'text': query},
                    timeout=10
                )
                end_time = time.time()
                
                if response.status_code == 200:
                    data = response.json()
                    self.results['recommendation'].append({
                        'query': query,
                        'response_time': end_time - start_time,
                        'recommendations_count': len(data.get('recommend', [])),
                        'sentiment': data.get('sentiment', 'unknown'),
                        'success': True
                    })
                else:
                    self.results['recommendation'].append({
                        'query': query,
                        'response_time': end_time - start_time,
                        'success': False,
                        'error': response.status_code
                    })
            except Exception as e:
                self.results['recommendation'].append({
                    'query': query,
                    'success': False,
                    'error': str(e)
                })
            
            print(f"完成 {i+1}/{len(test_queries)} 推荐测试")
            
    def test_sentiment_analysis(self, test_texts):
        """测试情感分析性能"""
        print("开始测试情感分析...")
        
        for i, text in enumerate(test_texts):
            start_time = time.time()
            try:
                response = requests.post(
                    f"{self.base_url}/api/chatbot/direct_chat/",
                    json={
                        'user_id': 'test_user',
                        'message': text
                    },
                    timeout=10
                )
                end_time = time.time()
                
                if response.status_code == 200:
                    data = response.json()
                    self.results['sentiment'].append({
                        'text': text,
                        'response_time': end_time - start_time,
                        'success': True
                    })
                else:
                    self.results['sentiment'].append({
                        'text': text,
                        'response_time': end_time - start_time,
                        'success': False,
                        'error': response.status_code
                    })
            except Exception as e:
                self.results['sentiment'].append({
                    'text': text,
                    'success': False,
                    'error': str(e)
                })
            
            print(f"完成 {i+1}/{len(test_texts)} 情感分析测试")
    
    def test_conversation_system(self, conversation_scenarios):
        """测试对话系统性能"""
        print("开始测试对话系统...")
        
        for i, scenario in enumerate(conversation_scenarios):
            scenario_results = []
            user_id = f"test_user_{i}"
            
            for j, message in enumerate(scenario):
                start_time = time.time()
                try:
                    response = requests.post(
                        f"{self.base_url}/api/chatbot/direct_chat/",
                        json={
                            'user_id': user_id,
                            'message': message
                        },
                        timeout=15
                    )
                    end_time = time.time()
                    
                    if response.status_code == 200:
                        data = response.json()
                        scenario_results.append({
                            'message': message,
                            'response_time': end_time - start_time,
                            'reply_length': len(data.get('reply', '')),
                            'success': True
                        })
                    else:
                        scenario_results.append({
                            'message': message,
                            'response_time': end_time - start_time,
                            'success': False,
                            'error': response.status_code
                        })
                except Exception as e:
                    scenario_results.append({
                        'message': message,
                        'success': False,
                        'error': str(e)
                    })
                
                time.sleep(1)  # 避免请求过于频繁
            
            self.results['conversation'].append({
                'scenario_id': i,
                'messages': scenario_results
            })
            
            print(f"完成 {i+1}/{len(conversation_scenarios)} 对话场景测试")
    
    def collect_database_metrics(self, db_path="backend/db.sqlite3"):
        """收集数据库性能指标"""
        print("收集数据库指标...")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 统计各表数据量
            tables = ['reading_plan', 'daily_status', 'user_emotion_history', 'conversation', 'message']
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                self.results['database'][table] = count
            
            # 统计用户活跃度
            cursor.execute("""
                SELECT user_id, COUNT(*) as activity_count 
                FROM daily_status 
                GROUP BY user_id 
                ORDER BY activity_count DESC
            """)
            user_activity = cursor.fetchall()
            self.results['database']['user_activity'] = user_activity
            
            # 统计情绪分布
            cursor.execute("""
                SELECT emotion, COUNT(*) as count 
                FROM user_emotion_history 
                WHERE emotion IS NOT NULL 
                GROUP BY emotion
            """)
            emotion_distribution = cursor.fetchall()
            self.results['database']['emotion_distribution'] = emotion_distribution
            
            conn.close()
            
        except Exception as e:
            print(f"数据库指标收集失败: {e}")
    
    def generate_performance_report(self):
        """生成性能报告"""
        print("生成性能报告...")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {},
            'detailed_results': dict(self.results)
        }
        
        # 推荐系统性能统计
        if self.results['recommendation']:
            rec_data = pd.DataFrame(self.results['recommendation'])
            successful_recs = rec_data[rec_data['success'] == True]
            
            report['summary']['recommendation'] = {
                'total_queries': len(rec_data),
                'success_rate': len(successful_recs) / len(rec_data) * 100,
                'avg_response_time': successful_recs['response_time'].mean() if len(successful_recs) > 0 else 0,
                'max_response_time': successful_recs['response_time'].max() if len(successful_recs) > 0 else 0,
                'avg_recommendations': successful_recs['recommendations_count'].mean() if len(successful_recs) > 0 else 0
            }
        
        # 情感分析性能统计
        if self.results['sentiment']:
            sent_data = pd.DataFrame(self.results['sentiment'])
            successful_sents = sent_data[sent_data['success'] == True]
            
            report['summary']['sentiment'] = {
                'total_texts': len(sent_data),
                'success_rate': len(successful_sents) / len(sent_data) * 100,
                'avg_response_time': successful_sents['response_time'].mean() if len(successful_sents) > 0 else 0,
                'max_response_time': successful_sents['response_time'].max() if len(successful_sents) > 0 else 0
            }
        
        # 对话系统性能统计
        if self.results['conversation']:
            conv_stats = []
            for scenario in self.results['conversation']:
                for msg in scenario['messages']:
                    if msg['success']:
                        conv_stats.append(msg['response_time'])
            
            report['summary']['conversation'] = {
                'total_scenarios': len(self.results['conversation']),
                'total_messages': sum(len(s['messages']) for s in self.results['conversation']),
                'avg_response_time': np.mean(conv_stats) if conv_stats else 0,
                'max_response_time': np.max(conv_stats) if conv_stats else 0
            }
        
        return report
    
    def save_results(self, filename="experiment_results.json"):
        """保存实验结果"""
        report = self.generate_performance_report()
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"实验结果已保存到 {filename}")
    
    def generate_visualizations(self):
        """生成可视化图表"""
        print("生成可视化图表...")
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 1. 推荐系统响应时间分布
        if self.results['recommendation']:
            rec_data = pd.DataFrame(self.results['recommendation'])
            successful_recs = rec_data[rec_data['success'] == True]
            
            if len(successful_recs) > 0:
                plt.figure(figsize=(10, 6))
                plt.hist(successful_recs['response_time'], bins=20, alpha=0.7, color='skyblue')
                plt.title('推荐系统响应时间分布')
                plt.xlabel('响应时间 (秒)')
                plt.ylabel('频次')
                plt.savefig('recommendation_response_time.png', dpi=300, bbox_inches='tight')
                plt.close()
        
        # 2. 情感分析性能对比
        if self.results['sentiment']:
            sent_data = pd.DataFrame(self.results['sentiment'])
            successful_sents = sent_data[sent_data['success'] == True]
            
            if len(successful_sents) > 0:
                plt.figure(figsize=(8, 6))
                plt.boxplot(successful_sents['response_time'])
                plt.title('情感分析响应时间分布')
                plt.ylabel('响应时间 (秒)')
                plt.savefig('sentiment_response_time.png', dpi=300, bbox_inches='tight')
                plt.close()
        
        # 3. 系统成功率对比
        success_rates = {}
        if self.results['recommendation']:
            rec_data = pd.DataFrame(self.results['recommendation'])
            success_rates['推荐系统'] = len(rec_data[rec_data['success'] == True]) / len(rec_data) * 100
        
        if self.results['sentiment']:
            sent_data = pd.DataFrame(self.results['sentiment'])
            success_rates['情感分析'] = len(sent_data[sent_data['success'] == True]) / len(sent_data) * 100
        
        if success_rates:
            plt.figure(figsize=(8, 6))
            modules = list(success_rates.keys())
            rates = list(success_rates.values())
            bars = plt.bar(modules, rates, color=['lightblue', 'lightgreen'])
            plt.title('各模块成功率对比')
            plt.ylabel('成功率 (%)')
            plt.ylim(0, 100)
            
            # 在柱状图上添加数值标签
            for bar, rate in zip(bars, rates):
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                        f'{rate:.1f}%', ha='center', va='bottom')
            
            plt.savefig('success_rates.png', dpi=300, bbox_inches='tight')
            plt.close()

def main():
    """主函数 - 运行完整的实验数据收集"""
    
    # 初始化数据收集器
    collector = ExperimentDataCollector()
    
    # 测试查询样本
    test_queries = [
        "我今天心情很好，想读一些轻松的小说",
        "最近工作压力大，需要一些励志的书籍",
        "我想了解中国传统文化",
        "推荐一些适合晚上阅读的书籍",
        "我对科幻小说很感兴趣",
        "想要一些关于爱情的文学作品",
        "推荐一些经典名著",
        "我想读一些哲学类的书籍",
        "最近很迷茫，需要一些指导性的书籍",
        "想要一些关于历史的书籍"
    ]
    
    # 情感分析测试文本
    test_texts = [
        "今天读完了这本书，感觉收获很大！",
        "这本书有点难懂，我需要更多时间消化",
        "阅读让我感到平静和满足",
        "今天的学习计划完成了，很有成就感",
        "这本书的内容很深刻，让我思考了很多",
        "今天没有按计划读书，有点愧疚",
        "这本书写得真好，推荐给大家",
        "阅读让我忘记了烦恼",
        "今天的学习效率不高，有点沮丧",
        "这本书给了我很多启发"
    ]
    
    # 对话场景测试
    conversation_scenarios = [
        [
            "你好，我想制定一个阅读计划",
            "我想读《红楼梦》",
            "今天读完了第一章",
            "这本书写得真好"
        ],
        [
            "我想了解如何提高阅读效率",
            "有什么好的建议吗？",
            "谢谢你的建议",
            "我会试试看"
        ]
    ]
    
    print("开始文化聊天AI系统实验数据收集...")
    print("=" * 50)
    
    # 执行各项测试
    collector.test_recommendation_system(test_queries)
    print("-" * 30)
    
    collector.test_sentiment_analysis(test_texts)
    print("-" * 30)
    
    collector.test_conversation_system(conversation_scenarios)
    print("-" * 30)
    
    collector.collect_database_metrics()
    print("-" * 30)
    
    # 生成报告和可视化
    collector.save_results()
    collector.generate_visualizations()
    
    print("=" * 50)
    print("实验数据收集完成！")
    print("生成的文件：")
    print("- experiment_results.json (详细结果)")
    print("- recommendation_response_time.png (推荐系统响应时间)")
    print("- sentiment_response_time.png (情感分析响应时间)")
    print("- success_rates.png (成功率对比)")

if __name__ == "__main__":
    main() 