require("dotenv").config(); // ⬅️ .env 지원
const { Telegraf, Markup } = require("telegraf");
const {
  getUserAnsweredIds,
  getAllQuestions,
  getStats,
  getWrongAnswers,
  insertAnswer,
} = require("./netlify/functions/db"); // ← 필요 시 경로 조정

const bot = new Telegraf(process.env.TELEGRAM_TOKEN);

// 🟢 /start
bot.start((ctx) => {
  console.log("🔵 /start 호출됨");
  ctx.reply(
    `안녕하세요! GMAT CR 문제풀이 봇입니다.\n사용할 수 있는 명령어:\n/q - 다음 문제\n/q12 - 12번 문제\n/wrong - 틀린 문제\n/stats - 통계\n/help - 전체 명령어`
  );
});

// 🆘 /help
bot.command("help", (ctx) => {
  console.log("🔵 /help 호출됨");
  ctx.reply(
    `📚 사용 가능한 명령어:\n/q - 다음 문제\n/q12 - 특정 문제 번호로 이동\n/wrong - 내가 틀린 문제 보기\n/stats - 문제 풀이 통계\n/help - 도움말 보기`
  );
});

// ❓ /q or /q<number>
bot.command("q", async (ctx) => {
  console.log("🔵 /q 호출됨");
  const user_id = String(ctx.from.id);
  const msg = ctx.message.text;
  const answeredIds = await getUserAnsweredIds(user_id);
  const questions = await getAllQuestions();

  let question;
  if (msg.length > 2) {
    const num = parseInt(msg.slice(2));
    question = questions.find((q) => Number(q.question_number) === num);
    if (!question) {
      console.log(`❌ ${num}번 문제 없음`);
      return ctx.reply(`${num}번 문제를 찾을 수 없습니다.`);
    }
  } else {
    question = questions.find((q) => !answeredIds.includes(q.id));
    if (!question) {
      console.log(`✅ ${user_id} - 모든 문제 풀이 완료`);
      return ctx.reply("👏 모든 문제를 푸셨습니다!");
    }
  }

  console.log(`🟡 유저 ${user_id} - 문제 ${question.question_number} 전송`);
  console.log("✅ choices:", question.choices);

  if (!Array.isArray(question.choices) || question.choices.length === 0) {
    console.error(`❌ 보기 배열 오류 - question.choices =`, question.choices);
    return ctx.reply("❌ 보기 항목을 불러올 수 없습니다.");
  }

  let text = `*문제 ${question.question_number}:*\n${question.question}\n\n`;
  question.choices.forEach((c, i) => {
    text += `${String.fromCharCode(65 + i)}. ${c}\n`;
  });

  const timestamp = Date.now();

  await ctx.reply(text, {
    reply_markup: Markup.inlineKeyboard(
      question.choices.map((_, i) =>
        Markup.button.callback(
          String.fromCharCode(65 + i),
          `${question.id}|${i + 1}|${timestamp}`
        )
      )
    ),
  });
});

// 🔘 버튼 선택
bot.on("callback_query", async (ctx) => {
  const [qid, selectedStr, startStr] = ctx.callbackQuery.data.split("|");
  const selected = parseInt(selectedStr);
  const start = parseInt(startStr);
  const submitted = Date.now();
  const user_id = String(ctx.from.id);

  const questions = await getAllQuestions();
  const q = questions.find((q) => q.id === qid);
  if (!q) return ctx.answerCbQuery("문제 정보를 찾을 수 없습니다.");

  const is_correct = selected === q.answer;
  const elapsed = Math.round((submitted - start) / 1000);

  // ✅ 로그 출력
  console.log(
    `🟢 유저 ${user_id} - 문제 ${q.question_number} 응답`,
    `선택: ${String.fromCharCode(64 + selected)} / 정답: ${String.fromCharCode(64 + q.answer)}`,
    `(${is_correct ? "정답" : "오답"})`,
    `소요시간: ${elapsed}s`
  );

  await insertAnswer({
    user_id,
    question_id: q.id,
    user_answer: selected,
    is_correct,
    started_at: new Date(start).toISOString(),
    submitted_at: new Date(submitted).toISOString(),
    answered_at: new Date(submitted).toISOString(),
  });

  const stats = await getStats(user_id);
  const mins = Math.floor(elapsed / 60);
  const secs = elapsed % 60;

  await ctx.editMessageText(
    `📘 문제 ${q.question_number}\n당신의 선택: ${String.fromCharCode(
      64 + selected
    )}\n${is_correct ? "✅ 정답입니다!" : "❌ 오답입니다."}\n\n📝 해설: ${
      q.explanation
    }\n\n(풀이 시간: ${mins}분 ${secs}초)\n(현재 ${stats.total}문제 중 ${
      stats.total
    }문제 풀이 완료)`
  );
});

// ❌ /wrong
bot.command("wrong", async (ctx) => {
  const user_id = String(ctx.from.id);
  console.log(`📛 유저 ${user_id} - 틀린 문제 요청`);
  const wrongs = await getWrongAnswers(user_id);
  if (!wrongs.length) return ctx.reply("🥳 틀린 문제가 없습니다!");
  ctx.reply("❌ 틀린 문제 목록:\n" + wrongs.map((n) => `문제 ${n}`).join("\n"));
});

// 📊 /stats
bot.command("stats", async (ctx) => {
  const user_id = String(ctx.from.id);
  const { total, correct } = await getStats(user_id);
  console.log(`📈 유저 ${user_id} - stats 요청 (${correct}/${total})`);
  if (total === 0) return ctx.reply("아직 문제를 푼 기록이 없습니다.");
  ctx.reply(
    `✅ 맞은 문제: ${correct}/${total} (${Math.round(
      (correct / total) * 100
    )}%)`
  );
});

// ✅ 실행
bot.launch();
console.log("🚀 로컬 텔레그램 봇 실행됨. /q 입력해 테스트하세요.");
