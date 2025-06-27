// netlify/functions/db.js
const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_KEY
);

async function getUserAnsweredIds(user_id) {
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

async function getStats(user_id) {
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

async function getWrongAnswers(user_id) {
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

  return questions.filter(q => ids.includes(q.id)).map(q => q.question_number);
}

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