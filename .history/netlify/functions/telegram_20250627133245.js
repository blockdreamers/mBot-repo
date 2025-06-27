// netlify/functions/telegram.js
const { Telegraf } = require('telegraf');

const bot = new Telegraf(process.env.TELEGRAM_TOKEN);

bot.on('text', (ctx) => {
  ctx.reply('✅ Netlify에 잘 배포되었어요!');
});

exports.handler = async (event, context) => {
  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      body: 'Method Not Allowed',
    };
  }

  try {
    const body = JSON.parse(event.body);
    await bot.handleUpdate(body);
    return {
      statusCode: 200,
      body: '',
    };
  } catch (err) {
    console.error('❌ Error handling Telegram update', err);
    return {
      statusCode: 500,
      body: 'Internal Server Error',
    };
  }
};
