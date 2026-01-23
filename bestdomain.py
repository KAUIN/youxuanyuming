import os
import requests
import re

def is_valid_ip(ip: str) -> bool:
    """验证IP地址是否有效"""
    ip_pattern = r'^\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b$'
    if not re.match(ip_pattern, ip):
        return False
    
    parts = ip.split('.')
    if len(parts) != 4:
        return False
        
    for part in parts:
        try:
            num = int(part)
            if num < 0 or num > 255:
                return False
        except ValueError:
            return False
    
    # 排除内网和特殊IP
    if ip.startswith('0.') or ip.startswith('10.') or ip.startswith('127.') or \
       ip.startswith('169.254.') or ip.startswith('172.16.') or \
       ip.startswith('192.168.') or ip.startswith('224.') or \
       ip.startswith('240.') or ip.startswith('255.'):
        return False
        
    return True

def get_item_list_from_file(filename: str):
    """从文件中读取IP列表，只返回IP地址"""
    ip_list = []
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                item = line.strip()
                if item and is_valid_ip(item):  # 只添加有效的IP地址
                    ip_list.append(item)
        
        print(f"从 {filename} 读取到 {len(ip_list)} 个IP地址")
        return ip_list
    except Exception as e:
        print(f"读取文件 {filename} 时出错: {e}")
        return []

def get_item_list_from_url(url: str):
    """从URL读取IP列表"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        items = response.text.strip().split('\n')
        # 过滤出有效的IP地址
        ip_list = [item.strip() for item in items if item.strip() and is_valid_ip(item.strip())]
        
        print(f"从 {url} 读取到 {len(ip_list)} 个IP地址")
        return ip_list
    except Exception as e:
        print(f"从URL {url} 读取时出错: {e}")
        return []

def get_cloudflare_zone(api_token):
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json',
    }
    response = requests.get('https://api.cloudflare.com/client/v4/zones', headers=headers)
    response.raise_for_status()
    zones = response.json().get('result', [])
    if not zones:
        raise Exception("No zones found")
    return zones[0]['id'], zones[0]['name']

def delete_existing_dns_records(api_token, zone_id, subdomain, domain):
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json',
    }
    record_name = domain if subdomain == '@' else f'{subdomain}.{domain}'
    while True:
        response = requests.get(f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?type=A&name={record_name}', headers=headers)
        response.raise_for_status()
        records = response.json().get('result', [])
        if not records:
            break
        for record in records:
            delete_response = requests.delete(f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record["id"]}', headers=headers)
            delete_response.raise_for_status()
            print(f"Del {subdomain}:{record['id']}")

def update_cloudflare_dns(ip_list, api_token, zone_id, subdomain, domain):
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json',
    }
    record_name = domain if subdomain == '@' else f'{subdomain}.{domain}'
    
    added_count = 0
    failed_count = 0
    
    for ip in ip_list:
        # 确保是有效的IP地址
        if not is_valid_ip(ip):
            print(f"跳过无效的IP地址: {ip}")
            failed_count += 1
            continue
            
        data = {
            "type": "A",
            "name": record_name,
            "content": ip,
            "ttl": 1,
            "proxied": False
        }
        response = requests.post(f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records', json=data, headers=headers)
        if response.status_code == 200:
            print(f"Add {subdomain}:{ip}")
            added_count += 1
        else:
            print(f"Failed to add A record for IP {ip} to subdomain {subdomain}: {response.status_code} {response.text}")
            failed_count += 1
    
    return added_count, failed_count

if __name__ == "__main__":
    api_token = os.getenv('CF_API_TOKEN')
    
    # 配置映射关系
    subdomain_source_mapping = {
        'bestcf': 'ip.txt',  # 从本地文件读取
        'api': 'https://raw.githubusercontent.com/KAUIN/youxuanyuming/refs/heads/main/ip.txt',  # 从URL读取
        # 可以添加更多子域名映射
        # 'cdn': 'ip.txt',  # 另一个子域名也从本地文件读取
        # 'proxy': 'another_ip_source.txt'  # 从另一个文件读取
    }
    
    try:
        if not api_token:
            raise Exception("CF_API_TOKEN 环境变量未设置")
        
        # 获取Cloudflare域区ID和域名
        zone_id, domain = get_cloudflare_zone(api_token)
        print(f"找到域区: {domain}, ID: {zone_id}")
        
        for subdomain, source in subdomain_source_mapping.items():
            print(f"\n处理子域名: {subdomain}")
            
            # 根据source类型获取IP列表
            if source.startswith('http://') or source.startswith('https://'):
                # 从URL获取
                ip_list = get_item_list_from_url(source)
            else:
                # 从本地文件获取
                ip_list = get_item_list_from_file(source)
            
            if not ip_list:
                print(f"警告: {subdomain} 没有获取到有效的IP地址")
                continue
            
            print(f"获取到 {len(ip_list)} 个有效IP地址")
            
            # 删除现有的DNS记录
            delete_existing_dns_records(api_token, zone_id, subdomain, domain)
            
            # 更新Cloudflare DNS记录
            added_count, failed_count = update_cloudflare_dns(ip_list, api_token, zone_id, subdomain, domain)
            
            print(f"子域名 {subdomain} 完成: 添加了 {added_count} 条记录, 失败 {failed_count} 条")
            
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
