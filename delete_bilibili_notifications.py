import time
import os
import sys


DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/128.0.0.0 Safari/537.36"
)

NOTIFICATION_TYPES = {
    1: ("点赞", "love"),
    2: ("回复", "reply"),
    3: ("@我", "at"),
}


def _get_chromedriver_path():
    """获取 ChromeDriver 路径，优先使用同目录下的 chromedriver.exe"""
    # PyInstaller 打包后的临时目录
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, 'chromedriver.exe')
    # 开发环境下的同目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    driver_path = os.path.join(current_dir, 'chromedriver.exe')
    if os.path.exists(driver_path):
        return driver_path
    return None


def _build_chrome_driver(headless=False):
    """构建 Chrome WebDriver，失败时返回 None。"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
    except ImportError:
        print("[错误] 未安装 selenium，请执行：")
        print("    .venv\\Scripts\\python -m pip install selenium webdriver-manager")
        return None

    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument(f"--user-agent={DEFAULT_UA}")
    if headless:
        chrome_options.add_argument("--headless=new")

    try:
        # 优先使用打包的或同目录下的 ChromeDriver
        driver_path = _get_chromedriver_path()
        if driver_path:
            print(f"使用本地 ChromeDriver: {driver_path}")
            service = Service(driver_path)
            return webdriver.Chrome(service=service, options=chrome_options)
        
        # 降级使用 webdriver-manager
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            return webdriver.Chrome(service=service, options=chrome_options)
        except ImportError:
            pass
        
        # 最后尝试系统 PATH 中的 chromedriver
        return webdriver.Chrome(options=chrome_options)
    except Exception as e:
        print(f"[错误] 无法启动 Chrome：{e}")
        print("  解决方案：")
        print("  1) 确认已安装 Chrome 浏览器")
        print("  2) 手动下载 ChromeDriver 并放到程序同目录中")
        return None


def login_by_qr(driver):
    """引导用户扫码登录，返回是否成功。"""
    print("\n正在打开 B 站首页，请扫码登录...")
    driver.get("https://www.bilibili.com/")
    print("操作步骤：")
    print("  1) 点击浏览器右上角的【登录】按钮")
    print("  2) 使用手机 B 站 APP 扫码完成登录")
    print("  3) 登录成功后回到终端按回车键继续")
    input("（按回车键继续...）")

    start_time = time.time()
    timeout = 600
    while time.time() - start_time < timeout:
        try:
            driver.get("https://message.bilibili.com/")
            time.sleep(2)
            cookies = driver.get_cookies()
            cookie_dict = {c["name"]: c["value"] for c in cookies}
            if cookie_dict.get("SESSDATA") and cookie_dict.get("DedeUserID"):
                print("检测到登录成功！")
                return True
        except Exception:
            pass
        print("尚未检测到登录状态，请确认已完成扫码...（3秒后重试）")
        time.sleep(3)

    print("登录超时")
    return False


def delete_notifications_by_ui(driver, notify_type):
    """在浏览器中通过 UI 删除指定类型的通知。"""
    name, url_suffix = NOTIFICATION_TYPES[notify_type]
    url = f"https://message.bilibili.com/#/{url_suffix}"

    print(f"\n===== 开始清理【{name}】通知 =====")
    driver.get(url)
    time.sleep(5)

    total_deleted = 0
    max_cycles = 50

    for cycle in range(max_cycles):
        try:
            from selenium.webdriver.common.by import By

            items = driver.find_elements(By.CSS_SELECTOR, "div.interaction-item")
            if not items:
                print(f"  第 {cycle+1} 轮：未找到通知，结束")
                break

            print(f"  第 {cycle+1} 轮：找到 {len(items)} 条通知")
            cycle_deleted = 0

            for item in items:
                try:
                    driver.execute_script("""
                        const container = arguments[0];
                        
                        let noNotifyBtn = null;
                        const allElements = container.querySelectorAll('*');
                        for (const el of allElements) {
                            if (el.textContent && el.textContent.includes('不再通知')) {
                                noNotifyBtn = el;
                                break;
                            }
                        }
                        
                        if (noNotifyBtn) {
                            noNotifyBtn.click();
                            
                            const startTime = Date.now();
                            while (Date.now() - startTime < 2000) {
                                let confirmBtn = null;
                                const allBtns = document.querySelectorAll('button');
                                for (const btn of allBtns) {
                                    if (btn.textContent && btn.textContent.includes('确认')) {
                                        confirmBtn = btn;
                                        break;
                                    }
                                }
                                if (confirmBtn) {
                                    confirmBtn.click();
                                    break;
                                }
                                for (let j = 0; j < 1000000; j++);
                            }
                            
                            for (let j = 0; j < 5000000; j++);
                        }
                    """, item)
                    
                    time.sleep(1)
                    
                    delete_ok = driver.execute_script("""
                        const container = arguments[0];
                        const deleteBtn = container.querySelector('.interaction-item__btn.delete, button[class*="delete"]');
                        if (deleteBtn) {
                            deleteBtn.click();
                            return true;
                        }
                        const btns = container.querySelectorAll('button');
                        for (const b of btns) {
                            const svg = b.querySelector('svg');
                            if (svg || (b.textContent && b.textContent.includes('删除'))) {
                                b.click();
                                return true;
                            }
                        }
                        return false;
                    """, item)

                    if delete_ok:
                        time.sleep(0.8)
                        try:
                            confirm = driver.find_element(
                                By.CSS_SELECTOR,
                                "button.b-modal-button.b-modal-confirm, "
                                "button.bili-modal__confirm-btn"
                            )
                            if confirm.is_displayed():
                                confirm.click()
                                total_deleted += 1
                                cycle_deleted += 1
                        except Exception:
                            pass
                        time.sleep(1)
                except Exception as e:
                    continue

            if cycle_deleted > 0:
                print(f"  本轮删除 {cycle_deleted} 条，累计 {total_deleted} 条")
                driver.refresh()
                time.sleep(5)
            else:
                print(f"  本轮未删除任何通知")
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)

        except Exception as e:
            print(f"  第 {cycle+1} 轮出错：{e}")
            break

    print(f"===== 【{name}】清理完成，共删除 {total_deleted} 条 =====")
    return total_deleted


def select_notification_types():
    print("\n请选择要清理的通知类型：")
    print("  1) 仅点赞")
    print("  2) 仅回复")
    print("  3) 仅 @我")
    print("  4) 全部三种（推荐）")
    choice = input("请输入选择（1/2/3/4，默认 4）：").strip() or "4"
    mapping = {"1": [1], "2": [2], "3": [3], "4": [1, 2, 3]}
    return mapping.get(choice, [1, 2, 3])


def main():
    print("=" * 60)
    print("B站通知清理工具（Selenium UI 模式）")
    print("=" * 60)

    driver = _build_chrome_driver()
    if driver is None:
        return

    try:
        if not login_by_qr(driver):
            print("登录失败，程序退出")
            return

        types = select_notification_types()

        total = 0
        for t in types:
            deleted = delete_notifications_by_ui(driver, t)
            total += deleted

        print(f"\n===== 全部完成，共删除 {total} 条通知 =====")

    finally:
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户中断，程序退出")
