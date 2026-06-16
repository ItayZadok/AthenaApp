import os
import subprocess
import uuid

from flask import Flask, request

app = Flask(__name__)
submissions = {}


@app.route("/compile", methods=["POST"])
def compile_code():
    data = request.json
    code = data["code"]

    uid = str(uuid.uuid4())
    folder = f"/tmp/{uid}"
    os.makedirs(folder, exist_ok=True)

    file_path = os.path.join(folder, "RobotProgram.java")

    with open(file_path, "w") as f:
        f.write(code)

    result = subprocess.run(
        ["javac", file_path],
        capture_output=True,
        text=True
    )

    errors = []

    if result.returncode != 0:
        for line in result.stderr.splitlines():
            parts = line.split(":")
            if len(parts) >= 4:
                try:
                    line_num = int(parts[1])
                    msg = ":".join(parts[3:]).strip()

                    errors.append({
                        "message": msg,
                        "startLineNumber": line_num,
                        "endLineNumber": line_num,
                        "startColumn": 1,
                        "endColumn": 100,
                        "severity": 8
                    })
                except:
                    pass

    return {"errors": errors}


@app.route("/submit", methods=["POST"])
def submit():
    data = request.json
    code = data["code"]
    team = data["team"]

    uid = str(uuid.uuid4())
    folder = f"/tmp/{uid}"
    os.makedirs(folder, exist_ok=True)

    file_path = os.path.join(folder, "RobotProgram.java")

    with open(file_path, "w") as f:
        f.write(code)

    result = subprocess.run(
        ["javac", file_path],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return {
            "status": "error",
            "message": "Compilation failed",
            "errors": result.stderr
        }, 400

    submissions[team] = code
    return {"status": "ok"}


@app.route("/team/<team>")
def team_page(team):
    return f"""
<!DOCTYPE html>
<html>
<head>
<title>Team {team}</title>

<style>
body {{
    margin: 0;
    font-family: Arial;
}}

#topbar {{
    padding: 10px;
    background: #1e1e1e;
    color: white;
    display: flex;
    align-items: center;
    justify-content: left;
    gap: 1em;
}}

#editor {{
    height: 92vh;
}}

button {{
    font-weight: bolder;
    color: white;
    background-color: #424242;
    padding: 10px 14px;
    border: 16px white;
    border-radius: 8px;
}}

button:hover {{
    cursor: pointer;
    background-color: #3b3939; 
    color: #e3e3e3;
}}

button:disabled {{
    opacity: 0.6;
    cursor: not-allowed;
}}

#toast {{
    padding: 10px 14px;
    background: #222;
    color: white;
    border-radius: 8px;
    display: none;
    font-size: 13px;
    transition: all 0.25s ease;
}}

#statusBar {{
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 6px 12px;
    background: #111;
    color: #aaa;
    font-family: monospace;
    font-size: 12px;
    border-top: 1px solid #222;
}}
</style>

<script src="/static/vs/loader.js"></script>
</head>

<body>

<div id="topbar">
    <div><b>Team {team}</b></div>
    <button id="submitBtn" onclick="submitCode()">Submit</button>
    <div id="toast"></div>
</div>

<div id="editor"></div>

<div id="statusBar">Loading...</div>

<script>
require.config({{
    paths: {{
        vs: "/static/vs"
    }}
}});

let editor;
let compileTimeout;

require(["vs/editor/editor.main"], function () {{

    editor = monaco.editor.create(document.getElementById("editor"), {{
        value:
`public class RobotProgram {{

    public static void main(String[] args) {{
        // EXAMPLE:
        driveForwardInSeconds(2);
        turnLeftInSeconds(1);
    }}

    public static void driveForwardInSeconds(double seconds) {{}}
    public static void driveBackwardInSeconds(double seconds) {{}}
    public static void turnLeftInSeconds(double seconds) {{}}
    public static void turnRightInSeconds(double seconds) {{}}
}}`,
        language: "java",
        theme: "vs-dark",
        automaticLayout: true,
        minimap: {{ enabled: false }},
        overviewRulerLanes: 0,
        hideCursorInOverviewRuler: true
    }});

    setStatus("Ready");

    editor.onDidChangeModelContent(() => {{
        scheduleCompile();
    }});

}});

function showToast(msg, color = "#222") {{
    const toast = document.getElementById("toast");
    toast.innerText = msg;
    toast.style.background = color;
    toast.style.display = "block";

    clearTimeout(window.toastTimer);
    window.toastTimer = setTimeout(() => {{
        toast.style.display = "none";
    }}, 2500);
}}

function setStatus(msg) {{
    document.getElementById("statusBar").innerText = msg;
}}

function setSubmitting(state) {{
    const btn = document.getElementById("submitBtn");
    btn.disabled = state;
    btn.innerText = state ? "Submitting..." : "Submit";
}}

function scheduleCompile() {{
    clearTimeout(compileTimeout);
    compileTimeout = setTimeout(() => {{
        compile(editor.getValue());
    }}, 100);
}}

function compile(code) {{
    fetch("/compile", {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify({{ code }})
    }})
    .then(res => res.json())
    .then(data => {{

        monaco.editor.setModelMarkers(
            editor.getModel(),
            "javac",
            data.errors
        );

        setStatus(
            data.errors.length > 0
                ? data.errors.length + " error(s)"
                : "No errors"
        );
    }});
}}

function submitCode() {{
    if (document.getElementById("submitBtn").disabled) return;

    const code = editor.getValue();

    setSubmitting(true);
    setStatus("Compiling...");
    showToast("Checking code...", "#1f6feb");

    fetch("/compile", {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify({{ code }})
    }})
    .then(res => res.json())
    .then(data => {{

        monaco.editor.setModelMarkers(
            editor.getModel(),
            "javac",
            data.errors
        );

        if (data.errors.length > 0) {{
            setStatus(data.errors.length + " error(s)");
            showToast("Fix errors before submitting", "#b91c1c");
            setSubmitting(false);
            return;
        }}

        setStatus("Submitting...");
        showToast("Submitting...", "#1f6feb");

        return fetch("/submit", {{
            method: "POST",
            headers: {{ "Content-Type": "application/json" }},
            body: JSON.stringify({{
                team: "{team}",
                code: code
            }})
        }});
    }})
    .then(res => {{
        if (!res) return;

        if (!res.ok) throw new Error();

        setStatus("Submitted");
        showToast("Submitted ✔", "#16a34a");
    }})
    .catch(() => {{
        setStatus("Error submitting");
        showToast("Submission failed", "#b91c1c");
    }})
    .finally(() => {{
        setSubmitting(false);
    }});
}}
</script>

</body>
</html>
"""


@app.route("/admin")
def admin():
    teams = list(submissions.keys())
    first_team = teams[0] if teams else None

    html = f"""
<html>
<head>
<title>Admin Dashboard</title>
<style>
body {{
    margin: 0;
    font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial;

    /* soft gray base */
    background: #3b4e76;
    color: #111827;
}}

/* HEADER */
header {{
    padding: 14px 18px;

    background: #e5e7eb;
    border-bottom: 1px solid #d1d5db;

    display: flex;
    align-items: center;
    justify-content: space-between;

    box-shadow: 0 1px 0 rgba(0,0,0,0.04);
}}

header h3 {{
    margin: 0;
    font-weight: 600;
    font-size: 15px;
    color: #111827;
}}

/* TEAM BAR */
.team-bar {{
    display: flex;
    gap: 8px;
    padding: 10px 12px;
    flex-wrap: wrap;

    background: #6183a5;
}}

/* TEAM BUTTONS */
.team-btn {{
    padding: 6px 10px;
    border-radius: 8px;

    border: 1px solid #6183a5;

    cursor: pointer;

    background: #e5e7eb;
    color: #3b4e76;

    transition: all 0.15s ease;
    font-size: 13px;
}}

# .team-btn:hover {{
#     background: #dbeafe;
#     border-color: #a7c7ff;
#     color: #1d4ed8;
# }}

.team-btn.active {{
    background: #cfe3ff;
    border-color: #7aa7ff;
    color: #1d4ed8;
    font-weight: 600;
}}

/* CONTAINER */
.container {{
    padding: 18px;
}}

/* CARD */
.card {{
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 12px;

    padding: 14px;
    margin-bottom: 14px;

    box-shadow: 0 4px 12px rgba(0,0,0,0.04);
}}

.card h3 {{
    margin: 0 0 10px 0;
    font-size: 14px;
    font-weight: 600;
    color: #111827;
}}

/* CODE BLOCK */
pre {{
    background: #e5e7eb;
    color: #111827;

    padding: 12px;
    border-radius: 10px;

    overflow-x: auto;
    white-space: pre-wrap;

    border: 1px solid #d1d5db;

    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 12.5px;
    line-height: 1.5;
}}

/* BUTTONS */
button {{
    padding: 7px 10px;
    border-radius: 8px;

    cursor: pointer;

    border: 1px solid #d1d5db;

    background: #e5e7eb;
    color: #111827;

    font-size: 13px;

    transition: all 0.15s ease;
}}

button:hover {{
    background: #dbeafe;
    border-color: #a7c7ff;
    color: #1d4ed8;
}}

button:active {{
    transform: scale(0.98);
}}

/* TOP ACTIONS */
.top-actions {{
    display: flex;
    gap: 10px;
    align-items: center;
}}

/* SCROLLBAR */
::-webkit-scrollbar {{
    height: 8px;
    width: 8px;
}}

::-webkit-scrollbar-thumb {{
    background: rgba(0,0,0,0.2);
    border-radius: 8px;
}}

::-webkit-scrollbar-track {{
    background: transparent;
}}
</style>
</head>

<body>

<header>
    <h3>Admin Dashboard</h3>
    <div class="top-actions">
        <button onclick="location.reload()">Refresh</button>
    </div>
</header>

<div class="team-bar">
"""

    for team in teams:
        html += f"""
        <button class="team-btn" id="btn_{team}" onclick="showTeam('{team}')">
            {team}
        </button>
        """

    html += """
</div>

<div class="container">
"""

    for team, code in submissions.items():
        safe = code.replace("</", "<\\/")

        html += f"""
        <div class="card team-view" id="view_{team}" style="display:none;">
            <h3>Team {team}</h3>

            <button onclick="copy_{team}()">Copy Code</button>

            <pre id="code_{team}">{safe}</pre>
        </div>

        <script>
        function copy_{team}() {{
            navigator.clipboard.writeText(
                document.getElementById("code_{team}").innerText
            );
        }}
        </script>
        """

    html += f"""
</div>

<script>
let current = null;

function showTeam(team) {{
    document.querySelectorAll('.team-view').forEach(v => {{
        v.style.display = 'none';
    }});

    document.querySelectorAll('.team-btn').forEach(b => {{
        b.classList.remove('active');
    }});

    document.getElementById('view_' + team).style.display = 'block';
    document.getElementById('btn_' + team).classList.add('active');

    current = team;
}}

window.onload = function() {{
    const first = {first_team!r};
    if (first) {{
        showTeam(first);
    }}
}}
</script>

</body>
</html>
"""

    return html


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
