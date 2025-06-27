// netlify/functions/telegram.js

const { Telegraf } = require('telegraf');

// 👉 토큰은 환경변수로부터 읽음 (.env 또는 Netlify UI에서 설정)
const bot = new Telegraf(process.env.TELEGRAM_TOKEN);

// ✅ 텍스트 메시지 핸들링
bot.on('text', async (ctx) => {
  await ctx.reply('✅ Netlify에 잘 배포되었어요!');
});

// ✅ Netlify Function entry point
exports.handler = async (event, context) => {
  // ❗POST 요청만 처리
  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      body: 'Method Not Allowed',
    };
  }

  try {
    // Telegram webhook에서 온 JSON 파싱
    const update = JSON.parse(event.body);
    await bot.handleUpdate(update);
    
    // 응답
    return {
      statusCode: 200,
      body: 'OK',
    };
  } catch (err) {
    console.error('❌ Telegram update 처리 중 에러 발생:', err);
    return {
      statusCode: 500,
      body: 'Internal Server Error',
    };
  }
};
