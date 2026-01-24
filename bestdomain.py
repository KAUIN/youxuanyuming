import os
import requests
import re
import ipaddress

def is_valid_ip(ip: str, ip_type: str = 'all') -> bool:
    """验证IP地址是否有效，支持IPv4和IPv6
    
    Args:
        ip: IP地址字符串
        ip_type: 验证类型，'all'表示IPv4和IPv6都接受，'ipv4'只接受IPv4，'ipv6'只接受IPv6
    """
    try:
        # 使用Python的ipaddress模块进行更准确的IP验证
        ip_obj = ipaddress.ip_address(ip)
        
        # 根据ip_type参数过滤类型
        if ip_type == 'ipv4' and not isinstance(ip_obj, ipaddress.IPv4Address):
            return False
        if ip_type == 'ipv6' and not isinstance(ip_obj, ipaddress.IPv6Address):
            return False
        
        # 排除内网和特殊IP
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or \
           ip_obj.is_multicast or ip_obj.is_reserved or ip_obj.is_unspecified:
            return False
        
        # 排除IPv4的广播地址
        if isinstance(ip_obj, ipaddress.IPv4Address) and str(ip_obj) == '255.255.255.255':
            return False
            
        return True
        
    except ValueError:
        return False

def get_item_list_from_file(filename: str, ip_type: str = 'all'):
    """从文件中读取IP列表，支持IPv4和IPv6"""
    ip_list = []
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                item = line.strip()
                if item and is_valid_ip(item, ip_type):
                    ip_list.append(item)
        
        print(f"从 {filename} 读取到 {len(ip_list)} 个{'IPv4' if ip_type == 'ipv4' else 'IPv6' if ip_type == 'ipv6' else 'IP'}地址")
        return ip_list
    except Exception as e:
        print(f"读取文件 {filename} 时出错: {e}")
        return []

def get_item_list_from_url(url: str, ip_type: str = 'all'):
    """从URL读取IP列表，支持IPv4和IPv6"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        items = response.text.strip().split('\n')
        # 过滤出有效的IP地址
        ip_list = [item.strip() for item in items if item.strip() and is_valid_ip(item.strip(), ip_type)]
        
        print(f"从 {url} 读取到 {len(ip_list)} 个{'IPv4' if ip_type == 'ipv4' else 'IPv6' if ip_type == 'ipv6' else 'IP'}地址")
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

def delete_existing_dns_records(api_token, zone_id, subdomain, domain, record_type=None):
    """删除现有的DNS记录，支持A和AAAA记录
    
    Args:
        record_type: 记录类型，None表示删除所有A和AAAA记录，'A'只删除A记录，'AAAA'只删除AAAA记录
    """
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json',
    }
    record_name = domain if subdomain == '@' else f'{subdomain}.{domain}'
    
    # 如果指定了记录类型，只删除该类型的记录
    # 否则删除A和AAAA两种类型的记录
    record_types = [record_type] if record_type else ['A', 'AAAA']
    
    for rtype in record_types:
        while True:
            response = requests.get(
                f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?type={rtype}&name={record_name}', 
                headers=headers
            )
            response.raise_for_status()
            records = response.json().get('result', [])
            if not records:
                break
            for record in records:
                delete_response = requests.delete(
                    f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record["id"]}', 
                    headers=headers
                )
                delete_response.raise_for_status()
                print(f"Del {subdomain} ({rtype}): {record['id']}")

def update_cloudflare_dns(ip_list, api_token, zone_id, subdomain, domain):
    """更新Cloudflare DNS记录，自动识别IPv4和IPv6"""
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json',
    }
    record_name = domain if subdomain == '@' else f'{subdomain}.{domain}'
    
    added_count = 0
    failed_count = 0
    
    for ip in ip_list:
        try:
            ip_obj = ipaddress.ip_address(ip)
            
            # 根据IP版本确定记录类型
            if isinstance(ip_obj, ipaddress.IPv4Address):
                record_type = "A"
            elif isinstance(ip_obj, ipaddress.IPv6Address):
                record_type = "AAAA"
            else:
                print(f"跳过未知IP类型: {ip}")
                failed_count += 1
                continue
            
            # 确保是有效的公网IP地址
            if not is_valid_ip(ip):
                print(f"跳过无效的IP地址: {ip}")
                failed_count += 1
                continue
                
            data = {
                "type": record_type,
                "name": record_name,
                "content": ip,
                "ttl": 1,
                "proxied": False
            }
            
            response = requests.post(
                f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records', 
                json=data, 
                headers=headers
            )
            
            if response.status_code == 200:
                print(f"Add {subdomain} ({record_type}): {ip}")
                added_count += 1
            else:
                print(f"Failed to add {record_type} record for IP {ip} to subdomain {subdomain}: {response.status_code} {response.text}")
                failed_count += 1
                
        except ValueError:
            print(f"跳过无效的IP地址: {ip}")
            failed_count += 1
            continue
    
    return added_count, failed_count

if __name__ == "__main__":
    api_token = os.getenv('CF_API_TOKEN')
    
    # 配置映射关系 - 可以指定每个子域名的IP类型或使用混合列表
    # 格式: '子域名': {'source': '来源URL或文件', 'ip_type': 'all/ipv4/ipv6'}
    subdomain_config_mapping = {
        'api': {
            'source': 'https://raw.githubusercontent.com/KAUIN/youxuanyuming/refs/heads/main/ip.txt',
            'ip_type': 'all'  # 支持IPv4和IPv6混合
        },
    }
    
    try:
        if not api_token:
            raise Exception("CF_API_TOKEN 环境变量未设置")
        
        # 获取Cloudflare域区ID和域名
        zone_id, domain = get_cloudflare_zone(api_token)
        print(f"找到域区: {domain}, ID: {zone_id}")
        
        for subdomain, config in subdomain_config_mapping.items():
            print(f"\n处理子域名: {subdomain}")
            
            source = config['source']
            ip_type = config.get('ip_type', 'all')
            
            # 根据source类型获取IP列表
            if source.startswith('http://') or source.startswith('https://'):
                # 从URL获取
                ip_list = get_item_list_from_url(source, ip_type)
            else:
                # 从本地文件获取
                ip_list = get_item_list_from_file(source, ip_type)
            
            if not ip_list:
                print(f"警告: {subdomain} 没有获取到有效的IP地址")
                continue
            
            print(f"获取到 {len(ip_list)} 个有效IP地址")
            
            # 删除现有的DNS记录（A和AAAA记录都会删除）
            delete_existing_dns_records(api_token, zone_id, subdomain, domain)
            
            # 更新Cloudflare DNS记录，自动识别IPv4/IPv6
            added_count, failed_count = update_cloudflare_dns(ip_list, api_token, zone_id, subdomain, domain)
            
            print(f"子域名 {subdomain} 完成: 添加了 {added_count} 条记录, 失败 {failed_count} 条")
            
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
