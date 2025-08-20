import os
from supabase import create_client
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# Supabase 설정
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Supabase 환경 변수가 설정되지 않았습니다.")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def check_table_schema():
    """questions 테이블의 스키마를 확인합니다."""
    try:
        # 테이블에서 한 개의 레코드를 가져와서 구조 확인
        result = supabase.table("questions").select("*").limit(1).execute()
        
        if result.data:
            sample_record = result.data[0]
            print("=== questions 테이블 스키마 ===")
            print(f"사용 가능한 컬럼들:")
            for key, value in sample_record.items():
                print(f"  - {key}: {type(value).__name__} = {value}")
            
            print(f"\n총 {len(sample_record)}개의 컬럼이 있습니다.")
            return sample_record.keys()
        else:
            print("❌ 테이블에 데이터가 없습니다.")
            return []
            
    except Exception as e:
        print(f"❌ 스키마 확인 오류: {e}")
        return []

def check_existing_questions():
    """기존 문제들의 구조를 확인합니다."""
    try:
        result = supabase.table("questions").select("*").limit(5).execute()
        
        if result.data:
            print("\n=== 기존 문제 샘플 ===")
            for i, question in enumerate(result.data):
                print(f"\n문제 {i+1}:")
                for key, value in question.items():
                    if key == 'choices' and isinstance(value, list):
                        print(f"  {key}: {len(value)}개 보기")
                        for j, choice in enumerate(value):
                            print(f"    {j+1}. {choice[:50]}...")
                    else:
                        print(f"  {key}: {str(value)[:100]}...")
        else:
            print("❌ 테이블에 데이터가 없습니다.")
            
    except Exception as e:
        print(f"❌ 기존 문제 확인 오류: {e}")

def main():
    print("=" * 60)
    print("Supabase questions 테이블 스키마 확인")
    print("=" * 60)
    
    # 1. 테이블 스키마 확인
    columns = check_table_schema()
    
    # 2. 기존 문제 구조 확인
    check_existing_questions()
    
    print(f"\n✅ 스키마 확인 완료!")

if __name__ == "__main__":
    main() 