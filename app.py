import sys
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
from config import SYSTEM_NAME, DEFAULT_EXAM_DURATION_MINS, PASSING_PERCENTAGE
from questions import get_all_questions
from scoring import calculate_score
from auth import users_db, authenticate

app = Flask(__name__)
app.secret_key = "exam_secret_session_key"

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ system_name }}</title>
    <style>
        :root {
            --primary: #2563eb;
            --primary-hover: #1d4ed8;
            --bg: #f8fafc;
            --card: #ffffff;
            --text: #1e293b;
            --muted: #64748b;
            --success: #16a34a;
            --danger: #dc2626;
            --border: #e2e8f0;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.5;
            padding: 24px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: var(--card);
            border-radius: 16px;
            padding: 32px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
            border: 1px solid var(--border);
        }
        header {
            border-bottom: 2px solid var(--border);
            padding-bottom: 16px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        h1 { font-size: 24px; color: var(--primary); }
        .badge {
            background: #dbeafe;
            color: var(--primary);
            padding: 4px 12px;
            border-radius: 999px;
            font-size: 13px;
            font-weight: 600;
        }
        .user-pill {
            background: #f1f5f9;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 500;
        }
        .form-group { margin-bottom: 20px; }
        label { display: block; font-weight: 600; margin-bottom: 8px; }
        select, input[type="text"], input[type="password"] {
            width: 100%;
            padding: 12px;
            border: 1px solid var(--border);
            border-radius: 8px;
            font-size: 15px;
        }
        .btn {
            display: inline-block;
            background: var(--primary);
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            transition: background 0.2s;
        }
        .btn:hover { background: var(--primary-hover); }
        .btn-logout { background: #ef4444; margin-left: 10px; font-size: 13px; padding: 6px 14px; }
        .btn-logout:hover { background: #dc2626; }
        .question-card {
            background: #f8fafc;
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .question-title { font-weight: 600; margin-bottom: 12px; font-size: 16px; }
        .option-label {
            display: flex;
            align-items: center;
            padding: 10px 14px;
            background: white;
            border: 1px solid var(--border);
            border-radius: 8px;
            margin-bottom: 8px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .option-label:hover { border-color: var(--primary); background: #f0f7ff; }
        .option-label input { margin-right: 12px; }
        .timer-box {
            background: #fef3c7;
            color: #92400e;
            padding: 10px 18px;
            border-radius: 10px;
            font-weight: 700;
            font-size: 16px;
            border: 1px solid #fde68a;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        .timer-box.warning {
            background: #fee2e2;
            color: #b91c1c;
            border-color: #fca5a5;
            animation: pulse 1s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        .result-box {
            text-align: center;
            padding: 32px 16px;
        }
        .result-score {
            font-size: 48px;
            font-weight: 800;
            margin: 16px 0;
        }
        .passed { color: var(--success); }
        .failed { color: var(--danger); }
        .students-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
            margin-top: 16px;
        }
        .student-chip {
            background: #f1f5f9;
            padding: 12px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid var(--border);
            cursor: pointer;
            font-weight: 600;
            transition: all 0.2s;
        }
        .student-chip:hover { border-color: var(--primary); background: #eff6ff; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>{{ system_name }}</h1>
                <span class="badge">Duration: {{ duration }} Mins | Pass: {{ pass_pct }}%</span>
            </div>
            {% if user %}
            <div style="display:flex; align-items:center;">
                <span class="user-pill">👤 {{ user.name }} ({{ user.role }})</span>
                <a href="/logout" class="btn btn-logout">Logout</a>
            </div>
            {% endif %}
        </header>

        {% if page == "login" %}
        <div style="max-width: 480px; margin: 0 auto;">
            <h2 style="margin-bottom: 16px;">Student / Proctor Login</h2>
            <p style="color: var(--muted); margin-bottom: 20px;">Click a student profile to fast-login:</p>
            
            <div class="students-grid">
                <a href="/fast-login?user=siva" class="student-chip" style="text-decoration:none; color:inherit;">🎓 Siva Sathvik</a>
                <a href="/fast-login?user=saketh" class="student-chip" style="text-decoration:none; color:inherit;">🎓 Saketh</a>
                <a href="/fast-login?user=shveni" class="student-chip" style="text-decoration:none; color:inherit;">🎓 Shveni</a>
                <a href="/fast-login?user=sahithi" class="student-chip" style="text-decoration:none; color:inherit;">🎓 Sahithi</a>
            </div>

            <div style="text-align: center; margin: 24px 0; color: var(--muted);">— OR LOGIN MANUALLY —</div>

            <form method="POST" action="/login">
                <div class="form-group">
                    <label>Username</label>
                    <select name="username">
                        <option value="siva">siva (Siva Sathvik)</option>
                        <option value="saketh">saketh (Saketh)</option>
                        <option value="shveni">shveni (Shveni)</option>
                        <option value="sahithi">sahithi (Sahithi)</option>
                        <option value="proctor1">proctor1 (Prof. Smith)</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" name="password" value="password" required>
                </div>
                <button type="submit" class="btn" style="width: 100%;">Sign In to Exam</button>
            </form>
        </div>

        {% elif page == "exam" %}
        <div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; position: sticky; top: 0; background: var(--card); z-index: 10; padding: 12px 0; border-bottom: 1px solid var(--border);">
                <div>
                    <h2>Online Multiple-Choice Assessment</h2>
                    <small style="color: var(--muted);">Select the best answer for each question</small>
                </div>
                <div id="timerBox" class="timer-box">
                    <span>⏱️ Time Remaining:</span>
                    <span id="timerDisplay" style="font-family: monospace; font-size: 18px;">{{ duration }}:00</span>
                </div>
            </div>

            <form id="examForm" method="POST" action="/submit">
                {% for q in questions %}
                <div class="question-card">
                    <div class="question-title">Question {{ q.id }}: {{ q.question }}</div>
                    {% for opt in q.options %}
                    <label class="option-label">
                        <input type="radio" name="q_{{ q.id }}" value="{{ opt }}" required>
                        <span>{{ opt }}</span>
                    </label>
                    {% endfor %}
                </div>
                {% endfor %}
                <button type="submit" class="btn" style="width: 100%; font-size: 16px;">Submit Exam Assessment</button>
            </form>

            <script>
                // Live Running Countdown Timer
                let totalSeconds = {{ duration }} * 60;
                const timerDisplay = document.getElementById("timerDisplay");
                const timerBox = document.getElementById("timerBox");
                const examForm = document.getElementById("examForm");

                function updateCountdown() {
                    if (totalSeconds <= 0) {
                        clearInterval(timerInterval);
                        timerDisplay.innerText = "00:00";
                        alert("Time is up! Your examination will be submitted automatically.");
                        examForm.submit();
                        return;
                    }

                    totalSeconds--;

                    let minutes = Math.floor(totalSeconds / 60);
                    let seconds = totalSeconds % 60;

                    let formattedMin = String(minutes).padStart(2, '0');
                    let formattedSec = String(seconds).padStart(2, '0');

                    timerDisplay.innerText = ${formattedMin}:;

                    // Warning state when less than 5 minutes remaining
                    if (totalSeconds <= 300) {
                        timerBox.classList.add("warning");
                    }
                }

                const timerInterval = setInterval(updateCountdown, 1000);
            </script>
        </div>

        {% elif page == "result" %}
        <div class="result-box">
            <h2>Assessment Evaluation Result</h2>
            <p style="color: var(--muted);">Candidate: <strong>{{ user.name }}</strong></p>
            
            <div class="result-score {{ 'passed' if passed else 'failed' }}">
                {{ score }}%
            </div>
            
            <h3 class="{{ 'passed' if passed else 'failed' }}">
                {% if passed %}
                    ✅ PASSED (Requirement: {{ pass_pct }}%)
                {% else %}
                    ❌ FAILED (Requirement: {{ pass_pct }}%)
                {% endif %}
            </h3>

            <p style="margin: 20px 0; color: var(--muted);">
                Answer evaluation performed via scoring engine (<code>scoring.py</code>).
            </p>

            <a href="/exam" class="btn">Retake Exam</a>
            <a href="/logout" class="btn btn-logout">Sign Out</a>
        </div>
        {% endif %}
    </div>
</body>
</html>
'''

@app.route("/")
def index():
    if "user" not in session:
        return render_template_string(
            HTML_TEMPLATE,
            system_name=SYSTEM_NAME,
            duration=DEFAULT_EXAM_DURATION_MINS,
            pass_pct=PASSING_PERCENTAGE,
            page="login",
            user=None
        )
    return redirect(url_for("exam"))

@app.route("/fast-login")
def fast_login():
    user_key = request.args.get("user", "siva")
    user = users_db.get(user_key)
    if user:
        session["user"] = {"username": user_key, "name": user["name"], "role": user["role"]}
    return redirect(url_for("exam"))

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    user = users_db.get(username)
    if user:
        session["user"] = {"username": username, "name": user["name"], "role": user["role"]}
        return redirect(url_for("exam"))
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/exam")
def exam():
    if "user" not in session:
        return redirect(url_for("index"))
    questions = get_all_questions()
    return render_template_string(
        HTML_TEMPLATE,
        system_name=SYSTEM_NAME,
        duration=DEFAULT_EXAM_DURATION_MINS,
        pass_pct=PASSING_PERCENTAGE,
        page="exam",
        user=session["user"],
        questions=questions
    )

@app.route("/submit", methods=["POST"])
def submit():
    if "user" not in session:
        return redirect(url_for("index"))
    
    questions = get_all_questions()
    submissions = {}
    for q in questions:
        key = f"q_{q['id']}"
        submissions[q["id"]] = request.form.get(key)
    
    score, passed = calculate_score(submissions, questions)
    return render_template_string(
        HTML_TEMPLATE,
        system_name=SYSTEM_NAME,
        duration=DEFAULT_EXAM_DURATION_MINS,
        pass_pct=PASSING_PERCENTAGE,
        page="result",
        user=session["user"],
        score=round(score, 1),
        passed=passed
    )

if __name__ == "__main__":
    print(f"Starting {SYSTEM_NAME} on http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
