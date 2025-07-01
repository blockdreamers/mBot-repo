const express = require("express");
const bodyParser = require("body-parser");
const dotenv = require("dotenv");
const { bot } = require("./telegram"); // 📦 봇 객체 import

// ✅ 루트에 있는 .env 명시적으로 로드
dotenv.config({ path: "../.env" });

// ✅ 환경변수 확인 로그
console.log("🌍 현재 로드된 환경변수:", {
  SUPABASE_URL: process.env.SUPABASE_URL,
  SUPABASE_KEY: process.env.SUPABASE_KEY,
  TELEGRAM_TOKEN: process.env.TELEGRAM_TOKEN,
});

// ✅ 환경변수 체크 경고 (선택사항)
if (!process.env.SUPABASE_URL || !process.env.SUPABASE_KEY) {
  console.warn("⚠️ 환경변수(SUPABASE_URL, SUPABASE_KEY)가 비어 있습니다. .env 확인 필요");
}

const app = express();
app.use(bodyParser.json());

const PORT = process.env.PORT || 3000;

// ✅ Telegram Webhook 엔드포인트
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
