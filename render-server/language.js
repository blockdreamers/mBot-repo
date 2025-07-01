const { Markup } = require("telegraf");
const { createClient } = require("@supabase/supabase-js");

// ✅ Supabase 연결
const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_KEY
);

// 🔤 다국어 텍스트 사전
const TEXTS = {
  help: {
    ko: `📚 사용 가능한 명령어:\n/cr, /math, /rc, /di - 과목 선택\n/q - 다음 문제\n/q123 - 특정 번호 보기\n/wrong - 틀린 문제 보기\n/stats - 통계 보기\n/language - 언어 변경`,
    en: `📚 Available commands:\n/cr, /math, /rc, /di - Choose subject\n/q - Next question\n/q123 - Go to a question\n/wrong - View wrong answers\n/stats - View stats\n/language - Change language`,
  },
  select_language: {
    ko: "언어를 선택해주세요:",
    en: "Please select your language:",
  },
  lang_set: {
    ko: "✅ 언어가 한국어로 설정되었습니다.",
    en: "✅ Language set to English.",
  },
  noQuestions: {
    ko: "✅ 모든 문제를 푸셨습니다!",
    en: "✅ You’ve completed all available questions!",
  },
  result: {
    ko: {
      correct: "✅ 정답입니다!",
      wrong: "❌ 오답입니다.",
      your_choice: "당신의 선택",
      explanation: "📝 해설",
      time: (m, s) => `⏱ 풀이 시간: ${m}분 ${s}초`,
      stats: (correct, total) => `📊 현재 ${total}문제 중 ${correct}문제 정답`,
    },
    en: {
      correct: "✅ Correct!",
      wrong: "❌ Incorrect.",
      your_choice: "Your choice",
      explanation: "📝 Explanation",
      time: (m, s) => `⏱ Time taken: ${m} min ${s} sec`,
      stats: (correct, total) => `📊 ${correct} out of ${total} correct`,
    },
  },
};

// ✅ 언어 선택 버튼 UI
function getLanguageKeyboard() {
  return Markup.inlineKeyboard([
    [Markup.button.callback("🇰🇷 한국어", "lang|ko")],
    [Markup.button.callback("🇺🇸 English", "lang|en")],
  ]);
}

// ✅ 다국어 텍스트 조회 함수
function getText(key, lang = "ko") {
  const val = TEXTS[key];
  if (!val) return key;

  if (typeof val === "object" && typeof val[lang] !== "undefined") {
    return val[lang];
  }

  return val["ko"] || key;
}

// ✅ 유저 언어 가져오기 (Supabase 조회)
async function getLanguage(userId) {
  const { data, error } = await supabase
    .from("users")
    .select("language")
    .eq("user_id", userId)
    .single();

  if (error || !data || !data.language) {
    console.warn("⚠️ 언어 정보 없음, 기본값 'ko' 사용:", { userId });
    return "ko";
  }

  return data.language;
}

// ✅ 유저 언어 저장 (Supabase upsert)
async function setLanguage(userId, lang) {
  const { error } = await supabase
    .from("users")
    .upsert({ user_id: userId, language: lang }, { onConflict: ["user_id"] });

  if (error) {
    console.error("❌ 언어 저장 오류:", error);
  } else {
    console.log(`🌐 언어 설정 완료 → ${userId}: ${lang}`);
  }
}

// ✅ 언어 명령어 핸들러 등록
function registerLanguageHandlers(bot) {
  // /language 명령어
  bot.command("language", async (ctx) => {
    const userId = String(ctx.from.id);
    const lang = await getLanguage(userId);
    console.log(`📥 /language 요청 by ${userId} (${lang})`);
    ctx.reply(getText("select_language", lang), getLanguageKeyboard());
  });

  // 버튼 콜백 처리
  bot.action(/^lang\|(ko|en)$/, async (ctx) => {
    const lang = ctx.match[1];
    const userId = String(ctx.from.id);
    await setLanguage(userId, lang);
    await ctx.answerCbQuery();
    await ctx.reply(getText("lang_set", lang), getLanguageKeyboard());
  });
}

module.exports = {
  getText,
  getLanguage,
  setLanguage,
  getLanguageKeyboard,
  registerLanguageHandlers,
};
