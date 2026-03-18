import json
import openai
from flask import request, jsonify
from flask_login import login_required, current_user
from . import chatbot
from langchain_openai import ChatOpenAI
from ..models import db, Progress, Module
from flask import current_app
from langchain.indexes import VectorstoreIndexCreator
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import DirectoryLoader
from markupsafe import Markup
import re
from markdown import markdown

loader = DirectoryLoader("data/")
embeddings = OpenAIEmbeddings(api_key="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")
index_creator = VectorstoreIndexCreator(embedding=embeddings)
index0 = index_creator.from_loaders([loader])

llm = ChatOpenAI(
    model="gpt-4o",
    openai_api_key="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",
)

def get_learning_objective(role, module_key, current_level):
    # Learning objectives mapping as per your spec.
    # For brevity, only a few entries included, expand as needed.
    objectives = {
        "ai_specialist": {
            "A1": {"Apprentice": "remember", "Practitioner": "understand", "Competent": "apply"},
            "A2": {"Apprentice": "remember", "Practitioner": "apply", "Competent": "analyze"},
            "A3": {"Practitioner": "understand", "Competent": "apply"},
            "A4": {},  # No mapping specified
            "A5": {},  # No mapping specified

            "B1": {"Apprentice": "apply", "Practitioner": "apply", "Competent": "evaluate"},
            "B2": {"Apprentice": "understand", "Practitioner": "apply", "Competent": "analyze"},
            "B3": {"Apprentice": "remember", "Practitioner": "understand", "Competent": "understand"},
            "B4": {},  # No mapping specified
            "B5": {},  # No mapping specified
            "B6": {},  # No mapping specified

            "C1": {"Apprentice": "understand", "Practitioner": "understand", "Competent": "apply"},

            "D1": {"Apprentice": "understand", "Practitioner": "understand", "Competent": "apply"},
            "D2": {"Apprentice": "remember", "Practitioner": "understand", "Competent": "apply"},
            "D3": {"Apprentice": "apply", "Practitioner": "apply", "Competent": "apply"},

            "E1": {"Apprentice": "understand", "Practitioner": "apply", "Competent": "evaluate"},
            "E2": {"Apprentice": "understand", "Practitioner": "apply", "Competent": "create"},
            "E3": {}  # No mapping specified
        },
        "comp_chem_specialist": {
            "A1": {"Apprentice": "remember", "Practitioner": "understand", "Competent": "apply"},
            "A2": {"Apprentice": "remember", "Practitioner": "apply", "Competent": "analyze"},
            "A3": {"Practitioner": "understand", "Competent": "apply"},
            "A4": {},  # No mapping specified
            "A5": {},  # No mapping specified

            "B1": {"Apprentice": "apply", "Practitioner": "apply", "Competent": "evaluate"},
            "B2": {"Competent": "apply"},  # Only specified for Competent
            "B3": {"Apprentice": "remember", "Practitioner": "understand", "Competent": "apply"},
            "B4": {},  # No mapping specified
            "B5": {},  # No mapping specified
            "B6": {},  # No mapping specified

            "C1": {"Apprentice": "remember", "Practitioner": "understand", "Competent": "apply"},

            "D1": {"Apprentice": "understand", "Practitioner": "understand", "Competent": "apply"},
            "D2": {"Apprentice": "remember", "Practitioner": "understand", "Competent": "apply"},
            "D3": {"Apprentice": "apply", "Practitioner": "apply", "Competent": "apply"},

            "E1": {"Apprentice": "understand", "Practitioner": "apply", "Competent": "evaluate"},
            "E2": {"Apprentice": "understand", "Practitioner": "apply", "Competent": "create"},
            "E3": {}  # No mapping specified
        }
    }

    # Default fallback
    return objectives.get(role, {}).get(module_key, {}).get(current_level, "remember")
@chatbot.route('/message', methods=['POST'])
@login_required
def message():
    data = request.json
    user_message = data.get('message', '').strip()
    module_id = data.get('module_id')
    progress = Progress.query.filter_by(user_id=current_user.id, module_id=module_id).first()
    module = Module.query.get(module_id)
    module_desc = module.description or ""

    # Detect greeting or first interaction
    greetings = ['hello', 'hi', 'hey', 'start', 'good morning', 'good afternoon', 'good evening']
    first_interaction = not progress or (progress and not progress.quiz_in_progress and not progress.quiz_passed and not getattr(progress, "awaiting_quiz_confirmation", False))
    is_greeting = any(user_message.lower().startswith(g) for g in greetings) or user_message.strip() == ""

    role = current_user.role
    level = current_user.current_level
    skill = get_learning_objective(role, module.key, level)

    # Ensure Progress record exists
    if not progress:
        progress = Progress(user_id=current_user.id, module_id=module_id, status='in_progress')
        db.session.add(progress)
        db.session.commit()

    # --- 1. If user greets or it's first time, greet and explain, then ask if ready for MCQ ---
    if first_interaction or is_greeting:
        lesson_prompt, _ = build_lesson_and_quiz_prompts(skill, module.name, module_desc=module_desc)
        lesson = index0.query(lesson_prompt, llm=llm)
        progress.awaiting_quiz_confirmation = True
        progress.quiz_in_progress = False
        progress.quiz_passed = False
        db.session.commit()
        reply = (
            f"👋 Hello! Welcome to the **{module.name}** module.\n\n"
            f"{lesson}\n\n"
            "Are you ready for a multiple-choice question? (Reply 'yes' to continue, or ask if you need more explanation.)"
        )
        return jsonify({'reply': Markup(markdown(reply))})

    # --- 2. If waiting for quiz confirmation, handle YES or questions ---
    if getattr(progress, "awaiting_quiz_confirmation", False) and not progress.quiz_in_progress:
        # If user is ready for quiz
        if user_message.lower() in ['yes', 'ready', 'ok', 'yep', 'go', 'sure']:
            state = _start_mastery_check(index0, llm, skill, module.name, module_desc)

            progress.quiz_in_progress = True
            progress.awaiting_quiz_confirmation = False
            progress.quiz_passed = False
            progress.quiz_type = 'multi'
            progress.current_quiz_question = json.dumps(state)
            progress.last_wrong_attempt = 0
            db.session.commit()

            q0 = state["questions"][0]
            reply = (
                "✅ Ok — quick mastery check (3 questions).\n\n"
                + _render_question_md(q0, 0, state["total"])
            )
            return jsonify({'reply': Markup(markdown(reply))})

        else:
            # User asked a question, provide answer and ask again if ready for MCQ
            user_question_prompt = (
                f"You are an expert tutor for HPC. The learner said: '{user_message}'. "
                f"Provide a helpful, concise explanation about '{module.name}'.\n\n"
                f"After your answer, say: 'Are you ready for a multiple-choice question? (Reply 'yes' to continue, or ask if you need more explanation.)'"
            )
            explanation = index0.query(user_question_prompt, llm=llm)
            # Remain in quiz confirmation state
            progress.awaiting_quiz_confirmation = True
            db.session.commit()
            return jsonify({'reply': Markup(markdown(explanation))})

    # --- 3. If in quiz mode, check answer ---
    # if progress.quiz_in_progress:
    #     user_answer = user_message.strip().upper()

    #    ############################################
       

    #    ###########################################


    #     if user_answer == progress.quiz_answer:
    #         progress.quiz_in_progress = False
    #         progress.quiz_passed = True
    #         db.session.commit()
    #         reply = (
    #             "✅ Correct! Great job—you have mastered this concept. "
    #             "You can now mark this module as complete."
    #         )
    #         return jsonify({'reply': Markup(markdown(reply)), 'quiz_passed': True})
    #     else:
    #         # Incorrect: explain again and repeat the SAME quiz (no answer shown)
    #         progress.last_wrong_attempt += 1
    #         db.session.commit()
    #         # Explain again with skill+module+desc, repeat same MCQ
    #         lesson_prompt, quiz_prompt = build_lesson_and_quiz_prompts(
    #             progress.current_skill, module.name, module_desc=module_desc, previous_wrong=progress.current_quiz_question
    #         )
    #         improved = index0.query(lesson_prompt, llm=llm)
    #         quiz_text = progress.current_quiz_question.split('Answer')[0].strip()
    #         reply = (
    #             f"❌ That's not correct. Here's a clearer explanation:\n\n"
    #             f"{improved}\n\n"
    #             "Let's try the same question again:\n\n"
    #             f"{quiz_text}\n\n"
    #             "Please answer with A, B, C, or D."
    #         )
    #         return jsonify({'reply': Markup(markdown(reply)), 'quiz_passed': False})
# --- 3. If in quiz mode, run multi-question mastery check ---
    if progress.quiz_in_progress:
        # Load state
        try:
            state = json.loads(progress.current_quiz_question or "{}")
        except Exception:
            state = {}

        questions = state.get("questions") or []
        total = int(state.get("total") or len(questions) or 0)
        idx = int(state.get("idx") or 0)

        # If state is broken, reset to confirmation
        if not questions or idx >= total:
            progress.quiz_in_progress = False
            progress.awaiting_quiz_confirmation = True
            db.session.commit()
            return jsonify({'reply': Markup(markdown(
                "Something went wrong with the quiz state. Reply **yes** to start again."
            ))})

        q = questions[idx]
        qtype = (q.get("type") or "").lower()
        attempts = int(state.get("attempts_on_current") or 0)

        correct = False

        if qtype == "mcq":
            ua = _normalize_mcq_answer(user_message)
            if ua is None:
                # treat as clarification request, do not consume attempt
                hint = q.get("hint") or "Reply with A, B, C, or D."
                reply = (
                    f"ℹ️ {hint}\n\n" +
                    _render_question_md(q, idx, total)
                )
                return jsonify({'reply': Markup(markdown(reply))})

            correct = (ua == (q.get("answer") or "").upper())

        else:
            # task
            rubric = q.get("rubric") or {}
            correct = _check_task_answer(user_message, rubric)

        if correct:
            state["score"] = int(state.get("score") or 0) + 1
            state["attempts_on_current"] = 0

            if qtype == "task":
                state["task_ok"] = True

            feedback = q.get("explain") or "Nice work."
            idx += 1
            state["idx"] = idx

            # Finished?
            if idx >= total:
                passed = (state["score"] >= int(state.get("required") or 2))
                if bool(state.get("require_task", True)):
                    passed = passed and bool(state.get("task_ok", False))

                progress.quiz_in_progress = False
                progress.quiz_passed = bool(passed)
                progress.current_quiz_question = None
                progress.quiz_type = 'multi'
                db.session.commit()

                if passed:
                    reply = (
                        f"✅ **Passed!** Score: **{state['score']}/{total}**.\n\n"
                        "You can now mark this module as complete."
                    )
                    return jsonify({'reply': Markup(markdown(reply)), 'quiz_passed': True})
                else:
                    reply = (
                        f"❌ **Not passed yet.** Score: **{state['score']}/{total}**.\n\n"
                        "If you want, ask me to explain any part, then reply **yes** to try a new short mastery check."
                    )
                    progress.awaiting_quiz_confirmation = True
                    db.session.commit()
                    return jsonify({'reply': Markup(markdown(reply)), 'quiz_passed': False})

            # Continue to next question
            next_q = questions[idx]
            reply = (
                f"✅ Correct.\n\n"
                f"{feedback}\n\n"
                + _render_question_md(next_q, idx, total)
            )
            progress.current_quiz_question = json.dumps(state)
            db.session.commit()
            return jsonify({'reply': Markup(markdown(reply))})

    # Incorrect
    attempts += 1
    state["attempts_on_current"] = attempts

    hint = q.get("hint") or "Try again."
    explain = q.get("explain") or ""

    if attempts <= 1:
        # one retry, same question
        reply = (
            f"❌ Not quite.\n\n"
            f"**Hint:** {hint}\n\n"
            + _render_question_md(q, idx, total)
        )
        progress.current_quiz_question = json.dumps(state)
        db.session.commit()
        return jsonify({'reply': Markup(markdown(reply))})

    # second miss: reveal + move on
    correct_reveal = ""
    if qtype == "mcq":
        correct_reveal = f"Correct answer: **{(q.get('answer') or '').upper()}**"
    else:
        correct_reveal = f"Example answer: `{q.get('sample_answer','')}`"

    # Move to next question
    state["attempts_on_current"] = 0
    idx += 1
    state["idx"] = idx

    if idx >= total:
        passed = (int(state.get("score") or 0) >= int(state.get("required") or 2))
        if bool(state.get("require_task", True)):
            passed = passed and bool(state.get("task_ok", False))

        progress.quiz_in_progress = False
        progress.quiz_passed = bool(passed)
        progress.current_quiz_question = None
        db.session.commit()

        if passed:
            reply = (
                f"✅ Finished. Score: **{state.get('score',0)}/{total}**.\n\n"
                "You can now mark this module as complete."
            )
            return jsonify({'reply': Markup(markdown(reply)), 'quiz_passed': True})

        reply = (
            f"❌ Finished, but not passed. Score: **{state.get('score',0)}/{total}**.\n\n"
            f"{correct_reveal}\n\n"
            f"{explain}\n\n"
            "Ask me for clarification, then reply **yes** to try a new short mastery check."
        )
        progress.awaiting_quiz_confirmation = True
        db.session.commit()
        return jsonify({'reply': Markup(markdown(reply)), 'quiz_passed': False})

    next_q = questions[idx]
    reply = (
        f"❌ Incorrect.\n\n"
        f"{correct_reveal}\n\n"
        f"{explain}\n\n"
        "Next question:\n\n"
        + _render_question_md(next_q, idx, total)
    )
    progress.current_quiz_question = json.dumps(state)
    db.session.commit()
    return jsonify({'reply': Markup(markdown(reply))})

    # --- Fallback: always bring user back to explanation and ask if ready for MCQ ---
    lesson_prompt, _ = build_lesson_and_quiz_prompts(skill, module.name, module_desc=module_desc)
    lesson = index0.query(lesson_prompt, llm=llm)
    progress.awaiting_quiz_confirmation = True
    progress.quiz_in_progress = False
    db.session.commit()
    reply = (
        f"{lesson}\n\n"
        "Are you ready for a multiple-choice question? (Reply 'yes' to continue, or ask if you need more explanation.)"
    )
    return jsonify({'reply': Markup(markdown(reply))})

def build_lesson_and_quiz_prompts(skill, concept, module_desc="", previous_wrong=None):
    """
    Returns (lesson_prompt, quiz_prompt) tailored to skill and module content.
    """
    context = f"Module: '{concept}'. Description: {module_desc}\n"
    skill = skill.lower()
    if skill == "remember" or skill == "remembering":
        lesson_prompt = (
             
            f"Present basic facts, key terms, or essential commands for {context}"
            "List what every beginner should know for this topic. Keep it concise and clear."
        )
        quiz_prompt = (
            context +
            "Ask a single multiple-choice (A-D) question to recall one of the facts or commands presented above. "
            "State the correct answer at the end, e.g. 'Answer: B'."
        )
    elif skill == "understand" or skill == "understanding":
        lesson_prompt = (
            
            f"Explain the core concept of {context} in very simple terms, using analogies if helpful. "
            "Clarify what it does, why it's important, and how it fits into the HPC workflow, based on the description."
        )
        quiz_prompt = (
            context +
            "Write an easy fill-in-the-blank multiple-choice (A-D) question specifically about the concepts in the description. "
            "Example: 'The main function of a job scheduler in HPC is to ___ (A: manage jobs, B: edit scripts, ...)' State the correct answer at the end."
        )
    elif skill == "apply" or skill == "applying":
        lesson_prompt = (
            
            f"Show a practical example of how to use the module/topic of {context} in an HPC setting. "
            "Include a simple job script, command, or hands-on step from the module description. Explain what each line does."
        )
        quiz_prompt = (
            context +
            "Give a very short command or script completion MCQ (A-D) based on the example above. "
            "If the answer is code, include hints. Example: 'Which line submits the job? A: sbatch myjob.sh ...' State the correct answer."
        )
    elif skill == "analyze" or skill == "analyzing":
        lesson_prompt = (
            
            f"Compare two basic methods or commands described in the module of {context}, or show a short script with one obvious error from the content. "
            "Explain their pros/cons or what the error is."
        )
        quiz_prompt = (
            context +
            "Ask a multiple-choice (A-D) question where the user has to spot the error or choose the better option, using the material in the description. "
            "Example: 'Which of these two scripts will run efficiently? Why?' Include the answer at the end."
        )
    elif skill == "evaluate" or skill == "evaluating":
        lesson_prompt = (
            f"Present a simple scenario from the module of {context} requiring a judgment call (e.g., choosing a parallelization strategy). "
            "Describe two options with pros and cons."
        )
        quiz_prompt = (
            context +
            "Ask: 'Which would you choose and why?' as a multiple-choice (A or B) about the scenario. "
            "Give two reasonable options based on the module, and at the end, indicate which is better and why."
        )
    elif skill == "create" or skill == "creating":
        lesson_prompt = (
            f"Challenge the learner to write a simple job script or design a basic workflow as described in the module of {context} . "
            "Give an example and highlight key requirements from the module content."
        )
        quiz_prompt = (
            context +
            "Present a partially completed script or workflow from the module. Ask the learner to fill in a missing line (MCQ, A-D) that achieves a specific task described in the module. "
            "State the correct answer at the end."
        )
    else:
        lesson_prompt = (
            f"Present basic facts, terms, or commands related to the module of {context}."
        )
        quiz_prompt = (
            context +
            "Ask a single multiple-choice (A-D) question to recall a fact from the module description. State the answer at the end."
        )

    # --- FIXED RETRY LOGIC ---
    if previous_wrong:
        lesson_prompt = (
            context +
            "The learner gave a wrong answer to a multiple-choice question about this module. "
            "Provide a clearer and more detailed explanation of the *module's main concept* (not the cognitive skill), using the description above. "
            "Give tips, practical examples, or highlight common mistakes learners make with this topic. "
            "Do NOT explain the meaning of skill levels like 'remember', 'apply', etc. "
            "After your explanation, repeat the same question as before."
        )
        quiz_prompt = previous_wrong

    return lesson_prompt, quiz_prompt


def _extract_json_obj(text: str):
    """
    Attempts to parse a JSON object from LLM output (handles code fences / extra text).
    """
    if not text:
        return None

    # Strip code fences if present
    if "```" in text:
        parts = text.split("```")
        # try to take the largest middle chunk
        candidate = max(parts, key=len)
        text = candidate

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    try:
        return json.loads(text[start:end+1])
    except Exception:
        return None


def build_assessment_prompt(skill: str, concept: str, module_desc: str = "") -> str:
    """
    Ask the model to generate a 3-item mastery check with at least one practical task.
    Output MUST be pure JSON.
    """
    context = f"Module: {concept}\nDescription: {module_desc or 'N/A'}\nTarget skill: {skill}\n"
    return (
        "You are an HPC tutor. Create a short mastery check.\n"
        + context +
        "\nRules:\n"
        "- Output ONLY valid JSON. No markdown, no prose.\n"
        "- Exactly 3 questions.\n"
        "- Questions must be grounded in the module name/description (or general HPC best practice if description is empty).\n"
        "- Include: 2 MCQs and 1 TASK.\n"
        "- MCQ format: A-D choices.\n"
        "- TASK format: learner writes ONE line (command or a single corrected line).\n"
        "- Provide a simple rubric for TASK grading as keywords the answer must include.\n"
        "- Explanations should NOT reference letters like 'Option B'. Explain conceptually.\n"
        "\nJSON schema:\n"
        "{\n"
        '  "required_correct": 2,\n'
        '  "require_task": true,\n'
        '  "questions": [\n'
        "    {\n"
        '      "type": "mcq",\n'
        '      "stem": "...",\n'
        '      "choices": {"A":"...","B":"...","C":"...","D":"..."},\n'
        '      "answer": "A|B|C|D",\n'
        '      "hint": "...",\n'
        '      "explain": "..." \n'
        "    },\n"
        "    {\n"
        '      "type": "mcq",\n'
        '      "stem": "...",\n'
        '      "choices": {"A":"...","B":"...","C":"...","D":"..."},\n'
        '      "answer": "A|B|C|D",\n'
        '      "hint": "...",\n'
        '      "explain": "..." \n'
        "    },\n"
        "    {\n"
        '      "type": "task",\n'
        '      "stem": "...",\n'
        '      "rubric": {"must_include": ["...","..."], "must_not_include": []},\n'
        '      "sample_answer": "...",\n'
        '      "hint": "...",\n'
        '      "explain": "..." \n'
        "    }\n"
        "  ]\n"
        "}\n"
    )


def _render_question_md(q: dict, q_idx: int, total: int) -> str:
    qtype = (q.get("type") or "").lower()
    header = f"**Question {q_idx+1}/{total}**"
    stem = q.get("stem", "").strip()

    if qtype == "mcq":
        choices = q.get("choices") or {}
        return (
            f"{header} *(MCQ)*\n\n"
            f"{stem}\n\n"
            f"A) {choices.get('A','')}\n"
            f"B) {choices.get('B','')}\n"
            f"C) {choices.get('C','')}\n"
            f"D) {choices.get('D','')}\n\n"
            "Reply with **A**, **B**, **C**, or **D**."
        )

    # task
    return (
        f"{header} *(Task — one line)*\n\n"
        f"{stem}\n\n"
        "Reply with a **single line** (command or corrected line)."
    )


def _normalize_mcq_answer(user_message: str):
    if not user_message:
        return None
    s = user_message.strip().upper()
    # Accept "A", "A.", "A)", "Answer: A"
    for ch in s:
        if ch in "ABCD":
            return ch
    return None


def _check_task_answer(user_message: str, rubric: dict) -> bool:
    """
    Simple keyword rubric: must_include tokens must appear; must_not_include tokens must not.
    """
    txt = (user_message or "").strip().lower()
    must_include = [t.lower() for t in (rubric or {}).get("must_include", []) if t]
    must_not = [t.lower() for t in (rubric or {}).get("must_not_include", []) if t]

    if not txt:
        return False
    for t in must_include:
        if t not in txt:
            return False
    for t in must_not:
        if t in txt:
            return False
    return True


def _start_mastery_check(index0, llm, skill: str, module_name: str, module_desc: str):
    """
    Generates assessment JSON (via RAG/LLM), validates it, returns a state dict.
    Falls back to a tiny hardcoded set if parsing fails.
    """
    prompt = build_assessment_prompt(skill, module_name, module_desc)
    raw = index0.query(prompt, llm=llm)
    obj = _extract_json_obj(raw)

    # Validate minimal structure
    if (
        not isinstance(obj, dict)
        or "questions" not in obj
        or not isinstance(obj["questions"], list)
        or len(obj["questions"]) != 3
    ):
        # Fallback (generic)
        obj = {
            "required_correct": 2,
            "require_task": True,
            "questions": [
                {
                    "type": "mcq",
                    "stem": "In an HPC environment, what is the main purpose of a job scheduler (e.g., Slurm)?",
                    "choices": {
                        "A": "To compile source code automatically",
                        "B": "To allocate resources and manage job execution",
                        "C": "To encrypt user files",
                        "D": "To replace the Linux shell"
                    },
                    "answer": "B",
                    "hint": "Think about queues, resource allocation, and fair sharing.",
                    "explain": "Schedulers control when and where jobs run by allocating shared compute resources."
                },
                {
                    "type": "mcq",
                    "stem": "You need to run a long computation on a shared cluster. What is the best practice?",
                    "choices": {
                        "A": "Run it interactively on the login node",
                        "B": "Run it locally on your laptop only",
                        "C": "Submit it as a batch job requesting needed resources",
                        "D": "Disable resource limits"
                    },
                    "answer": "C",
                    "hint": "Login nodes are for editing/compiling, not heavy compute.",
                    "explain": "Batch submission ensures fair scheduling and proper allocation of CPU/memory/time."
                },
                {
                    "type": "task",
                    "stem": "Write a typical Slurm command to submit a batch script named `job.sh`.",
                    "rubric": {"must_include": ["sbatch", "job.sh"], "must_not_include": []},
                    "sample_answer": "sbatch job.sh",
                    "hint": "It is a single word command plus the script filename.",
                    "explain": "Slurm commonly uses `sbatch` for batch submission."
                }
            ]
        }

    questions = obj["questions"]
    total = len(questions)
    required = int(obj.get("required_correct", 2))
    require_task = bool(obj.get("require_task", True))

    return {
        "idx": 0,
        "score": 0,
        "required": required,
        "require_task": require_task,
        "task_ok": False,
        "attempts_on_current": 0,   # 0 or 1 (one retry)
        "questions": questions,
        "total": total
    }

@chatbot.route('/module_intro', methods=['POST'])
@login_required
def module_intro():
    data = request.json
    module_id = data.get('module_id')
    module = Module.query.get(module_id)

    # You could store introductions in DB, or generate via RAG/LangChain/OpenAI
    intro_prompt = (
        f"You are an expert AI tutor for the HPC App. Give a brief, motivational introduction and overview for the module '{module.name}' "
        f"({module.key}). Include what the learner will achieve and key topics covered. Write in 3-5 short sentences."
    )
    intro = index0.query(intro_prompt, llm=llm)
    return jsonify({'intro': Markup(markdown(intro))})

