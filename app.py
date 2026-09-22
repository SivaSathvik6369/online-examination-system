import sys
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
from config import SYSTEM_NAME, DEFAULT_EXAM_DURATION_MINS, PASSING_PERCENTAGE
from questions import get_all_questions
from scoring import calculate_score
from auth import users_db, authenticate, register_student

app = Flask(__name__)
app.secret_key = "exam_secret_session_key_vitap"

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ system_name }}</title>
    <style>
        :root {
            --primary: #1e40af;
            --primary-hover: #1d4ed8;
            --bg: #f8fafc;
            --card: #ffffff;
            --text: #0f172a;
            --muted: #64748b;
            --success: #16a34a;
            --danger: #dc2626;
            --border: #cbd5e1;
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
        }
        h1 { font-size: 24px; color: var(--primary); }
        .user-pill {
            background: #f1f5f9;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 600;
        }
        .form-group { margin-bottom: 16px; }
        label { display: block; font-weight: 600; margin-bottom: 6px; font-size: 14px; }
        input[type="text"], input[type="email"], input[type="password"] {
            width: 100%;
            padding: 11px 14px;
            border: 1px solid var(--border);
            border-radius: 8px;
            font-size: 15px;
        }
        input:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(30, 64, 175, 0.15);
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
            text-align: center;
        }
        .btn:hover { background: var(--primary-hover); }
        .btn-logout { background: #ef4444; margin-left: 10px; font-size: 13px; padding: 6px 14px; }
        .btn-logout:hover { background: #dc2626; }

        /* Auth Tabs */
        .tab-nav {
            display: flex;
            gap: 12px;
            border-bottom: 2px solid #e2e8f0;
            margin-bottom: 20px;
        }
        .tab-btn {
            padding: 10px 20px;
            font-weight: 700;
            cursor: pointer;
            background: none;
            border: none;
            font-size: 15px;
            color: var(--muted);
            border-bottom: 3px solid transparent;
            margin-bottom: -2px;
        }
        .tab-btn.active {
            color: var(--primary);
            border-bottom-color: var(--primary);
        }
        
        .alert {
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
            font-weight: 500;
        }
        .alert-error {
            background: #fee2e2;
            color: #991b1b;
            border: 1px solid #fca5a5;
        }
        .alert-success {
            background: #dcfce7;
            color: #166534;
            border: 1px solid #86efac;
        }

        /* Single Sticky Exam Timer */
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
        .live-timer-badge {
            background: #fef2f2;
            border: 2px solid #ef4444;
            color: #991b1b;
            padding: 10px 20px;
            border-radius: 999px;
            font-weight: 700;
            font-size: 15px;
            display: inline-flex;
            align-items: center;
            gap: 10px;
            box-shadow: 0 2px 10px rgba(239, 68, 68, 0.15);
        }
        .blinking-dot {
            width: 12px;
            height: 12px;
            background-color: #ef4444;
            border-radius: 50%;
            display: inline-block;
            animation: blink 1s infinite;
        }
        @keyframes blink {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.3; transform: scale(0.85); }
        }
        .timer-display {
            font-family: "Courier New", Courier, monospace;
            font-size: 24px;
            font-weight: 800;
            color: #b91c1c;
            letter-spacing: 1px;
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
            gap: 10px;
            margin-top: 14px;
            margin-bottom: 24px;
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
            text-decoration: none;
            color: inherit;
            display: flex;
            flex-direction: column;
            gap: 2px;
        }
        .student-chip small { color: var(--muted); font-size: 11px; font-weight: normal; }
        .student-chip:hover { border-color: var(--primary); background: #eff6ff; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>{{ system_name }}</h1>
            </div>
            
            {% if user %}
            <div style="display:flex; align-items:center;">
                <span class="user-pill">👤 {{ user.name }} ({{ user.email or user.username }})</span>
                <a href="/logout" class="btn btn-logout">Logout</a>
            </div>
            {% endif %}
        </header>

        {% if error %}
        <div class="alert alert-error">⚠️ {{ error }}</div>
        {% endif %}
        {% if message %}
        <div class="alert alert-success">✅ {{ message }}</div>
        {% endif %}

        {% if page == "auth" %}
        <div style="max-width: 520px; margin: 0 auto;">
            <div class="tab-nav">
                <button type="button" class="tab-btn {{ 'active' if tab == 'login' else '' }}" onclick="switchTab('login')">Sign In</button>
                <button type="button" class="tab-btn {{ 'active' if tab == 'register' else '' }}" onclick="switchTab('register')">Register New Student</button>
            </div>

            <!-- LOGIN TAB -->
            <div id="loginTab" style="display: {{ 'block' if tab == 'login' else 'none' }};">
                <div style="margin-bottom: 16px;">
                    <p style="color: var(--muted); font-size: 14px;">One-click student login:</p>
                    <div class="students-grid">
                        <a href="/fast-login?user=siva" class="student-chip">
                            <strong>Siva Sathvik</strong>
                            <small>siva.sathvik@vitapstudent.ac.in</small>
                        </a>
                        <a href="/fast-login?user=saketh" class="student-chip">
                            <strong>Saketh</strong>
                            <small>saketh.k@vitapstudent.ac.in</small>
                        </a>
                        <a href="/fast-login?user=shveni" class="student-chip">
                            <strong>Shveni</strong>
                            <small>shveni.r@vitapstudent.ac.in</small>
                        </a>
                        <a href="/fast-login?user=sahithi" class="student-chip">
                            <strong>Sahithi</strong>
                            <small>sahithi.m@vitapstudent.ac.in</small>
                        </a>
                    </div>
                </div>

                <div style="text-align: center; margin: 16px 0; color: var(--muted); font-size: 13px;">— OR ENTER CREDENTIALS —</div>

                <form method="POST" action="/login">
                    <div class="form-group">
                        <label>Email or Username</label>
                        <input type="text" name="login_id" placeholder="Enter email or username" required>
                    </div>
                    <div class="form-group">
                        <label>Password</label>
                        <input type="password" name="password" placeholder="Enter password" required>
                    </div>
                    <button type="submit" class="btn" style="width: 100%;">Sign In</button>
                </form>
            </div>

            <!-- REGISTER TAB -->
            <div id="registerTab" style="display: {{ 'block' if tab == 'register' else 'none' }};">
                <p style="color: var(--muted); margin-bottom: 16px; font-size: 14px;">
                    Create a new student examination account:
                </p>

                <form method="POST" action="/register">
                    <div class="form-group">
                        <label>Full Name</label>
                        <input type="text" name="name" placeholder="e.g. Rahul Sharma" required>
                    </div>
                    <div class="form-group">
                        <label>Email Address</label>
                        <input type="email" name="email" placeholder="Enter your email address" required>
                    </div>
                    <div class="form-group">
                        <label>Username</label>
                        <input type="text" name="username" placeholder="Choose a username" required>
                    </div>
                    <div class="form-group">
                        <label>Password</label>
                        <input type="password" name="password" placeholder="Create password" required>
                    </div>
                    <button type="submit" class="btn" style="width: 100%; background: #059669;">Register Account</button>
                </form>
            </div>
        </div>

        <script>
            function switchTab(tab) {
                if (tab === 'login') {
                    document.getElementById('loginTab').style.display = 'block';
                    document.getElementById('registerTab').style.display = 'none';
                    document.querySelectorAll('.tab-btn')[0].classList.add('active');
                    document.querySelectorAll('.tab-btn')[1].classList.remove('active');
                } else {
                    document.getElementById('loginTab').style.display = 'none';
                    document.getElementById('registerTab').style.display = 'block';
                    document.querySelectorAll('.tab-btn')[0].classList.remove('active');
                    document.querySelectorAll('.tab-btn')[1].classList.add('active');
                }
            }
        </script>

        {% elif page == "exam" %}
        <div>
            <!-- ONLY ONE EXAM TIMER HERE: STARTS ONLY AFTER LOGIN -->
            <div class="exam-banner">
                <div>
                    <h2>Online Examination</h2>
                    <small style="color: var(--muted);">Candidate: <strong>{{ user.name }}</strong></small>
                </div>
                <div class="live-timer-badge">
                    <span class="blinking-dot"></span>
                    <span>TIME LEFT:</span>
                    <span id="examTimerDisplay" class="timer-display">{{ duration }}:00</span>
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

            <script>
                (function() {
                    let totalSeconds = {{ duration }} * 60;
                    const timerDisplay = document.getElementById("examTimerDisplay");
                    const form = document.getElementById("examForm");

                    function updateClock() {
                        if (totalSeconds <= 0) {
                            clearInterval(timerInterval);
                            timerDisplay.innerText = "00:00";
                            alert("Time has expired! Submitting your answers automatically.");
                            form.submit();
                            return;
                        }

                        totalSeconds--;

                        const mins = Math.floor(totalSeconds / 60);
                        const secs = totalSeconds % 60;
                        const formatted = String(mins).padStart(2, '0') + ":" + String(secs).padStart(2, '0');
                        timerDisplay.innerText = formatted;
                    }

                    updateClock();
                    const timerInterval = setInterval(updateClock, 1000);
                })();
            </script>
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
                Answer key evaluated by <code>scoring.py</code> engine.
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
            page="auth",
            tab="login",
            error=request.args.get("error"),
            message=request.args.get("message"),
            user=None
        )
    return redirect(url_for("exam"))

@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name", "")
    email = request.form.get("email", "")
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    success, msg = register_student(name, email, username, password)
    if not success:
        return render_template_string(
            HTML_TEMPLATE,
            system_name=SYSTEM_NAME,
            duration=DEFAULT_EXAM_DURATION_MINS,
            pass_pct=PASSING_PERCENTAGE,
            page="auth",
            tab="register",
            error=msg,
            message=None,
            user=None
        )
    return redirect(url_for("index", message=msg))

@app.route("/login", methods=["POST"])
def login():
    login_id = request.form.get("login_id", "")
    password = request.form.get("password", "")
    auth_result = authenticate(login_id, password)

    if auth_result["authenticated"]:
        session["user"] = auth_result
        return redirect(url_for("exam"))
    else:
        return render_template_string(
            HTML_TEMPLATE,
            system_name=SYSTEM_NAME,
            duration=DEFAULT_EXAM_DURATION_MINS,
            pass_pct=PASSING_PERCENTAGE,
            page="auth",
            tab="login",
            error="Invalid credentials. Please verify your email/username and password.",
            message=None,
            user=None
        )

@app.route("/fast-login")
def fast_login():
    user_key = request.args.get("user", "siva")
    user = users_db.get(user_key)
    if user:
        session["user"] = {
            "username": user_key,
            "name": user["name"],
            "email": user.get("email"),
            "role": user["role"]
        }
    return redirect(url_for("exam"))

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
