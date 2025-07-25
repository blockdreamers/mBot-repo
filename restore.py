import shutil
import os

# 백업 파일을 원본으로 복원
backup_file = 'questionbank/cr/CR문제.txt.backup_20250725_133717'
original_file = 'questionbank/cr/CR문제.txt'

if os.path.exists(backup_file):
    shutil.copy2(backup_file, original_file)
    print(f"✅ 백업 복원 완료!")
    print(f"  {backup_file} → {original_file}")
    
    # 파일 크기 확인
    backup_size = os.path.getsize(backup_file)
    original_size = os.path.getsize(original_file)
    print(f"  백업 파일 크기: {backup_size:,} bytes")
    print(f"  복원된 파일 크기: {original_size:,} bytes")
else:
    print(f"❌ 백업 파일을 찾을 수 없습니다: {backup_file}") 