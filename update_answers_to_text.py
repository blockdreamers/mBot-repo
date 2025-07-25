import os
from supabase import create_client, Client
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# Supabase 설정
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

def update_answers_to_text():
    """기존 데이터의 answer 값을 integer에서 text로 변환"""
    
    print("=" * 60)
    print("🔄 Answer 값 업데이트: integer → text")
    print("=" * 60)
    
    # 환경 변수 확인
    if not SUPABASE_URL:
        print("❌ SUPABASE_URL이 설정되지 않았습니다.")
        return
    
    if not SUPABASE_SERVICE_KEY:
        print("❌ SUPABASE_SERVICE_ROLE_KEY가 설정되지 않았습니다.")
        return
    
    print("✅ Supabase 연결 설정 확인 완료")
    print(f"   URL: {SUPABASE_URL}")
    
    # Supabase 클라이언트 생성
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    try:
        # 1. 기존 CR 문제들 조회 (type='cr'인 것들만)
        print("\n📋 기존 CR 문제 데이터 조회 중...")
        result = supabase.table('questions').select('id, question_number, answer, type').eq('type', 'cr').order('question_number').execute()
        
        if not result.data:
            print("❌ CR 문제 데이터를 찾을 수 없습니다.")
            return
        
        questions = result.data
        print(f"✅ {len(questions)}개 CR 문제 발견")
        
        # 변환 매핑 (integer → text)
        answer_mapping = {
            0: 'A',
            1: 'B', 
            2: 'C',
            3: 'D',
            4: 'E'
        }
        
        # 2. 각 문제의 answer 값 업데이트
        print("\n🔄 Answer 값 업데이트 시작...")
        updated_count = 0
        error_count = 0
        
        for question in questions:
            question_id = question['id']
            question_number = question['question_number']
            current_answer = question['answer']
            
            # 이미 A-E 형태인 경우 스킵
            if isinstance(current_answer, str) and current_answer in ['A', 'B', 'C', 'D', 'E']:
                print(f"  ⏭️  문제 {question_number}: 이미 text 형태 (answer: {current_answer})")
                continue
            
            # integer이거나 문자열 숫자인 경우 변환
            answer_value = None
            
            # 정수인 경우
            if isinstance(current_answer, int) and current_answer in answer_mapping:
                answer_value = current_answer
            # 문자열 숫자인 경우 ("0", "1", "2", "3", "4")
            elif isinstance(current_answer, str) and current_answer.isdigit():
                int_value = int(current_answer)
                if int_value in answer_mapping:
                    answer_value = int_value
            
            if answer_value is not None:
                new_answer = answer_mapping[answer_value]
                
                try:
                    # 업데이트 실행
                    update_result = supabase.table('questions').update({
                        'answer': new_answer
                    }).eq('id', question_id).execute()
                    
                    if update_result.data:
                        print(f"  ✅ 문제 {question_number}: {current_answer} → {new_answer}")
                        updated_count += 1
                    else:
                        print(f"  ❌ 문제 {question_number}: 업데이트 실패")
                        error_count += 1
                        
                except Exception as e:
                    print(f"  ❌ 문제 {question_number}: 오류 - {e}")
                    error_count += 1
                    
            else:
                print(f"  ⚠️  문제 {question_number}: 예상치 못한 answer 값 - {current_answer}")
                error_count += 1
        
        # 3. 결과 요약
        print("\n" + "=" * 60)
        print("📊 업데이트 완료!")
        print("=" * 60)
        print(f"총 문제 수: {len(questions)}개")
        print(f"업데이트 성공: {updated_count}개")
        print(f"스킵/오류: {error_count}개")
        print(f"성공률: {updated_count/len(questions)*100:.1f}%")
        
        # 4. 업데이트 검증
        print("\n🔍 업데이트 검증 중...")
        verify_result = supabase.table('questions').select('question_number, answer').eq('type', 'cr').order('question_number').limit(10).execute()
        
        if verify_result.data:
            print("📋 처음 10개 문제 확인:")
            for item in verify_result.data:
                q_num = item['question_number']
                answer = item['answer']
                original_num = 140 + q_num  # question_number 1 = 원본 141번
                print(f"  문제 {original_num}번 (DB: {q_num}): {answer}")
        
        print("\n✅ 모든 작업이 완료되었습니다!")
        
    except Exception as e:
        print(f"\n❌ 오류가 발생했습니다: {e}")

def main():
    update_answers_to_text()

if __name__ == "__main__":
    main() 