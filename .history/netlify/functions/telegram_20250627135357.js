// netlify/functions/telegram.js
const { Telegraf, Markup } = require('telegraf');
const {
  getUserAnsweredIds,
  getAllQuestions,
  getStats,
  getWrongAnswers,
  insertAnswer,
} = require('./db');

const bot = new Telegraf(process.env.TELEGRAM_TOKEN);

// 🟢 /start
bot.start((ctx) => {
  ctx.reply(
    `안녕하세요! GMAT CR 문제풀이 봇입니다.\n사용할 수 있는 명령어:\n/q - 다음 문제\n/q12 - 12번 문제\n/wrong - 틀린 문제\n/stats - 통계\n/help - 전체 명령어`
  );
});

// 🆘 /help
bot.command('help', (ctx) => {
  ctx.reply(
    `📚 사용 가능한 명령어:\n/q - 다음 문제\n/q12 - 특정 문제 번호로 이동\n/wrong - 내가 틀린 문제 보기\n/stats - 문제 풀이 통계\n/help - 도움말 보기`
  );
});

// ❓ /q or /q<number>
bot.command('q', async (ctx) => {
  const user_id = String(ctx.from.id);
  const msg = ctx.message.text;
  const answeredIds = await getUserAnsweredIds(user_id);
  const questions = await getAllQuestions();

  let question;
  if (msg.length > 2) {
    const num = parseInt(msg.slice(2));
    question = questions.find(q => q.question_number === num);
    if (!question) return ctx.reply(`${num}번 문제를 찾을 수 없습니다.`);
  } else {
    question = questions.find(q => !answeredIds.includes(q.id));
    if (!question) return ctx.reply("👏 모든 문제를 푸셨습니다!");
  }

  ctx.session = {
    current_question: question,
    start_time: Date.now(),
  };

  let text = `*문제 ${question.question_number}:*\n${question.question}\n\n`;
  question.choices.forEach((c, i) => {
    text += `${String.fromCharCode(65 + i)}. ${c}\n`;
  });

  await ctx.reply(text, {
    parse_mode: 'Markdown',
    reply_markup: Markup.inlineKeyboard(
      question.choices.map((_, i) => [Markup.button.callback(String.fromCharCode(65 + i), `${i + 1}`)])
    ),
  });
});

// 🔘 버튼 선택
bot.on('callback_query', async (ctx) => {
  const selected = parseInt(ctx.callbackQuery.data);
  const user_id = String(ctx.from.id);
  const session = ctx.session || {};
  const q = session.current_question;
  const start = session.start_time;
  const submitted = Date.now();

  if (!q || !start) {
    return ctx.answerCbQuery('먼저 /q 명령어로 문제를 받아주세요.');
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

  const stats = await getStats(user_id);

  await ctx.editMessageText(
    `📘 문제 ${q.question_number}\n당신의 선택: ${String.fromCharCode(64 + selected)}\n$${is_correct ? '✅ 정답입니다!' : '❌ 오답입니다.'}\n\n📝 해설: ${q.explanation}\n\n(풀이 시간: ${Math.floor(elapsed / 60)}분 ${elapsed % 60}초)\n(현재 ${stats.total}문제 중 ${stats.total}문제 풀이 완료)`
  );
});

// ❌ /wrong
bot.command('wrong', async (ctx) => {
  const user_id = String(ctx.from.id);
  const wrongs = await getWrongAnswers(user_id);
  if (!wrongs.length) return ctx.reply('🥳 틀린 문제가 없습니다!');
  ctx.reply('❌ 틀린 문제 목록:\n' + wrongs.map(n => `문제 ${n}`).join('\n'));
});

// 📊 /stats
bot.command('stats', async (ctx) => {
  const user_id = String(ctx.from.id);
  const { total, correct } = await getStats(user_id);
  if (total === 0) return ctx.reply('아직 문제를 푼 기록이 없습니다.');
  ctx.reply(`✅ 맞은 문제: ${correct}/${total} (${Math.round((correct / total) * 100)}%)`);
});

// ✅ Netlify entry point
exports.handler = async (event) => {
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, body: 'Method Not Allowed' };
  }
  try {
    const body = JSON.parse(event.body);
    await bot.handleUpdate(body);
    return { statusCode: 200, body: 'OK' };
  } catch (e) {
    console.error('❌ handleUpdate error:', e);
    return { statusCode: 500, body: 'Internal Server Error' };
  }
};