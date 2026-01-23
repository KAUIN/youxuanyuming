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
    'delay_between_requests': 0.3,
    'output_file': 'ip.txt'
}

# 请求头配置
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# IP地址正则表达式
IP_PATTERN = re.compile(
    r'(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
    r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
)

# 要抓取的网页列表（请根据实际情况修改）
URLS = [
    'https://ip.164746.xyz',
    'https://api.uouin.com/cloudflare.html',
    'https://www.wetest.vip/page/cloudflare/address_v4.html',
    'https://stock.hostmonit.com/CloudFlareYes'
]

class WebIPScraper:
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
    
    def _detect_encoding(self, response: requests.Response) -> str:
        """自动检测文本编码"""
        if response.encoding:
            return response.encoding
        return 'utf-8'
    
    def _extract_ips_with_regex(self, text: str) -> List[str]:
        """使用正则表达式从文本中提取IP地址"""
        return IP_PATTERN.findall(text)
    
    def _parse_json_content(self, text: str) -> List[str]:
        """尝试解析JSON格式的内容"""
        ips = []
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                # 尝试从常见字段中提取IP
                for key in ['ips', 'ip', 'addresses', 'data', 'info', 'results']:
                    if key in data:
                        value = data[key]
                        if isinstance(value, str):
                            ips.extend(self._extract_ips_with_regex(value))
                        elif isinstance(value, list):
                            for item in value:
                                if isinstance(item, str):
                                    ips.extend(self._extract_ips_with_regex(item))
        except json.JSONDecodeError:
            pass
        return ips
    
    def _parse_html_content(self, text: str) -> List[str]:
        """解析HTML内容提取IP地址"""
        ips = []
        try:
            soup = BeautifulSoup(text, 'html.parser')
            
            # 常见包含IP的标签和class
            tag_selectors = [
                ('code', []),
                ('pre', []),
                ('div', ['ip', 'address', 'ip-address']),
                ('span', ['ip', 'ip-address']),
                ('p', ['ip']),
                ('td', ['ip']),
                ('li', ['ip']),
            ]
            
            for tag_name, class_list in tag_selectors:
                if class_list:
                    for class_name in class_list:
                        elements = soup.find_all(tag_name, class_=class_name)
                        for element in elements:
                            ips.extend(self._extract_ips_with_regex(element.get_text()))
                else:
                    elements = soup.find_all(tag_name)
                    for element in elements:
                        text_content = element.get_text()
                        if any(char.isdigit() for char in text_content) and '.' in text_content:
                            ips.extend(self._extract_ips_with_regex(text_content))
            
            # 如果没找到，尝试整个文档
            if not ips:
                all_text = soup.get_text()
                ips = self._extract_ips_with_regex(all_text)
                
        except Exception:
            # 回退到正则匹配
            ips = self._extract_ips_with_regex(text)
        return ips
    
    def _parse_text_content(self, text: str) -> List[str]:
        """解析纯文本内容"""
        ips = []
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith(('#', '//', '/*', '*', '--')):
                continue
            if '#' in line:
                line = line.split('#')[0].strip()
            if '//' in line:
                line = line.split('//')[0].strip()
            ips.extend(self._extract_ips_with_regex(line))
        return ips
    
    def scrape_url(self, url: str) -> List[str]:
        """抓取单个URL并提取IP地址"""
        response = self._make_request(url)
        if not response:
            return []
        
        # 检测编码并获取文本
        encoding = self._detect_encoding(response)
        try:
            content = response.content.decode(encoding)
        except UnicodeDecodeError:
            content = response.text
        
        ips = []
        content_type = response.headers.get('Content-Type', '').lower()
        
        # 根据内容类型选择解析方法
        if 'application/json' in content_type or url.endswith('.json'):
            ips = self._parse_json_content(content)
        elif 'text/html' in content_type:
            ips = self._parse_html_content(content)
        else:
            ips = self._parse_text_content(content)
        
        # 验证IP格式并去重
        validated_ips = []
        for ip in set(ips):
            if IP_PATTERN.fullmatch(ip):
                validated_ips.append(ip)
        
        return validated_ips
    
    def scrape_all(self, urls: List[str]) -> Set[str]:
        """抓取所有URL"""
        print("开始抓取IP地址...")
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
        
        self.all_ips = all_ips
        return all_ips
    
    def save_results(self) -> bool:
        """保存结果到文件"""
        if not self.all_ips:
            print("警告：未收集到任何IP地址")
            return False
        
        # 按IP地址数字排序
        def ip_key(ip: str) -> tuple:
            return tuple(map(int, ip.split('.')))
        
        sorted_ips = sorted(self.all_ips, key=ip_key)
        
        try:
            with open(self.config['output_file'], 'w', encoding='utf-8') as f:
                for ip in sorted_ips:
                    f.write(ip + '\n')
            
            print(f"完成！总共收集到 {len(self.all_ips)} 个IP地址")
            print(f"结果已保存到: {self.config['output_file']}")
            return True
            
        except Exception as e:
            print(f"保存文件时出错: {e}")
            return False

def main():
    """主函数"""
    # 创建爬虫实例
    scraper = WebIPScraper()
    
    # 执行抓取
    scraper.scrape_all(URLS)
    
    # 保存结果
    scraper.save_results()

if __name__ == "__main__":
    main()
