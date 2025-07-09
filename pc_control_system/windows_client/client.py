import os
import sys
import socket
import threading
import time
import json
import requests
import websocket
from datetime import datetime
import tkinter as tk
from tkinter import messagebox

from login_screen import LoginScreen

class PCControlClient:
    def __init__(self):
        # 설정
        self.server_host = "localhost"  # 서버 IP 주소
        self.server_port = 8000
        self.server_url = f"http://{self.server_host}:{self.server_port}"
        self.ws_url = f"ws://{self.server_host}:{self.server_port}/ws/pc"
        
        # PC ID (고유 식별자)
        self.pc_id = self.get_pc_id()
        
        # 상태 관리
        self.is_running = True
        self.is_logged_in = False
        self.username = None
        self.organization = None
        
        # WebSocket 연결
        self.ws = None
        self.ws_thread = None
        
        # 로그인 화면
        self.login_screen = None
        
        # 하트비트 스레드
        self.heartbeat_thread = None
        
        print(f"PC Control Client 시작 - PC ID: {self.pc_id}")
        print(f"서버 URL: {self.server_url}")
        
    def get_pc_id(self):
        """PC 고유 ID 생성"""
        try:
            # 컴퓨터 이름 기반으로 ID 생성
            computer_name = socket.gethostname()
            # 간단한 ID로 변환 (예: DESKTOP-ABC123 -> ABC123)
            pc_id = computer_name.replace('DESKTOP-', '').replace('LAPTOP-', '')[:6]
            return pc_id
        except Exception as e:
            print(f"PC ID 생성 오류: {e}")
            return "UNKNOWN"
    
    def get_local_ip(self):
        """로컬 IP 주소 가져오기"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            print(f"IP 주소 가져오기 오류: {e}")
            return "127.0.0.1"
    
    def connect_websocket(self):
        """WebSocket 연결"""
        try:
            ws_url = f"{self.ws_url}/{self.pc_id}"
            print(f"WebSocket 연결 시도: {ws_url}")
            
            self.ws = websocket.WebSocketApp(
                ws_url,
                on_open=self.on_ws_open,
                on_message=self.on_ws_message,
                on_error=self.on_ws_error,
                on_close=self.on_ws_close
            )
            
            # WebSocket 연결 시작
            self.ws.run_forever()
            
        except Exception as e:
            print(f"WebSocket 연결 오류: {e}")
            
    def on_ws_open(self, ws):
        """WebSocket 연결 열림"""
        print("WebSocket 연결 성공")
        
        # 초기 상태 전송
        self.send_status_update()
        
    def on_ws_message(self, ws, message):
        """WebSocket 메시지 수신"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "login_success":
                # 로그인 성공 처리
                self.handle_login_success(data.get("data", {}))
                
            elif message_type == "logout":
                # 로그아웃 처리
                self.handle_logout()
                
            elif message_type == "force_logout":
                # 강제 로그아웃 처리
                self.handle_force_logout()
                
            else:
                print(f"알 수 없는 메시지 타입: {message_type}")
                
        except json.JSONDecodeError:
            print(f"잘못된 JSON 메시지: {message}")
        except Exception as e:
            print(f"메시지 처리 오류: {e}")
    
    def on_ws_error(self, ws, error):
        """WebSocket 오류 처리"""
        print(f"WebSocket 오류: {error}")
        
    def on_ws_close(self, ws, close_status_code, close_msg):
        """WebSocket 연결 종료"""
        print("WebSocket 연결 종료")
        
        # 재연결 시도
        if self.is_running:
            print("3초 후 재연결 시도...")
            time.sleep(3)
            if self.is_running:
                self.connect_websocket()
    
    def send_message(self, message):
        """WebSocket 메시지 전송"""
        if self.ws and self.ws.sock and self.ws.sock.connected:
            try:
                self.ws.send(json.dumps(message))
                return True
            except Exception as e:
                print(f"메시지 전송 오류: {e}")
                return False
        return False
    
    def send_status_update(self):
        """상태 업데이트 전송"""
        status = "logged_in" if self.is_logged_in else "locked"
        
        message = {
            "type": "status_update",
            "data": {
                "status": status,
                "username": self.username,
                "organization": self.organization,
                "ip_address": self.get_local_ip()
            }
        }
        
        self.send_message(message)
    
    def send_heartbeat(self):
        """하트비트 전송"""
        while self.is_running:
            try:
                # HTTP 하트비트 전송
                heartbeat_data = {
                    "pc_id": self.pc_id,
                    "ip_address": self.get_local_ip()
                }
                
                response = requests.post(
                    f"{self.server_url}/api/heartbeat",
                    json=heartbeat_data,
                    timeout=5
                )
                
                if response.status_code == 200:
                    print("하트비트 전송 성공")
                else:
                    print(f"하트비트 전송 실패: {response.status_code}")
                    
                # WebSocket 하트비트
                self.send_message({
                    "type": "heartbeat",
                    "data": {
                        "ip_address": self.get_local_ip()
                    }
                })
                
            except Exception as e:
                print(f"하트비트 전송 오류: {e}")
                
            time.sleep(30)  # 30초마다 하트비트 전송
    
    def handle_login_success(self, data):
        """로그인 성공 처리"""
        print(f"로그인 성공: {data}")
        
        if self.login_screen:
            # 로그인 화면을 성공 화면으로 전환
            self.login_screen.root.after(0, self.login_screen.show_logged_in_screen)
    
    def handle_logout(self):
        """로그아웃 처리"""
        print("로그아웃 처리")
        
        self.is_logged_in = False
        self.username = None
        self.organization = None
        
        # 상태 업데이트 전송
        self.send_status_update()
        
        # 로그인 화면으로 돌아가기
        if self.login_screen:
            self.login_screen.root.after(0, self.login_screen.reset_to_login_screen)
    
    def handle_force_logout(self):
        """강제 로그아웃 처리"""
        print("강제 로그아웃 처리")
        
        self.is_logged_in = False
        self.username = None
        self.organization = None
        
        # 로그아웃 API 호출
        try:
            logout_data = {"pc_id": self.pc_id}
            requests.post(f"{self.server_url}/api/logout", json=logout_data, timeout=5)
        except Exception as e:
            print(f"로그아웃 API 호출 오류: {e}")
        
        # 상태 업데이트 전송
        self.send_status_update()
        
        # 로그인 화면으로 돌아가기
        if self.login_screen:
            self.login_screen.root.after(0, self.login_screen.force_logout)
    
    def on_login_success(self, username, organization):
        """로그인 성공 콜백"""
        print(f"로그인 성공 콜백: {username} ({organization})")
        
        self.is_logged_in = True
        self.username = username
        self.organization = organization
        
        # 상태 업데이트 전송
        self.send_status_update()
        
        # 로그인 화면을 성공 화면으로 전환
        if self.login_screen:
            self.login_screen.root.after(0, self.login_screen.show_logged_in_screen)
    
    def run(self):
        """클라이언트 실행"""
        try:
            # WebSocket 연결 스레드 시작
            self.ws_thread = threading.Thread(target=self.connect_websocket, daemon=True)
            self.ws_thread.start()
            
            # 하트비트 스레드 시작
            self.heartbeat_thread = threading.Thread(target=self.send_heartbeat, daemon=True)
            self.heartbeat_thread.start()
            
            # 로그인 화면 실행
            self.login_screen = LoginScreen(
                server_url=self.server_url,
                pc_id=self.pc_id,
                on_login_success=self.on_login_success
            )
            
            print("로그인 화면 시작...")
            self.login_screen.run()
            
        except KeyboardInterrupt:
            print("프로그램 종료 요청")
        except Exception as e:
            print(f"프로그램 실행 오류: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """정리 작업"""
        print("정리 작업 중...")
        
        self.is_running = False
        
        # 로그아웃 처리
        if self.is_logged_in:
            try:
                logout_data = {"pc_id": self.pc_id}
                requests.post(f"{self.server_url}/api/logout", json=logout_data, timeout=5)
            except Exception as e:
                print(f"로그아웃 오류: {e}")
        
        # WebSocket 연결 종료
        if self.ws:
            try:
                self.ws.close()
            except Exception as e:
                print(f"WebSocket 종료 오류: {e}")
        
        # 로그인 화면 종료
        if self.login_screen:
            try:
                self.login_screen.close()
            except Exception as e:
                print(f"로그인 화면 종료 오류: {e}")
        
        print("정리 작업 완료")

def main():
    """메인 함수"""
    # 관리자 권한 체크 (선택사항)
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if not is_admin:
            print("경고: 관리자 권한으로 실행하는 것을 권장합니다.")
    except Exception:
        pass
    
    # 클라이언트 실행
    client = PCControlClient()
    client.run()

if __name__ == "__main__":
    main() 