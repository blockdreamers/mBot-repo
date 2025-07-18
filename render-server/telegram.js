if (process.env.NODE_ENV !== "production") {
  require("dotenv").config();
  console.log("🌱 .env 환경변수 로드됨 (로컬 개발 환경)");
}

const { Telegraf, Markup } = require("telegraf");
const {
  getUserAnsweredIds,
  getAllQuestions,
  getStats,
  getWrongAnswers,
  insertAnswer,
} = require("./db");

const {
  getText,
  getLanguage,
  setLanguage,
  registerLanguageHandlers,
  getLanguageKeyboard,
} = require("./language");

const bot = new Telegraf(process.env.TELEGRAM_TOKEN);

const userSubjects = {};
const SUBJECT_TYPES = ["cr", "math", "rc", "di"];
SUBJECT_TYPES.forEach((type) => {
  bot.command(type, (ctx) => {
    const user_id = String(ctx.from.id);
    userSubjects[user_id] = type;
    console.log(`🧭 과목 설정: ${user_id} → ${type}`);
    ctx.reply(`✅ 현재 과목이 [${type.toUpperCase()}]로 설정되었습니다.`);
  });
});

registerLanguageHandlers(bot);

bot.start(async (ctx) => {
  const user_id = String(ctx.from.id);
  const lang = await getLanguage(user_id);
  ctx.reply(getText("select_language", lang), getLanguageKeyboard());
});

bot.command("help", async (ctx) => {
  const user_id = String(ctx.from.id);
  const lang = await getLanguage(user_id);
  ctx.reply(getText("help", lang));
});

bot.hears(/^\/q(\d*)$/, async (ctx) => {
  const user_id = String(ctx.from.id);
  const lang = await getLanguage(user_id);
  const currentSubject = userSubjects[user_id] || "cr";
  const msg = ctx.message.text;

  const answeredIds = await getUserAnsweredIds(user_id, currentSubject);
  const allQuestions = await getAllQuestions();

  const questions = allQuestions.filter(
    (q) => q.type.toLowerCase() === currentSubject.toLowerCase()
  );

  console.log(`🧾 유저 ${user_id} 요청한 과목: ${currentSubject}`);
  console.log(`📚 총 ${questions.length}개의 ${currentSubject} 문제 중에서 선택`);

  let question;
  if (msg.length > 2) {
    const num = parseInt(msg.slice(2));
    question = questions.find((q) => Number(q.question_number) === num);
    if (!question) return ctx.reply(`${num}번 문제를 찾을 수 없습니다.`);
  } else {
    const answeredIdSet = new Set(answeredIds.map((id) => id.toString()));
    question = questions.find((q) => !answeredIdSet.has(q.id.toString()));
  }

  if (!question) return ctx.reply(getText("noQuestions", lang));

  console.log("🆕 출제 문제:", {
    id: question.id,
    number: question.question_number,
    type: question.type,
  });

  function escapeMarkdown(text) {
    return text
      .replace(/_/g, "\\_")
      .replace(/\*/g, "\\*")
      .replace(/\[/g, "\\[")
      .replace(/\]/g, "\\]")
      .replace(/\(/g, "\\(")
      .replace(/\)/g, "\\)")
      .replace(/~/g, "\\~")
      .replace(/`/g, "\\`")
      .replace(/>/g, ">")
      .replace(/#/g, "#")
      .replace(/\+/g, "+")
      .replace(/-/g, "-")
      .replace(/=/g, "=")
      .replace(/\|/g, "|")
      .replace(/{/g, "{")
      .replace(/}/g, "}");
  }

  let text = `*문제 ${question.question_number}:*\n${escapeMarkdown(question.question)}\n\n`;
  question.choices.forEach((c, i) => {
    text += `${String.fromCharCode(65 + i)}. ${escapeMarkdown(c.trim())}\n`;
  });

  const timestamp = Date.now();
  const buttons = question.choices.map((_, i) => {
    const payload = `${question.id}|${i + 1}|${timestamp}|${currentSubject}`;
    console.log(`📤 버튼 생성 → ${String.fromCharCode(65 + i)} = ${payload}`);
    return Markup.button.callback(String.fromCharCode(65 + i), payload);
  });

  await ctx.reply(text, {
    parse_mode: "Markdown",
    reply_markup: { inline_keyboard: [buttons] },
  });
});

bot.on("callback_query", async (ctx) => {
  const user_id = String(ctx.from.id);
  const lang = await getLanguage(user_id);
  console.log("📩 수신된 콜백 데이터:", ctx.callbackQuery.data);
  console.log("🌐 현재 언어 설정:", lang);

  if (!ctx.callbackQuery.data || ctx.callbackQuery.data.split("|").length !== 4) {
    console.error("❌ 잘못된 콜백 데이터 형식:", ctx.callbackQuery.data);
    return ctx.answerCbQuery("❌ 잘못된 응답 형식입니다.");
  }

  const [qid, selectedStr, startStr, subject] = ctx.callbackQuery.data.split("|");
  const selected = parseInt(selectedStr);
  const start = parseInt(startStr);
  const submitted = Date.now();

  console.log("🧪 파싱된 값:", { qid, selected, start, subject });

  const allQuestions = await getAllQuestions();
  const questions = allQuestions.filter(
    (q) => q.type.toLowerCase() === subject.toLowerCase()
  );

  const q = questions.find((q) => q.id.toString() === qid);
  console.log("🔍 최종 매칭된 문제:", q || "❌ 매칭 실패");

  if (!q) {
    return ctx.answerCbQuery("❌ 문제 정보를 불러올 수 없습니다.");
  }

  const is_correct = selected === q.answer;
  const elapsed = Math.round((submitted - start) / 1000);

  await insertAnswer({
    user_id,
    question_id: q.id,
    user_answer: selected,
    is_correct,
    started_at: new Date(start).toISOString(),
    submitted_at: new Date(submitted).toISOString(),
    answered_at: new Date(submitted).toISOString(),
  });

  const stats = await getStats(user_id, subject);
  const mins = Math.floor(elapsed / 60);
  const secs = elapsed % 60;

  const explanation = lang === "en" ? q.explanation_en : q.explanation;
  console.log("🧾 해설 선택 분기:", {
    lang,
    explanation_ko: q.explanation,
    explanation_en: q.explanation_en,
    selected: explanation,
  });

  const resultText = getText("result", lang);

  await ctx.reply(
    `📘 ${lang === "en" ? "Question" : "문제"} ${q.question_number}\n` +
      `${resultText.your_choice}: ${String.fromCharCode(64 + selected)}\n` +
      `${is_correct ? resultText.correct : resultText.wrong}\n\n` +
      `${resultText.explanation}: ${explanation}\n\n` +
      `${resultText.time(mins, secs)}\n${resultText.stats(stats.correct, stats.total)}`
  );

  await ctx.answerCbQuery();
});

bot.command("wrong", async (ctx) => {
  const user_id = String(ctx.from.id);
  const lang = await getLanguage(user_id);
  const subject = userSubjects[user_id] || "cr";

  try {
    const wrongs = await getWrongAnswers(user_id, subject);
    console.log("[/wrong 디버깅] 반환된 목록:", wrongs);

    if (!Array.isArray(wrongs)) {
      console.error("❌ getWrongAnswers() 반환값이 배열이 아님:", wrongs);
      return ctx.reply("⚠️ 틀린 문제 데이터를 불러오는 데 문제가 발생했습니다.");
    }

    if (wrongs.length === 0) {
      return ctx.reply(lang === "en" ? "🥳 No wrong answers!" : "🥳 틀린 문제가 없습니다!");
    }

    const text =
      `❌ [${subject.toUpperCase()}] ${lang === "en" ? "Wrong questions:" : "틀린 문제"}\n` +
      wrongs.map((n) => `문제 ${n}`).join("\n");

    ctx.reply(text);
  } catch (err) {
    console.error("❌ /wrong 처리 중 오류 발생:", err);
    ctx.reply("⚠️ 오류가 발생했습니다.");
  }
});

bot.command("stats", async (ctx) => {
  const user_id = String(ctx.from.id);
  const lang = await getLanguage(user_id);
  const subject = userSubjects[user_id] || "cr";

  try {
    const stats = await getStats(user_id, subject);
    console.log("[/stats 디버깅]", stats);

    if (!stats || typeof stats !== "object") {
      return ctx.reply("⚠️ 통계 데이터를 불러오는 데 문제가 발생했습니다.");
    }

    const { total, correct } = stats;
    const percent = Math.round((correct / total) * 100);
    const msg = lang === "en"
      ? `📊 [${subject.toUpperCase()}] Accuracy: ${correct}/${total} (${percent}%)`
      : `📊 [${subject.toUpperCase()}] 정답률: ${correct}/${total} (${percent}%)`;

    ctx.reply(msg);
  } catch (err) {
    console.error("❌ /stats 처리 중 오류 발생:", err);
    ctx.reply("⚠️ 오류가 발생했습니다.");
  }
});

module.exports.handler = async (event) => {
  if (event.httpMethod === "POST") {
    try {
      const body = JSON.parse(event.body);
      console.log("📩 Webhook 요청 수신됨:", body);
      await bot.handleUpdate(body);
      return {
        statusCode: 200,
        body: "OK",
      };
    } catch (err) {
      console.error("❌ Webhook 처리 중 오류:", err.message);
      return {
        statusCode: 500,
        body: "Internal Server Error: " + err.message,
      };
    }
  } else {
    return {
      statusCode: 405,
      body: "Method Not Allowed",
    };
  }
};

const IS_NETLIFY = !!process.env.NETLIFY || !!process.env.NETLIFY_DEV;
if (!IS_NETLIFY) {
  bot.launch();
  console.log("🤖 Telegraf 봇 로컬 실행 중 (Polling 모드)");
}

module.exports = { bot };
