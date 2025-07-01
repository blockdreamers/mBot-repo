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
    console.warn("❗ No message or callback_query in body");
    return res.send("No message received");
  }

  const chatId = message.chat.id;
  const text = message.text || message.data;

  console.log("📥 Received:", text);

  try {
    if (text === "/start") {
      await axios.post(`${TELEGRAM_API}/sendMessage`, {
        chat_id: chatId,
        text: "Render에서 실행 중인 텔레봇입니다 🤖",
      });
    } else if (text === "/q") {
      // 여기에 실제 문제 출제 로직을 연결할 수 있음
      const sampleQuestion = "다음 중 논리적으로 가장 약한 주장을 고르시오:\n\n(A) A는 B다\n(B) B는 C다\n(C) A는 C다";
      await axios.post(`${TELEGRAM_API}/sendMessage`, {
        chat_id: chatId,
        text: `🧠 문제입니다:\n\n${sampleQuestion}`,
      });
    } else {
      await axios.post(`${TELEGRAM_API}/sendMessage`, {
        chat_id: chatId,
        text: `❓ 인식할 수 없는 명령어입니다: ${text}`,
      });
    }
  } catch (err) {
    console.error("❌ 메시지 처리 중 오류 발생:", err.message);
    await axios.post(`${TELEGRAM_API}/sendMessage`, {
      chat_id: chatId,
      text: "⚠️ 오류가 발생했어요. 나중에 다시 시도해주세요.",
    });
  }

  res.send("OK");
});

// Render가 자동으로 할당한 포트
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`🚀 Telegram bot server running on port ${PORT}`);
});
