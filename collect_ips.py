import requests
import json
import re
from bs4 import BeautifulSoup
import time
from typing import Set, Dict, Any
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.ipv4_set = set()  # 存储IPv4地址
        self.ipv6_set = set()  # 存储IPv6地址
        self.domain_set = set()  # 使用集合避免重复域名
        
    def scrape_ip_164746_xyz(self, url: str) -> tuple[Set[str], Set[str]]:
        """爬取第一个网站的IP信息（IPv4和IPv6）"""
        logger.info(f"开始爬取 {url}")
        ipv4_set = set()
        ipv6_set = set()
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 方法1: 通过a标签查找
            ip_links = soup.find_all('a', href=re.compile(r'ipv4/\d+\.\d+\.\d+\.\d+'))
            for link in ip_links:
                ip_match = re.search(r'ipv4/(\d+\.\d+\.\d+\.\d+)', link['href'])
                if ip_match:
                    ipv4_set.add(ip_match.group(1))
            
            # 查找IPv6地址
            ipv6_links = soup.find_all('a', href=re.compile(r'ipv6/[0-9a-fA-F:]+'))
            for link in ipv6_links:
                ipv6_match = re.search(r'ipv6/([0-9a-fA-F:]+)', link['href'])
                if ipv6_match and self.is_valid_ipv6(ipv6_match.group(1)):
                    ipv6_set.add(ipv6_match.group(1))
            
            # 方法2: 通过文本模式查找（备用方法）
            if not ipv4_set:
                ipv4_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
                found_ips = re.findall(ipv4_pattern, response.text)
                # 过滤掉一些明显不是IP的数字
                for ip in found_ips:
                    if self.is_valid_ipv4(ip):
                        ipv4_set.add(ip)
            
            # 查找文本中的IPv6地址
            if not ipv6_set:
                ipv6_pattern = self._get_ipv6_pattern()
                found_ipv6s = re.findall(ipv6_pattern, response.text)
                for ipv6 in found_ipv6s:
                    if self.is_valid_ipv6(ipv6):
                        ipv6_set.add(ipv6)
            
            logger.info(f"从 {url} 爬取到 {len(ipv4_set)} 个IPv4地址和 {len(ipv6_set)} 个IPv6地址")
            return ipv4_set, ipv6_set
            
        except Exception as e:
            logger.error(f"爬取 {url} 时出错: {e}")
            return set(), set()
    
    def scrape_api_uouin(self, url: str) -> tuple[Set[str], Set[str]]:
        """爬取第二个网站的IP信息（IPv4和IPv6）"""
        logger.info(f"开始爬取 {url}")
        ipv4_set = set()
        ipv6_set = set()
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找包含IP的表格行
            rows = soup.find_all('tr')
            for row in rows:
                tds = row.find_all('td')
                if len(tds) >= 3:
                    # 第三个td包含IP地址
                    ip_candidate = tds[2].get_text(strip=True)
                    # 检查是否是IPv4
                    if self.is_valid_ipv4(ip_candidate):
                        ipv4_set.add(ip_candidate)
                    # 检查是否是IPv6
                    elif self.is_valid_ipv6(ip_candidate):
                        ipv6_set.add(ip_candidate)
            
            # 备用方法：使用正则表达式直接搜索
            if not ipv4_set and not ipv6_set:
                # 搜索IPv4
                ipv4_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
                found_ips = re.findall(ipv4_pattern, response.text)
                for ip in found_ips:
                    if self.is_valid_ipv4(ip):
                        ipv4_set.add(ip)
                
                # 搜索IPv6
                ipv6_pattern = self._get_ipv6_pattern()
                found_ipv6s = re.findall(ipv6_pattern, response.text)
                for ipv6 in found_ipv6s:
                    if self.is_valid_ipv6(ipv6):
                        ipv6_set.add(ipv6)
            
            logger.info(f"从 {url} 爬取到 {len(ipv4_set)} 个IPv4地址和 {len(ipv6_set)} 个IPv6地址")
            return ipv4_set, ipv6_set
            
        except Exception as e:
            logger.error(f"爬取 {url} 时出错: {e}")
            return set(), set()
    
    def scrape_wetest_vip(self, url: str) -> tuple[Set[str], Set[str]]:
        """爬取第三个网站的IP信息（IPv4和IPv6）"""
        logger.info(f"开始爬取 {url}")
        ipv4_set = set()
        ipv6_set = set()
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找所有tr标签
            rows = soup.find_all('tr')
            for row in rows:
                # 查找具有data-label="优选地址"的td标签
                ip_tds = row.find_all('td', attrs={'data-label': '优选地址'})
                for td in ip_tds:
                    ip_text = td.get_text(strip=True)
                    # 检查是否是IPv4
                    if self.is_valid_ipv4(ip_text):
                        ipv4_set.add(ip_text)
                    # 检查是否是IPv6
                    elif self.is_valid_ipv6(ip_text):
                        ipv6_set.add(ip_text)
            
            # 备用方法
            if not ipv4_set and not ipv6_set:
                # 搜索IPv4
                ipv4_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
                found_ips = re.findall(ipv4_pattern, response.text)
                for ip in found_ips:
                    if self.is_valid_ipv4(ip):
                        ipv4_set.add(ip)
                
                # 搜索IPv6
                ipv6_pattern = self._get_ipv6_pattern()
                found_ipv6s = re.findall(ipv6_pattern, response.text)
                for ipv6 in found_ipv6s:
                    if self.is_valid_ipv6(ipv6):
                        ipv6_set.add(ipv6)
            
            logger.info(f"从 {url} 爬取到 {len(ipv4_set)} 个IPv4地址和 {len(ipv6_set)} 个IPv6地址")
            return ipv4_set, ipv6_set
            
        except Exception as e:
            logger.error(f"爬取 {url} 时出错: {e}")
            return set(), set()
    
    def scrape_hostmonit_api(self, url: str) -> tuple[Set[str], Set[str]]:
        """爬取hostmonit的API数据（同时获取IPv4和IPv6）"""
        logger.info(f"开始爬取hostmonit API")
        ipv4_set = set()
        ipv6_set = set()
        
        try:
            # 根据您提供的请求头设置
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Content-Type': 'application/json',
                'Origin': 'https://stock.hostmonit.com',
                'Referer': 'https://stock.hostmonit.com/',
                'DNT': '1',
            }
            
            # 获取IPv4地址
            payload_v4 = {"key": "iDetkOys"}
            logger.info(f"发送POST请求获取IPv4地址")
            logger.info(f"请求载荷: {payload_v4}")
            
            response_v4 = self.session.post(
                'https://api.hostmonit.com/get_optimization_ip', 
                headers=headers, 
                json=payload_v4, 
                timeout=20
            )
            response_v4.raise_for_status()
            
            # 获取IPv6地址
            payload_v6 = {"key": "iDetkOys", "type": "v6"}
            logger.info(f"发送POST请求获取IPv6地址")
            logger.info(f"请求载荷: {payload_v6}")
            
            response_v6 = self.session.post(
                'https://api.hostmonit.com/get_optimization_ip', 
                headers=headers, 
                json=payload_v6, 
                timeout=20
            )
            response_v6.raise_for_status()
            
            # 解析IPv4响应
            data_v4 = json.loads(response_v4.text)
            if data_v4.get('code') == 200:
                for item in data_v4.get('info', []):
                    if 'ip' in item and self.is_valid_ipv4(item['ip']):
                        ipv4_set.add(item['ip'])
                logger.info(f"从hostmonit API成功获取 {len(ipv4_set)} 个IPv4地址")
            else:
                logger.error(f"IPv4 API返回错误code: {data_v4.get('code')}")
                logger.error(f"响应内容: {data_v4}")
            
            # 解析IPv6响应
            data_v6 = json.loads(response_v6.text)
            if data_v6.get('code') == 200:
                for item in data_v6.get('info', []):
                    if 'ip' in item and self.is_valid_ipv6(item['ip']):
                        ipv6_set.add(item['ip'])
                logger.info(f"从hostmonit API成功获取 {len(ipv6_set)} 个IPv6地址")
            else:
                logger.error(f"IPv6 API返回错误code: {data_v6.get('code')}")
                logger.error(f"响应内容: {data_v6}")
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
        except Exception as e:
            logger.error(f"爬取hostmonit API时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        return ipv4_set, ipv6_set
    
    def scrape_cf_090227_xyz(self, url: str) -> tuple[Set[str], Set[str]]:
        """爬取cf.090227.xyz网站的域名信息"""
        logger.info(f"开始爬取域名网站 {url}")
        domains = set()
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 方法1: 从按钮的onclick属性中提取域名
            buttons = soup.find_all('button', class_='copy-domain')
            for button in buttons:
                onclick_value = button.get('onclick', '')
                # 匹配copyDomain('域名')格式
                domain_match = re.search(r"copyDomain\('([^']+)'\)", onclick_value)
                if domain_match:
                    domain = domain_match.group(1)
                    if self.is_valid_domain(domain):
                        domains.add(domain)
            
            # 方法2: 从按钮的文本内容中提取域名
            if not domains:
                for button in buttons:
                    button_text = button.get_text(strip=True)
                    # 尝试从按钮文本中提取域名
                    domain_match = re.search(r'([a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9](\.[a-zA-Z]{2,})+)$', button_text)
                    if domain_match:
                        domain = domain_match.group(0)
                        if self.is_valid_domain(domain):
                            domains.add(domain)
            
            # 方法3: 从所有文本中提取域名
            if not domains:
                domain_pattern = r'[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9](\.[a-zA-Z]{2,})+'
                found_domains = re.findall(domain_pattern, response.text)
                for domain_tuple in found_domains:
                    # 处理匹配结果，获取完整域名
                    domain_match = re.search(domain_pattern, response.text)
                    if domain_match:
                        domain = domain_match.group(0)
                        if self.is_valid_domain(domain):
                            domains.add(domain)
            
            logger.info(f"从 {url} 爬取到 {len(domains)} 个域名")
            return domains, set()
            
        except Exception as e:
            logger.error(f"爬取域名网站 {url} 时出错: {e}")
            return set(), set()
    
    def scrape_generic_website(self, url: str) -> tuple[Set[str], Set[str]]:
        """通用爬取方法，用于未来添加新网站（支持IPv4和IPv6）"""
        logger.info(f"开始通用爬取 {url}")
        ipv4_set = set()
        ipv6_set = set()
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # 首先尝试JSON格式
            try:
                data = json.loads(response.text)
                def find_ips_in_dict(obj, ipv4_set, ipv6_set):
                    if isinstance(obj, dict):
                        for key, value in obj.items():
                            if isinstance(value, str):
                                if self.is_valid_ipv4(value):
                                    ipv4_set.add(value)
                                elif self.is_valid_ipv6(value):
                                    ipv6_set.add(value)
                            else:
                                find_ips_in_dict(value, ipv4_set, ipv6_set)
                    elif isinstance(obj, list):
                        for item in obj:
                            find_ips_in_dict(item, ipv4_set, ipv6_set)
                
                find_ips_in_dict(data, ipv4_set, ipv6_set)
                if ipv4_set or ipv6_set:
                    logger.info(f"从 {url} 的JSON中爬取到 {len(ipv4_set)} 个IPv4地址和 {len(ipv6_set)} 个IPv6地址")
                    return ipv4_set, ipv6_set
            except:
                pass
            
            # 尝试HTML格式
            try:
                soup = BeautifulSoup(response.text, 'html.parser')
                # 搜索IPv4
                ipv4_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
                found_ipv4s = re.findall(ipv4_pattern, response.text)
                for ip in found_ipv4s:
                    if self.is_valid_ipv4(ip):
                        ipv4_set.add(ip)
                
                # 搜索IPv6
                ipv6_pattern = self._get_ipv6_pattern()
                found_ipv6s = re.findall(ipv6_pattern, response.text)
                for ipv6 in found_ipv6s:
                    if self.is_valid_ipv6(ipv6):
                        ipv6_set.add(ipv6)
                
                if ipv4_set or ipv6_set:
                    logger.info(f"从 {url} 的HTML中爬取到 {len(ipv4_set)} 个IPv4地址和 {len(ipv6_set)} 个IPv6地址")
                    return ipv4_set, ipv6_set
            except:
                pass
            
            # 纯文本搜索
            ipv4_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
            found_ipv4s = re.findall(ipv4_pattern, response.text)
            for ip in found_ipv4s:
                if self.is_valid_ipv4(ip):
                    ipv4_set.add(ip)
            
            ipv6_pattern = self._get_ipv6_pattern()
            found_ipv6s = re.findall(ipv6_pattern, response.text)
            for ipv6 in found_ipv6s:
                if self.is_valid_ipv6(ipv6):
                    ipv6_set.add(ipv6)
            
            logger.info(f"从 {url} 爬取到 {len(ipv4_set)} 个IPv4地址和 {len(ipv6_set)} 个IPv6地址")
            return ipv4_set, ipv6_set
            
        except Exception as e:
            logger.error(f"爬取 {url} 时出错: {e}")
            return set(), set()

    def _get_ipv6_pattern(self) -> str:
        """获取IPv6正则表达式模式"""
        # IPv6地址的复杂模式（简化的版本，覆盖大多数情况）
        return r'(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|' \
               r'(?:[0-9a-fA-F]{1,4}:){1,7}:|' \
               r'(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|' \
               r'(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|' \
               r'(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|' \
               r'(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|' \
               r'(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|' \
               r'[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})|' \
               r':(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)|' \
               r'fe80:(?::[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]+|' \
               r'::(?:ffff(?::0{1,4})?:)?(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(?:\.(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}'
    
    def is_valid_ipv4(self, ip: str) -> bool:
        """验证IPv4地址是否有效"""
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
    
    def is_valid_ipv6(self, ipv6: str) -> bool:
        """验证IPv6地址是否有效"""
        # 首先用正则表达式进行基本验证
        ipv6_pattern = self._get_ipv6_pattern()
        if not re.fullmatch(ipv6_pattern, ipv6):
            return False
        
        # 进一步验证（简化验证）
        parts = ipv6.split(':')
        
        # 处理双冒号情况
        if '::' in ipv6:
            if ipv6.count('::') > 1:
                return False
            # 双冒号可以表示多个0段
        
        # 检查每个段的长度和内容
        for part in parts:
            if not part:
                continue  # 空段可能是双冒号的一部分
            if len(part) > 4:
                return False
            try:
                int(part, 16)
            except ValueError:
                return False
        
        return True
    
    def is_valid_domain(self, domain: str) -> bool:
        """验证域名是否有效"""
        # 基本的域名验证规则
        domain_pattern = r'^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9](\.[a-zA-Z]{2,})+$'
        
        if not re.match(domain_pattern, domain):
            return False
        
        # 排除常见的一些非域名字符串
        excluded_patterns = [
            r'\.com$',  # 需要更具体的域名，不是顶级域名本身
            r'\.net$',
            r'\.org$',
            r'\.gov$',
            r'\.edu$',
            r'example\.com$',
            r'test\.com$',
            r'localhost$'
        ]
        
        for pattern in excluded_patterns:
            if re.search(pattern, domain, re.IGNORECASE):
                # 检查是否只是顶级域名本身（没有子域名）
                if domain.count('.') == 1:
                    return False
        
        # 域名长度检查
        if len(domain) < 4 or len(domain) > 253:
            return False
        
        # 确保域名包含至少一个点
        if '.' not in domain:
            return False
        
        return True
    
    def save_to_files(self, ipv4_filename: str = 'ipv4.txt', ipv6_filename: str = 'ipv6.txt', domain_filename: str = 'domain.txt'):
        """将IPv4、IPv6地址和域名分别保存到文件"""
        logger.info(f"开始保存IP和域名到文件")
        
        # 保存IPv4地址
        if self.ipv4_set:
            sorted_ipv4 = sorted(list(self.ipv4_set))
            with open(ipv4_filename, 'w', encoding='utf-8') as f:
                for ip in sorted_ipv4:
                    f.write(f"{ip}\n")
            logger.info(f"共保存 {len(sorted_ipv4)} 个IPv4地址到 {ipv4_filename}")
        
        # 保存IPv6地址
        if self.ipv6_set:
            sorted_ipv6 = sorted(list(self.ipv6_set))
            with open(ipv6_filename, 'w', encoding='utf-8') as f:
                for ip in sorted_ipv6:
                    f.write(f"{ip}\n")
            logger.info(f"共保存 {len(sorted_ipv6)} 个IPv6地址到 {ipv6_filename}")
        
        # 保存域名
        if self.domain_set:
            sorted_domains = sorted(list(self.domain_set))
            with open(domain_filename, 'w', encoding='utf-8') as f:
                for domain in sorted_domains:
                    f.write(f"{domain}\n")
            logger.info(f"共保存 {len(sorted_domains)} 个域名到 {domain_filename}")
    
    def save_combined_to_file(self, filename: str = 'ip.txt'):
        """将IPv4、IPv6地址和域名合并保存到一个文件"""
        logger.info(f"开始保存所有IP和域名到文件 {filename}")
        
        # 合并所有项目
        all_items = []
        all_items.extend(sorted(list(self.ipv4_set)))
        all_items.extend(sorted(list(self.ipv6_set)))
        all_items.extend(sorted(list(self.domain_set)))
        
        with open(filename, 'w', encoding='utf-8') as f:
            for item in all_items:
                f.write(f"{item}\n")
        
        logger.info(f"共保存 {len(all_items)} 个条目到 {filename}")
        logger.info(f"其中包含 {len(self.ipv4_set)} 个IPv4地址, {len(self.ipv6_set)} 个IPv6地址, {len(self.domain_set)} 个域名")
    
    def run(self, urls: list = None):
        """主运行函数"""
        if urls is None:
            urls = [
                'https://ip.164746.xyz',
                'https://api.uouin.com/cloudflare.html',
                'https://www.wetest.vip/page/cloudflare/address_v4.html',
                'https://www.wetest.vip/page/cloudflare/address_v6.html',
                'https://stock.hostmonit.com/CloudFlareYes',
                'https://stock.hostmonit.com/CloudFlareYesV6',
                'https://cf.090227.xyz/'  # 新增的域名网站
            ]
        logger.info(f"开始爬取 {len(urls)} 个网站")
        
        # 定义网站与爬取方法的映射
        website_handlers = {
            'ip.164746.xyz': self.scrape_ip_164746_xyz,
            'api.uouin.com': self.scrape_api_uouin,
            'www.wetest.vip': self.scrape_wetest_vip,
            'stock.hostmonit.com': self.scrape_hostmonit_api,  # 同时处理IPv4和IPv6
            'cf.090227.xyz': self.scrape_cf_090227_xyz  # 新增域名网站处理器
        }
        
        for url in urls:
            logger.info(f"正在处理: {url}")
            
            # 确定使用哪个爬取方法
            handler = None
            for domain, method in website_handlers.items():
                if domain in url:
                    handler = method
                    break
            
            if handler is None:
                handler = self.scrape_generic_website
            
            # 爬取数据
            ipv4_items, ipv6_items = handler(url)
            
            # 添加到对应的集合
            if ipv4_items:
                before_count = len(self.ipv4_set)
                self.ipv4_set.update(ipv4_items)
                added_count = len(self.ipv4_set) - before_count
                logger.info(f"从 {url} 添加了 {added_count} 个新IPv4地址")
            
            if ipv6_items:
                before_count = len(self.ipv6_set)
                self.ipv6_set.update(ipv6_items)
                added_count = len(self.ipv6_set) - before_count
                logger.info(f"从 {url} 添加了 {added_count} 个新IPv6地址")
            
            # 对于域名网站，特殊处理
            if 'cf.090227.xyz' in url:
                # 从域名网站返回的第一个集合是域名
                domains = ipv4_items  # 注意：这里ipv4_items实际上包含域名
                if domains:
                    before_count = len(self.domain_set)
                    self.domain_set.update(domains)
                    added_count = len(self.domain_set) - before_count
                    logger.info(f"从 {url} 添加了 {added_count} 个新域名")
            
            # 添加延迟避免被屏蔽
            time.sleep(1)
        
        # 保存到文件（可以选择分开保存或合并保存）
        #self.save_to_files('ipv4.txt', 'ipv6.txt', 'domain.txt')
        # 或者合并保存到一个文件
        self.save_combined_to_file('ip.txt')
        
        # 打印统计信息
        logger.info("=" * 50)
        logger.info(f"爬取完成！总共收集到:")
        logger.info(f"  - {len(self.ipv4_set)} 个唯一IPv4地址")
        logger.info(f"  - {len(self.ipv6_set)} 个唯一IPv6地址")
        logger.info(f"  - {len(self.domain_set)} 个唯一域名")
        
        # 显示前5个IPv4作为示例
        if self.ipv4_set:
            logger.info("示例IPv4地址:")
            for i, ip in enumerate(sorted(self.ipv4_set)[:5]):
                logger.info(f"  {i+1}. {ip}")
            if len(self.ipv4_set) > 5:
                logger.info(f"  ... 还有 {len(self.ipv4_set) - 5} 个IPv4地址")
        
        # 显示前5个IPv6作为示例
        if self.ipv6_set:
            logger.info("示例IPv6地址:")
            for i, ip in enumerate(sorted(self.ipv6_set)[:5]):
                logger.info(f"  {i+1}. {ip}")
            if len(self.ipv6_set) > 5:
                logger.info(f"  ... 还有 {len(self.ipv6_set) - 5} 个IPv6地址")
        
        # 显示前5个域名作为示例
        if self.domain_set:
            logger.info("示例域名:")
            for i, domain in enumerate(sorted(self.domain_set)[:5]):
                logger.info(f"  {i+1}. {domain}")
            if len(self.domain_set) > 5:
                logger.info(f"  ... 还有 {len(self.domain_set) - 5} 个域名")


def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("IP和域名爬虫脚本启动")
    logger.info("=" * 50)
    
    # 创建爬虫实例
    scraper = IPScraper()
    
    # 定义要爬取的网站列表（可以在此添加新网站）
    urls_to_scrape = [
        'https://ip.164746.xyz',
        'https://api.uouin.com/cloudflare.html',
        'https://www.wetest.vip/page/cloudflare/address_v4.html',
        'https://www.wetest.vip/page/cloudflare/address_v6.html',
        'https://stock.hostmonit.com',
        'https://cf.090227.xyz/'  # 新增的域名网站
    ]
    
    # 运行爬虫
    scraper.run(urls_to_scrape)
    
    logger.info("脚本执行完成，自动退出")


if __name__ == "__main__":
    # 安装依赖的提示
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        print("缺少必要的依赖库，请运行以下命令安装：")
        print("pip install requests beautifulsoup4")
        exit(1)
    
    main()
