require("dotenv").config();
const { Telegraf, Markup } = require("telegraf");
const {
  getUserAnsweredIds,
  getAllQuestions,
  getStats,
  getWrongAnswers,
  insertAnswer,
} = require("./local-db"); // ✅ 변경된 경로

const bot = new Telegraf(process.env.TELEGRAM_TOKEN);

// ✅ 유저별 현재 과목 세션 (메모리 저장)
const userSubjects = {};  // e.g., { "123456": "math" }
const SUBJECT_TYPES = ["cr", "math", "rc", "di"];

// ✅ 과목 선택 명령어 핸들링
SUBJECT_TYPES.forEach((type) => {
  bot.command(type, (ctx) => {
    const user_id = String(ctx.from.id);
    userSubjects[user_id] = type;
    ctx.reply(`✅ 현재 과목이 [${type.toUpperCase()}]로 설정되었습니다.`);
  });
});

// 🟢 /start
bot.start((ctx) => {
  ctx.reply(
    `안녕하세요! GMAT 문제풀이 봇입니다.\n\n🧭 과목 선택:\n/cr - CR 문제\n/math - Math 문제\n/rc - RC 문제\n/di - DI 문제\n\n📌 명령어:\n/q - 다음 문제\n/q<number> - 특정 번호 문제\n/wrong - 틀린 문제 목록\n/stats - 과목별 통계\n/help - 전체 명령어`
  );
});

// 🆘 /help
bot.command("help", (ctx) => {
  ctx.reply(
    `📚 사용 가능한 명령어:\n/cr, /math, /rc, /di - 과목 선택\n/q - 다음 문제\n/q123 - 특정 문제 보기\n/wrong - 틀린 문제 보기\n/stats - 통계 보기`
  );
});

// ❓ /q or /q<number>
bot.hears(/^\/q(\d*)$/, async (ctx) => {
  const user_id = String(ctx.from.id);
  const currentSubject = userSubjects[user_id] || "cr";
  const msg = ctx.message.text;

  const answeredIds = await getUserAnsweredIds(user_id, currentSubject);
  const questions = (await getAllQuestions()).filter((q) => q.type === currentSubject);

  let question;
  if (msg.length > 2) {
    const num = parseInt(msg.slice(2));
    question = questions.find((q) => Number(q.question_number) === num);
    if (!question) return ctx.reply(`${num}번 문제를 찾을 수 없습니다.`);
  } else {
    question = questions.find((q) => !answeredIds.includes(q.id));
    if (!question) return ctx.reply("👏 해당 과목의 모든 문제를 푸셨습니다!");
  }

  let text = `*문제 ${question.question_number}:*\n${question.question}\n\n`;
  question.choices.forEach((c, i) => {
    text += `${String.fromCharCode(65 + i)}. ${c.trim()}\n`;
  });

  const timestamp = Date.now();
  const buttons = question.choices.map((_, i) =>
    Markup.button.callback(
      String.fromCharCode(65 + i),
      `${question.id}|${i + 1}|${timestamp}|${currentSubject}`
    )
  );

  await ctx.reply(text, {
    parse_mode: "Markdown",
    reply_markup: { inline_keyboard: [buttons] },
  });

  console.log(`📨 유저 ${user_id}에게 [${currentSubject.toUpperCase()}] ${question.question_number}번 전송`);
});

// 🔘 버튼 응답 처리
bot.on("callback_query", async (ctx) => {
  const [qid, selectedStr, startStr, subject] = ctx.callbackQuery.data.split("|");
  const selected = parseInt(selectedStr);
  const start = parseInt(startStr);
  const submitted = Date.now();
  const user_id = String(ctx.from.id);

  const questions = (await getAllQuestions()).filter((q) => q.type === subject);
  const q = questions.find((q) => q.id === qid);
  if (!q) return ctx.answerCbQuery("문제 정보를 찾을 수 없습니다.");

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

  await ctx.reply(
    `📘 문제 ${q.question_number}\n당신의 선택: ${String.fromCharCode(
      64 + selected
    )}\n${is_correct ? "✅ 정답입니다!" : "❌ 오답입니다."}\n\n📝 해설: ${
      q.explanation
    }\n\n⏱ 풀이 시간: ${mins}분 ${secs}초\n📊 현재까지 ${stats.total}문제 중 ${stats.correct}문제 정답`
  );

  await ctx.answerCbQuery();
});

// ❌ /wrong
bot.command("wrong", async (ctx) => {
  const user_id = String(ctx.from.id);
  const subject = userSubjects[user_id] || "cr";
  const wrongs = await getWrongAnswers(user_id, subject);
  if (!wrongs.length) return ctx.reply("🥳 틀린 문제가 없습니다!");

  const text = `❌ [${subject.toUpperCase()}] 틀린 문제:\n` + wrongs.map((n) => `문제 ${n}`).join("\n");
  ctx.reply(text);
});

// 📊 /stats
bot.command("stats", async (ctx) => {
  const user_id = String(ctx.from.id);
  const subject = userSubjects[user_id] || "cr";
  const { total, correct } = await getStats(user_id, subject);
  if (total === 0) return ctx.reply(`[${subject.toUpperCase()}] 아직 푼 문제가 없습니다.`);

  const percent = Math.round((correct / total) * 100);
  ctx.reply(`📊 [${subject.toUpperCase()}] 정답률: ${correct}/${total} (${percent}%)`);
});

// ✅ 로컬 실행용
bot.launch().then(() => {
  console.log("🚀 Local Telegram Bot started");
});
