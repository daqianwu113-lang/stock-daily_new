import akshare as ak
import pandas as pd
import datetime
import json
import os

# --- 1. 真实政策配置 (精选当前真实有效的宏观方向) ---
# 这些链接都是真实可访问的政府官网链接
REAL_POLICIES = [
    {
        "id": "p1",
        "title": "推动大规模设备更新和消费品以旧换新",
        "source": "国务院",
        "url": "https://www.gov.cn/zhengce/content/202403/content_6939232.htm",
        "desc": "实施设备更新、消费品以旧换新、回收循环利用、标准提升四大行动。",
        "keywords": ["机械设备", "家电", "汽车", "环保", "钢铁"] # 扩大了行业范围
    },
    {
        "id": "p2",
        "title": "加快“宽带边疆”建设",
        "source": "工信部",
        "url": "https://www.gov.cn/zhengce/zhengceku/202401/content_6928357.htm",
        "desc": "加强农村及边疆地区网络覆盖，利好通信基础设施及算力网络。",
        "keywords": ["通信", "计算机", "电子"]
    },
    {
        "id": "p3",
        "title": "支持创新药全链条发展",
        "source": "政府工作报告重点",
        "url": "https://www.gov.cn/yaowen/liebiao/202407/content_6961298.htm",
        "desc": "加强基础研究，完善审评审批，加大创新药医保支持力度。",
        "keywords": ["医药生物"]
    }
]

def get_stock_url(code):
    """
    生成东方财富的个股详情页链接
    """
    # 简单的市场判断：6开头是沪市(sh)，0/3开头是深市(sz)
    prefix = "sh" if code.startswith("6") else "sz"
    return f"https://quote.eastmoney.com/{prefix}{code}.html"

def run_analysis():
    print("🚀 开始执行 AlphaMiner 深度挖掘...")
    
    final_stocks = []
    
    try:
        # 1. 拉取A股所有股票实时行情 (速度快，包含市值、PE、PB等核心指标)
        print("正在连接交易所数据接口...")
        df = ak.stock_zh_a_spot_em()
        
        # 数据清洗：转为数值型，处理异常值
        numeric_cols = ['最新价', '涨跌幅', '市盈率-动态', '市净率', '总市值', '换手率']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 2. 遍历政策进行筛选
        for policy in REAL_POLICIES:
            print(f"正在分析政策: {policy['title']} (覆盖行业: {policy['keywords']})")
            
            # 这里我们需要知道哪些股票属于这些行业
            # 由于akshare没有直接的"根据行业名反查股票"的高效接口，
            # 为了保证稳定性，我们使用【板块行情】接口来获取成分股
            
            for industry_name in policy['keywords']:
                try:
                    # 获取该行业板块的成分股
                    df_board = ak.stock_board_industry_cons_em(symbol=industry_name)
                    
                    # 取出代码列表
                    board_codes = df_board['代码'].tolist()
                    
                    # 在全市场数据中找到这些股票的详细财务指标
                    # 筛选条件：
                    # 1. 属于该板块
                    # 2. 市值 > 50亿 (过滤小票)
                    # 3. PE > 0 (剔除亏损股)
                    mask = (df['代码'].isin(board_codes)) & (df['总市值'] > 50_0000_0000) & (df['市盈率-动态'] > 0)
                    target_stocks = df[mask].copy()
                    
                    # 按市盈率从小到大排序，取前3个龙头（便宜的龙头）
                    target_stocks = target_stocks.sort_values('市盈率-动态').head(3)
                    
                    for _, row in target_stocks.iterrows():
                        # 生成自动化的基本面点评（代替爬取不到的文本）
                        pe_val = row['市盈率-动态']
                        pb_val = row['市净率']
                        cap_val = row['总市值'] / 100000000 # 转为亿
                        
                        analysis_text = (
                            f"【财务透视】当前市盈率(PE)为 {pe_val:.2f}倍，市净率(PB)为 {pb_val:.2f}倍。"
                            f"总市值 {cap_val:.0f} 亿元。作为 {industry_name} 行业的优质标的，"
                            f"在“{policy['title']}”政策背景下，具备估值修复空间。"
                        )
                        
                        final_stocks.append({
                            "code": row['代码'],
                            "name": row['名称'],
                            "industry": industry_name,
                            "price": row['最新价'],
                            "change_percent": row['涨跌幅'],
                            "pe": round(pe_val, 2),
                            "market_cap": f"{cap_val:.2f}亿",
                            # 政策字段
                            "policy_title": policy['title'],
                            "policy_desc": policy['desc'],
                            "policy_url": policy['url'],
                            # 深度资料字段
                            "analysis": analysis_text,
                            "f10_url": get_stock_url(row['代码']) # 重点：外链跳转
                        })
                        
                except Exception as e:
                    print(f"行业 {industry_name} 数据获取异常: {e}")
                    continue

    except Exception as e:
        print(f"全局运行错误: {e}")

    # 3. 构造最终数据包
    output_data = {
        "date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "policies": REAL_POLICIES, # 传递完整的政策列表给前端展示
        "stocks": final_stocks
    }

    # 4. 保存
    if not os.path.exists('docs'):
        os.makedirs('docs')

    with open('docs/data.json', 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print("✅ 数据生成完毕！")

if __name__ == "__main__":
    run_analysis()
