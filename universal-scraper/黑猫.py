import time
import random
import hashlib
import json
import sys
import urllib.parse
import re


def generate_signature(keyword=""):
    c = str(int(time.time() * 1000))   # 13位时间戳
    a = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]
    h = ''.join(random.choice(a) for i in range(16))   # 随机16个字符
    d = '$d6eb7ff91ee257475%'   # 默认值
    
    # 用于获取最新投诉列表的参数
    e = '2'       # 最新信息为2
    u = '10'      # 每页数量
    page = str(1)   # 页码
    
    ts = c
    rs = h
    
    # 构建签名参数
    if keyword:
        # 搜索接口使用不同的参数组合
        bb = [d, keyword, str(10), ts, str(1), rs]
    else:
        # 获取最新投诉列表的参数组合
        bb = [d, u, c, e, page, h]
    
    bb.sort()
    signature = hashlib.sha256((''.join(bb)).encode('utf-8')).hexdigest()
    
    return ts, rs, signature

def search_complaints(keyword="", cookie=None):
    try:
        ts, rs, signature = generate_signature(keyword)
        print(f"时间戳: {ts}, 随机字符串: {rs}, 签名: {signature}")
        
        import requests
        
        # 设置请求头
        headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            "accept": "*/*",
            "accept-language": "zh-CN,zh;q=0.9",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "sec-ch-ua": '"Chromium";v="136", "Not.A/Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "x-requested-with": "XMLHttpRequest"
        }
        
        # 如果传入了Cookie，添加到请求头
        if cookie:
            headers["cookie"] = cookie
        
        # 构建URL
        if keyword:
            # 使用搜索API
            encoded_keyword = urllib.parse.quote(keyword)
            base_url = f"https://tousu.sina.com.cn/api/index/s?ts={ts}&rs={rs}&signature={signature}&keywords={encoded_keyword}&page_size=10&page=1"
            
            # 添加referer头
            headers["referer"] = f"https://tousu.sina.com.cn/index/search/?keywords={encoded_keyword}&t=1"
        else:
            # 使用获取最新投诉列表API
            base_url = f"https://tousu.sina.com.cn/api/index/feed?ts={ts}&rs={rs}&signature={signature}&type=2&page_size=10&page=1&_={ts}"
        
        print(f"请求URL: {base_url}")
        response = requests.request("GET", base_url, headers=headers)
        
        # 检查是否重定向到登录页面
        if "<!doctype html>" in response.text.lower() or "登录" in response.text or "微博" in response.text:
            if keyword and not cookie:
                print("\n需要登录Cookie才能使用搜索功能！")
                print("系统将自动为您显示最新投诉列表...\n")
                return search_complaints()  # 递归调用，不带关键词
            elif not cookie:
                print("未提供Cookie，将获取不需要登录的最新投诉")
            else:
                print("提供的Cookie无效或已过期，请更新Cookie")
                return None
        
        # 尝试解析JSON
        if response.text.strip():
            try:
                result = json.loads(response.text)
                
                # 输出结果
                if result['result']['status']['code'] == 0:
                    lists = result['result']['data']['lists']
                    print(f"\n找到 {len(lists)} 条投诉:")
                    
                    # 如果有关键词且没有Cookie，尝试在本地过滤结果
                    filtered_lists = lists
                    if keyword and not cookie:
                        filtered_lists = []
                        for item in lists:
                            # 在标题、公司名或内容中搜索关键词
                            title = item['main'].get('title', '')
                            cotitle = item['main'].get('cotitle', '')
                            summary = item['main'].get('summary', '')
                            if (
                                keyword.lower() in title.lower() or 
                                keyword.lower() in cotitle.lower() or 
                                keyword.lower() in summary.lower()
                            ):
                                filtered_lists.append(item)
                        
                        if filtered_lists:
                            print(f"在最新投诉中找到 {len(filtered_lists)} 条含 '{keyword}' 的投诉:")
                        else:
                            print(f"在最新投诉中未找到含 '{keyword}' 的投诉")
                    
                    # 显示结果
                    for idx, item in enumerate(filtered_lists, 1):
                        print(f"\n--- 投诉 {idx} ---")
                        print(f"标题: {item['main']['title']}")
                        print(f"公司: {item['main']['cotitle']}")
                        print(f"内容: {item['main']['summary']}")
                        print(f"链接: {item['main']['url']}")
                else:
                    print("请求失败:", result)
                
                return result
            except json.JSONDecodeError as e:
                print(f"JSON解析错误: {e}")
                print(f"原始响应: {response.text[:200]}...")
                return None
        else:
            print("响应内容为空")
            return None
    except Exception as e:
        print(f"发生错误: {e}")
        return None

def print_help():
    print("""
黑猫投诉数据获取工具

使用方法:
    python3 黑猫.py                     # 获取最新投诉列表
    python3 黑猫.py 关键词              # 在最新投诉中搜索关键词
    python3 黑猫.py --cookie "COOKIE"   # 使用Cookie获取投诉列表
    python3 黑猫.py 关键词 --cookie "COOKIE"  # 使用Cookie搜索关键词
    python3 黑猫.py --help              # 显示帮助信息

注意:
    1. 搜索功能需要登录Cookie，否则只能在最新投诉中进行本地筛选
    2. 可以从浏览器开发者工具中获取Cookie
    """)

if __name__ == "__main__":
    # 处理命令行参数
    cookie = None
    keyword = None
    
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--help" or arg == "-h":
            print_help()
            sys.exit(0)
        elif arg == "--cookie" and i < len(sys.argv)-1:
            cookie = sys.argv[i+1]
        elif arg == "--cookie":
            print("错误: --cookie 参数需要提供Cookie值")
            sys.exit(1)
        elif not arg.startswith("--") and not keyword:
            keyword = arg
    
    if keyword:
        print(f"正在搜索关键词: {keyword}")
        search_complaints(keyword, cookie)
    else:
        print("未提供搜索关键词，显示最新投诉")
        search_complaints(cookie=cookie)