// ✅ 로컬 개발환경에서만 .env 로드 (.env가 루트에 있을 경우 정확한 경로 지정)
if (process.env.NODE_ENV !== "production") {
  const path = require("path");
  // ✅ .env 경로 명시 (루트 기준으로 두 단계 위)
  require("dotenv").config({ path: require("path").resolve(__dirname, "../.env") });
}

// ✅ 환경변수 누락 경고
if (!process.env.SUPABASE_URL || !process.env.SUPABASE_KEY) {
  console.warn("⚠️ 환경변수(SUPABASE_URL, SUPABASE_KEY)가 비어 있습니다. .env 확인 필요");
}

const { createClient } = require("@supabase/supabase-js");

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_KEY
);

// ✅ 유저가 푼 문제 ID 리스트 (과목별 필터 지원)
async function getUserAnsweredIds(user_id, subjectType = null) {
  console.log(`📥 getUserAnsweredIds() called with subjectType: ${subjectType}`);

  if (!subjectType) {
    const { data, error } = await supabase
      .from("user_answers")
      .select("question_id")
      .eq("user_id", user_id);

    if (error) {
      console.error("❌ Supabase fetch error (user_answers):", error);
      return [];
    }

    console.log(`📦 ${data.length} answered questions (no subject filter)`);
    return data.map((row) => row.question_id);
  }

  const { data, error } = await supabase.rpc("get_answered_ids_by_type", {
    input_user_id: user_id,
    input_type: subjectType,
  });

  if (error) {
    console.error("❌ Supabase fetch error (get_answered_ids_by_type):", error);
    return [];
  }

  console.log(`📦 ${data.length} answered questions for subject "${subjectType}"`);
  return data.map((row) => row.question_id);
}

// ✅ 전체 문제 리스트 (정렬 포함, id 필드 명시)
async function getAllQuestions() {
  const { data, error } = await supabase
    .from("questions")
    .select("id, question_number, question, choices, type, answer, explanation, explanation_en") // ✅ 추가됨
    .order("question_number", { ascending: true });

  if (error) {
    console.error("❌ Supabase fetch error (questions):", error);
    return [];
  }

  console.log(`📚 총 ${data.length}문제 불러옴`);
  if (data.length > 0) {
    console.log("🧪 샘플 문제 예시:", {
      id: data[0].id,
      explanation: data[0].explanation,
      explanation_en: data[0].explanation_en,
    });
  }

  return data;
}

// ✅ 유저의 통계 (총 푼 문제, 맞춘 문제)
async function getStats(user_id, subjectType = null) {
  console.log(`📊 getStats() for ${user_id}, subjectType: ${subjectType}`);

  if (!subjectType) {
    const { data, error } = await supabase
      .from("user_answers")
      .select("is_correct")
      .eq("user_id", user_id);

    if (error) {
      console.error("❌ Supabase stats fetch error:", error);
      return { total: 0, correct: 0 };
    }

    const total = data.length;
    const correct = data.filter((r) => r.is_correct).length;
    return { total, correct };
  }

  const { data, error } = await supabase.rpc("get_cr_stats", {
    input_user_id: user_id,
    input_type: subjectType.toLowerCase(),
  });

  if (error) {
    console.error("❌ Supabase stats fetch error (get_cr_stats):", error);
    return { total: 0, correct: 0 };
  }

  const result = data?.[0] ?? { total: 0, correct: 0 };
  console.log(`[/stats 디버깅] 총 ${result.total}개 중 정답 ${result.correct}개`);
  return result;
}

// ✅ 유저가 틀린 문제 번호 리스트
async function getWrongAnswers(user_id, subjectType = null) {
  console.log(`🚫 getWrongAnswers() for ${user_id}, subjectType: ${subjectType}`);

  if (!subjectType) {
    const { data: wrongs, error } = await supabase
      .from("user_answers")
      .select("question_id")
      .eq("user_id", user_id)
      .eq("is_correct", false);

    if (error) {
      console.error("❌ Supabase wrongs fetch error:", error);
      return [];
    }

    const ids = wrongs.map((r) => r.question_id);

    const { data: questions, error: qErr } = await supabase
      .from("questions")
      .select("question_number, id");

    if (qErr) {
      console.error("❌ Supabase questions fetch error:", qErr);
      return [];
    }

    return questions.filter((q) => ids.includes(q.id)).map((q) => q.question_number);
  }

  const { data, error } = await supabase.rpc("get_wrong_question_numbers_by_type", {
    input_user_id: user_id,
    input_type: subjectType,
  });

  if (error) {
    console.error("❌ Supabase wrongs fetch error by type:", error);
    return [];
  }

  return data.map((r) => r.question_number);
}

// ✅ 유저 응답 삽입
async function insertAnswer(answerData) {
  const { error } = await supabase.from("user_answers").insert(answerData);

  if (error) {
    console.error("❌ Insert error (user_answers):", error);
  } else {
    console.log(
      `📌 답안 기록됨: user_id=${answerData.user_id}, q=${answerData.question_id}, 정답여부=${answerData.is_correct}`
    );
  }
}

module.exports = {
  getUserAnsweredIds,
  getAllQuestions,
  getStats,
  getWrongAnswers,
  insertAnswer,
};
