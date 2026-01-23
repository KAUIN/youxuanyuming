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
        self.ip_set = set()  # 使用集合避免重复IP
        
    def scrape_ip_164746_xyz(self, url: str) -> Set[str]:
        """爬取第一个网站的IP信息"""
        logger.info(f"开始爬取 {url}")
        ips = set()
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 方法1: 通过a标签查找
            ip_links = soup.find_all('a', href=re.compile(r'ipv4/\d+\.\d+\.\d+\.\d+'))
            for link in ip_links:
                ip_match = re.search(r'ipv4/(\d+\.\d+\.\d+\.\d+)', link['href'])
                if ip_match:
                    ips.add(ip_match.group(1))
            
            # 方法2: 通过文本模式查找（备用方法）
            if not ips:
                ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
                found_ips = re.findall(ip_pattern, response.text)
                # 过滤掉一些明显不是IP的数字
                for ip in found_ips:
                    if all(0 <= int(part) <= 255 for part in ip.split('.')):
                        ips.add(ip)
            
            logger.info(f"从 {url} 爬取到 {len(ips)} 个IP")
            return ips
            
        except Exception as e:
            logger.error(f"爬取 {url} 时出错: {e}")
            return set()
    
    def scrape_api_uouin(self, url: str) -> Set[str]:
        """爬取第二个网站的IP信息"""
        logger.info(f"开始爬取 {url}")
        ips = set()
        
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
                    ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
                    if re.match(ip_pattern, ip_candidate):
                        ips.add(ip_candidate)
            
            # 备用方法：使用正则表达式直接搜索
            if not ips:
                ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
                found_ips = re.findall(ip_pattern, response.text)
                for ip in found_ips:
                    if all(0 <= int(part) <= 255 for part in ip.split('.')):
                        ips.add(ip)
            
            logger.info(f"从 {url} 爬取到 {len(ips)} 个IP")
            return ips
            
        except Exception as e:
            logger.error(f"爬取 {url} 时出错: {e}")
            return set()
    
    def scrape_wetest_vip(self, url: str) -> Set[str]:
        """爬取第三个网站的IP信息"""
        logger.info(f"开始爬取 {url}")
        ips = set()
        
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
                    ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
                    if re.match(ip_pattern, ip_text):
                        ips.add(ip_text)
            
            # 备用方法
            if not ips:
                ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
                found_ips = re.findall(ip_pattern, response.text)
                for ip in found_ips:
                    if all(0 <= int(part) <= 255 for part in ip.split('.')):
                        ips.add(ip)
            
            logger.info(f"从 {url} 爬取到 {len(ips)} 个IP")
            return ips
            
        except Exception as e:
            logger.error(f"爬取 {url} 时出错: {e}")
            return set()
    
    def scrape_hostmonit_api(self, url: str) -> Set[str]:
        """爬取hostmonit的API数据（使用正确的key和参数）"""
        url = 'https://api.hostmonit.com/get_optimization_ip'
        logger.info(f"开始爬取hostmonit API: {url}")
        ips = set()
        
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
            
            # 根据您提供的载荷设置
            payload = {"key": "iDetkOys"}
            
            logger.info(f"发送POST请求到 {url}")
            logger.info(f"请求载荷: {payload}")
            
            response = self.session.post(
                url, 
                headers=headers, 
                json=payload, 
                timeout=20
            )
            response.raise_for_status()
            
            logger.debug(f"响应状态码: {response.status_code}")
            logger.debug(f"响应内容类型: {response.headers.get('content-type')}")
            
            # 解析JSON响应
            data = json.loads(response.text)
            
            if data.get('code') == 200:
                for item in data.get('info', []):
                    if 'ip' in item and self.is_valid_ip(item['ip']):
                        ips.add(item['ip'])
                
                logger.info(f"从hostmonit API成功获取 {len(ips)} 个IP")
            else:
                logger.error(f"API返回错误code: {data.get('code')}")
                logger.error(f"响应内容: {data}")
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            logger.error(f"响应文本: {response.text[:500]}")
        except Exception as e:
            logger.error(f"爬取hostmonit API时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        return ips
    
    def scrape_generic_website(self, url: str) -> Set[str]:
        """通用爬取方法，用于未来添加新网站"""
        logger.info(f"开始通用爬取 {url}")
        ips = set()
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # 首先尝试JSON格式
            try:
                data = json.loads(response.text)
                def find_ips_in_dict(obj):
                    if isinstance(obj, dict):
                        for key, value in obj.items():
                            if isinstance(value, str) and self.is_valid_ip(value):
                                ips.add(value)
                            else:
                                find_ips_in_dict(value)
                    elif isinstance(obj, list):
                        for item in obj:
                            find_ips_in_dict(item)
                
                find_ips_in_dict(data)
                if ips:
                    logger.info(f"从 {url} 的JSON中爬取到 {len(ips)} 个IP")
                    return ips
            except:
                pass
            
            # 尝试HTML格式
            try:
                soup = BeautifulSoup(response.text, 'html.parser')
                ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
                found_ips = re.findall(ip_pattern, response.text)
                for ip in found_ips:
                    if self.is_valid_ip(ip):
                        ips.add(ip)
                
                if ips:
                    logger.info(f"从 {url} 的HTML中爬取到 {len(ips)} 个IP")
                    return ips
            except:
                pass
            
            # 纯文本搜索
            ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
            found_ips = re.findall(ip_pattern, response.text)
            for ip in found_ips:
                if self.is_valid_ip(ip):
                    ips.add(ip)
            
            logger.info(f"从 {url} 爬取到 {len(ips)} 个IP")
            return ips
            
        except Exception as e:
            logger.error(f"爬取 {url} 时出错: {e}")
            return set()

    def is_valid_ip(self, ip: str) -> bool:
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
    
    def save_to_file(self, filename: str = 'ip.txt'):
        """将IP地址保存到文件"""
        logger.info(f"开始保存IP到文件 {filename}")
        
        with open(filename, 'w', encoding='utf-8') as f:
            for ip in sorted(self.ip_set):
                f.write(f"{ip}\n")
        
        logger.info(f"共保存 {len(self.ip_set)} 个IP到 {filename}")
    
    def run(self, urls: list = None):
        """主运行函数"""
        if urls is None:
            urls = [
                'https://ip.164746.xyz',
                'https://api.uouin.com/cloudflare.html',
                'https://www.wetest.vip/page/cloudflare/address_v4.html',
                'https://stock.hostmonit.com/CloudFlareYes'
            ]
        
        logger.info(f"开始爬取 {len(urls)} 个网站")
        
        # 定义网站与爬取方法的映射
        website_handlers = {
            'ip.164746.xyz': self.scrape_ip_164746_xyz,
            'api.uouin.com': self.scrape_api_uouin,
            'www.wetest.vip': self.scrape_wetest_vip,
            'stock.hostmonit.com': self.scrape_hostmonit_api
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
            
            # 爬取IP
            ips = handler(url)
            
            # 添加到总集合
            before_count = len(self.ip_set)
            self.ip_set.update(ips)
            added_count = len(self.ip_set) - before_count
            
            logger.info(f"从 {url} 添加了 {added_count} 个新IP")
            
            # 添加延迟避免被屏蔽
            time.sleep(1)
        
        # 保存到文件
        self.save_to_file()
        
        # 打印统计信息
        logger.info("=" * 50)
        logger.info(f"爬取完成！总共收集到 {len(self.ip_set)} 个唯一IP地址")
        logger.info(f"IP地址已保存到 ip.txt")
        
        # 显示前10个IP作为示例
        if self.ip_set:
            logger.info("示例IP地址:")
            for i, ip in enumerate(sorted(self.ip_set)[:10]):
                logger.info(f"  {i+1}. {ip}")
            if len(self.ip_set) > 10:
                logger.info(f"  ... 还有 {len(self.ip_set) - 10} 个IP")


def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("IP爬虫脚本启动")
    logger.info("=" * 50)
    
    # 创建爬虫实例
    scraper = IPScraper()
    
    # 定义要爬取的网站列表（可以在此添加新网站）
    urls_to_scrape = [
        'https://ip.164746.xyz',
        'https://api.uouin.com/cloudflare.html',
        'https://www.wetest.vip/page/cloudflare/address_v4.html',
        'https://stock.hostmonit.com/CloudFlareYes'
        # 可以在此添加更多网站，例如：
        # 'https://example.com/ip-list.html',
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
