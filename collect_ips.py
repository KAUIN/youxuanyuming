import requests
from bs4 import BeautifulSoup
import re
import os

# 设置请求头
headers = {
    'User-Agent': 'Mozilla/5.0 ...'  # 保留你的原有User-Agent
}

# 首先，更新你的urls列表
urls = [
    'https://ip.164746.xyz/ipTop10.html',
    'https://cf.090227.xyz/ct?ips=6',  # 修改为新的、具体的API地址
    'https://api.uouin.com/cloudflare.html',
    'https://www.wetest.vip/page/cloudflare/address_v4.html',
    'https://stock.hostmonit.com/CloudFlareYes'
]

ip_pattern = r'\b(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'

all_ips = set()

for url in urls:
    try:
        print(f"正在处理: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'

        if response.status_code != 200:
            print(f"  请求失败，状态码: {response.status_code}")
            continue

        soup = BeautifulSoup(response.text, 'html.parser')
        found_ips = []

        # --- 策略1：针对不同网站的原有精细规则 ---
        if url == 'https://ip.164746.xyz/ipTop10.html':
            ip_list = response.text.strip().split(',')
            found_ips = [ip.strip() for ip in ip_list if re.fullmatch(ip_pattern, ip.strip())]
        elif url == 'https://cf.090227.xyz/ct?ips=6':
            # 新格式解析：按行分割，然后提取每行中“#”号前的IP
            lines = response.text.strip().split('\n')
            found_ips = []
            for line in lines:
            # 分割每行，取“#”前面的部分，并去除空格
            ip_part = line.split('#')[0].strip()
            # 用正则验证它是否是一个合法的IP地址（安全过滤）
        if re.fullmatch(ip_pattern, ip_part):
            found_ips.append(ip_part)
        elif url == 'https://api.uouin.com/cloudflare.html':
            elements = soup.find_all('div', class_='ip')
        elif url == 'https://www.wetest.vip/page/cloudflare/address_v4.html':
            elements = soup.find_all('p')
        else:
            elements = []

        for element in elements:
            element_text = element.get_text()
            ip_matches = re.findall(ip_pattern, element_text)
            found_ips.extend(ip_matches)

        # --- 策略2：如果策略1没找到，启动暴力全文搜索 ---
        if not found_ips:
            print(f"  策略1未找到IP，启动全文搜索...")
            all_text = soup.get_text()
            found_ips = re.findall(ip_pattern, all_text)

        # 去重并添加到总集合
        unique_ips_from_this_page = set(found_ips)
        for ip in unique_ips_from_this_page:
            all_ips.add(ip)
        print(f"  从 {url} 找到 {len(unique_ips_from_this_page)} 个唯一IP")

    except Exception as e:
        print(f"处理 {url} 时出错: {e}")

# 写入最终文件
if all_ips:
    with open('ip.txt', 'w') as file:
        for ip in sorted(all_ips):
            file.write(ip + '\n')
    print(f'完成！总共收集到 {len(all_ips)} 个唯一IP地址。')
else:
    print('警告：未收集到任何IP地址。')
