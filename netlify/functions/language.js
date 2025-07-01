// language.js

const { Markup } = require("telegraf");

const userLanguages = {}; // user_id → 'ko' | 'en'

// 🔤 지원 언어별 텍스트 정의
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
};

// ✅ 언어 선택 버튼
function getLanguageKeyboard() {
  return Markup.inlineKeyboard([
    [Markup.button.callback("🇰🇷 한국어", "lang|ko")],
    [Markup.button.callback("🇺🇸 English", "lang|en")],
  ]);
}

// ✅ 언어 텍스트 반환 함수
function getText(key, lang = "ko") {
  return TEXTS[key]?.[lang] || TEXTS[key]?.ko || key;
}

// ✅ 유저 언어 저장 및 조회
function setLanguage(userId, lang) {
  userLanguages[userId] = lang;
}
function getLanguage(userId) {
  return userLanguages[userId] || "ko";
}

// ✅ 언어 관련 핸들러 등록
function registerLanguageHandlers(bot) {
  // /language 명령어
  bot.command("language", (ctx) => {
    const lang = getLanguage(String(ctx.from.id));
    ctx.reply(getText("select_language", lang), getLanguageKeyboard());
  });

  // 언어 버튼 콜백 처리
  bot.action(/^lang\|(ko|en)$/, async (ctx) => {
    const lang = ctx.match[1];
    const userId = String(ctx.from.id);
    setLanguage(userId, lang);
    await ctx.answerCbQuery();
    await ctx.reply(getText("lang_set", lang));
  });
}

module.exports = {
  getText,
  getLanguage,
  setLanguage,
  registerLanguageHandlers,
};
