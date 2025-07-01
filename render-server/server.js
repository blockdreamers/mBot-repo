// server.js
const express = require("express");
const bodyParser = require("body-parser");
const dotenv = require("dotenv");
const { bot } = require("./telegram"); // 📦 봇 객체를 직접 가져옴

dotenv.config();

const app = express();
app.use(bodyParser.json());

const PORT = process.env.PORT || 3000;

// ✅ Webhook 엔드포인트 (Render가 호출함)
app.post("/webhook", async (req, res) => {
  try {
    const body = req.body;
    console.log("📩 Webhook 수신:", JSON.stringify(body, null, 2));

    // ✅ Telegram 봇에게 이벤트 전달
    await bot.handleUpdate(body);
    res.status(200).send("OK");
  } catch (err) {
    console.error("❌ Webhook 처리 오류:", err.message);
    res.status(500).send("Internal Server Error");
  }
});

app.listen(PORT, () => {
  console.log(`🚀 서버 실행 중 (포트 ${PORT})`);
});
