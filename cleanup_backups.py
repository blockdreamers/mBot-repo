import os
import glob

def cleanup_backups():
    """백업 파일들을 정리합니다"""
    
    print("=" * 50)
    print("백업 파일 정리 스크립트")
    print("=" * 50)
    
    cr_folder = 'questionbank/cr'
    
    # 백업 파일 패턴들
    backup_patterns = [
        '*.backup_*',
        '*_backup_*',
        '*.bak'
    ]
    
    backup_files = []
    for pattern in backup_patterns:
        backup_files.extend(glob.glob(os.path.join(cr_folder, pattern)))
    
    if not backup_files:
        print("✅ 삭제할 백업 파일이 없습니다.")
        return
    
    print(f"발견된 백업 파일들 ({len(backup_files)}개):")
    for backup_file in backup_files:
        file_size = os.path.getsize(backup_file)
        print(f"  📁 {backup_file} ({file_size:,} bytes)")
    
    print("\n정말로 모든 백업 파일을 삭제하시겠습니까?")
    print("원본 파일들 (CR문제.txt, CR 정답.txt, CR 답 풀이.txt)은 그대로 유지됩니다.")
    
    # 자동으로 삭제 (스크립트이므로)
    deleted_count = 0
    total_size = 0
    
    for backup_file in backup_files:
        try:
            file_size = os.path.getsize(backup_file)
            os.remove(backup_file)
            print(f"  ✅ 삭제됨: {backup_file}")
            deleted_count += 1
            total_size += file_size
        except Exception as e:
            print(f"  ❌ 삭제 실패: {backup_file} - {e}")
    
    print(f"\n🗑️ 정리 완료!")
    print(f"  삭제된 파일 수: {deleted_count}개")
    print(f"  절약된 공간: {total_size:,} bytes ({total_size/1024:.1f}KB)")
    
    # 남은 파일들 확인
    remaining_files = []
    for file in os.listdir(cr_folder):
        if file.endswith('.txt'):
            remaining_files.append(file)
    
    print(f"\n📂 남은 파일들:")
    for file in sorted(remaining_files):
        file_path = os.path.join(cr_folder, file)
        file_size = os.path.getsize(file_path)
        print(f"  📄 {file} ({file_size:,} bytes)")

if __name__ == "__main__":
    cleanup_backups() 