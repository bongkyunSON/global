import os
import sys
import threading
import subprocess
import time
import webbrowser
import tkinter as tk
from tkinter import messagebox
import winreg
import ctypes
from ctypes import wintypes
import signal
import atexit
import json
from pathlib import Path
import asyncio
import websockets

class PCControlClient:
    def __init__(self):
        self.backend_process = None
        self.config_file = Path("config.json")
        self.config = self.load_config()
        self.setup_directories()
        self.websocket_thread = None
        self.stop_websocket = threading.Event()
        
    def setup_directories(self):
        """필요한 디렉토리 생성"""
        os.makedirs("backend", exist_ok=True)
        os.makedirs("frontend", exist_ok=True)
        
    def load_config(self):
        """설정 파일 로드"""
        default_config = {
            "pc_number": 1,
            "server_port": 8000,
            "auto_start": True,
            "fullscreen": True
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 기본값과 병합
                    return {**default_config, **config}
            except:
                pass
                
        return default_config
        
    def save_config(self):
        """설정 파일 저장"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def check_admin_rights(self):
        """관리자 권한 확인"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
            
    def request_admin_rights(self):
        """관리자 권한 요청"""
        if not self.check_admin_rights():
            try:
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, " ".join(sys.argv), None, 1
                )
                sys.exit(0)
            except:
                messagebox.showerror("오류", "관리자 권한이 필요합니다.")
                sys.exit(1)
    
    def disable_system_keys(self):
        """시스템 키 비활성화 (관리자 권한 필요)"""
        try:
            # Windows API를 통한 키 후킹
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            
            # 후킹할 키들 정의
            self.blocked_keys = [
                0x5B,  # Left Windows key
                0x5C,  # Right Windows key  
                0x09,  # Tab
                0x1B,  # Escape
                0x73,  # F4
                0x7B,  # F12
            ]
            
            # 키보드 후킹 설정
            self.hook_id = None
            self.setup_keyboard_hook()
            
        except Exception as e:
            print(f"시스템 키 비활성화 실패: {e}")
    
    def setup_keyboard_hook(self):
        """키보드 후킹 설정"""
        try:
            import win32api
            import win32con
            import win32gui
            import win32hook
            
            def low_level_keyboard_proc(nCode, wParam, lParam):
                if nCode >= 0:
                    # 블록할 키 검사
                    if wParam in [win32con.WM_KEYDOWN, win32con.WM_SYSKEYDOWN]:
                        key_code = lParam[0]
                        # Alt+Tab, Alt+F4, Windows키 등 차단
                        if (key_code in self.blocked_keys or 
                            (win32api.GetAsyncKeyState(win32con.VK_MENU) & 0x8000 and key_code == 0x09) or  # Alt+Tab
                            (win32api.GetAsyncKeyState(win32con.VK_MENU) & 0x8000 and key_code == 0x73)):   # Alt+F4
                            return 1  # 키 입력 차단
                
                return win32api.CallNextHookEx(self.hook_id, nCode, wParam, lParam)
            
            # 후킹 설치
            self.hook_id = win32api.SetWindowsHookEx(
                win32con.WH_KEYBOARD_LL,
                low_level_keyboard_proc,
                win32api.GetModuleHandle(None),
                0
            )
            
        except ImportError:
            print("⚠️ pywin32가 설치되지 않아 고급 키 차단 기능을 사용할 수 없습니다.")
        except Exception as e:
            print(f"키보드 후킹 설정 실패: {e}")
    
    def disable_task_manager(self):
        """작업 관리자 비활성화 (레지스트리 방법)"""
        try:
            # 현재 사용자 레지스트리 키 수정
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
            
            # 레지스트리 키 열기/생성
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            except FileNotFoundError:
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            
            # 작업 관리자 비활성화 값 설정
            winreg.SetValueEx(key, "DisableTaskMgr", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            
            print("✅ 작업 관리자가 비활성화되었습니다.")
            
        except Exception as e:
            print(f"작업 관리자 비활성화 실패: {e}")
    
    def enable_task_manager(self):
        """작업 관리자 활성화 (복구)"""
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
            
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, "DisableTaskMgr", 0, winreg.REG_DWORD, 0)
                winreg.CloseKey(key)
                print("✅ 작업 관리자가 활성화되었습니다.")
            except FileNotFoundError:
                # 키가 없으면 이미 활성화된 상태
                pass
                
        except Exception as e:
            print(f"작업 관리자 활성화 실패: {e}")
    
    def start_backend_server(self):
        """백엔드 서버 시작"""
        try:
            # .env 파일 확인
            env_file = Path(".env")
            if not env_file.exists():
                messagebox.showerror("오류", 
                    ".env 파일이 없습니다.\n"
                    "SLACK_BOT_TOKEN과 SLACK_APP_TOKEN을 설정해주세요.")
                return False
            
            # 백엔드 서버 시작
            backend_dir = Path("backend")
            if not backend_dir.exists() or not (backend_dir / "main.py").exists():
                messagebox.showerror("오류", "백엔드 파일이 없습니다.")
                return False
            
            # Python 실행 명령
            cmd = [
                sys.executable, "-m", "uvicorn", 
                "backend.main:app", 
                "--host", "127.0.0.1", 
                "--port", str(self.config["server_port"]),
                "--reload"
            ]
            
            # 백그라운드에서 서버 실행
            self.backend_process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # 서버가 시작될 때까지 잠시 대기
            time.sleep(3)
            
            # 서버 상태 확인
            if self.backend_process.poll() is None:
                print("✅ 백엔드 서버가 시작되었습니다.")
                return True
            else:
                error_output = self.backend_process.stderr.read().decode('utf-8', errors='ignore')
                messagebox.showerror("서버 시작 오류", f"백엔드 서버 시작에 실패했습니다:\n{error_output}")
                return False
                
        except Exception as e:
            messagebox.showerror("오류", f"백엔드 서버 시작 중 오류가 발생했습니다:\n{str(e)}")
            return False
    
    async def websocket_listener(self):
        """웹소켓 리스너"""
        pc_number = self.config.get("pc_number", 1)
        port = self.config.get("server_port", 8000)
        uri = f"ws://127.0.0.1:{port}/ws/{pc_number}"
        
        while not self.stop_websocket.is_set():
            try:
                async with websockets.connect(uri) as websocket:
                    print(f"✅ WebSocket connected to {uri}")
                    while not self.stop_websocket.is_set():
                        try:
                            message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                            print(f"⬅️ Received message: {message}")
                            if message == "reboot":
                                self.reboot_pc()
                        except asyncio.TimeoutError:
                            continue # 1초마다 stop_websocket 플래그 확인
                        except websockets.exceptions.ConnectionClosed:
                            print("⚠️ WebSocket connection closed. Reconnecting...")
                            break # Reconnect loop
            except Exception as e:
                print(f"❌ WebSocket connection failed: {e}. Retrying in 5 seconds...")
                await asyncio.sleep(5)

    def start_websocket_listener(self):
        """웹소켓 리스너 스레드 시작"""
        def run_loop():
            asyncio.run(self.websocket_listener())

        self.websocket_thread = threading.Thread(target=run_loop, daemon=True)
        self.websocket_thread.start()
        print("🚀 WebSocket listener started in background thread.")

    def stop_websocket_listener(self):
        """웹소켓 리스너 스레드 종료"""
        if self.websocket_thread and self.websocket_thread.is_alive():
            self.stop_websocket.set()
            # self.websocket_thread.join() # 데몬 스레드라 join 필요 없음
            print("🛑 WebSocket listener stopped.")
            
    def reboot_pc(self):
        """PC 재부팅"""
        print("🔴 Rebooting PC in 3 seconds...")
        
        # 재부팅용 배치 파일 실행 (Python 없는 환경에서도 작동)
        try:
            # 재부팅용 배치 파일 생성
            batch_content = """@echo off
echo 시스템을 재시작합니다...
shutdown /r /t 3 /c "PC방 제어시스템에 의한 재시작"
"""
            batch_file = Path("restart_pc.bat")
            with open(batch_file, 'w', encoding='utf-8') as f:
                f.write(batch_content)
            
            # 배치 파일 실행
            subprocess.Popen([str(batch_file)], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            print("✅ 재부팅 명령이 실행되었습니다.")
            
        except Exception as e:
            print(f"❌ 재부팅 실행 실패: {e}")
            # 백업 방법: 직접 shutdown 명령 실행
            subprocess.run(["shutdown", "/r", "/t", "3"], shell=True)


    def open_browser(self):
        """전체화면 브라우저 열기"""
        try:
            url = f"http://127.0.0.1:{self.config['server_port']}"
            
            if self.config.get("fullscreen", True):
                # Chrome을 전체화면 키오스크 모드로 실행
                chrome_paths = [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                ]
                
                chrome_path = None
                for path in chrome_paths:
                    if os.path.exists(path):
                        chrome_path = path
                        break
                
                if chrome_path:
                    cmd = [
                        chrome_path,
                        "--kiosk",  # 전체화면 키오스크 모드
                        "--disable-web-security",
                        "--disable-features=VizDisplayCompositor",
                        "--start-fullscreen",
                        "--disable-infobars",
                        "--disable-extensions",
                        "--disable-plugins",
                        "--disable-translate",
                        "--no-first-run",
                        "--no-default-browser-check",
                        url
                    ]
                    
                    subprocess.Popen(cmd, creationflags=subprocess.CREATE_NO_WINDOW)
                    print("✅ Chrome 키오스크 모드로 실행되었습니다.")
                else:
                    # Chrome이 없으면 기본 브라우저 사용
                    webbrowser.open(url)
                    print("✅ 기본 브라우저로 실행되었습니다.")
            else:
                webbrowser.open(url)
                print("✅ 브라우저가 실행되었습니다.")
                
        except Exception as e:
            print(f"브라우저 실행 실패: {e}")
            messagebox.showerror("오류", f"브라우저 실행에 실패했습니다:\n{str(e)}")
    
    def cleanup(self):
        """정리 작업"""
        print("🧹 시스템 정리 중...")
        
        # 백엔드 서버 종료
        if self.backend_process and self.backend_process.poll() is None:
            self.backend_process.terminate()
            try:
                self.backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
            print("✅ 백엔드 서버가 종료되었습니다.")
        
        # 웹소켓 리스너 종료
        self.stop_websocket_listener()
        
        # 작업 관리자 활성화
        self.enable_task_manager()
        
        # 키보드 후킹 해제
        if hasattr(self, 'hook_id') and self.hook_id:
            try:
                import win32api
                win32api.UnhookWindowsHookEx(self.hook_id)
                print("✅ 키보드 후킹이 해제되었습니다.")
            except:
                pass
    
    def show_settings_dialog(self):
        """설정 대화상자 표시"""
        dialog = tk.Tk()
        dialog.title("PC방 제어시스템 설정")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        
        # PC 번호 설정
        tk.Label(dialog, text="PC 번호 (1-4):", font=("Arial", 10, "bold")).pack(pady=5)
        pc_number_var = tk.StringVar(value=str(self.config["pc_number"]))
        pc_entry = tk.Entry(dialog, textvariable=pc_number_var, font=("Arial", 12))
        pc_entry.pack(pady=5)
        
        # 포트 설정
        tk.Label(dialog, text="서버 포트:", font=("Arial", 10, "bold")).pack(pady=5)
        port_var = tk.StringVar(value=str(self.config["server_port"]))
        port_entry = tk.Entry(dialog, textvariable=port_var, font=("Arial", 12))
        port_entry.pack(pady=5)
        
        # 전체화면 옵션
        fullscreen_var = tk.BooleanVar(value=self.config.get("fullscreen", True))
        tk.Checkbutton(dialog, text="전체화면으로 실행", variable=fullscreen_var, 
                      font=("Arial", 10)).pack(pady=5)
        
        # 자동 시작 옵션
        auto_start_var = tk.BooleanVar(value=self.config.get("auto_start", True))
        tk.Checkbutton(dialog, text="프로그램 시작시 자동으로 서버 시작", variable=auto_start_var, 
                      font=("Arial", 10)).pack(pady=5)
        
        def save_settings():
            try:
                pc_num = int(pc_number_var.get())
                if pc_num < 1 or pc_num > 4:
                    raise ValueError("PC 번호는 1-4 사이여야 합니다.")
                
                port = int(port_var.get())
                if port < 1000 or port > 65535:
                    raise ValueError("포트는 1000-65535 사이여야 합니다.")
                
                self.config["pc_number"] = pc_num
                self.config["server_port"] = port
                self.config["fullscreen"] = fullscreen_var.get()
                self.config["auto_start"] = auto_start_var.get()
                
                self.save_config()
                messagebox.showinfo("성공", "설정이 저장되었습니다.")
                dialog.destroy()
                
            except ValueError as e:
                messagebox.showerror("오류", str(e))
        
        # 버튼
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="저장", command=save_settings, 
                 font=("Arial", 10, "bold"), bg="#4CAF50", fg="white", 
                 padx=20, pady=5).pack(side=tk.LEFT, padx=10)
        
        tk.Button(button_frame, text="취소", command=dialog.destroy, 
                 font=("Arial", 10), padx=20, pady=5).pack(side=tk.LEFT, padx=10)
        
        dialog.mainloop()
    
    def run(self):
        """메인 실행 함수"""
        print("🚀 PC방 제어시스템 클라이언트를 시작합니다...")
        
        # 설정 확인 및 업데이트
        if len(sys.argv) > 1 and sys.argv[1] == "--settings":
            self.show_settings_dialog()
            return
        
        # 관리자 권한 요청
        # self.request_admin_rights()  # 필요시 활성화
        
        # 정리 작업 등록
        atexit.register(self.cleanup)
        signal.signal(signal.SIGTERM, lambda s, f: self.cleanup())
        signal.signal(signal.SIGINT, lambda s, f: self.cleanup())
        
        try:
            # 시스템 보안 설정
            # self.disable_system_keys()
            # self.disable_task_manager()
            
            # 백엔드 서버 시작
            if not self.start_backend_server():
                return
            
            # 웹소켓 리스너 시작
            self.start_websocket_listener()
            
            # 브라우저 열기
            time.sleep(2)  # 서버 완전 시작 대기
            self.open_browser()
            
            print("✅ PC방 제어시스템이 성공적으로 시작되었습니다!")
            print(f"🖥️ PC 번호: {self.config['pc_number']}")
            print(f"🌐 서버 주소: http://127.0.0.1:{self.config['server_port']}")
            print("\n종료하려면 Ctrl+C를 누르세요.")
            
            # 서버 프로세스 유지
            if self.backend_process:
                self.backend_process.wait()
            
        except KeyboardInterrupt:
            print("\n👋 프로그램을 종료합니다...")
        except Exception as e:
            print(f"❌ 오류가 발생했습니다: {e}")
        finally:
            self.cleanup()

if __name__ == "__main__":
    client = PCControlClient()
    client.run() 