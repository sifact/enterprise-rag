# input_guard.py

Detects prompt injection in employee questions and in retrieved passages.

- Two signals: Llama Prompt Guard 2 (86M) on Groq returns an injection probability, and regex rules catch instruction overrides ("ignore … instructions"), prompt extraction ("system prompt"), role play ("you are now", "admin mode") and role claims ("as c_level", "I'm the CFO").
- On the golden set the classifier alone flagged 2 of the 5 direct attacks; the rules flag all 5, and neither flagged any ordinary question (classifier scores ≤ 0.001).
- A question or passage is flagged when any rule fires or the classifier score reaches `guard_threshold` (0.9). Every question is scored; a passage is scored only if it addresses the assistant (e.g. "assistant", "you must", "reply with", 6.9% of passages), because the classifier is limited to 30 requests a minute on the free tier.
- Role-claim rules apply only to questions, because documents legitimately mention roles; the other rules also apply to passages.
- If the classifier is unreachable the rules still run and the result notes "classifier unavailable", so an outage weakens the guard rather than turning it off; `filter_context` returns the kept passages and the removed ones with their reason.
