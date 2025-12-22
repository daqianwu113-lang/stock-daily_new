import akshare as ak
import pandas as pd
import datetime
import json
import random
import os

# --- 1. 模拟今日的【多条】重磅宏观政策输入 ---
# 在真实商业版中，这部分通过爬虫+GPT生成。
# 这里我们模拟今天有三条大的政策落地：
TODAY_POLICIES = [
    {
        "title": "大规模设备更新行动方案",
        "industries": ["机械设备", "家电", "汽车"],
        "desc": "发改委指出，重点支持工业机械、家电以旧换新，提供财政贴息。",
        "url": "https://www.ndrc.gov.cn/ (模拟链接)", # 这里可以放真实的政府网链接
        "type": "财政刺激"
    },
    {
        "title": "数字中国建设整体布局",
        "industries": ["计算机", "通信", "传媒"],
        "desc": "加快5G网络与千兆光网协同建设，利好算力基础设施。",
        "url": "http://www.gov.cn/ (模拟链接)",
        "type": "新基建"
    },
    {
        "title": "创新药全链条支持",
        "industries": ["医药生物"],
        "desc": "针对创新药研发端给予税收优惠，加速审批流程。",
        "url": "http://www.nmpa.gov.cn/ (模拟链接)",
        "type": "产业扶持"
    }
]

MIN_MARKET_CAP = 50_0000_0000  # 50亿

def run_analysis():
    print("🚀 开始执行多维度挖掘任务...")
    
    final_results = []
    all_target_industries = [] # 用于前端生成筛选标签

    try:
        # --- 获取A股实时数据 ---
        print("正在拉取A股实时行情...")
        df = ak.stock_zh_a_spot_em()
        
        # 数据清洗
        df['总市值'] = pd.to_numeric(df['总市值'], errors='coerce')
        df['市盈率-动态'] = pd.to_numeric(df['市盈率-动态'], errors='coerce')
        
        # 基础筛选：市值 > 50亿
        df_big = df[df['总市值'] > MIN_MARKET_CAP].copy()
        
        # --- 遍历每一条政策进行挖掘 ---
        for policy in TODAY_POLICIES:
            print(f"正在分析政策板块: {policy['title']}...")
            
            # 把这个政策涉及的行业加入总列表
            all_target_industries.extend(policy['industries'])
            
            # 在符合市值要求的股票里找
            # (注意：因为接口限制，我们依然模拟行业匹配，真实环境需merge行业表)
            count = 0
            for index, row in df_big.iterrows():
                # 模拟：随机给这个股票分配一个行业
                # 技巧：为了让演示效果好，我们让前20%的股票大概率命中当前政策的行业
                if random.random() < 0.2: 
                    mock_industry = random.choice(policy['industries'])
                else:
                    mock_industry = "其他行业"

                if mock_industry in policy['industries']:
                    pe = row['市盈率-动态']
                    # 估值筛选：PE在 0-40 之间
                    if 0 < pe < 40:
                        final_results.append({
                            "code": row['代码'],
                            "name": row['名称'],
                            "industry": mock_industry,
                            "price": row['最新价'],
                            "pe": pe,
                            "market_cap": f"{row['总市值']/100000000:.2f}亿",
                            # 下面是新增的字段，用于前端展示解读
                            "policy_title": policy['title'],
                            "policy_desc": policy['desc'],
                            "policy_url": policy['url'],
                            "policy_type": policy['type']
                        })
                        count += 1
                if count >= 6: break # 每个政策只选6个龙头，避免列表太长

    except Exception as e:
        print(f"运行出错: {e}")

    # --- 生成最终数据结构 ---
    final_data = {
        "date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "summary": f"今日共捕获 {len(TODAY_POLICIES)} 条核心政策，覆盖 {len(set(all_target_industries))} 个行业。",
        "all_industries": list(set(all_target_industries)), # 去重后的行业列表
        "stocks": final_results
    }

    if not os.path.exists('docs'):
        os.makedirs('docs')

    with open('docs/data.json', 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    print("✅ 成功生成多维度报告: docs/data.json")

if __name__ == "__main__":
    run_analysis()
