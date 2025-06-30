// ✅ 환경 설정
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

const bot = new Telegraf(process.env.TELEGRAM_TOKEN);

// 🧠 유저별 과목 세션 저장
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
  const allQuestions = await getAllQuestions();

  const questions = allQuestions.filter(
    (q) => q.type.toLowerCase() === currentSubject.toLowerCase()
  );

  console.log(`🧾 유저 ${user_id} 요청한 과목: ${currentSubject}`);
  console.log(
    `📚 총 ${questions.length}개의 ${currentSubject} 문제 중에서 선택`
  );

  let question;
  if (msg.length > 2) {
    const num = parseInt(msg.slice(2));
    question = questions.find((q) => Number(q.question_number) === num);
    if (!question) return ctx.reply(`${num}번 문제를 찾을 수 없습니다.`);
  } else {
    const answeredIdSet = new Set(answeredIds.map((id) => id.toString()));
    question = questions.find((q) => !answeredIdSet.has(q.id.toString()));
  }

  if (!question) return ctx.reply("👏 해당 과목의 모든 문제를 푸셨습니다!");

  console.log("🆕 출제 문제:", {
    id: question.id,
    number: question.question_number,
    type: question.type,
  });

  let text = `*문제 ${question.question_number}:*\n${question.question}\n\n`;
  question.choices.forEach((c, i) => {
    text += `${String.fromCharCode(65 + i)}. ${c.trim()}\n`;
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

// 🔘 버튼 응답 처리
bot.on("callback_query", async (ctx) => {
  const user_id = String(ctx.from.id);
  console.log("📩 수신된 콜백 데이터:", ctx.callbackQuery.data);

  if (
    !ctx.callbackQuery.data ||
    ctx.callbackQuery.data.split("|").length !== 4
  ) {
    console.error("❌ 잘못된 콜백 데이터 형식:", ctx.callbackQuery.data);
    return ctx.answerCbQuery("❌ 잘못된 응답 형식입니다.");
  }

  const [qid, selectedStr, startStr, subject] =
    ctx.callbackQuery.data.split("|");
  const selected = parseInt(selectedStr);
  const start = parseInt(startStr);
  const submitted = Date.now();

  console.log("🧪 파싱된 값:", { qid, selected, start, subject });

  const allQuestions = await getAllQuestions();
  const questions = allQuestions.filter(
    (q) => q.type.toLowerCase() === subject.toLowerCase()
  );

  const availableIds = questions.map((q) => q.id.toString());
  console.log("📚 매칭 시도 중인 ID 목록:", availableIds);

  const q = questions.find((q) => q.id.toString() === qid);
  console.log("🔍 최종 매칭된 문제:", q || "❌ 매칭 실패");

  if (!q) {
    console.error("❌ 질문 ID 매칭 실패", { qid, availableIds });
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

  await ctx.reply(
    `📘 문제 ${q.question_number}\n당신의 선택: ${String.fromCharCode(
      64 + selected
    )}\n` +
      `${is_correct ? "✅ 정답입니다!" : "❌ 오답입니다."}\n\n📝 해설: ${
        q.explanation
      }\n\n` +
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
  console.log("[/stats 디버깅]", { total, correct });

  if (!total || total === 0) {
    return ctx.reply(`[${subject.toUpperCase()}] 아직 푼 문제가 없습니다.`);
  }

  const percent = Math.round((correct / total) * 100);
  ctx.reply(
    `📊 [${subject.toUpperCase()}] 정답률: ${correct}/${total} (${percent}%)`
  );
});

// ✅ Netlify 서버리스 함수용 핸들러
module.exports.handler = async (event) => {
  if (event.httpMethod === "POST") {
    const body = JSON.parse(event.body);
    await bot.handleUpdate(body);
    return {
      statusCode: 200,
      body: "",
    };
  } else {
    return {
      statusCode: 405,
      body: "Method Not Allowed",
    };
  }
};

// ✅ 로컬 테스트 시 polling 으로 실행
if (process.env.NODE_ENV !== "production" && !module.parent) {
  bot.launch();
  console.log("🤖 Telegraf 봇 로컬 실행 중 (Polling 모드)");
}
