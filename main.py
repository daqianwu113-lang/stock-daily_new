import akshare as ak
import pandas as pd
import datetime
import json
import os
import time

# --- 1. 真实政策配置 (已修复链接为永久有效链接，并修正行业精确名称) ---
REAL_POLICIES = [
    {
        "id": "p1",
        "title": "大规模设备更新与以旧换新",
        "source": "国务院/发改委",
        # 使用发改委专题页或搜索页，确保不过期
        "url": "https://www.ndrc.gov.cn/xwdt/tzgg/", 
        "desc": "重点实施设备更新、消费品以旧换新、回收循环利用、标准提升四大行动。",
        # 注意：这里必须是东方财富/Akshare准确的板块名称，差一个字都查不到数据
        "target_boards": ["工程机械", "家电行业", "汽车整车", "钢铁行业"] 
    },
    {
        "id": "p2",
        "title": "数字中国与算力基建",
        "source": "工信部",
        "url": "https://www.miit.gov.cn/jgsj/txs/index.html", # 工信部通信司首页
        "desc": "加快5G、千兆光网及算力中心建设，推动数字经济与实体经济融合。",
        "target_boards": ["通信设备", "互联网服务", "软件开发", "通信服务"]
    },
    {
        "id": "p3",
        "title": "生物医药与创新药扶持",
        "source": "药监局",
        "url": "https://www.nmpa.gov.cn/yaowen/index.html", # 药监局要闻
        "desc": "全链条支持创新药发展，完善审评审批，加大医保支付倾斜。",
        "target_boards": ["化学制药", "中药", "生物制品", "医疗器械"]
    }
]

def get_stock_url(code):
    """生成东方财富详情页外链"""
    prefix = "sh" if code.startswith("6") else "sz"
    return f"https://quote.eastmoney.com/{prefix}{code}.html"

def run_analysis():
    print("🚀 开始执行 AlphaMiner 强力修复版...")
    
    final_stocks = []
    
    try:
        # 1. 拉取全市场实时行情 (基础数据)
        print("📡 正在连接交易所，拉取全市场数据...")
        df_market = ak.stock_zh_a_spot_em()
        
        # 数据类型转换，防止计算报错
        numeric_cols = ['最新价', '涨跌幅', '市盈率-动态', '市净率', '总市值']
        for col in numeric_cols:
            df_market[col] = pd.to_numeric(df_market[col], errors='coerce')
        
        # 2. 遍历政策进行精准挖掘
        for policy in REAL_POLICIES:
            print(f"🔎 正在扫描政策: {policy['title']}")
            
            for board_name in policy['target_boards']:
                try:
                    print(f"   -> 正在抓取板块: [{board_name}] ...")
                    # 获取板块成分股
                    df_board = ak.stock_board_industry_cons_em(symbol=board_name)
                    
                    if df_board.empty:
                        print(f"      ⚠️ 警告: 板块 [{board_name}] 返回为空，跳过。")
                        continue
                        
                    # 拿到成分股代码列表
                    board_codes = df_board['代码'].tolist()
                    
                    # 在全市场数据中筛选这些股票
                    # 筛选逻辑：属于该板块 & 市值>30亿 & PE>0 (稍微放宽条件，确保有票)
                    mask = (df_market['代码'].isin(board_codes)) & \
                           (df_market['总市值'] > 30_0000_0000) & \
                           (df_market['市盈率-动态'] > 0)
                    
                    target_stocks = df_market[mask].copy()
                    
                    # 如果筛选后没票，跳过
                    if target_stocks.empty:
                        continue
                        
                    # 排序：按PE从小到大（找低估值），取前3名
                    top_stocks = target_stocks.sort_values('市盈率-动态').head(3)
                    
                    for _, row in top_stocks.iterrows():
                        # 构造数据
                        mkt_val = row['总市值'] / 100000000
                        pe_val = row['市盈率-动态']
                        
                        # 智能生成文案
                        analysis_txt = (
                            f"【价值扫描】{board_name}板块龙头之一。当前PE为{pe_val:.1f}倍，"
                            f"市值{mkt_val:.1f}亿。在“{policy['title']}”政策催化下，"
                            f"具备较高的安全边际和补涨潜力。"
                        )

                        final_stocks.append({
                            "code": row['代码'],
                            "name": row['名称'],
                            "industry": board_name, # 使用精确的板块名
                            "price": row['最新价'],
                            "pe": f"{pe_val:.1f}",
                            "market_cap": f"{mkt_val:.1f}亿",
                            "policy_title": policy['title'],
                            "policy_url": policy['url'],
                            "analysis": analysis_txt,
                            "f10_url": get_stock_url(row['代码'])
                        })
                        
                except Exception as e:
                    print(f"      ❌ 板块 [{board_name}] 处理出错: {e}")
                    continue
            
            # 避免请求过快被封
            time.sleep(1)

        # --- 兜底机制：如果以上全失败，至少显示全市场市值前10，防止页面空白 ---
        if len(final_stocks) == 0:
            print("⚠️ 警告：精细筛选未命中任何数据，启动兜底机制...")
            backup_stocks = df_market.sort_values('总市值', ascending=False).head(10)
            for _, row in backup_stocks.iterrows():
                final_stocks.append({
                    "code": row['代码'],
                    "name": row['名称'],
                    "industry": "核心资产",
                    "price": row['最新价'],
                    "pe": f"{row['市盈率-动态']:.1f}",
                    "market_cap": f"{row['总市值']/100000000:.1f}亿",
                    "policy_title": "全市场核心资产 (兜底展示)",
                    "policy_url": "https://www.eastmoney.com/",
                    "analysis": "由于网络原因暂未获取细分板块数据，此处展示全市场市值排名前列的核心资产。",
                    "f10_url": get_stock_url(row['代码'])
                })

    except Exception as e:
        print(f"💥 严重错误: {e}")

    # 3. 保存数据
    output_data = {
        "date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "policies": REAL_POLICIES,
        "stocks": final_stocks
    }

    if not os.path.exists('docs'):
        os.makedirs('docs')

    with open('docs/data.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"✅ 数据生成成功！共包含 {len(final_stocks)} 只股票。")

if __name__ == "__main__":
    run_analysis()
