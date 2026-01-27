import requests
import json
import re
from bs4 import BeautifulSoup
import time
from typing import Set, Tuple
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IPScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.ipv4_set = set()
        self.ipv6_set = set()
        self.domain_set = set()
        
    def _fetch_page(self, url: str, **kwargs) -> str:
        """通用页面获取方法"""
        try:
            response = self.session.get(url, timeout=10, **kwargs)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"请求 {url} 失败: {e}")
            return ""
    
    def _extract_ips_from_text(self, text: str) -> Tuple[Set[str], Set[str]]:
        """从文本中提取IPv4和IPv6地址"""
        ipv4_set = set()
        ipv6_set = set()
        
        # IPv4正则 - 更严格的匹配
        ipv4_pattern = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
        for ip in re.findall(ipv4_pattern, text):
            if self._is_valid_ipv4(ip):
                ipv4_set.add(ip)
        
        # IPv6正则 - 更严格的匹配，排除时间格式
        # 匹配标准的IPv6地址格式
        ipv6_pattern = r'\b(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}\b|\b(?:[A-Fa-f0-9]{1,4}:){1,7}:\b|\b:(?:[A-Fa-f0-9]{1,4}:){1,7}[A-Fa-f0-9]{1,4}\b|\b(?:[A-Fa-f0-9]{1,4}:){1,6}:[A-Fa-f0-9]{1,4}\b'
        
        # 先匹配所有可能的IPv6模式
        potential_ipv6 = re.findall(ipv6_pattern, text)
        
        # 过滤掉时间格式和其他无效格式
        for ip in potential_ipv6:
            ip = ip.strip()
            # 排除时间格式 (HH:MM:SS)
            if re.match(r'^\d{1,2}:\d{2}:\d{2}$', ip):
                continue
            # 排除只有冒号的情况
            if ip == ':' or ip == '::':
                continue
            # 排除部分时间格式 (如 01:32)
            if re.match(r'^\d{1,2}:\d{2}$', ip) and len(ip) <= 5:
                continue
                
            if self._is_valid_ipv6(ip):
                ipv6_set.add(ip)
        
        return ipv4_set, ipv6_set
    
    def scrape_ip_164746_xyz(self, url: str) -> Tuple[Set[str], Set[str]]:
        """爬取第一个网站的IP信息"""
        logger.info(f"开始爬取 {url}")
        text = self._fetch_page(url)
        if not text:
            return set(), set()
        
        soup = BeautifulSoup(text, 'html.parser')
        ipv4_set, ipv6_set = set(), set()
        
        # 从链接提取
        for link in soup.find_all('a', href=True):
            href = link['href']
            if 'ipv4' in href:
                match = re.search(r'ipv4/(\d+\.\d+\.\d+\.\d+)', href)
                if match and self._is_valid_ipv4(match.group(1)):
                    ipv4_set.add(match.group(1))
            elif 'ipv6' in href:
                match = re.search(r'ipv6/([0-9a-fA-F:]+)', href)
                if match and self._is_valid_ipv6(match.group(1)):
                    ipv6_set.add(match.group(1))
        
        # 备用方法
        if not ipv4_set and not ipv6_set:
            ipv4_set, ipv6_set = self._extract_ips_from_text(text)
        
        logger.info(f"从 {url} 爬取到 {len(ipv4_set)} 个IPv4地址和 {len(ipv6_set)} 个IPv6地址")
        return ipv4_set, ipv6_set
    
    def scrape_api_uouin(self, url: str) -> Tuple[Set[str], Set[str]]:
        """爬取第二个网站的IP信息"""
        logger.info(f"开始爬取 {url}")
        text = self._fetch_page(url)
        if not text:
            return set(), set()
        
        soup = BeautifulSoup(text, 'html.parser')
        ipv4_set, ipv6_set = set(), set()
        
        for row in soup.find_all('tr'):
            tds = row.find_all('td')
            if len(tds) >= 3:
                ip = tds[2].get_text(strip=True)
                if self._is_valid_ipv4(ip):
                    ipv4_set.add(ip)
                elif self._is_valid_ipv6(ip):
                    ipv6_set.add(ip)
        
        # 备用方法
        if not ipv4_set and not ipv6_set:
            ipv4_set, ipv6_set = self._extract_ips_from_text(text)
        
        logger.info(f"从 {url} 爬取到 {len(ipv4_set)} 个IPv4地址和 {len(ipv6_set)} 个IPv6地址")
        return ipv4_set, ipv6_set
    
    def scrape_wetest_vip(self, url: str) -> Tuple[Set[str], Set[str]]:
        """爬取第三个网站的IP信息"""
        logger.info(f"开始爬取 {url}")
        text = self._fetch_page(url)
        if not text:
            return set(), set()
        
        soup = BeautifulSoup(text, 'html.parser')
        ipv4_set, ipv6_set = set(), set()
        
        for td in soup.find_all('td', attrs={'data-label': '优选地址'}):
            ip = td.get_text(strip=True)
            if self._is_valid_ipv4(ip):
                ipv4_set.add(ip)
            elif self._is_valid_ipv6(ip):
                ipv6_set.add(ip)
        
        # 备用方法
        if not ipv4_set and not ipv6_set:
            ipv4_set, ipv6_set = self._extract_ips_from_text(text)
        
        logger.info(f"从 {url} 爬取到 {len(ipv4_set)} 个IPv4地址和 {len(ipv6_set)} 个IPv6地址")
        return ipv4_set, ipv6_set
    
    def scrape_hostmonit_api(self, url: str) -> Tuple[Set[str], Set[str]]:
        """爬取hostmonit的API数据"""
        logger.info(f"开始爬取hostmonit API")
        ipv4_set, ipv6_set = set(), set()
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'Referer': 'https://stock.hostmonit.com/',
        }
        
        try:
            # IPv4
            response_v4 = self.session.post(
                'https://api.hostmonit.com/get_optimization_ip',
                headers=headers,
                json={"key": "iDetkOys"},
                timeout=10
            )
            data_v4 = response_v4.json()
            if data_v4.get('code') == 200:
                for item in data_v4.get('info', []):
                    if 'ip' in item and self._is_valid_ipv4(item['ip']):
                        ipv4_set.add(item['ip'])
            
            # IPv6
            response_v6 = self.session.post(
                'https://api.hostmonit.com/get_optimization_ip',
                headers=headers,
                json={"key": "iDetkOys", "type": "v6"},
                timeout=10
            )
            data_v6 = response_v6.json()
            if data_v6.get('code') == 200:
                for item in data_v6.get('info', []):
                    if 'ip' in item and self._is_valid_ipv6(item['ip']):
                        ipv6_set.add(item['ip'])
            
            logger.info(f"从hostmonit API获取到 {len(ipv4_set)} 个IPv4地址和 {len(ipv6_set)} 个IPv6地址")
        except Exception as e:
            logger.error(f"爬取hostmonit API失败: {e}")
        
        return ipv4_set, ipv6_set
    
    def scrape_cf_090227_xyz(self, url: str) -> Tuple[Set[str], Set[str]]:
        """爬取域名信息"""
        logger.info(f"开始爬取域名网站 {url}")
        text = self._fetch_page(url)
        if not text:
            return set(), set()
        
        domains = set()
        soup = BeautifulSoup(text, 'html.parser')
        
        # 从按钮提取
        for button in soup.find_all('button', class_='copy-domain'):
            onclick = button.get('onclick', '')
            match = re.search(r"copyDomain\('([^']+)'\)", onclick)
            if match:
                domain = match.group(1)
                if '.' in domain and len(domain) > 3:
                    domains.add(domain)
        
        # 从文本提取
        if not domains:
            domain_pattern = r'[a-zA-Z0-9][a-zA-Z0-9-]*\.[a-zA-Z]{2,}'
            for domain in re.findall(domain_pattern, text):
                if '.' in domain and len(domain) > 3:
                    domains.add(domain)
        
        logger.info(f"从 {url} 爬取到 {len(domains)} 个域名")
        return set(), domains  # 返回空IPv4集合和域名集合
    
    def scrape_generic_website(self, url: str) -> Tuple[Set[str], Set[str]]:
        """通用爬取方法"""
        logger.info(f"开始通用爬取 {url}")
        text = self._fetch_page(url)
        if not text:
            return set(), set()
        
        # 先尝试解析JSON
        try:
            data = json.loads(text)
            ipv4_set, ipv6_set = set(), set()
            def extract_from_obj(obj):
                if isinstance(obj, dict):
                    for v in obj.values():
                        if isinstance(v, str):
                            if self._is_valid_ipv4(v):
                                ipv4_set.add(v)
                            elif self._is_valid_ipv6(v):
                                ipv6_set.add(v)
                        else:
                            extract_from_obj(v)
                elif isinstance(obj, list):
                    for item in obj:
                        extract_from_obj(item)
            
            extract_from_obj(data)
            if ipv4_set or ipv6_set:
                return ipv4_set, ipv6_set
        except:
            pass
        
        # 普通HTML/文本提取
        return self._extract_ips_from_text(text)
    
    def _is_valid_ipv4(self, ip: str) -> bool:
        """验证IPv4地址"""
        pattern = r'^\b(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b$'
        if not re.match(pattern, ip):
            return False
        
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        
        for part in parts:
            try:
                num = int(part)
                if num < 0 or num > 255:
                    return False
            except:
                return False
        
        # 排除内网地址
        if ip.startswith(('0.', '10.', '127.', '169.254.', '192.168.', '172.16.', '172.17.', '172.18.', '172.19.',
                         '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.', '172.26.', '172.27.',
                         '172.28.', '172.29.', '172.30.', '172.31.', '224.', '240.', '255.')):
            return False
        
        return True
    
    def _is_valid_ipv6(self, ipv6: str) -> bool:
        """验证IPv6地址"""
        # 首先排除时间格式
        if re.match(r'^\d{1,2}:\d{2}:\d{2}$', ipv6):
            return False
        if re.match(r'^\d{1,2}:\d{2}$', ipv6) and len(ipv6) <= 5:
            return False
            
        # 简化验证
        if ':' not in ipv6 or len(ipv6) < 3:
            return False
        
        # 检查基本格式
        parts = ipv6.split(':')
        if len(parts) > 8 or ipv6.count('::') > 1:
            return False
        
        # 检查每个部分是否为有效的十六进制
        for part in parts:
            if not part:
                continue
            if len(part) > 4:
                return False
            try:
                int(part, 16)
            except:
                return False
        
        # 进一步验证：确保至少有2个冒号（标准IPv6格式）
        if ipv6.count(':') < 2:
            return False
            
        # 排除一些常见错误格式
        if ipv6.startswith(':') and not ipv6.startswith('::'):
            return False
        if ipv6.endswith(':') and not ipv6.endswith('::'):
            return False
        
        return True
    
    def _save_to_file(self, items: Set[str], filename: str, desc: str):
        """保存数据到文件"""
        if not items:
            return
        
        sorted_items = sorted(items)
        with open(filename, 'w', encoding='utf-8') as f:
            for item in sorted_items:
                f.write(f"{item}\n")
        logger.info(f"保存 {len(sorted_items)} 个{desc}到 {filename}")
    
    def run(self, urls: list = None):
        """主运行函数"""
        if urls is None:
            urls = [
                'https://ip.164746.xyz',
                'https://api.uouin.com/cloudflare.html',
                'https://www.wetest.vip/page/cloudflare/address_v4.html',
                'https://www.wetest.vip/page/cloudflare/address_v6.html',
                'https://stock.hostmonit.com',
                'https://cf.090227.xyz/'
            ]
        
        # 网站处理映射
        handlers = {
            'ip.164746.xyz': self.scrape_ip_164746_xyz,
            'api.uouin.com': self.scrape_api_uouin,
            'www.wetest.vip': self.scrape_wetest_vip,
            'stock.hostmonit.com': self.scrape_hostmonit_api,
            'cf.090227.xyz': self.scrape_cf_090227_xyz
        }
        
        for url in urls:
            logger.info(f"处理: {url}")
            
            # 选择处理器
            handler = None
            for domain, method in handlers.items():
                if domain in url:
                    handler = method
                    break
            if handler is None:
                handler = self.scrape_generic_website
            
            # 执行爬取
            ipv4_items, ipv6_items = handler(url)
            
            # 处理结果
            if 'cf.090227.xyz' in url:
                self.domain_set.update(ipv6_items)  # ipv6_items实际是域名集合
            else:
                if ipv4_items:
                    self.ipv4_set.update(ip for ip in ipv4_items if self._is_valid_ipv4(ip))
                if ipv6_items:
                    self.ipv6_set.update(ip for ip in ipv6_items if self._is_valid_ipv6(ip))
            
            time.sleep(0.5)  # 降低延迟
        
        # 保存文件
        self._save_to_file(self.ipv4_set, 'ipv4.txt', 'IPv4地址')
        self._save_to_file(self.ipv6_set, 'ipv6.txt', 'IPv6地址')
        self._save_to_file(self.domain_set, 'domain.txt', '域名')
        
        # 合并保存
        all_items = sorted(self.ipv4_set) + sorted(self.ipv6_set) + sorted(self.domain_set)
        with open('ip.txt', 'w', encoding='utf-8') as f:
            for item in all_items:
                f.write(f"{item}\n")
        
        # 输出统计
        logger.info("=" * 40)
        logger.info(f"总计: {len(self.ipv4_set)} IPv4, {len(self.ipv6_set)} IPv6, {len(self.domain_set)} 域名")


def main():
    """主函数"""
    logger.info("IP和域名爬虫启动")
    
    scraper = IPScraper()
    urls = [
        'https://ip.164746.xyz',
        'https://api.uouin.com/cloudflare.html',
        'https://www.wetest.vip/page/cloudflare/address_v4.html',
        'https://www.wetest.vip/page/cloudflare/address_v6.html',
        'https://stock.hostmonit.com',
        'https://cf.090227.xyz/'
    ]
    
    scraper.run(urls)
    logger.info("执行完成")


if __name__ == "__main__":
    main()
