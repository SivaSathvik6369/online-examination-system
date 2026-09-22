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
            padding: 20px;
        }
        .container {
            max-width: 850px;
            margin: 0 auto;
            background: var(--card);
            border-radius: 16px;
            padding: 32px;
            box-shadow: 0 4px 25px rgba(0, 0, 0, 0.08);
            border: 1px solid var(--border);
        }
        header {
            border-bottom: 2px solid var(--border);
            padding-bottom: 16px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
        }
        h1 { font-size: 24px; color: var(--primary); }
        
        /* Prominent Live Ticking Timer Box */
        .live-timer-badge {
            background: #fef2f2;
            border: 2px solid #ef4444;
            color: #991b1b;
            padding: 8px 16px;
            border-radius: 999px;
            font-weight: 700;
            font-size: 15px;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 2px 8px rgba(239, 68, 68, 0.2);
        }
        .blinking-dot {
            width: 10px;
            height: 10px;
            background-color: #ef4444;
            border-radius: 50%;
            display: inline-block;
            animation: blink 1s infinite;
        }
        @keyframes blink {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.3; transform: scale(0.8); }
        }
        .timer-display {
            font-family: "Courier New", Courier, monospace;
            font-size: 20px;
            font-weight: 800;
            color: #b91c1c;
            letter-spacing: 1px;
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
        
        .exam-banner {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
            position: sticky;
            top: 0;
            background: var(--card);
            z-index: 10;
            padding: 14px 0;
            border-bottom: 2px solid #e2e8f0;
        }
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

        .result-box {
            text-align: center;
            padding: 32px 16px;
        }
        .result-score {
            font-size: 52px;
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
            padding: 14px;
            border-radius: 10px;
            text-align: center;
            border: 1px solid var(--border);
            cursor: pointer;
            font-weight: 600;
            transition: all 0.2s;
            text-decoration: none;
            color: inherit;
        }
        .student-chip:hover { border-color: var(--primary); background: #eff6ff; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>{{ system_name }}</h1>
                <small style="color: var(--muted);">Pass Mark: {{ pass_pct }}% | Standard Duration: {{ duration }} mins</small>
            </div>
            
            <div style="display:flex; align-items:center; gap: 12px;">
                <div class="live-timer-badge">
                    <span class="blinking-dot"></span>
                    <span>TIMER:</span>
                    <span class="timer-display">59:59</span>
                </div>

                {% if user %}
                <div style="display:flex; align-items:center;">
                    <span class="user-pill">👤 {{ user.name }}</span>
                    <a href="/logout" class="btn btn-logout">Logout</a>
                </div>
                {% endif %}
            </div>
        </header>

        {% if page == "login" %}
        <div style="max-width: 500px; margin: 0 auto;">
            <h2 style="margin-bottom: 12px;">Student / Proctor Portal</h2>
            <p style="color: var(--muted); margin-bottom: 16px;">Select your student identity to begin:</p>
            
            <div class="students-grid">
                <a href="/fast-login?user=siva" class="student-chip">🎓 Siva Sathvik</a>
                <a href="/fast-login?user=saketh" class="student-chip">🎓 Saketh</a>
                <a href="/fast-login?user=shveni" class="student-chip">🎓 Shveni</a>
                <a href="/fast-login?user=sahithi" class="student-chip">🎓 Sahithi</a>
            </div>

            <div style="text-align: center; margin: 24px 0; color: var(--muted);">— OR CREDENTIAL LOGIN —</div>

            <form method="POST" action="/login">
                <div class="form-group">
                    <label>Select User</label>
                    <select name="username">
                        <option value="siva">siva (Siva Sathvik)</option>
                        <option value="saketh">saketh (Saketh)</option>
                        <option value="shveni">shveni (Shveni)</option>
                        <option value="sahithi">sahithi (Sahithi)</option>
                        <option value="proctor1">proctor1 (Prof. Smith - Proctor)</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" name="password" value="password" required>
                </div>
                <button type="submit" class="btn" style="width: 100%;">Sign In & Start Exam</button>
            </form>
        </div>

        {% elif page == "exam" %}
        <div>
            <div class="exam-banner">
                <div>
                    <h2>Online Examination Assessment</h2>
                    <small style="color: var(--muted);">All questions are mandatory</small>
                </div>
                <div class="live-timer-badge" style="background:#fee2e2; padding: 10px 20px;">
                    <span class="blinking-dot"></span>
                    <span>EXAM TIME REMAINING:</span>
                    <span class="timer-display" style="font-size: 24px;">59:59</span>
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
                <button type="submit" class="btn" style="width: 100%; font-size: 16px; padding: 14px;">Submit Examination</button>
            </form>
        </div>

        {% elif page == "result" %}
        <div class="result-box">
            <h2>Assessment Evaluation Result</h2>
            <p style="color: var(--muted); margin-top: 4px;">Candidate: <strong>{{ user.name }}</strong></p>
            
            <div class="result-score {{ 'passed' if passed else 'failed' }}">
                {{ score }}%
            </div>
            
            <h3 class="{{ 'passed' if passed else 'failed' }}" style="font-size: 22px;">
                {% if passed %}
                    ✅ PASSED (Qualifying: {{ pass_pct }}%)
                {% else %}
                    ❌ FAILED (Qualifying: {{ pass_pct }}%)
                {% endif %}
            </h3>

            <p style="margin: 20px 0; color: var(--muted);">
                Grading evaluated accurately using the <code>scoring.py</code> engine.
            </p>

            <a href="/reset-timer" class="btn">Retake Exam (Reset Timer)</a>
            <a href="/logout" class="btn btn-logout">Sign Out</a>
        </div>
        {% endif %}
    </div>

    <!-- Active Real-Time Ticking Countdown Engine -->
    <script>
        (function() {
            const initialMinutes = {{ duration }};
            let totalSeconds = sessionStorage.getItem("exam_time_remaining");
            
            if (!totalSeconds || isNaN(totalSeconds) || parseInt(totalSeconds, 10) <= 0) {
                totalSeconds = initialMinutes * 60;
                sessionStorage.setItem("exam_time_remaining", totalSeconds);
            } else {
                totalSeconds = parseInt(totalSeconds, 10);
            }

            function tick() {
                if (totalSeconds <= 0) {
                    totalSeconds = 0;
                    sessionStorage.removeItem("exam_time_remaining");
                    document.querySelectorAll(".timer-display").forEach(el => el.innerText = "00:00");
                    const form = document.getElementById("examForm");
                    if (form) {
                        alert("Time has expired! Automatically submitting your assessment.");
                        form.submit();
                    }
                    return;
                }

                totalSeconds--;
                sessionStorage.setItem("exam_time_remaining", totalSeconds);

                const mins = Math.floor(totalSeconds / 60);
                const secs = totalSeconds % 60;
                const formatted = String(mins).padStart(2, '0') + ":" + String(secs).padStart(2, '0');

                document.querySelectorAll(".timer-display").forEach(el => {
                    el.innerText = formatted;
                });
            }

            // Immediately execute tick so it visibly decrements right upon page load
            tick();
            setInterval(tick, 1000);
        })();
    </script>
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

@app.route("/reset-timer")
def reset_timer():
    return '''
    <script>
        sessionStorage.removeItem("exam_time_remaining");
        window.location.href = "/exam";
    </script>
    '''

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
