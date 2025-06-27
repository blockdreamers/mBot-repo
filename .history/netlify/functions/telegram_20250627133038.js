const { Telegraf } = require('telegraf');

const bot = new Telegraf(process.env.TELEGRAM_TOKEN);

bot.on('message', async (ctx) => {
  await ctx.reply('🤖 Netlify에서 동작 중인 텔레그램 봇이야!');
});

exports.handler = async (event) => {
  try {
    const body = JSON.parse(event.body);
    await bot.handleUpdate(body);
    return { statusCode: 200, body: 'ok' };
  } catch (err) {
    console.error('❌ Webhook Error:', err);
    return { statusCode: 500, body: 'error' };
  }
};
