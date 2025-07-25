// ✅ .env를 가장 먼저 명확히 불러옴
require("dotenv").config({ path: require("path").resolve(__dirname, ".env") });

const { Telegraf, Markup } = require("telegraf");
const {
  getUserAnsweredIds,
  getAllQuestions,
  getStats,
  getWrongAnswers,
  insertAnswer,
} = require("./netlify/functions/local-db");

const bot = new Telegraf(process.env.TELEGRAM_TOKEN);

// 🧠 유저별 과목 세션 저장
const userSubjects = {}; // user_id: "math" | "cr" | ...

const SUBJECT_TYPES = ["cr", "math", "rc", "di"];
SUBJECT_TYPES.forEach((type) => {
  bot.command(type, (ctx) => {
    const user_id = String(ctx.from.id);
    userSubjects[user_id] = type;
    console.log(`🧭 과목 설정: ${user_id} → ${type}`);
    ctx.reply(`✅ 현재 과목이 [${type.toUpperCase()}]로 설정되었습니다.`);
  });
});

// 🟢 /start
bot.start((ctx) => {
  ctx.reply(
    `안녕하세요! GMAT 문제풀이 봇입니다.\n\n🧭 과목 설정:\n` +
    `/cr, /math, /rc, /di\n\n📌 문제 명령어:\n` +
    `/q - 다음 문제\n/q123 - 특정 문제 번호\n` +
    `/wrong - 틀린 문제 목록\n/stats - 통계 보기\n/help - 전체 명령어`
  );
});

// 🆘 /help
bot.command("help", (ctx) => {
  ctx.reply(
    `📚 사용 가능한 명령어:\n` +
    `/cr, /math, /rc, /di - 과목 선택\n` +
    `/q - 다음 문제\n/q123 - 특정 번호 문제 보기\n` +
    `/wrong - 내가 틀린 문제 보기\n/stats - 과목별 통계 보기`
  );
});

// ❓ /q 또는 /q<number>
bot.hears(/^\/q(\d*)$/, async (ctx) => {
  const user_id = String(ctx.from.id);
  const currentSubject = userSubjects[user_id] || "cr";
  const msg = ctx.message.text;

  const answeredIds = await getUserAnsweredIds(user_id, currentSubject);
  const questions = (await getAllQuestions()).filter(
    (q) => q.type.toLowerCase() === currentSubject.toLowerCase()
  );

  let question;
  if (msg.length > 2) {
    const num = parseInt(msg.slice(2));
    question = questions.find((q) => Number(q.question_number) === num);
    if (!question) return ctx.reply(`${num}번 문제를 찾을 수 없습니다.`);
  } else {
    // ✅ UUID 문자형 비교를 위한 Set 변환
    const answeredIdSet = new Set(answeredIds.map((id) => id.toString()));
    console.log("🧾 answeredIdSet =", [...answeredIdSet]);

    question = questions.find((q) => {
      const isAnswered = answeredIdSet.has(q.id.toString());
      if (isAnswered) {
        console.log(`⚠️ ${q.question_number}번 (${q.id})는 이미 풀이됨`);
      }
      return !isAnswered;
    });
  }

  if (!question) return ctx.reply("👏 해당 과목의 모든 문제를 푸셨습니다!");

  let text = `*문제 ${question.question_number}:*\n${question.question}\n\n`;
  question.choices.forEach((c, i) => {
    text += `${String.fromCharCode(65 + i)}. ${c.trim()}\n`;
  });

  const timestamp = Date.now();
  const buttons = question.choices.map((_, i) => {
    const letter = String.fromCharCode(65 + i); // A, B, C, D, E
    return Markup.button.callback(letter, `${question.id}|${letter}|${timestamp}|${currentSubject}`);
  });

  await ctx.reply(text, {
    parse_mode: "Markdown",
    reply_markup: { inline_keyboard: [buttons] },
  });

  console.log(
    `📨 유저 ${user_id}에게 [${currentSubject.toUpperCase()}] ${question.question_number}번 전송`
  );
});

// 🔘 버튼 응답 처리
bot.on("callback_query", async (ctx) => {
  const [qid, selectedLetter, startStr, subject] = ctx.callbackQuery.data.split("|");
  const start = parseInt(startStr);
  const submitted = Date.now();
  const user_id = String(ctx.from.id);

  const questions = (await getAllQuestions()).filter((q) => q.type === subject);
  const q = questions.find((q) => q.id === qid);
  if (!q) return ctx.answerCbQuery("문제 정보를 찾을 수 없습니다.");

  // A~E 문자열 직접 비교 (변환 불필요!)
  console.log("🔍 정답 비교:", { selectedLetter, dbAnswer: q.answer, match: selectedLetter === q.answer });
  const is_correct = selectedLetter === q.answer;
  const elapsed = Math.round((submitted - start) / 1000);

  await insertAnswer({
    user_id,
    question_id: q.id,
    user_answer: selectedLetter,  // A,B,C,D,E 직접 저장!
    is_correct,
    started_at: new Date(start).toISOString(),
    submitted_at: new Date(submitted).toISOString(),
    answered_at: new Date(submitted).toISOString(),
  });

  const stats = await getStats(user_id, subject);
  const mins = Math.floor(elapsed / 60);
  const secs = elapsed % 60;

  await ctx.reply(
    `📘 문제 ${q.question_number}\n당신의 선택: ${selectedLetter}\n` +
    `${is_correct ? "✅ 정답입니다!" : "❌ 오답입니다."}\n` +
    `정답 : ${q.answer}\n\n📝 해설: ${q.explanation}\n\n` +
    `⏱ 풀이 시간: ${mins}분 ${secs}초\n📊 현재 ${stats.total}문제 중 ${stats.correct}문제 정답`
  );

  await ctx.answerCbQuery();
});

// ❌ /wrong
bot.command("wrong", async (ctx) => {
  const user_id = String(ctx.from.id);
  const subject = userSubjects[user_id] || "cr";
  const wrongs = await getWrongAnswers(user_id, subject);
  if (!wrongs.length) return ctx.reply("🥳 틀린 문제가 없습니다!");

  const text =
    `❌ [${subject.toUpperCase()}] 틀린 문제:\n` +
    wrongs.map((n) => `문제 ${n}`).join("\n");
  ctx.reply(text);
});

// 📊 /stats
bot.command("stats", async (ctx) => {
  const user_id = String(ctx.from.id);
  const subject = userSubjects[user_id] || "cr";
  const { total, correct } = await getStats(user_id, subject);
  if (total === 0)
    return ctx.reply(`[${subject.toUpperCase()}] 아직 푼 문제가 없습니다.`);

  const percent = Math.round((correct / total) * 100);
  ctx.reply(`📊 [${subject.toUpperCase()}] 정답률: ${correct}/${total} (${percent}%)`);
});

// ✅ 로컬 실행 확인 로그 (webhook 삭제 후 시작)
bot.telegram.deleteWebhook()
  .then(() => {
    console.log("✅ Webhook 삭제 완료");
    return bot.launch();
  })
  .then(() => {
    console.log("🚀 Local Telegram Bot started");
    console.log("✅ SUPABASE_URL =", process.env.SUPABASE_URL);
  })
  .catch((error) => {
    console.log("⚠️ 봇 시작 중 오류:", error.message);
    // webhook 삭제 실패해도 봇 시작 시도
    bot.launch()
      .then(() => {
        console.log("🚀 Local Telegram Bot started - Webhook 삭제 실패했지만 시작됨");
        console.log("✅ SUPABASE_URL =", process.env.SUPABASE_URL);
      })
      .catch((launchError) => {
        console.error("❌ 봇 시작 실패:", launchError.message);
      });
  });
