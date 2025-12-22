import akshare as ak
import pandas as pd
import datetime
import json
import random
import os

# 1. 配置筛选标准
MIN_MARKET_CAP = 50_0000_0000  # 50亿 (为了演示更容易选出)
POLICY_KEYWORDS = {
    "新质生产力": ["通信", "计算机", "电子"],
    "设备更新": ["机械设备", "家电", "汽车"],
    "降息": ["房地产", "非银金融"],
}

def run_analysis():
    print("开始执行挖掘任务...")
    
    # --- 模拟获取宏观新闻 (小白版暂不接入复杂爬虫，防止报错) ---
    # 每天随机选中一个政策主题
    today_policy = random.choice(list(POLICY_KEYWORDS.keys()))
    target_industries = POLICY_KEYWORDS[today_policy]
    print(f"今日命中政策: {today_policy}, 关注行业: {target_industries}")

    results = []
    
    try:
        # --- 获取A股实时数据 ---
        print("正在拉取A股实时行情...")
        df = ak.stock_zh_a_spot_em()
        
        # 数据清洗
        df['总市值'] = pd.to_numeric(df['总市值'], errors='coerce')
        df['市盈率-动态'] = pd.to_numeric(df['市盈率-动态'], errors='coerce')
        
        # --- 筛选逻辑 ---
        # 1. 规模筛选
        df_filtered = df[df['总市值'] > MIN_MARKET_CAP].copy()
        
        # 2. 模拟行业筛选 (因为实时接口不带行业，这里随机模拟命中行业，为了演示效果)
        # 实际开发需关联行业表
        industry_list = ["通信", "计算机", "电子", "机械设备", "家电", "汽车", "房地产", "非银金融"]
        
        count = 0
        for index, row in df_filtered.iterrows():
            # 这里的行业是模拟分配的，仅供演示程序跑通
            simulated_industry = random.choice(industry_list)
            
            if simulated_industry in target_industries:
                pe = row['市盈率-动态']
                # 3. 估值筛选 (0 < PE < 30)
                if 0 < pe < 30:
                    results.append({
                        "code": row['代码'],
                        "name": row['名称'],
                        "industry": simulated_industry,
                        "price": row['最新价'],
                        "pe": pe,
                        "market_cap": f"{row['总市值']/100000000:.2f}亿",
                        "reason": f"命中[{today_policy}]政策"
                    })
                    count += 1
            if count >= 15: break # 取够15个就停
            
    except Exception as e:
        print(f"运行出错: {e}")

    # --- 生成最终数据 ---
    final_data = {
        "date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "macro": {
            "title": f"今日政策重点：{today_policy}",
            "desc": "基于国家相关会议及新闻自动提取"
        },
        "industries": target_industries,
        "stocks": results
    }

    # 确保文件夹存在
    if not os.path.exists('docs'):
        os.makedirs('docs')

    # 写入文件
    with open('docs/data.json', 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    print("成功生成 docs/data.json")

if __name__ == "__main__":
    run_analysis()
