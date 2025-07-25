-- 1. user_answers 테이블 전체 구조 확인
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default,
    character_maximum_length
FROM information_schema.columns 
WHERE table_name = 'user_answers' 
ORDER BY ordinal_position;

-- 2. 인덱스 및 제약조건 확인  
SELECT 
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename = 'user_answers';

-- 3. 최근 데이터 샘플 확인 (최근 10개)
SELECT 
    id,
    user_id,
    question_id,
    user_answer,
    is_correct,
    created_at
FROM user_answers 
ORDER BY created_at DESC 
LIMIT 10;

-- 4. user_answer 컬럼의 데이터 타입과 값들 확인
SELECT 
    user_answer,
    COUNT(*) as count,
    pg_typeof(user_answer) as data_type
FROM user_answers 
GROUP BY user_answer, pg_typeof(user_answer)
ORDER BY count DESC; 