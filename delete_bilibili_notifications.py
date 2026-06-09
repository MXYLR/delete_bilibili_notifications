import time
import os
import sys
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

COOKIE_FILES = ['cookies.json', 'cookies.txt', 'data/cookies.json']

def _get_chromedriver_path():
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, 'chromedriver.exe')
    try:
        return ChromeDriverManager().install()
    except:
        pass
    for path in ['chromedriver.exe', os.path.join(os.path.dirname(__file__), 'chromedriver.exe')]:
        if os.path.exists(path):
            return path
    return None

def _load_cookies_from_file():
    for cookie_file in COOKIE_FILES:
        full_path = os.path.join(os.path.dirname(__file__), cookie_file)
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content.startswith('{'):
                        return json.loads(content)
                    else:
                        cookies = {}
                        for line in content.split(';'):
                            line = line.strip()
                            if '=' in line:
                                key, value = line.split('=', 1)
                                cookies[key.strip()] = value.strip()
                        return cookies
            except Exception as e:
                print(f"读取Cookie文件失败 {cookie_file}: {e}")
    return None

def _build_chrome_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins-discovery")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--enable-features=NetworkService")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--mute-audio")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--no-default-browser-check")
    
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    
    chromedriver_path = _get_chromedriver_path()
    if chromedriver_path:
        try:
            driver = webdriver.Chrome(service=Service(chromedriver_path), options=chrome_options)
            
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['zh-CN', 'zh', 'en']
                    });
                    Object.defineProperty(navigator, 'platform', {
                        get: () => 'Win32'
                    });
                    Object.defineProperty(navigator, 'product', {
                        get: () => 'Gecko'
                    });
                    window.chrome = {
                        runtime: {}
                    };
                '''
            })
            
            return driver
        except Exception as e:
            print(f"启动失败: {e}")
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh', 'en']
                });
                Object.defineProperty(navigator, 'platform', {
                    get: () => 'Win32'
                });
                Object.defineProperty(navigator, 'product', {
                    get: () => 'Gecko'
                });
                window.chrome = {
                    runtime: {}
                };
            '''
        })
        
        return driver
    except Exception as e:
        print(f"[错误] 无法启动 Chrome：{e}")
        return None

def _inject_cookies(driver, cookies):
    driver.get("https://www.bilibili.com")
    time.sleep(2)
    
    for name, value in cookies.items():
        try:
            driver.add_cookie({
                'name': name,
                'value': value,
                'domain': '.bilibili.com'
            })
        except Exception as e:
            pass
    
    driver.refresh()
    time.sleep(2)
    return True

def _validate_login(driver):
    try:
        driver.get("https://www.bilibili.com")
        time.sleep(3)
        login_btn = driver.find_elements("css selector", ".header-login-btn, .nav-user")
        return not login_btn
    except Exception as e:
        print(f"验证登录状态失败: {e}")
        return False

def login_and_clean():
    driver = _build_chrome_driver()
    if not driver:
        return
    
    try:
        print("===== B站通知清理工具 =====")
        
        cookies = _load_cookies_from_file()
        auto_login = False
        
        if cookies:
            print(f"检测到Cookie文件，尝试自动登录...")
            if _inject_cookies(driver, cookies):
                if _validate_login(driver):
                    print("Cookie登录成功！")
                    auto_login = True
        
        if not auto_login:
            print("正在打开 B 站首页，请扫码登录...")
            driver.get("https://www.bilibili.com/")
            input("\n请在浏览器中点击「登录」按钮并扫码完成登录，登录成功后按回车键继续...")
        
        print("\n登录成功，正在进入消息中心...")
        driver.get("https://message.bilibili.com/#/")
        time.sleep(5)
        
        print("\n请选择要清理的通知类型：")
        print("  1) 点赞通知")
        print("  2) 回复通知")
        print("  3) @我通知")
        print("  4) 全部（点赞+回复+@我）")
        choice = input("请输入选择（1/2/3/4，默认 4）：") or "4"
        
        types = []
        if choice == "1":
            types = [("点赞", "love")]
        elif choice == "2":
            types = [("回复", "reply")]
        elif choice == "3":
            types = [("@我", "at")]
        else:
            types = [("点赞", "love"), ("回复", "reply"), ("@我", "at")]
        
        total_deleted = 0
        
        for name, url_type in types:
            print(f"\n===== 开始清理【{name}】通知 =====")
            
            if url_type == "love":
                driver.get("https://message.bilibili.com/#/love")
            elif url_type == "reply":
                driver.get("https://message.bilibili.com/#/reply")
            elif url_type == "at":
                driver.get("https://message.bilibili.com/#/at")
            else:
                driver.get(f"https://message.bilibili.com/#/{url_type}")
            time.sleep(5)
            
            deleted = 0
            max_cycles = 50
            
            for cycle in range(max_cycles):
                items = driver.find_elements("css selector", ".interaction-item")
                if not items:
                    print(f"  第 {cycle+1} 轮：未找到通知")
                    break
                
                print(f"  第 {cycle+1} 轮：找到 {len(items)} 条通知")
                cycle_deleted = 0
                
                for item in items:
                    try:
                        actions = ActionChains(driver)
                        actions.move_to_element(item).perform()
                        
                        time.sleep(0.3)
                        
                        no_notify_btn = None
                        no_notify_spans = item.find_elements(By.XPATH, './/span[text()="不再通知"]')
                        if no_notify_spans:
                            no_notify_btn = no_notify_spans[0].find_element(By.XPATH, '..')
                        
                        if no_notify_btn:
                            no_notify_btn.click()
                            
                            try:
                                confirm_btn = WebDriverWait(driver, 5).until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, '.b-modal .b-modal-confirm'))
                                )
                                confirm_btn.click()
                                
                                WebDriverWait(driver, 5).until(
                                    EC.invisibility_of_element_located((By.CSS_SELECTOR, '.b-modal'))
                                )
                                
                                time.sleep(0.5)
                            except TimeoutException:
                                try:
                                    driver.execute_script("document.querySelector('.b-modal .b-modal-confirm')?.click();")
                                    time.sleep(1)
                                    driver.execute_script("document.querySelector('.b-modal')?.remove();")
                                except:
                                    pass
                        
                        time.sleep(0.3)
                        
                        delete_btns = item.find_elements(By.CSS_SELECTOR, '.interaction-item__btn.delete, button[class*="delete"]')
                        if not delete_btns:
                            delete_btns = item.find_elements(By.TAG_NAME, 'button')
                            
                        delete_btn = None
                        for btn in delete_btns:
                            try:
                                btn_text = btn.text.strip() if btn.text else ''
                                if btn_text == '' or btn_text == '删除' or btn.find_element(By.TAG_NAME, 'svg'):
                                    delete_btn = btn
                                    break
                            except:
                                pass
                        
                        if delete_btn:
                            delete_btn.click()
                            
                            try:
                                confirm_btn = WebDriverWait(driver, 5).until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, '.b-modal .b-modal-confirm'))
                                )
                                confirm_btn.click()
                                
                                WebDriverWait(driver, 5).until(
                                    EC.invisibility_of_element_located((By.CSS_SELECTOR, '.b-modal'))
                                )
                                
                                deleted += 1
                                cycle_deleted += 1
                                time.sleep(0.5)
                            except TimeoutException:
                                try:
                                    driver.execute_script("document.querySelector('.b-modal .b-modal-confirm')?.click();")
                                    time.sleep(1)
                                    driver.execute_script("document.querySelector('.b-modal')?.remove();")
                                    deleted += 1
                                    cycle_deleted += 1
                                except:
                                    pass
                    except Exception as e:
                        continue
                
                if cycle_deleted == 0:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)
                else:
                    driver.refresh()
                    time.sleep(2)
            
            print(f"===== 【{name}】 清理完成：成功 {deleted} 条 =====\n")
            total_deleted += deleted
        
        print(f"===== 全部完成，共删除 {total_deleted} 条通知 =====")
        
    except Exception as e:
        print(f"[错误] 清理过程出错: {e}")
    finally:
        input("\n按回车键关闭浏览器...")
        driver.quit()

if __name__ == "__main__":
    login_and_clean()
