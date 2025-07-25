# 🎯 CR 문제 Supabase 업로드 가이드

이 스크립트는 CR문제.txt 파일의 문제들을 파싱하여 Supabase 데이터베이스에 업로드합니다.
각 문제마다 OpenAI GPT-3.5-turbo를 사용하여 한글/영문 설명을 자동 생성합니다.

## 📋 사전 준비

### 1. Python 패키지 설치
```bash
# 필요한 패키지 설치
pip install -r requirements_upload.txt

# 또는 개별 설치
pip install openai==0.28.1 supabase==1.2.0 python-dotenv==1.0.0
```

**⚠️ 설치 오류 시:**
```bash
# Python 버전 확인 (3.8 이상 필요)
python --version

# pip 업그레이드
python -m pip install --upgrade pip

# 재시도
pip install -r requirements_upload.txt
```

### 2. 환경 변수 설정
`.env` 파일에 다음 키들을 설정하세요:

```env
# OpenAI API Key
OPENAI_API_KEY=sk-proj-suz...

# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJh...
SUPABASE_PUBLIC_KEY=eyJh...
```

### 3. 파일 준비 확인
- `questionbank/cr/CR문제.txt` 파일이 있는지 확인
- 파일에 정답이 "142. 정답 : D" 형식으로 추가되어 있는지 확인

## 🚀 실행 방법

### 전체 프로세스 실행
```bash
# 0단계: 패키지 설치 (처음 한 번만)
pip install -r requirements_upload.txt

# 1단계: 백업 복원 (원본 상태로)
python restore_backup.py

# 2단계: v5.0 포맷팅 (안전한 방식)
python format_questions_v5.py

# 3단계: 정답 추가
python add_answers.py

# 4단계: Supabase 업로드 🎯
python upload_to_supabase.py

# 5단계: 백업 파일 정리 (선택사항)
python cleanup_backups.py
```

### 업로드만 실행 (파일이 이미 준비된 경우)
```bash
python upload_to_supabase.py
```

## 📊 진행 과정

스크립트 실행 시 다음과 같이 진행됩니다:

### 1. 파일 파싱 단계
```
📖 questionbank/cr/CR문제.txt 파일 파싱 중...
🔍 총 149개 문제 발견
✅ 141번 문제 파싱 완료 (정답: C)
✅ 142번 문제 파싱 완료 (정답: D)
...
📊 총 149개 문제 파싱 완료
```

### 2. 업로드 단계
```
🚀 149개 문제 업로드 시작...
================================================================================

📝 진행률: 1/149 (0.7%)
원본 번호: 141번
🤖 141번 문제 설명 생성 중...
✅ 141번 문제 업로드 완료 (DB 번호: 1)
   한국어 설명: 이 문제는 강화 논증 유형입니다. 계획의 효율성을 높이려면...
   영어 설명: This is a strengthen question. To increase efficiency of the plan...
✅ 성공

📝 진행률: 2/149 (1.3%)
...
```

### 3. 중간 집계 (10개마다)
```
📊 중간 집계 (10개 처리)
   성공: 10개
   실패: 0개
   성공률: 100.0%
----------------------------------------
```

### 4. 최종 결과
```
🎉 업로드 완료!
================================================================================
📊 최종 결과:
   총 문제 수: 149개
   성공: 149개
   실패: 0개
   성공률: 100.0%
```

## 📝 데이터베이스 구조

업로드되는 데이터 형식:

| 필드 | 타입 | 값 | 예시 |
|------|------|-----|------|
| type | text | "cr" | "cr" |
| question | text | 문제 본문 | "PhishCo runs a number of farms..." |
| choices | ARRAY | 보기 배열 | ["A. Most of the vegetation...", "B. Fish raised..."] |
| answer | integer | 정답 인덱스 | 2 (C가 정답인 경우) |
| explanation | text | 한글 설명 | "이 문제는 강화 논증 유형입니다..." |
| explanation_en | text | 영문 설명 | "This is a strengthen question..." |
| question_number | integer | DB 내 번호 | 1, 2, 3... |

## ⚠️ 주의사항

### API 비용
- **OpenAI API**: 문제당 약 $0.01-0.02 (149개 문제 기준 약 $1.5-3)
- **Supabase**: 일반적으로 무료 티어 내에서 처리 가능

### 시간 소요
- **총 소요 시간**: 약 3-5분 (149개 문제 기준)
- **API 대기 시간**: 문제당 1초씩 대기 (률제한 방지)

### 오류 처리
- 네트워크 오류나 API 오류 시 해당 문제만 스킵
- 전체 진행 상황은 로그로 추적 가능
- 실패한 문제는 수동으로 재시도 가능

## 🔧 문제 해결

### 패키지 설치 오류
```
ModuleNotFoundError: No module named 'openai'
```
→ 패키지가 설치되지 않았습니다:
```bash
pip install -r requirements_upload.txt
```

### 환경 변수 오류
```
❌ OPENAI_API_KEY가 설정되지 않았습니다.
❌ SUPABASE_URL이 설정되지 않았습니다.
❌ SUPABASE_SERVICE_ROLE_KEY가 설정되지 않았습니다.
```
→ `.env` 파일에 필요한 모든 키를 설정하세요:
```env
OPENAI_API_KEY=sk-proj-...
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJh...
```

### 파일 찾기 오류
```
❌ questionbank/cr/CR문제.txt 파일을 찾을 수 없습니다.
```
→ 파일 경로와 이름을 확인하고, 필요시 포맷팅 단계를 먼저 실행하세요.

### Supabase 연결 오류
```
❌ Supabase 연결 실패
```
→ `.env` 파일의 Supabase 설정을 확인하세요:
- SUPABASE_URL이 올바른 형식인지 (https://...)
- SERVICE_ROLE_KEY가 올바른지 (secret key, public key 아님)
- 네트워크 연결 상태 확인

### 파싱 오류
```
⚠️ 142번 문제의 정답을 찾을 수 없습니다.
```
→ 정답 추가 단계(`add_answers.py`)를 먼저 실행하세요.

## 📈 성공 확인

업로드 완료 후 Supabase 대시보드에서 확인:
1. Table Editor → questions 테이블
2. 총 149개 행이 추가되었는지 확인
3. type이 모두 "cr"로 설정되었는지 확인
4. question_number가 1부터 149까지 순서대로 들어갔는지 확인

---

**💡 팁**: 처음 실행 시에는 소수의 문제로 테스트해보고 싶다면, `upload_to_supabase.py`의 파싱 부분에서 `questions = questions[:5]` 같은 식으로 제한할 수 있습니다. 