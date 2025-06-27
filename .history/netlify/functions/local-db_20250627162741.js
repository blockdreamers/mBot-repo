const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_KEY
);

// ✅ 과목 필터를 적용한 getUserAnsweredIds
async function getUserAnsweredIds(user_id, subjectType = null) {
  if (!subjectType) {
    // 기존과 동일하게 전체 과목
    const { data, error } = await supabase
      .from('user_answers')
      .select('question_id')
      .eq('user_id', user_id);
    if (error) {
      console.error('❌ Supabase fetch error (user_answers):', error);
      return [];
    }
    return data.map(row => row.question_id);
  }

  // 과목별 필터 적용
  const { data, error } = await supabase
    .rpc('get_answered_ids_by_type', {
      input_user_id: user_id,
      input_type: subjectType,
    });

  if (error) {
    console.error('❌ Supabase fetch error (user_answers by type):', error);
    return [];
  }

  return data.map(row => row.question_id);
}

// ✅ 전체 문제 가져오기 (기존 그대로)
async function getAllQuestions() {
  const { data, error } = await supabase
    .from('questions')
    .select('*')
    .order('question_number', { ascending: true });
  if (error) {
    console.error('❌ Supabase fetch error (questions):', error);
    return [];
  }
  return data;
}

// ✅ 과목 필터를 적용한 getStats
async function getStats(user_id, subjectType = null) {
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

  const { data, error } = await supabase
    .rpc('get_stats_by_type', {
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

// ✅ 과목 필터를 적용한 getWrongAnswers
async function getWrongAnswers(user_id, subjectType = null) {
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
    const { data: questions } = await supabase
      .from('questions')
      .select('question_number, id');

    return questions
      .filter(q => ids.includes(q.id))
      .map(q => q.question_number);
  }

  const { data, error } = await supabase
    .rpc('get_wrong_question_numbers_by_type', {
      input_user_id: user_id,
      input_type: subjectType,
    });

  if (error) {
    console.error('❌ Supabase wrongs fetch error by type:', error);
    return [];
  }

  return data.map(r => r.question_number);
}

// ✅ 그대로 유지
async function insertAnswer(answerData) {
  const { error } = await supabase.from('user_answers').insert(answerData);
  if (error) console.error('❌ Insert error:', error);
}

module.exports = {
  getUserAnsweredIds,
  getAllQuestions,
  getStats,
  getWrongAnswers,
  insertAnswer,
};
