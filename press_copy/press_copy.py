import paramiko
import time
import re
import sys
import os

def copy_press_files(file_prefix):
    # Validate file format (e.g., PHP202504021041)
    pattern = r'^[A-Z]{3}\d{12}$'
    if not re.match(pattern, file_prefix):
        print(f"Error: 파일 형식이 올바르지 않습니다. 예: PHP202504021041")
        return False
    
    # Extract year from file prefix
    year = file_prefix[3:7]
    
    # Setup SSH connection
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print("SSH 서버에 연결 중...")
        ssh.connect('10.20.30.11', username='user01', password='P@ssw0rd!')
        
        # Create shell session
        channel = ssh.invoke_shell()
        
        # Wait for connection
        time.sleep(1)
        output = channel.recv(1024).decode('utf-8')
        print(f"연결됨: {output}")
        
        # Switch to root user
        channel.send('su\n')
        time.sleep(1)
        
        # Change to source directory
        cmd = f'cd /miosoft/data2/VOD/PRESS/{year}\n'
        channel.send(cmd)
        time.sleep(1)
        output = channel.recv(1024).decode('utf-8')
        print(f"소스 디렉토리로 이동: {output}")
        
        # Files to copy
        file_prefixes = ['PHP', 'PMP', 'PKP']
        
        # Copy the files
        for prefix in file_prefixes:
            filename = f"{prefix}{file_prefix[3:]}.mp4"
            copy_cmd = f"cp {filename} /miosoft/data/vod/PRESS/{year}\n"
            channel.send(copy_cmd)
            time.sleep(1)
            output = channel.recv(1024).decode('utf-8')
            print(f"파일 복사 중 {filename}: {output}")
        
        # Change to destination directory to verify
        channel.send(f'cd /miosoft/data/vod/PRESS/{year}\n')
        time.sleep(1)
        
        # Check if files exist
        channel.send(f'ls -l *{file_prefix[3:]}.mp4\n')
        time.sleep(2)
        output = channel.recv(4096).decode('utf-8')
        
        success = True
        for prefix in file_prefixes:
            if f"{prefix}{file_prefix[3:]}.mp4" not in output:
                print(f"오류: {prefix}{file_prefix[3:]}.mp4 파일이 대상 디렉토리에 존재하지 않습니다.")
                success = False
                
        if success:
            print("\n모든 파일이 성공적으로 복사되었습니다!")
        else:
            print("\n일부 파일이 복사되지 않았습니다. 로그를 확인하세요.")
            
        # Close connection
        ssh.close()
        return success
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("사용법: python press_copy.py [파일 접두사]")
        print("예: python press_copy.py PHP202504021041")
        sys.exit(1)
    
    file_prefix = sys.argv[1]
    copy_press_files(file_prefix) 