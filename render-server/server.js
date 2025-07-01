// render-server/server.js

const express = require("express");
const bodyParser = require("body-parser");
const axios = require("axios");
require("dotenv").config();

const app = express();
app.use(bodyParser.json());

const TELEGRAM_TOKEN = process.env.TELEGRAM_TOKEN;
const TELEGRAM_API = `https://api.telegram.org/bot${TELEGRAM_TOKEN}`;

// Telegram Webhook entry point
app.post("/webhook", async (req, res) => {
  const body = req.body;
  const message = body.message || body.callback_query;

  if (!message) {
    return res.send("No message received");
  }

  const chatId = message.chat.id;
  const text = message.text || message.data;

  console.log("📥 Received:", text);

  // 🧠 간단한 응답
  if (text === "/start") {
    await axios.post(`${TELEGRAM_API}/sendMessage`, {
      chat_id: chatId,
      text: "Render에서 실행 중인 텔레봇입니다 🤖",
    });
  }

  res.send("OK");
});

// Render가 자동으로 할당한 포트
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`🚀 Telegram bot server running on port ${PORT}`);
});
