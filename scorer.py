def judge(question: str, expects: str, answer: str, results) -> bool:

    if not expects:
        return False
    phrases = [expects] if isinstance(expects, str) else expects
    answer = (answer or "").lower()
    return all(p.strip().lower() in answer for p in phrases)

