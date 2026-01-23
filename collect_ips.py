import requests
from bs4 import BeautifulSoup
import re
import time
import json
from urllib.parse import urlparse
from typing import Set, List, Optional, Dict, Any

# 配置参数
CONFIG = {
    'timeout': 15,
    'max_retries': 2,
    'delay_between_requests': 0.5,
    'output_file': 'ip.txt'
}

# 请求头配置
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}

# IP地址正则表达式
IP_PATTERN = re.compile(
    r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
    r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
)

# 要抓取的网页列表
URLS = [
    'https://ip.164746.xyz',
    'https://api.uouin.com/cloudflare.html',
    'https://www.wetest.vip/page/cloudflare/address_v4.html',
    'https://stock.hostmonit.com/CloudFlareYes',
]

class TargetedIPScraper:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = {**CONFIG, **(config or {})}
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.all_ips: Set[str] = set()
    
    def _make_request(self, url: str) -> Optional[requests.Response]:
        """发送HTTP请求，支持重试"""
        for attempt in range(self.config['max_retries']):
            try:
                response = self.session.get(
                    url,
                    timeout=self.config['timeout'],
                    allow_redirects=True
                )
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException:
                if attempt < self.config['max_retries'] - 1:
                    time.sleep(0.5)
                continue
        return None
    
    def _parse_ip_164746_xyz(self, content: str) -> List[str]:
        """解析 https://ip.164746.xyz 格式"""
        ips = []
        try:
            soup = BeautifulSoup(content, 'html.parser')
            # 查找所有包含IP的<a>标签
            for a_tag in soup.find_all('a', href=True):
                # 检查链接文本是否为IP地址
                link_text = a_tag.get_text().strip()
                if IP_PATTERN.fullmatch(link_text):
                    ips.append(link_text)
            
            # 如果没有找到，尝试查找包含IP地址的td单元格
            if not ips:
                for td in soup.find_all('td'):
                    td_text = td.get_text().strip()
                    if IP_PATTERN.fullmatch(td_text):
                        ips.append(td_text)
                    else:
                        # 尝试从文本中提取IP
                        found = IP_PATTERN.findall(td_text)
                        ips.extend(found)
            
        except Exception as e:
            print(f"  解析ip.164746.xyz时出错: {e}")
        
        return list(set(ips))
    
    def _parse_api_uouin_com(self, content: str) -> List[str]:
        """解析 https://api.uouin.com/cloudflare.html 格式"""
        ips = []
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # 查找所有表格行
            for tr in soup.find_all('tr'):
                # 获取行中所有td单元格
                tds = tr.find_all('td')
                if len(tds) >= 3:  # 至少要有3个td
                    # 第三个td包含IP地址（索引为2）
                    ip_td = tds[2]
                    ip_text = ip_td.get_text().strip()
                    
                    # 验证是否为IP地址
                    if IP_PATTERN.fullmatch(ip_text):
                        ips.append(ip_text)
            
            # 备用方法：从所有td中查找IP
            if not ips:
                for td in soup.find_all('td'):
                    td_text = td.get_text().strip()
                    if IP_PATTERN.fullmatch(td_text):
                        ips.append(td_text)
            
        except Exception as e:
            print(f"  解析api.uouin.com时出错: {e}")
        
        return list(set(ips))
    
    def _parse_stock_hostmonit_com(self, content: str) -> List[str]:
        """解析 https://stock.hostmonit.com/CloudFlareYes JSON格式"""
        ips = []
        try:
            # 解析JSON
            data = json.loads(content)
            
            # 检查code是否为200
            if data.get('code') == 200 and 'info' in data:
                for item in data['info']:
                    if 'ip' in item:
                        ip = str(item['ip']).strip()
                        if IP_PATTERN.fullmatch(ip):
                            ips.append(ip)
            
        except json.JSONDecodeError as e:
            print(f"  解析JSON失败: {e}")
        except Exception as e:
            print(f"  解析stock.hostmonit.com时出错: {e}")
        
        return list(set(ips))
    
    def _parse_wetest_vip(self, content: str) -> List[str]:
        """解析 https://www.wetest.vip/page/cloudflare/address_v4.html"""
        ips = []
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # 查找所有<p>标签
            for p_tag in soup.find_all('p'):
                p_text = p_tag.get_text().strip()
                # 尝试提取IP地址
                found = IP_PATTERN.findall(p_text)
                ips.extend(found)
            
            # 如果没有找到，尝试查找所有包含数字的文本
            if not ips:
                for element in soup.find_all(text=True):
                    if element.parent.name in ['script', 'style']:
                        continue
                    text = str(element).strip()
                    if text:
                        found = IP_PATTERN.findall(text)
                        ips.extend(found)
            
        except Exception as e:
            print(f"  解析wetest.vip时出错: {e}")
        
        return list(set(ips))
    
    def scrape_url(self, url: str) -> List[str]:
        """抓取单个URL并提取IP地址"""
        response = self._make_request(url)
        if not response:
            return []
        
        # 检测编码
        try:
            content = response.content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                content = response.content.decode('gbk')
            except UnicodeDecodeError:
                content = response.text
        
        # 根据URL选择解析方法
        domain = urlparse(url).netloc
        
        if domain == 'ip.164746.xyz':
            ips = self._parse_ip_164746_xyz(content)
        elif domain == 'api.uouin.com':
            ips = self._parse_api_uouin_com(content)
        elif domain == 'stock.hostmonit.com':
            ips = self._parse_stock_hostmonit_com(content)
        elif domain == 'www.wetest.vip':
            ips = self._parse_wetest_vip(content)
        else:
            # 通用解析方法
            ips = IP_PATTERN.findall(content)
            # 去重
            ips = list(set(ips))
        
        # 验证IP格式
        validated_ips = []
        for ip in ips:
            if IP_PATTERN.fullmatch(ip):
                validated_ips.append(ip)
        
        return validated_ips
    
    def scrape_all(self, urls: List[str]) -> Set[str]:
        """抓取所有URL"""
        print("开始抓取IP地址...")
        print("=" * 50)
        
        all_ips = set()
        
        for i, url in enumerate(urls, 1):
            domain = urlparse(url).netloc
            print(f"[{i}/{len(urls)}] 正在抓取: {domain}")
            
            try:
                ips = self.scrape_url(url)
                if ips:
                    all_ips.update(ips)
                    print(f"  找到 {len(ips)} 个IP地址")
                else:
                    print(f"  未找到IP地址")
                    
                # 请求间隔延迟
                if i < len(urls):
                    time.sleep(self.config['delay_between_requests'])
                    
            except Exception as e:
                print(f"  抓取失败: {e}")
        
        print("=" * 50)
        self.all_ips = all_ips
        return all_ips
    
    def save_results(self) -> bool:
        """保存结果到文件"""
        if not self.all_ips:
            print("警告：未收集到任何IP地址")
            return False
        
        # 按IP地址数字排序
        def ip_key(ip: str) -> tuple:
            parts = ip.split('.')
            return tuple(int(part) for part in parts)
        
        sorted_ips = sorted(self.all_ips, key=ip_key)
        
        try:
            with open(self.config['output_file'], 'w', encoding='utf-8') as f:
                for ip in sorted_ips:
                    f.write(ip + '\n')
            
            print(f"完成！总共收集到 {len(self.all_ips)} 个唯一IP地址")
            print(f"结果已保存到: {self.config['output_file']}")
            
            # 显示部分结果
            if sorted_ips:
                print("\n前20个IP地址:")
                for i, ip in enumerate(sorted_ips[:20], 1):
                    print(f"  {i:2d}. {ip}")
                if len(sorted_ips) > 20:
                    print(f"  ... 还有 {len(sorted_ips) - 20} 个")
            print("=" * 50)
            
            return True
            
        except Exception as e:
            print(f"保存文件时出错: {e}")
            return False

def main():
    """主函数"""
    # 创建爬虫实例
    scraper = TargetedIPScraper()
    
    # 执行抓取
    scraper.scrape_all(URLS)
    
    # 保存结果
    scraper.save_results()

if __name__ == "__main__":
    main()
