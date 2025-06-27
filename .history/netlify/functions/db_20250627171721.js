// ✅ 로컬 개발환경에서만 .env 로드
if (process.env.NODE_ENV !== "production") {
  require("dotenv").config();
}

const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_KEY
);

// ✅ 유저가 푼 문제 ID 리스트 (과목별 필터 지원)
async function getUserAnsweredIds(user_id, subjectType = null) {
  console.log(`📥 getUserAnsweredIds() called with subjectType: ${subjectType}`);

  if (!subjectType) {
    const { data, error } = await supabase
      .from('user_answers')
      .select('question_id')
      .eq('user_id', user_id);

    if (error) {
      console.error('❌ Supabase fetch error (user_answers):', error);
      return [];
    }

    console.log(`📦 ${data.length} answered questions (no subject filter)`);
    return data.map(row => row.question_id);
  }

  const { data, error } = await supabase.rpc('get_answered_ids_by_type', {
    input_user_id: user_id,
    input_type: subjectType,
  });

  if (error) {
    console.error('❌ Supabase fetch error (get_answered_ids_by_type):', error);
    return [];
  }

  console.log(`📦 ${data.length} answered questions for subject "${subjectType}"`);
  return data.map(row => row.question_id);
}

// ✅ 전체 문제 리스트 (정렬 포함)
async function getAllQuestions() {
  const { data, error } = await supabase
    .from('questions')
    .select('*')
    .order('question_number', { ascending: true });

  if (error) {
    console.error('❌ Supabase fetch error (questions):', error);
    return [];
  }

  console.log(`📚 총 ${data.length}문제 불러옴`);
  return data;
}

// ✅ 유저의 통계 (총 푼 문제, 맞춘 문제)
async function getStats(user_id, subjectType = null) {
  console.log(`📊 getStats() for ${user_id}, subjectType: ${subjectType}`);

  if (!subjectType) {
    const { data, error } = await supabase
      .from('user_answers')
      .select('is_correct')
      .eq('user_id', user_id);

    if (error) {
      console.error('❌ Supabase stats fetch error:', error);
      return { total: 0, correct: 0 };
    }

    const total = data.length;
    const correct = data.filter(r => r.is_correct).length;
    return { total, correct };
  }

  const { data, error } = await supabase.rpc('get_stats_by_type', {
    input_user_id: user_id,
    input_type: subjectType,
  });

  if (error) {
    console.error('❌ Supabase stats fetch error by type:', error);
    return { total: 0, correct: 0 };
  }

  const total = data.length;
  const correct = data.filter(r => r.is_correct).length;
  return { total, correct };
}

// ✅ 유저가 틀린 문제 번호 리스트
async function getWrongAnswers(user_id, subjectType = null) {
  console.log(`🚫 getWrongAnswers() for ${user_id}, subjectType: ${subjectType}`);

  if (!subjectType) {
    const { data: wrongs, error } = await supabase
      .from('user_answers')
      .select('question_id')
      .eq('user_id', user_id)
      .eq('is_correct', false);

    if (error) {
      console.error('❌ Supabase wrongs fetch error:', error);
      return [];
    }

    const ids = wrongs.map(r => r.question_id);

    const { data: questions, error: qErr } = await supabase
      .from('questions')
      .select('question_number, id');

    if (qErr) {
      console.error('❌ Supabase questions fetch error:', qErr);
      return [];
    }

    return questions
      .filter(q => ids.includes(q.id))
      .map(q => q.question_number);
  }

  const { data, error } = await supabase.rpc('get_wrong_question_numbers_by_type', {
    input_user_id: user_id,
    input_type: subjectType,
  });

  if (error) {
    console.error('❌ Supabase wrongs fetch error by type:', error);
    return [];
  }

  return data.map(r => r.question_number);
}

// ✅ 유저 응답 삽입
async function insertAnswer(answerData) {
  const { error } = await supabase
    .from('user_answers')
    .insert(answerData);

  if (error) {
    console.error('❌ Insert error (user_answers):', error);
  } else {
    console.log(`📌 답안 기록됨: user_id=${answerData.user_id}, q=${answerData.question_id}, 정답여부=${answerData.is_correct}`);
  }
}

module.exports = {
  getUserAnsweredIds,
  getAllQuestions,
  getStats,
  getWrongAnswers,
  insertAnswer,
};
