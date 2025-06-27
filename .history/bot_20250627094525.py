def handle_button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    selected = int(query.data)
    user_id = str(query.from_user.id)
    question = context.user_data.get("current_question")
    start_time = context.user_data.get("start_time")
    question_id = context.user_data.get("question_id")

    if not question or not start_time:
        query.edit_message_text("먼저 /q 명령어로 문제를 받아주세요.")
        return

    correct = int(question["answer"])
    is_correct = selected == correct
    submitted_at = datetime.now()
    duration = (submitted_at - start_time).total_seconds()
    qn = question.get("question_number", "?")
    explanation = question.get("explanation", "설명 없음")
    correct_letter = chr(64 + correct)

    try:
        supabase.table("user_answers").insert({
            "user_id": user_id,
            "question_id": question_id,
            "user_answer": selected,
            "is_correct": is_correct,
            "started_at": start_time.isoformat(),
            "submitted_at": submitted_at.isoformat(),
            "duration_seconds": duration,
            "answered_at": submitted_at.isoformat()
        }).execute()

        print(f"📝 User {user_id} answered Q{qn} -> {'Correct' if is_correct else 'Wrong'} ({chr(64+selected)}) in {duration:.1f}s")

    except Exception as e:
        print(f"❌ Failed to log answer for user {user_id}, question {qn}: {str(e)}")

    # ✅ 진척도 계산
    total_questions = supabase.table("questions").select("id").execute().data
    total_count = len(total_questions)

    answered = supabase.table("user_answers").select("question_id").eq("user_id", user_id).execute().data
    answered_ids = {row["question_id"] for row in answered}
    progress = len(answered_ids)

    # ✅ 결과 메시지
    result_text = (
        f"📘 문제 {qn}번\n"
        f"당신의 선택: {chr(64+selected)}\n"
        f"{'✅ 정답입니다!' if is_correct else '❌ 오답입니다.'}\n\n"
        f"📝 해설: {explanation.strip()}\n\n"
        f"(현재 {progress}/{total_count} 문제 풀이완료)"
    )

    try:
        query.edit_message_text(query.message.text_markdown_v2, parse_mode='MarkdownV2')
    except:
        query.edit_message_text(query.message.text, parse_mode='Markdown')
    query.message.reply_text(result_text)
