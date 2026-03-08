"""
高潜内容挖掘报告生成脚本
定期扫描数据库，生成分析报告供GEO内容创作使用
"""
import os
import sqlite3
import csv
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def generate_weekly_report(output_dir: str = "./reports"):
    """生成周度高潜内容报告"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 计算一周前的日期
    one_week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
    
    conn = sqlite3.connect('./data/analysis_records.db')
    c = conn.cursor()
    
    # 查询最近一周的高频访问记录和候选内容
    c.execute('''
        SELECT 
            id,
            source_url,
            task_type,
            created_at,
            raw_data_json,
            ai_analysis
        FROM analysis_records 
        WHERE (candidate_for_blog = 1 OR created_at >= ?)
        ORDER BY created_at DESC
    ''', (one_week_ago,))
    
    records = c.fetchall()
    conn.close()
    
    if not records:
        print("没有找到符合条件的记录")
        return
    
    # 生成CSV报告
    report_date = datetime.now().strftime('%Y%m%d')
    csv_path = os.path.join(output_dir, f"weekly_report_{report_date}.csv")
    
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow([
            'ID', '原始链接', '任务类型', '创建时间', 
            '内容概要', '分析概要', '是否候选内容', '发布建议'
        ])
        
        for record in records:
            id_, url, task_type, created_at, raw_data_json, ai_analysis = record
            
            # 提取内容概要
            try:
                raw_data = json.loads(raw_data_json)
                if task_type == 'single_content':
                    content_summary = raw_data.get('data', {}).get('desc', '')[:100] + '...'
                else:
                    content_summary = '账号分析'
            except:
                content_summary = '解析失败'
            
            # 提取分析概要
            analysis_summary = ai_analysis[:200] + '...' if ai_analysis else ''
            
            writer.writerow([
                id_,
                url,
                task_type,
                created_at,
                content_summary,
                analysis_summary,
                '是' if record[5] else '否',
                ''
            ])
    
    print(f"周度报告已生成: {csv_path}")
    print(f"共包含 {len(records)} 条记录")
    return csv_path

def generate_high_potential_list(threshold: int = 10):
    """生成高潜内容列表（被多次查询的内容）"""
    conn = sqlite3.connect('./data/analysis_records.db')
    c = conn.cursor()
    
    # 按URL分组统计查询次数
    c.execute('''
        SELECT 
            source_url,
            COUNT(*) as query_count,
            MAX(created_at) as last_query_at,
            GROUP_CONCAT(DISTINCT user_uuid) as user_uuids
        FROM analysis_records 
        GROUP BY source_url 
        HAVING query_count >= ?
        ORDER BY query_count DESC
    ''', (threshold,))
    
    records = c.fetchall()
    conn.close()
    
    if not records:
        print("没有找到高潜内容")
        return []
    
    print(f"\n高潜内容列表（查询次数≥{threshold}）：")
    print("=" * 80)
    for record in records:
        url, count, last_query, users = record
        print(f"查询次数: {count:3d} | 最后查询: {last_query} | URL: {url[:80]}...")
    
    return records

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='内容分析报告生成工具')
    parser.add_argument('--weekly', action='store_true', help='生成周度报告')
    parser.add_argument('--high-potential', type=int, metavar='THRESHOLD', help='生成高潜内容列表，指定查询次数阈值')
    
    args = parser.parse_args()
    
    if args.weekly:
        generate_weekly_report()
    
    if args.high_potential:
        generate_high_potential_list(args.high_potential)
    
    if not args.weekly and args.high_potential is None:
        # 默认执行两个任务
        generate_weekly_report()
        generate_high_potential_list()
