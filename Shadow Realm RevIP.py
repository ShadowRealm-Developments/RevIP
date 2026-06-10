#!/usr/bin/env python3
"""
SHADOW REALM REV IP – Ultimate Domain/IP/Subdomain Harvester
Author : @DarkKnight
Version: 2.0 (2026 Edition)
"""
import sys
import json
import socket
import argparse
import time
import concurrent.futures
from urllib.parse import urlparse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from colorama import init, Fore, Style

init(autoreset=True)

BANNER = f"""{Fore.RED}
 █████  ██    ██ ██████   █████      ██████  ███████ ██    ██     ██ ██████  
██   ██ ██    ██ ██   ██ ██   ██     ██   ██ ██      ██    ██     ██ ██   ██ 
███████ ██    ██ ██████  ███████     ██████  █████   ██    ██     ██ ██████  
██   ██ ██    ██ ██   ██ ██   ██     ██   ██ ██       ██  ██      ██ ██      
██   ██  ██████  ██   ██ ██   ██     ██   ██ ███████   ████       ██ ██      
                                                                             
                                                                                              
                                                      
{Style.RESET_ALL}"""
print(BANNER)
print(f"{Fore.CYAN}[ @DarkKnight // shadow-realm.gg // 2026 ]{Style.RESET_ALL}")
print(f"{Fore.YELLOW}[>] Module: Domain Intelligence | IP Recon | Sub Hunter{Style.RESET_ALL}")
print(f"{Fore.YELLOW}[>] Status: Finder // BruteForce // CVE Ready{Style.RESET_ALL}")
print()

# ---------- Session with retry logic ----------
def create_session():
    """Create a requests session with retry logic."""
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    return session

# ---------- Core Functions ----------
def fetch_crtsh(keyword, wildcard=True, max_retries=3):
    """Query crt.sh for certificate transparency logs with retry logic."""
    url = f"https://crt.sh/?q=%25.{keyword}%25&output=json"
    
    for attempt in range(max_retries):
        try:
            session = create_session()
            resp = session.get(url, timeout=30)
            
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    domains = set()
                    for entry in data:
                        name_value = entry.get("name_value", "")
                        for domain in name_value.split("\n"):
                            domain = domain.strip().lower()
                            if domain and not domain.startswith("*."):
                                domains.add(domain)
                            elif domain.startswith("*.") and wildcard:
                                domains.add(domain)
                            elif domain.startswith("*.") and not wildcard:
                                domains.add(domain[2:])
                    return sorted(domains)
                except json.JSONDecodeError:
                    print(f"{Fore.YELLOW}[!] JSON decode failed (attempt {attempt+1}){Style.RESET_ALL}")
                    continue
            elif resp.status_code == 502:
                print(f"{Fore.YELLOW}[!] crt.sh overloaded (502). Retry in 5...{Style.RESET_ALL}")
                time.sleep(5)
                continue
            else:
                print(f"{Fore.YELLOW}[!] crt.sh code {resp.status_code} (attempt {attempt+1}){Style.RESET_ALL}")
                time.sleep(2)
                
        except requests.exceptions.Timeout:
            print(f"{Fore.YELLOW}[!] Timeout (attempt {attempt+1}). Waiting 10...{Style.RESET_ALL}")
            time.sleep(10)
        except requests.exceptions.ConnectionError as e:
            print(f"{Fore.YELLOW}[!] Connection error: {e}. Retrying...{Style.RESET_ALL}")
            time.sleep(5)
        except Exception as e:
            print(f"{Fore.YELLOW}[!] Error: {e}. Retrying...{Style.RESET_ALL}")
            time.sleep(3)
    
    print(f"{Fore.RED}[!] crt.sh failed after {max_retries} attempts.{Style.RESET_ALL}")
    return []

def fetch_subdomains_alternative(domain):
    """Alternative subdomain discovery using SecurityTrails free API (limited) or others."""
    subdomains = set()
    
    # Alienvault OTX (no key needed)
    try:
        url = f"https://otx.alienvault.com/api/v1/indicators/domain/{domain}/passive_dns"
        session = create_session()
        resp = session.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            for entry in data.get('passive_dns', []):
                hostname = entry.get('hostname', '')
                if hostname and domain in hostname:
                    subdomains.add(hostname.strip().lower())
    except Exception:
        pass
    
    # URLscan.io (no key needed)
    try:
        url = f"https://urlscan.io/api/v1/search/?q=domain:{domain}&size=100"
        session = create_session()
        resp = session.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            for result in data.get('results', []):
                page_domain = result.get('page', {}).get('domain', '')
                if page_domain and domain in page_domain:
                    subdomains.add(page_domain.strip().lower())
    except Exception:
        pass
    
    return sorted(subdomains)

def domain_to_ip(domain):
    """Resolve domain to IP (IPv4)."""
    try:
        return socket.gethostbyname(domain)
    except:
        return None

def reverse_ip_lookup(ip):
    """Reverse IP lookup using multiple sources."""
    domains = set()
    
    # hackertarget.com
    try:
        url = f"https://api.hackertarget.com/reverseiplookup/?q={ip}"
        session = create_session()
        resp = session.get(url, timeout=20)
        if resp.status_code == 200:
            lines = resp.text.strip().split("\n")
            if "error" not in resp.text.lower() and "api limit" not in resp.text.lower():
                for line in lines:
                    if line.strip():
                        domains.add(line.strip().lower())
    except Exception as e:
        print(f"{Fore.YELLOW}[!] Hackertarget error: {e}{Style.RESET_ALL}")
    
    # ViewDNS.info fallback
    try:
        url = f"https://viewdns.info/reverseip/?host={ip}&t=1"
        session = create_session()
        resp = session.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, 'html.parser')
            for td in soup.find_all('td'):
                text = td.get_text().strip()
                if '.' in text and not text.startswith('http'):
                    domains.add(text.lower())
    except Exception:
        pass
    
    return sorted(domains)

def subdomain_brute(domain, wordlist):
    """Brute force subdomains using a wordlist (threaded)."""
    found = []
    
    def check_subdomain(sub):
        full = f"{sub}.{domain}"
        try:
            socket.gethostbyname(full)
            return full
        except:
            return None
    
    print(f"{Fore.MAGENTA}[*] Brute scanning {len(wordlist)} entries...{Style.RESET_ALL}")
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        results = executor.map(check_subdomain, wordlist)
        for result in results:
            if result:
                found.append(result)
                print(f"{Fore.GREEN}[+] Live: {result}{Style.RESET_ALL}")
    
    return found

# ---------- Interactive Menu ----------
def menu():
    print(f"{Fore.CYAN}┌─────────────────────────────────┐")
    print(f"│ [1] Domain Hunter                │")
    print(f"│ [2] IP Scanner / Reverse Lookup  │")
    print(f"│ [3] Subdomain Enumerator         │")
    print(f"│ [4] Exit                         │")
    print(f"└─────────────────────────────────┘{Style.RESET_ALL}")
    return input(f"{Fore.GREEN}@DarkKnight:~# {Style.RESET_ALL}")

def handle_domain_scraper():
    keyword = input(f"{Fore.GREEN}[?] Target keyword: {Style.RESET_ALL}").strip()
    if not keyword:
        print(f"{Fore.RED}[!] Empty input.{Style.RESET_ALL}")
        return
    
    print(f"\n{Fore.MAGENTA}[*] Harvesting domains for: {keyword}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[*] Estimated wait: 30-60 sec{Style.RESET_ALL}")
    
    domains = fetch_crtsh(keyword)
    
    if not domains:
        print(f"{Fore.YELLOW}[!] crt.sh empty. Switching to fallback...{Style.RESET_ALL}")
        domains = fetch_subdomains_alternative(keyword)
    
    if not domains:
        print(f"{Fore.RED}[!] Zero results.{Style.RESET_ALL}")
        return
    
    print(f"\n{Fore.YELLOW}[+] Captured {len(domains)} domains:{Style.RESET_ALL}")
    for d in domains[:50]:
        print(f"  {d}")
    if len(domains) > 50:
        print(f"{Fore.CYAN}[...] +{len(domains) - 50} more{Style.RESET_ALL}")
    
    save = input(f"{Fore.GREEN}[?] Save to file? (y/n): {Style.RESET_ALL}").lower()
    if save == 'y':
        filename = f"harvest_{keyword.replace('.', '_')}.txt"
        with open(filename, "w") as f:
            f.write("\n".join(domains))
        print(f"{Fore.CYAN}[+] Saved: {filename}{Style.RESET_ALL}")

def handle_ip():
    target = input(f"{Fore.GREEN}[?] Domain/IP: {Style.RESET_ALL}").strip()
    if not target:
        return
    
    try:
        socket.inet_aton(target)
        ip = target
        domain = None
    except socket.error:
        domain = target
        ip = domain_to_ip(domain)
        if not ip:
            print(f"{Fore.RED}[!] Resolution failed.{Style.RESET_ALL}")
            return
        print(f"{Fore.CYAN}[+] {domain} -> {ip}{Style.RESET_ALL}")
    
    print(f"{Fore.MAGENTA}[*] Reverse scanning {ip}...{Style.RESET_ALL}")
    reversed_domains = reverse_ip_lookup(ip)
    
    if reversed_domains:
        print(f"\n{Fore.YELLOW}[+] {len(reversed_domains)} hosted domains:{Style.RESET_ALL}")
        for d in reversed_domains[:30]:
            print(f"  {d}")
        if len(reversed_domains) > 30:
            print(f"{Fore.CYAN}[...] +{len(reversed_domains) - 30} more{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}[!] No reverse data (rate limit?).{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[*] Tip: VPN/proxy may help{Style.RESET_ALL}")

def handle_subdomain():
    mode = input(f"{Fore.GREEN}[?] Single or mass? (s/m): {Style.RESET_ALL}").lower()
    
    if mode == 's':
        domain = input(f"{Fore.GREEN}[?] Target domain: {Style.RESET_ALL}").strip()
        if not domain:
            return
        
        print(f"\n{Fore.MAGENTA}[*] Enumerating {domain}...{Style.RESET_ALL}")
        
        subs = fetch_crtsh(domain, wildcard=False)
        subs = [s for s in subs if s != domain and not s.startswith('*.')]
        
        if not subs:
            print(f"{Fore.YELLOW}[!] crt.sh empty. Fallback engaged...{Style.RESET_ALL}")
            subs = fetch_subdomains_alternative(domain)
        
        if subs:
            print(f"\n{Fore.YELLOW}[+] {len(subs)} subdomains:{Style.RESET_ALL}")
            for s in subs:
                print(f"  {s}")
        else:
            print(f"{Fore.RED}[!] Nothing found.{Style.RESET_ALL}")
    
    elif mode == 'm':
        file_path = input(f"{Fore.GREEN}[?] Domains file: {Style.RESET_ALL}").strip()
        try:
            with open(file_path, 'r') as f:
                domains = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"{Fore.RED}[!] File missing.{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.MAGENTA}[*] Mass scan on {len(domains)} domains...{Style.RESET_ALL}")
        
        all_subs = {}
        for dom in domains:
            print(f"{Fore.CYAN}[>] Processing: {dom}{Style.RESET_ALL}")
            subs = fetch_crtsh(dom, wildcard=False)
            subs = [s for s in subs if s != dom and not s.startswith('*.')]
            
            if not subs:
                subs = fetch_subdomains_alternative(dom)
            
            all_subs[dom] = subs
            if subs:
                print(f"{Fore.GREEN}[{dom}] +{len(subs)} found{Style.RESET_ALL}")
        
        print(f"\n{Fore.YELLOW}[+] Scan Summary:{Style.RESET_ALL}")
        for dom, subs in all_subs.items():
            print(f"  {dom}: {len(subs)} subs")
    
    else:
        print(f"{Fore.RED}[!] Invalid.{Style.RESET_ALL}")

def main():
    while True:
        choice = menu()
        if choice == "1":
            handle_domain_scraper()
        elif choice == "2":
            handle_ip()
        elif choice == "3":
            handle_subdomain()
        elif choice == "4":
            print(f"{Fore.BLUE}[*] shadow-realm.gg // @DarkKnight // 2026 -- Exiting{Style.RESET_ALL}")
            sys.exit(0)
        else:
            print(f"{Fore.RED}[!] Wrong option.{Style.RESET_ALL}")
        input(f"\n{Fore.YELLOW}[>] Press Enter to continue...{Style.RESET_ALL}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="shadow-realm.gg // @DarkKnight")
    parser.add_argument("--keyword", help="Domain harvest by keyword")
    parser.add_argument("--reverse-ip", help="Reverse IP lookup")
    parser.add_argument("--subdomain", help="Subdomain enumeration")
    parser.add_argument("--mass-sub", help="Mass subdomain from file")
    parser.add_argument("--timeout", type=int, default=30, help="Request timeout")
    args = parser.parse_args()
    
    if any([args.keyword, args.reverse_ip, args.subdomain, args.mass_sub]):
        if args.keyword:
            domains = fetch_crtsh(args.keyword)
            if domains:
                print("\n".join(domains))
        elif args.reverse_ip:
            rev = reverse_ip_lookup(args.reverse_ip)
            if rev:
                print("\n".join(rev))
        elif args.subdomain:
            subs = fetch_crtsh(args.subdomain, wildcard=False)
            subs = [s for s in subs if s != args.subdomain and not s.startswith('*.')]
            if not subs:
                subs = fetch_subdomains_alternative(args.subdomain)
            if subs:
                print("\n".join(subs))
        elif args.mass_sub:
            try:
                with open(args.mass_sub) as f:
                    for dom in f:
                        dom = dom.strip()
                        if dom:
                            subs = fetch_crtsh(dom, wildcard=False)
                            subs = [s for s in subs if s != dom and not s.startswith('*.')]
                            if not subs:
                                subs = fetch_subdomains_alternative(dom)
                            for s in subs:
                                print(s)
            except FileNotFoundError:
                print("File not found")
    else:
        main()
