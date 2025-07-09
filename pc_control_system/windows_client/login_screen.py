import tkinter as tk
from tkinter import messagebox, ttk
import threading
import time
import requests
import json
from datetime import datetime

class LoginScreen:
    def __init__(self, server_url, pc_id, on_login_success=None):
        self.server_url = server_url
        self.pc_id = pc_id
        self.on_login_success = on_login_success
        self.is_logged_in = False
        self.username = None
        self.organization = None
        
        # 메인 윈도우 설정
        self.root = tk.Tk()
        self.root.title("PC Control System - 로그인")
        self.root.configure(bg='#f0f0f0')
        
        # 전체 화면 설정
        self.setup_fullscreen()
        
        # UI 생성
        self.create_widgets()
        
    def setup_fullscreen(self):
        """전체 화면 설정"""
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        self.root.focus_set()
        
        # ESC 키로 전체 화면 해제 방지
        self.root.bind('<Escape>', lambda e: None)
        
        # Alt+Tab, Alt+F4 등 키 조합 방지
        self.root.bind('<Alt-Tab>', lambda e: "break")
        self.root.bind('<Alt-F4>', lambda e: "break")
        self.root.bind('<Control-Alt-Delete>', lambda e: "break")
        
    def create_widgets(self):
        """UI 위젯 생성"""
        # 메인 컨테이너
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(expand=True, fill='both')
        
        # 중앙 로그인 카드
        login_card = tk.Frame(main_frame, bg='white', relief='raised', bd=2)
        login_card.place(relx=0.5, rely=0.5, anchor='center', width=400, height=500)
        
        # 헤더
        header_frame = tk.Frame(login_card, bg='#3b82f6', height=80)
        header_frame.pack(fill='x', pady=0)
        header_frame.pack_propagate(False)
        
        # 제목
        title_label = tk.Label(
            header_frame,
            text="PC Control System",
            font=('Arial', 16, 'bold'),
            fg='white',
            bg='#3b82f6'
        )
        title_label.pack(pady=15)
        
        # PC ID 표시
        pc_id_label = tk.Label(
            header_frame,
            text=f"PC-{self.pc_id}",
            font=('Arial', 12),
            fg='white',
            bg='#3b82f6'
        )
        pc_id_label.pack()
        
        # 로그인 폼
        form_frame = tk.Frame(login_card, bg='white', pady=30)
        form_frame.pack(fill='both', expand=True)
        
        # 안내 메시지
        info_label = tk.Label(
            form_frame,
            text="PC 사용을 위해 로그인해주세요",
            font=('Arial', 12),
            fg='#374151',
            bg='white'
        )
        info_label.pack(pady=(0, 20))
        
        # 사용자명 입력
        tk.Label(
            form_frame,
            text="사용자명:",
            font=('Arial', 10),
            fg='#374151',
            bg='white'
        ).pack(anchor='w', padx=30)
        
        self.username_entry = tk.Entry(
            form_frame,
            font=('Arial', 12),
            relief='solid',
            bd=1,
            width=30
        )
        self.username_entry.pack(pady=(5, 15), padx=30)
        
        # 소속 입력
        tk.Label(
            form_frame,
            text="소속:",
            font=('Arial', 10),
            fg='#374151',
            bg='white'
        ).pack(anchor='w', padx=30)
        
        self.organization_entry = tk.Entry(
            form_frame,
            font=('Arial', 12),
            relief='solid',
            bd=1,
            width=30
        )
        self.organization_entry.pack(pady=(5, 20), padx=30)
        
        # 로그인 버튼
        self.login_button = tk.Button(
            form_frame,
            text="로그인",
            font=('Arial', 12, 'bold'),
            bg='#3b82f6',
            fg='white',
            relief='flat',
            bd=0,
            width=20,
            height=2,
            cursor='hand2',
            command=self.handle_login
        )
        self.login_button.pack(pady=10)
        
        # 상태 라벨
        self.status_label = tk.Label(
            form_frame,
            text="",
            font=('Arial', 10),
            fg='#ef4444',
            bg='white'
        )
        self.status_label.pack(pady=10)
        
        # 현재 시간 표시
        self.time_label = tk.Label(
            form_frame,
            text="",
            font=('Arial', 10),
            fg='#6b7280',
            bg='white'
        )
        self.time_label.pack(side='bottom', pady=10)
        
        # 시간 업데이트 시작
        self.update_time()
        
        # 엔터 키 이벤트
        self.root.bind('<Return>', lambda e: self.handle_login())
        
        # 포커스 설정
        self.username_entry.focus_set()
        
    def update_time(self):
        """현재 시간 업데이트"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)
        
    def handle_login(self):
        """로그인 처리"""
        username = self.username_entry.get().strip()
        organization = self.organization_entry.get().strip()
        
        if not username:
            self.show_error("사용자명을 입력해주세요.")
            self.username_entry.focus_set()
            return
            
        if not organization:
            self.show_error("소속을 입력해주세요.")
            self.organization_entry.focus_set()
            return
        
        # 로그인 버튼 비활성화
        self.login_button.config(state='disabled', text='로그인 중...')
        self.status_label.config(text="로그인 중입니다...", fg='#3b82f6')
        
        # 백그라운드에서 로그인 요청
        threading.Thread(target=self.perform_login, args=(username, organization), daemon=True).start()
        
    def perform_login(self, username, organization):
        """실제 로그인 요청 수행"""
        try:
            login_data = {
                "pc_id": self.pc_id,
                "username": username,
                "organization": organization
            }
            
            response = requests.post(
                f"{self.server_url}/api/login",
                json=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    self.username = username
                    self.organization = organization
                    self.is_logged_in = True
                    
                    # UI 업데이트
                    self.root.after(0, self.show_login_success)
                    
                    # 콜백 호출
                    if self.on_login_success:
                        self.on_login_success(username, organization)
                        
                else:
                    self.root.after(0, lambda: self.show_error(result.get("message", "로그인 실패")))
                    
            else:
                self.root.after(0, lambda: self.show_error("서버 연결 오류"))
                
        except requests.exceptions.Timeout:
            self.root.after(0, lambda: self.show_error("서버 응답 시간 초과"))
        except requests.exceptions.ConnectionError:
            self.root.after(0, lambda: self.show_error("서버에 연결할 수 없습니다"))
        except Exception as e:
            self.root.after(0, lambda: self.show_error(f"오류: {str(e)}"))
        finally:
            self.root.after(0, self.reset_login_button)
            
    def show_error(self, message):
        """오류 메시지 표시"""
        self.status_label.config(text=message, fg='#ef4444')
        
    def show_login_success(self):
        """로그인 성공 메시지 표시"""
        self.status_label.config(text="로그인 성공!", fg='#22c55e')
        
    def reset_login_button(self):
        """로그인 버튼 초기화"""
        self.login_button.config(state='normal', text='로그인')
        
    def show_logged_in_screen(self):
        """로그인 후 화면 표시"""
        # 기존 위젯 제거
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # 로그인 완료 화면
        success_frame = tk.Frame(self.root, bg='#f0f0f0')
        success_frame.pack(expand=True, fill='both')
        
        # 중앙 카드
        success_card = tk.Frame(success_frame, bg='white', relief='raised', bd=2)
        success_card.place(relx=0.5, rely=0.5, anchor='center', width=400, height=300)
        
        # 성공 메시지
        tk.Label(
            success_card,
            text="로그인 완료!",
            font=('Arial', 20, 'bold'),
            fg='#22c55e',
            bg='white'
        ).pack(pady=30)
        
        # 사용자 정보
        info_frame = tk.Frame(success_card, bg='white')
        info_frame.pack(pady=20)
        
        tk.Label(
            info_frame,
            text=f"사용자: {self.username}",
            font=('Arial', 14),
            fg='#374151',
            bg='white'
        ).pack(pady=5)
        
        tk.Label(
            info_frame,
            text=f"소속: {self.organization}",
            font=('Arial', 14),
            fg='#374151',
            bg='white'
        ).pack(pady=5)
        
        tk.Label(
            info_frame,
            text=f"PC: {self.pc_id}",
            font=('Arial', 14),
            fg='#374151',
            bg='white'
        ).pack(pady=5)
        
        # 안내 메시지
        tk.Label(
            success_card,
            text="PC 사용이 가능합니다.\n이 창을 닫으면 로그아웃됩니다.",
            font=('Arial', 10),
            fg='#6b7280',
            bg='white',
            justify='center'
        ).pack(pady=20)
        
    def force_logout(self):
        """강제 로그아웃 처리"""
        self.is_logged_in = False
        self.username = None
        self.organization = None
        
        # 로그인 화면으로 돌아가기
        self.root.after(0, self.reset_to_login_screen)
        
    def reset_to_login_screen(self):
        """로그인 화면으로 재설정"""
        # 기존 위젯 제거
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # 로그인 위젯 다시 생성
        self.create_widgets()
        
        # 강제 로그아웃 메시지
        self.show_error("관리자에 의해 로그아웃되었습니다.")
        
    def run(self):
        """애플리케이션 실행"""
        self.root.mainloop()
        
    def close(self):
        """애플리케이션 종료"""
        self.root.destroy() 