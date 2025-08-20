import os
from supabase import create_client
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

def clean_explanation_patterns():
    """questions 테이블에서 해설 칼럼의 불필요한 패턴 제거"""

    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    try:
        # question_number 147~999 범위의 데이터 조회
        result = supabase.table('questions').select('*').gte('question_number', 147).lte('question_number', 999).execute()

        if not result.data:
            print("❌ 해당 범위의 데이터를 찾을 수 없습니다.")
            return

        print(f"📊 처리할 데이터 수: {len(result.data)}개")
        updated_count = 0

        for question in result.data:
            question_id = question['id']
            question_number = question['question_number']

            # 한국어 설명에서 패턴 제거
            explanation_kor = question.get('explanation', '')
            if '[한국어 설명]' in explanation_kor:
                original_length = len(explanation_kor)
                explanation_kor = explanation_kor.replace('[한국어 설명]', '').strip()
                print(f"🧹 {question_number}번 - 한국어 설명 패턴 제거 ({original_length} → {len(explanation_kor)}자)")

            # 영어 설명에서 패턴 제거
            explanation_en = question.get('explanation_en', '')
            original_en = explanation_en

            # 다양한 패턴 제거
            patterns_to_remove = [
                '[English explanation]',
                '[영어 설명]',
                'English Explanation:',
                '영어 설명:',
                '[English Explanation]'
            ]

            for pattern in patterns_to_remove:
                explanation_en = explanation_en.replace(pattern, '').strip()

            # 대소문자 구분 없이도 제거
            explanation_en = explanation_en.replace('[english explanation]', '').strip()

            if explanation_en != original_en:
                print(f"🧹 {question_number}번 - 영어 설명 패턴 제거 ({len(original_en)} → {len(explanation_en)}자)")

            # 변경사항이 있으면 업데이트
            if explanation_kor != question.get('explanation', '') or explanation_en != question.get('explanation_en', ''):
                update_result = supabase.table('questions').update({
                    'explanation': explanation_kor,
                    'explanation_en': explanation_en
                }).eq('id', question_id).execute()

                if update_result.data:
                    updated_count += 1
                    print(f"✅ {question_number}번 업데이트 완료")
                else:
                    print(f"❌ {question_number}번 업데이트 실패")

        print(f"\n🎉 정리 완료!")
        print(f"   총 처리: {len(result.data)}개")
        print(f"   업데이트: {updated_count}개")

    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")

def main():
    print("=" * 60)
    print("🧹 Questions 테이블 해설 패턴 정리 스크립트")
    print("=" * 60)

    # 환경 변수 확인
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("❌ 환경 변수가 설정되지 않았습니다.")
        return

    print("✅ 환경 변수 확인 완료")
    print(f"   범위: question_number 147 ~ 999")

    clean_explanation_patterns()

if __name__ == "__main__":
    main()
