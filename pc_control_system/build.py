import os
import shutil
import subprocess
import sys
from pathlib import Path

class PCControlBuilder:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist" 
        self.output_dir = self.project_root / "pc_control_system_release"
        
    def clean_build(self):
        """이전 빌드 파일 정리"""
        print("🧹 이전 빌드 파일을 정리합니다...")
        
        for dir_path in [self.build_dir, self.dist_dir, self.output_dir]:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                
        print("✅ 정리 완료!")
    
    def install_dependencies(self):
        """의존성 설치"""
        print("📦 의존성을 설치합니다...")
        
        requirements = [
            "pyinstaller==6.2.0",
            "fastapi==0.104.1", 
            "uvicorn[standard]==0.24.0",
            "slack-bolt==1.18.0",
            "python-dotenv==1.0.0",
            "pydantic==2.5.0",
            "pywin32==306",
            "requests==2.31.0"
        ]
        
        for req in requirements:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", req], 
                             check=True, capture_output=True)
                print(f"✅ {req}")
            except subprocess.CalledProcessError as e:
                print(f"❌ {req} 설치 실패: {e}")
                return False
        
        print("✅ 의존성 설치 완료!")
        return True
    
    def build_executable(self):
        """실행 파일 빌드"""
        print("🔨 실행 파일을 빌드합니다...")
        
        # PyInstaller 명령 구성
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--onedir",  # 하나의 디렉토리에 모든 파일 포함
            "--windowed",  # 콘솔 창 숨김
            "--name", "PC방제어시스템",
            "--icon", "icon.ico" if Path("icon.ico").exists() else None,
            "--add-data", "backend;backend",
            "--add-data", "frontend;frontend", 
            "--add-data", ".env;.",
            "--hidden-import", "uvicorn.protocols.http.auto",
            "--hidden-import", "uvicorn.protocols.websockets.auto",
            "--hidden-import", "uvicorn.lifespan.on",
            "--hidden-import", "slack_bolt",
            "--collect-all", "fastapi",
            "--collect-all", "uvicorn",
            "client/pc_control_client.py"
        ]
        
        # None 값 제거
        cmd = [arg for arg in cmd if arg is not None]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("✅ 빌드 완료!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 빌드 실패: {e}")
            print(f"에러 출력: {e.stderr}")
            return False
    
    def create_release_package(self):
        """배포 패키지 생성"""
        print("📦 배포 패키지를 생성합니다...")
        
        # 출력 디렉토리 생성
        self.output_dir.mkdir(exist_ok=True)
        
        # 빌드된 파일 복사
        built_exe_dir = self.dist_dir / "PC방제어시스템"
        if built_exe_dir.exists():
            # 실행 파일과 라이브러리 복사
            shutil.copytree(built_exe_dir, self.output_dir / "PC방제어시스템", 
                          dirs_exist_ok=True)
        
        # 추가 파일들 복사
        additional_files = [
            (".env.example", ".env.example"),
            ("README.md", "사용법.txt"), 
            ("config.json.example", "config.json.example")
        ]
        
        for src, dst in additional_files:
            src_path = self.project_root / src
            dst_path = self.output_dir / dst
            if src_path.exists():
                shutil.copy2(src_path, dst_path)
        
        # 설정 예제 파일 생성
        self.create_example_files()
        
        print(f"✅ 배포 패키지가 생성되었습니다: {self.output_dir}")
    
    def create_example_files(self):
        """예제 설정 파일들 생성"""
        
        # .env 예제 파일
        env_example = """# 슬랙 설정
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_APP_TOKEN=xapp-your-slack-app-token

# PC 번호는 프로그램에서 설정하세요"""
        
        with open(self.output_dir / ".env.example", "w", encoding="utf-8") as f:
            f.write(env_example)
        
        # config.json 예제 파일
        config_example = """{
  "pc_number": 1,
  "server_port": 8000,
  "auto_start": true,
  "fullscreen": true
}"""
        
        with open(self.output_dir / "config.json.example", "w", encoding="utf-8") as f:
            f.write(config_example)
        
        # 사용법 파일
        readme = """# PC방 제어시스템 사용법

## 설치 방법

1. 이 폴더 전체를 윈도우 PC에 복사하세요.

2. .env.example 파일을 .env로 이름을 변경하고 슬랙 토큰을 입력하세요:
   - SLACK_BOT_TOKEN: 슬랙 봇 토큰
   - SLACK_APP_TOKEN: 슬랙 앱 토큰

3. PC방제어시스템.exe를 실행하세요.

## PC 번호 설정

프로그램을 처음 실행하기 전에 PC 번호를 설정하세요:

1. 명령프롬프트에서 다음 명령을 실행:
   PC방제어시스템.exe --settings

2. 또는 config.json 파일을 직접 편집하세요.

## 주의사항

- 관리자 권한으로 실행하면 더 강력한 보안 기능을 사용할 수 있습니다.
- 프로그램 종료 시 로그아웃 버튼을 눌러주세요.
- 문제 발생 시 작업 관리자에서 강제 종료할 수 있습니다.

## 문의

문제가 발생하면 개발자에게 연락하세요.
"""
        
        with open(self.output_dir / "사용법.txt", "w", encoding="utf-8") as f:
            f.write(readme)
    
    def build(self):
        """전체 빌드 프로세스 실행"""
        print("🚀 PC방 제어시스템 빌드를 시작합니다...\n")
        
        # 1. 이전 빌드 정리
        self.clean_build()
        
        # 2. 의존성 설치
        if not self.install_dependencies():
            print("❌ 의존성 설치 실패!")
            return False
        
        # 3. 실행 파일 빌드  
        if not self.build_executable():
            print("❌ 실행 파일 빌드 실패!")
            return False
        
        # 4. 배포 패키지 생성
        self.create_release_package()
        
        print("\n🎉 빌드가 완료되었습니다!")
        print(f"📁 배포 파일 위치: {self.output_dir}")
        print("\n이제 생성된 폴더를 윈도우 PC에 복사해서 사용하세요.")
        
        return True

if __name__ == "__main__":
    builder = PCControlBuilder()
    success = builder.build()
    
    if not success:
        sys.exit(1) 