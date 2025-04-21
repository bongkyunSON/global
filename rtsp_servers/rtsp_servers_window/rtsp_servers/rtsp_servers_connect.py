import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from requests.auth import HTTPDigestAuth, HTTPBasicAuth
from subprocess import Popen
import atexit
import requests
import time
import threading
import socket
import os
import psutil
from datetime import datetime
import sys

# ============ 상수 및 설정 ============
# RTSP 서버 설정
RTSP_SERVERS = {
    "192.168.116.41": "서버 1",
    "192.168.118.42": "서버 2"
}

# 스트림 장소 목록
STREAM_LOCATIONS = [
    "1so", "2so", "1se", "2se", "3se",
    "2gan", "3gan", "4gan", "5gan", "6gan",
    "7gan", "8gan", "9gan", "10gan", "11gan", "dae"
]

# 장치 리셋 IP 매핑
RESET_IPS = {
    "1so": "192.168.100.199", "2so": "192.168.101.199",
    "1se": "192.168.102.199", "2se": "192.168.103.199",
    "3se": "192.168.104.199", "2gan": "192.168.105.199",
    "3gan": "192.168.106.199", "4gan": "192.168.107.199",
    "5gan": "192.168.108.199", "6gan": "192.168.109.199",
    "7gan": "192.168.110.199", "8gan": "192.168.111.199",
    "9gan": "192.168.112.199", "10gan": "192.168.113.199",
    "11gan": "192.168.114.199", "dae": "192.168.120.199"
}

# 카메라 리스트: 회의장 이름, IP, 제어 방식
CAMERAS = [
    ("01소회의", "192.168.100.54", "visca"),
    ("02소회의", "192.168.101.54", "visca"),
    ("01세미나", "192.168.102.57", "http"),
    ("02세미나", "192.168.103.57", "visca"),
    ("03세미나", "192.168.104.54", "visca"),
    ("02간담회", "192.168.105.57", "http"),
    ("03간담회", "192.168.106.57", "http"),
    ("04간담회", "192.168.107.57", "http"),
    ("05간담회", "192.168.108.57", "visca"),
    ("06간담회", "192.168.109.57", "http"),
    ("07간담회", "192.168.110.57", "http"),
    ("08간담회", "192.168.111.57", "visca"),
    ("09간담회", "192.168.112.57", "http"),
    ("10간담회", "192.168.113.57", "http"),
    ("11간담회", "192.168.114.57", "http"),
]

# 카메라 인증 정보
CAMERA_AUTH = {
    "username": "admin",
    "password": "admin1234"
}

# ============ 스트림 관리 클래스 ============
class StreamManager:
    def __init__(self):
        self.processes_rtsp = []
        self.processes_rtmp = []
        self.should_restart = False
        self.selected_ip = list(RTSP_SERVERS.keys())[0]
        self.selected_location = None
        
    def play_rtsp(self, location, ip):
        """RTSP 스트림을 ffplay로 실행하는 함수 - 크로스 플랫폼 대응"""
        rtsp_url = f'rtsp://{ip}:554/{location}'
        
        # 기본 명령어
        cmd = ['ffplay', '-rtsp_transport', 'tcp', '-i', rtsp_url, 
               '-x', '640', '-y', '480', '-window_title', f'{location}']
        
        # ffplay 실행 경로 확인 (Mac에서는 경로가 다를 수 있음)
        try:
            process = Popen(cmd)
            self.processes_rtsp.append(process)
            print(f"RTSP 스트림 시작: {rtsp_url}")
        except FileNotFoundError:
            # Mac Homebrew 설치 경로 시도
            try:
                cmd[0] = '/opt/homebrew/bin/ffplay'  # Homebrew에서 설치한 경우 (Apple Silicon Mac)
                process = Popen(cmd)
                self.processes_rtsp.append(process)
                print(f"Homebrew 경로에서 RTSP 스트림 시작: {rtsp_url}")
            except Exception as e:
                try:
                    cmd[0] = '/usr/local/bin/ffplay'  # Intel Mac에서 Homebrew로 설치한 경우
                    process = Popen(cmd)
                    self.processes_rtsp.append(process)
                    print(f"Intel Mac Homebrew 경로에서 RTSP 스트림 시작: {rtsp_url}")
                except Exception as e:
                    print(f"RTSP 스트림 실행 오류: {e}")
                    print("Mac에서는 'brew install ffmpeg' 명령으로 ffmpeg/ffplay를 설치하세요.")
        except Exception as e:
            print(f"RTSP 스트림 실행 오류: {e}")
    
    def play_rtmp(self, location, ip, stream_key):
        """RTMP 스트림을 ffmpeg로 실행하는 함수"""
        self.should_restart = True
        
        # 별도의 스레드에서 RTMP 스트리밍 실행
        thread = threading.Thread(target=self._background_rtmp_task, 
                                 args=(location, ip, stream_key))
        thread.daemon = True
        thread.start()
        
        # 종료 함수 반환
        return self.stop_streaming
    
    def _background_rtmp_task(self, location, ip, stream_key):
        """백그라운드에서 RTMP 스트리밍 처리 - 크로스 플랫폼 대응"""
        # 로그 디렉토리 설정 - 크로스 플랫폼
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        log_dir = os.path.join(desktop, "doogie_logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        rtsp_url = f'rtsp://{ip}:554/{location}'
        rtmp_url = f'rtmp://a.rtmp.youtube.com/live2/{stream_key}'
        
        # 기본 명령어
        cmd = [
            'ffmpeg', '-re', '-timeout', '10000000', '-rtsp_transport', 'tcp',
            '-i', rtsp_url, '-c:v', 'copy', '-c:a', 'copy', '-f', 'flv',
            rtmp_url, '-loglevel', 'debug', '-report'
        ]
        
        while self.should_restart:
            try:
                print("FFmpeg 스트리밍 시작...")
                try:
                    # Mac Homebrew 설치 경로 시도
                    cmd[0] = '/opt/homebrew/bin/ffmpeg'  # Homebrew에서 설치한 경우 (Apple Silicon Mac)
                    try:
                        process_rtmp = Popen(cmd, cwd=log_dir)
                    except FileNotFoundError:
                        cmd[0] = '/usr/local/bin/ffmpeg'  # Intel Mac에서 Homebrew로 설치한 경우
                        process_rtmp = Popen(cmd, cwd=log_dir)
                except FileNotFoundError:
                    # Mac Homebrew 설치 경로 시도
                    cmd[0] = '/usr/local/bin/ffmpeg'  # Intel Mac에서 Homebrew로 설치한 경우
                    process_rtmp = Popen(cmd, cwd=log_dir)
                
                self.processes_rtmp.append(process_rtmp)
                process_rtmp.wait()
            except KeyboardInterrupt:
                print("스트리밍 중단됨.")
                break
            except Exception as e:
                print(f"오류 발생: {e}")
                print("Mac에서는 'brew install ffmpeg' 명령으로 ffmpeg/ffplay를 설치하세요.")
            finally:
                print("FFmpeg 중단.")
                if self.should_restart:
                    print("5초 후 다시 시도합니다.")
                    time.sleep(5)
    
    def stop_streaming(self):
        """RTMP 스트리밍 중지"""
        self.should_restart = False
        for process in self.processes_rtmp:
            try:
                process.terminate()
            except Exception as e:
                print(f"프로세스 종료 실패: {e}")
        self.processes_rtmp.clear()
        print("스트리밍이 종료되었습니다.")
    
    def stop_all_processes(self):
        """모든 스트리밍 프로세스 종료"""
        # RTSP 프로세스 종료
        for process in self.processes_rtsp:
            try:
                process.terminate()
            except Exception as e:
                print(f"RTSP 프로세스 종료 실패: {e}")
        self.processes_rtsp.clear()
        
        # RTMP 프로세스 종료
        for process in self.processes_rtmp:
            try:
                process.terminate()
            except Exception as e:
                print(f"RTMP 프로세스 종료 실패: {e}")
        self.processes_rtmp.clear()
        self.should_restart = False

    def select_ip(self, ip):
        """RTSP 서버 IP 선택"""
        self.selected_ip = ip
        print(f"현재 선택된 IP: {ip}")
        return ip
    
    def select_location(self, location):
        """스트림 위치 선택"""
        self.selected_location = location
        print(f"현재 선택된 위치: {location}")
        return location
    
    def start_view(self):
        """RTSP 스트림 시작"""
        if self.selected_location and self.selected_ip:
            self.play_rtsp(self.selected_location, self.selected_ip)
        else:
            print("위치 또는 IP가 선택되지 않았습니다.")
    
    def start_stream(self, stream_key):
        """RTMP 스트림 시작"""
        if self.selected_location and self.selected_ip and stream_key:
            return self.play_rtmp(self.selected_location, self.selected_ip, stream_key)
        else:
            print("위치, IP 또는 스트림 키가 선택되지 않았습니다.")
            return None

# ============ 장치 제어 클래스 ============
class DeviceController:
    def reset_device(self, ip):
        """장치 리셋 함수"""
        url = f"http://{ip}/api/v1/reboot.lua"
        username = "admin"
        password = "admin"
        try:
            response = requests.get(url, auth=HTTPBasicAuth(username, password), timeout=5)
            if response.status_code == 200:
                print(f"{ip}: Reset 성공")
                return True
            else:
                print(f"{ip}: Reset 실패 - HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"{ip}: Exception occurred - {str(e)}")
            return False
    
    def control_camera(self, ip, protocol, username, password, power_on):
        """카메라 제어 통합 함수"""
        if protocol == "http":
            return self._toggle_http_camera(ip, username, password, power_on)
        elif protocol == "visca":
            command = "81 01 04 00 02 FF" if power_on else "81 01 04 00 03 FF"
            return self._send_visca_command(ip, 52381, command)
        else:
            messagebox.showerror("오류", f"알 수 없는 프로토콜: {protocol}")
            return False
    
    def _toggle_http_camera(self, ip, username, password, power_on):
        """HTTP 방식으로 카메라 제어"""
        url = f"http://{ip}/command/main.cgi?System={'on' if power_on else 'standby'}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Referer": f"http://{ip}/",
            "Origin": f"http://{ip}",
        }
        try:
            response = requests.get(url, auth=HTTPDigestAuth(username, password), headers=headers)
            if response.status_code == 200:
                messagebox.showinfo("성공", f"HTTP 카메라 {ip} 전원 {'켜짐' if power_on else '꺼짐'}")
                return True
            elif response.status_code == 403:
                messagebox.showerror("오류", "403 오류: 권한 없음.")
            elif response.status_code == 401:
                messagebox.showerror("오류", "401 오류: 인증 실패.")
            else:
                messagebox.showerror("오류", f"요청 실패: {response.status_code}")
            return False
        except Exception as e:
            messagebox.showerror("오류", f"연결 실패: {e}")
            return False
    
    def _send_visca_command(self, ip, port, command):
        """VISCA 방식으로 카메라 제어"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.sendto(bytes.fromhex(command), (ip, port))
                print(f"명령 전송 성공: {command} (IP: {ip}, PORT: {port})")
                return True
        except Exception as e:
            messagebox.showerror("오류", f"VISCA 명령 전송 실패: {e}")
            return False

# ============ GUI 클래스 ============
class ApplicationGUI:
    def __init__(self):
        self.stream_manager = StreamManager()
        self.device_controller = DeviceController()
        self.root = None
        self.ip_label = None
        self.location_label = None
        self.text_box = None
        self.process_list_frame = None
    
    def create_gui(self):
        """GUI 생성 및 실행"""
        self.root = tk.Tk()
        self.root.title("통합 시스템 v6.0")
        
        # 아이콘 설정
        self._setup_icon()
        
        # 탭 컨트롤 생성
        notebook = ttk.Notebook(self.root)
        notebook.pack(expand=True, fill='both')
        
        # 각 탭 생성
        self._create_rtsp_tab(notebook)
        self._create_rtmp_status_tab(notebook)
        self._create_reset_tab(notebook)
        self._create_camera_tab(notebook)
        
        # 종료 버튼
        tk.Button(self.root, text="종료", command=self._on_close).pack(pady=20)
        
        # 종료 이벤트 설정
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # GUI 실행
        self.root.mainloop()
    
    def _setup_icon(self):
        """아이콘 설정 - 크로스 플랫폼 호환성 추가"""
        # 플랫폼 별 처리는 건너뛰고 로그만 출력
        print("아이콘 설정은 플랫폼에 따라 다를 수 있습니다.")
        # Mac/Linux에서는 아이콘 설정을 시도하지 않음
    
    def _create_rtsp_tab(self, notebook):
        """RTSP 스트림 관리 탭 생성"""
        rtsp_frame = tk.Frame(notebook)
        notebook.add(rtsp_frame, text="RTSP 스트림 관리")
        
        tk.Label(rtsp_frame, text="서버에 달라붙어서 FFPLAY로 영상보는 것", 
                font=("Arial", 12, "bold")).pack(pady=10)
        
        # IP 선택 영역
        ip_select_frame = tk.Frame(rtsp_frame)
        ip_select_frame.pack(pady=10)
        
        button_41 = tk.Button(
            ip_select_frame,
            text="192.168.116.41 선택",
            width=20, height=2,
            command=lambda: self._update_selected_ip("192.168.116.41", button_41, button_42)
        )
        button_41.grid(row=0, column=0, padx=10, pady=5)
        button_41.config(bg="lightblue")  # 기본 선택
        
        button_42 = tk.Button(
            ip_select_frame,
            text="192.168.118.42 선택",
            width=20, height=2,
            command=lambda: self._update_selected_ip("192.168.118.42", button_41, button_42)
        )
        button_42.grid(row=0, column=1, padx=10, pady=5)
        
        self.ip_label = tk.Label(rtsp_frame, 
                                text=f"선택된 IP: {self.stream_manager.selected_ip}", 
                                font=("Arial", 10))
        self.ip_label.pack(pady=10)
        
        # 스트림 위치 버튼 영역
        stream_button_frame = tk.Frame(rtsp_frame)
        stream_button_frame.pack()
        
        for idx, location in enumerate(STREAM_LOCATIONS):
            button = tk.Button(
                stream_button_frame,
                text=location,
                width=20, height=2,
                command=lambda loc=location: self._update_selected_location(loc)
            )
            button.grid(row=idx // 4, column=idx % 4, padx=10, pady=10)
        
        self.location_label = tk.Label(rtsp_frame, 
                                      text="선택된 위치: None", 
                                      font=("Arial", 10))
        self.location_label.pack(pady=10)
        
        # 스트림 키 입력
        tk.Label(rtsp_frame, text="스트림 키 입력", 
                font=("Arial", 10)).pack(pady=5)
        self.text_box = tk.Entry(rtsp_frame, width=30)
        self.text_box.pack(pady=10)
        
        # 작업 버튼 영역
        button_frame = tk.Frame(rtsp_frame)
        button_frame.pack(pady=10)
        
        view_button = tk.Button(
            button_frame,
            text="보기",
            width=20, height=2,
            command=self.stream_manager.start_view
        )
        view_button.grid(row=0, column=0, padx=10)
        
        stream_button = tk.Button(
            button_frame,
            text="송출",
            width=20, height=2,
            command=self._start_stream
        )
        stream_button.grid(row=0, column=1, padx=10)
    
    def _create_rtmp_status_tab(self, notebook):
        """RTMP 송출 상태 탭 생성"""
        rtmp_frame = tk.Frame(notebook)
        notebook.add(rtmp_frame, text="유튜브 송출 상태")
        
        tk.Label(rtmp_frame, text="실행 중인 유튜브 스트림 목록", 
                font=("Arial", 12, "bold")).pack(pady=10)
        
        self.process_list_frame = tk.Frame(rtmp_frame)
        self.process_list_frame.pack(pady=10)
        
        # 프로세스 목록 주기적 업데이트 시작
        self._update_rtmp_process_list()
    
    def _create_reset_tab(self, notebook):
        """장치 리셋 탭 생성"""
        reset_frame = tk.Frame(notebook)
        notebook.add(reset_frame, text="Kiloview 장치 리셋")
        
        tk.Label(reset_frame, text="장치 리셋 컨트롤", 
                font=("Arial", 12, "bold")).pack(pady=10)
        
        reset_button_frame = tk.Frame(reset_frame)
        reset_button_frame.pack()
        
        for idx, (location, ip) in enumerate(RESET_IPS.items()):
            button = tk.Button(
                reset_button_frame,
                text=f"리셋 {location}",
                width=20, height=2,
                command=lambda ip_addr=ip: self.device_controller.reset_device(ip_addr)
            )
            button.grid(row=idx // 4, column=idx % 4, padx=10, pady=10)
    
    def _create_camera_tab(self, notebook):
        """카메라 제어 탭 생성"""
        camera_frame = tk.Frame(notebook)
        notebook.add(camera_frame, text="카메라 제어")
        
        tk.Label(camera_frame, text="전경 카메라 제어", 
                font=("Arial", 16)).pack(pady=10)
        
        for name, ip, protocol in CAMERAS:
            frame = tk.Frame(camera_frame)
            frame.pack(pady=5)
            
            tk.Label(frame, text=name).pack(side=tk.LEFT, padx=10)
            
            tk.Button(
                frame, text="켜기", bg="green", fg="white",
                command=lambda ip=ip, protocol=protocol: 
                    self.device_controller.control_camera(
                        ip, protocol, CAMERA_AUTH["username"], CAMERA_AUTH["password"], True
                    )
            ).pack(side=tk.LEFT, padx=5)
            
            tk.Button(
                frame, text="끄기", bg="red", fg="white",
                command=lambda ip=ip, protocol=protocol: 
                    self.device_controller.control_camera(
                        ip, protocol, CAMERA_AUTH["username"], CAMERA_AUTH["password"], False
                    )
            ).pack(side=tk.LEFT, padx=5)
    
    def _update_selected_ip(self, ip, button_41, button_42):
        """IP 선택 업데이트 - 크로스 플랫폼 호환성 추가"""
        self.stream_manager.select_ip(ip)
        
        try:
            # Mac에서는 배경색 변경이 다르게 작동할 수 있음
            button_41.config(bg="lightblue" if ip == "192.168.116.41" else "lightgray")
            button_42.config(bg="lightblue" if ip == "192.168.118.42" else "lightgray")
        except tk.TclError:
            # Mac에서 색상 설정 오류 발생 시 스킵
            print("GUI 스타일링이 이 플랫폼에서 완전히 지원되지 않을 수 있습니다.")
            
        self.ip_label.config(text=f"선택된 IP: {ip}")
    
    def _update_selected_location(self, location):
        """위치 선택 업데이트"""
        self.stream_manager.select_location(location)
        self.location_label.config(text=f"선택된 위치: {location}")
    
    def _start_stream(self):
        """RTMP 스트림 시작"""
        stream_key = self.text_box.get()
        self.stream_manager.start_stream(stream_key)
    
    def _update_rtmp_process_list(self):
        """RTMP 프로세스 목록 업데이트"""
        # 비정상 종료된 프로세스 제거
        for process in self.stream_manager.processes_rtmp[:]:
            if not psutil.pid_exists(process.pid):
                print(f"비정상 종료된 프로세스 제거: PID {process.pid}")
                self.stream_manager.processes_rtmp.remove(process)
        
        # GUI 위젯 업데이트
        for widget in self.process_list_frame.winfo_children():
            widget.destroy()
        
        if self.stream_manager.processes_rtmp:
            for idx, process in enumerate(self.stream_manager.processes_rtmp):
                stream_key = self.text_box.get() if hasattr(self, 'text_box') else "N/A"
                process_info = f"프로세스 {idx + 1} (PID: {process.pid}) (스트림키: {stream_key}) 장소: {self.stream_manager.selected_location}"
                
                label = tk.Label(self.process_list_frame, text=process_info, font=("Arial", 10))
                label.grid(row=idx, column=0, padx=10, pady=5)
                
                button = tk.Button(
                    self.process_list_frame,
                    text="종료",
                    command=lambda p=process: self._terminate_process(p)
                )
                button.grid(row=idx, column=1, padx=10, pady=5)
        else:
            tk.Label(
                self.process_list_frame, 
                text="현재 실행 중인 유튜브 프로세스가 없습니다.", 
                font=("Arial", 10)
            ).pack()
        
        # 주기적 업데이트
        self.root.after(2000, self._update_rtmp_process_list)
    
    def _terminate_process(self, process):
        """선택된 RTMP 프로세스 종료"""
        try:
            process.terminate()
            process.wait(timeout=5)
            print(f"RTMP 프로세스 (PID: {process.pid}) 종료됨")
        except Exception as e:
            print(f"프로세스 종료 실패: {e}")
        finally:
            if not psutil.pid_exists(process.pid):
                self.stream_manager.processes_rtmp.remove(process)
    
    def _on_close(self):
        """프로그램 종료 처리"""
        self.stream_manager.stop_all_processes()
        self.root.destroy()

# ============ 메인 실행 부분 ============
def main():
    app = ApplicationGUI()
    app.create_gui()

if __name__ == "__main__":
    main() 