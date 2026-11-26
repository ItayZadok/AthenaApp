import re

from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# Team submissions (stored in memory)
submissions = {}

MAX_CODE_LENGTH = 100_000

# Program limits (must match the editor's limits below)
MAX_BLOCKS = 20
MIN_SECONDS = 0
MAX_SECONDS = 10

COMMAND_PATTERN = re.compile(
    r"^(driveForwardInSeconds|driveBackwardsInSeconds|"
    r"turnLeftInSeconds|turnRightInSeconds)\((\d+(?:\.\d+)?)\);$"
)


def validate_program(code):
    """Return an error message if the program breaks the limits, else None."""
    lines = [line.strip() for line in code.splitlines() if line.strip()]

    if len(lines) > MAX_BLOCKS:
        return f"Too many blocks (maximum is {MAX_BLOCKS})"

    for line in lines:
        match = COMMAND_PATTERN.match(line)

        if not match:
            return "Invalid code"

        seconds = float(match.group(2))

        if not MIN_SECONDS <= seconds <= MAX_SECONDS:
            return f"Seconds must be between {MIN_SECONDS} and {MAX_SECONDS}"

    return None


# -------------------------
# SUBMIT CODE
# -------------------------

@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json(silent=True) or {}

    team = data.get("team")
    code = data.get("code")

    if not isinstance(team, str) or not isinstance(code, str):
        return jsonify({"error": "Invalid data"}), 400

    if not team.strip():
        return jsonify({"error": "Team name is required"}), 400

    if len(code) > MAX_CODE_LENGTH:
        return jsonify({"error": "Code is too long"}), 400

    error = validate_program(code)

    if error:
        return jsonify({"error": error}), 400

    submissions[team] = code

    return jsonify({"status": "ok"})


# -------------------------
# HOME PAGE
# -------------------------

@app.route("/")
def home():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Project Athena</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f3f4f6;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
            }

            .container {
                background: white;
                padding: 30px;
                border-radius: 12px;
                width: 300px;
                text-align: center;
                box-shadow: 0 3px 12px #0002;
            }

            input, button {
                width: 100%;
                box-sizing: border-box;
                padding: 12px;
                margin-top: 12px;
                font-size: 16px;
            }

            button {
                background: #2563eb;
                color: white;
                border: none;
                border-radius: 6px;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <button id="language-toggle" type="button" onclick="toggleLanguage()">עברית</button>
            <h2 data-i18n="projectTitle">Project Athena</h2>
            <form id="teamForm">
                <input id="team" data-i18n-placeholder="teamPlaceholder" placeholder="Enter team name" required>
                <button type="submit" data-i18n="openEditor">Open Editor</button>
            </form>
        </div>

        <script>
            const translations = {
                en: {
                    projectTitle: "Project Athena",
                    teamPlaceholder: "Enter team name",
                    openEditor: "Open Editor"
                },
                he: {
                    projectTitle: "פרויקט אתנה",
                    teamPlaceholder: "הכנס שם קבוצה",
                    openEditor: "פתח עורך"
                }
            };

            let currentLanguage = localStorage.getItem("athena-language") || "en";

            function applyLanguage() {
                const isHebrew = currentLanguage === "he";
                document.documentElement.lang = currentLanguage;
                document.documentElement.dir = isHebrew ? "rtl" : "ltr";

                document.querySelectorAll("[data-i18n]").forEach(element => {
                    const key = element.dataset.i18n;
                    element.textContent = translations[currentLanguage][key];
                });

                document.querySelectorAll("[data-i18n-placeholder]").forEach(element => {
                    const key = element.dataset.i18nPlaceholder;
                    element.placeholder = translations[currentLanguage][key];
                });

                document.getElementById("language-toggle").textContent =
                    isHebrew ? "English" : "עברית";
            }

            function toggleLanguage() {
                currentLanguage = currentLanguage === "en" ? "he" : "en";
                localStorage.setItem("athena-language", currentLanguage);
                applyLanguage();
            }

            applyLanguage();

            document.getElementById("teamForm").addEventListener("submit", e => {
                e.preventDefault();

                const team = document.getElementById("team").value.trim();

                if (team) {
                    window.location.href = "/team/" + encodeURIComponent(team);
                }
            });
        </script>
    </body>
    </html>
    """)


# -------------------------
# TEAM EDITOR
# -------------------------

@app.route("/team/<team>")
def team_page(team):
    return render_template_string(EDITOR_HTML, team=team)


EDITOR_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Project Athena - {{ team }}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            padding: 20px;
            font-family: Arial, sans-serif;
            background: #f3f4f6;
        }

        h1 {
            margin-top: 0;
        }

        .page-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 15px;
            margin-bottom: 15px;
        }

        #language-toggle {
            padding: 9px 16px;
            background: #374151;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            flex-shrink: 0;
        }

        #editor {
            display: flex;
            align-items: flex-start;
            gap: 20px;
        }

        /* -------------------------
           AVAILABLE BLOCKS
        ------------------------- */

        #available {
            width: 220px;
            flex-shrink: 0;

            position: sticky;
            top: 20px;
            align-self: flex-start;

            max-height: calc(100vh - 40px);
            overflow-y: auto;

            background: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 8px #0001;
            z-index: 10;
        }

        #available h3 {
            margin-top: 0;
        }

        .palette-block {
            padding: 12px;
            margin: 10px 0;
            border-radius: 6px;
            color: white;
            cursor: grab;
            user-select: none;
            font-weight: bold;
        }

        .palette-block:active {
            cursor: grabbing;
        }

        .drive {
            background: #2563eb;
        }

        .turn {
            background: #16a34a;
        }

        /* -------------------------
           PROGRAM AREA
        ------------------------- */

        #workspace {
            flex: 1;
            min-width: 0;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 8px #0001;
        }

        #start-block {
            background: #374151;
            color: white;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 10px;
            font-weight: bold;
        }

        #program {
            min-height: 100px;
        }

        .program-item {
            margin: 4px 0;
        }

        .program-block {
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px;

            padding: 10px;
            border-radius: 6px;
            color: white;

            cursor: grab;
            user-select: none;
        }

        .program-block:active {
            cursor: grabbing;
        }

        .program-block.dragging {
            opacity: 0.5;
        }

        .line-number {
            min-width: 25px;
            color: #ffffffcc;
            font-size: 12px;
            font-weight: normal;
        }

        .drag-handle {
            font-size: 18px;
            cursor: grab;
        }

        .program-block input,
        .program-block select {
            padding: 5px;
            border: none;
            border-radius: 4px;
            font-size: 14px;
            max-width: 110px;
        }

        .program-block button {
            margin-left: auto;
            border: none;
            background: #0003;
            color: white;
            border-radius: 4px;
            padding: 5px 9px;
            cursor: pointer;
        }

        .program-block button:hover {
            background: #0005;
        }

        /* -------------------------
           DROP ZONES
        ------------------------- */

        .drop-zone {
            height: 8px;
            margin: 2px 0;
            border-radius: 5px;
            transition: background 0.1s;
        }

        .drop-zone.drag-over {
            height: 12px;
            background: #facc15;
        }

        /* -------------------------
           SUBMIT
        ------------------------- */

        #submit-button {
            margin-top: 20px;
            padding: 12px 20px;
            background: #2563eb;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
        }

        #submit-button:hover {
            background: #1d4ed8;
        }

        #status {
            margin-top: 10px;
        }

        @media (max-width: 700px) {
            body {
                padding: 10px;
            }

            #editor {
                flex-direction: column;
            }

            #available {
                position: sticky;
                top: 0;
                width: 100%;
                max-height: 220px;
            }

            #workspace {
                width: 100%;
            }
        }
    </style>
</head>

<body>

    <div class="page-header">
        <h1 data-i18n="editorTitle">Project Athena - {{ team }}</h1>
        <button id="language-toggle" type="button" onclick="toggleLanguage()">עברית</button>
    </div>

    <div id="editor">

        <!-- AVAILABLE BLOCKS -->

        <div id="available">
            <h3 data-i18n="availableBlocks">Available Blocks</h3>

            <div class="palette-block drive"
                 draggable="true"
                 data-type="drive"
                 onclick="addBlock('drive')">
                <span data-i18n="drive">Drive</span>
            </div>

            <div class="palette-block turn"
                 draggable="true"
                 data-type="turn"
                 onclick="addBlock('turn')">
                <span data-i18n="turn">Turn</span>
            </div>

        </div>

        <!-- PROGRAM WORKSPACE -->

        <div id="workspace">

            <div id="start-block" data-i18n="startBlock">
                When program starts
            </div>

            <div id="program"></div>

            <button id="submit-button" onclick="submitCode()" data-i18n="submitCode">
                Submit Code
            </button>

            <div id="status"></div>

        </div>

    </div>

    <script>
        const TEAM = {{ team | tojson }};

        const translations = {
            en: {
                editorTitle: "Project Athena - " + TEAM,
                availableBlocks: "Available Blocks",
                drive: "Drive",
                turn: "Turn",
                startBlock: "When program starts",
                submitCode: "Submit Code",
                forward: "Forward",
                backward: "Backward",
                left: "Left",
                right: "Right",
                for: "for",
                seconds: "seconds",
                removeBlock: "Remove block",
                submitting: "Submitting...",
                submitted: "Code submitted successfully!",
                submissionFailed: "Submission failed",
                maxBlocksReached: "Maximum of 20 blocks reached"
            },
            he: {
                editorTitle: "פרויקט אתנה - " + TEAM,
                availableBlocks: "בלוקים זמינים",
                drive: "נסיעה",
                turn: "סיבוב",
                startBlock: "כאשר התוכנית מתחילה",
                submitCode: "שלח קוד",
                forward: "קדימה",
                backward: "אחורה",
                left: "שמאלה",
                right: "ימינה",
                for: "במשך",
                seconds: "שניות",
                removeBlock: "הסר בלוק",
                submitting: "שולח...",
                submitted: "הקוד נשלח בהצלחה!",
                submissionFailed: "שליחת הקוד נכשלה",
                maxBlocksReached: "הגעת למקסימום של 20 בלוקים"
            }
        };

        let currentLanguage = localStorage.getItem("athena-language") || "en";

        function t(key) {
            return translations[currentLanguage][key] || key;
        }

        function applyLanguage() {
            const isHebrew = currentLanguage === "he";
            document.documentElement.lang = currentLanguage;
            document.documentElement.dir = isHebrew ? "rtl" : "ltr";

            document.querySelectorAll("[data-i18n]").forEach(element => {
                const key = element.dataset.i18n;
                element.textContent = t(key);
            });

            document.getElementById("language-toggle").textContent =
                isHebrew ? "English" : "עברית";

            document.title = t("editorTitle");
            renderBlocks();
        }

        function toggleLanguage() {
            currentLanguage = currentLanguage === "en" ? "he" : "en";
            localStorage.setItem("athena-language", currentLanguage);
            applyLanguage();
        }

        const MAX_BLOCKS = 20;
        const MIN_SECONDS = 0;
        const MAX_SECONDS = 10;

        let blocks = [];
        let nextId = 0;
        let dragged = null;


        // -------------------------
        // BLOCK CREATION
        // -------------------------

        function createBlock(type) {
            const block = {
                id: nextId++,
                type: type,
                seconds: 2,
                direction: type === "drive"
                    ? "FORWARD"
                    : "LEFT"
            };

            return block;
        }


        // -------------------------
        // ADD BLOCK
        // -------------------------

        function addBlock(type) {
            if (blocks.length >= MAX_BLOCKS) {
                showLimitMessage();
                return;
            }

            blocks.push(createBlock(type));
            renderBlocks();
        }


        // -------------------------
        // LIMITS
        // -------------------------

        function showLimitMessage() {
            const status = document.getElementById("status");

            status.dataset.kind = "limit";
            status.textContent = t("maxBlocksReached");
            status.style.color = "red";
        }


        function updateLimitMessage() {
            const status = document.getElementById("status");

            if (status.dataset.kind !== "limit") {
                return;
            }

            if (blocks.length >= MAX_BLOCKS) {
                status.textContent = t("maxBlocksReached");
            } else {
                status.dataset.kind = "";
                status.textContent = "";
            }
        }


        function clampSeconds(value) {
            const number = Number(value);

            if (!Number.isFinite(number)) {
                return MIN_SECONDS;
            }

            const rounded = Math.round(number * 100) / 100;

            return Math.min(MAX_SECONDS, Math.max(MIN_SECONDS, rounded));
        }


        // -------------------------
        // LIST HELPERS
        // -------------------------

        function removeBlock(id) {
            const index = blocks.findIndex(block => block.id === id);

            if (index === -1) {
                return null;
            }

            return blocks.splice(index, 1)[0];
        }


        function getNextBlockId(blockId) {
            const index = blocks.findIndex(block => block.id === blockId);

            if (index === -1 || index + 1 >= blocks.length) {
                return null;
            }

            return blocks[index + 1].id;
        }


        // -------------------------
        // DRAG AND DROP
        // -------------------------

        function clearDropHighlights() {
            document.querySelectorAll(".drag-over").forEach(zone => {
                zone.classList.remove("drag-over");
            });
        }


        function handleDrop(beforeId) {
            if (!dragged) {
                return;
            }

            // Create a new block from the palette.
            if (dragged.type === "new") {
                if (blocks.length >= MAX_BLOCKS) {
                    showLimitMessage();
                    return;
                }

                const newBlock = createBlock(dragged.blockType);

                const index = beforeId === null
                    ? blocks.length
                    : blocks.findIndex(block => block.id === beforeId);

                blocks.splice(
                    index === -1 ? blocks.length : index,
                    0,
                    newBlock
                );

                renderBlocks();
                return;
            }

            // Move an existing block.
            if (dragged.type === "existing") {
                // Do not drop a block directly before itself.
                if (beforeId === dragged.id) {
                    return;
                }

                const removed = removeBlock(dragged.id);

                if (!removed) {
                    return;
                }

                const index = beforeId === null
                    ? blocks.length
                    : blocks.findIndex(block => block.id === beforeId);

                blocks.splice(
                    index === -1 ? blocks.length : index,
                    0,
                    removed
                );

                renderBlocks();
            }
        }


        function createDropZone(beforeId) {
            const zone = document.createElement("div");

            zone.className = "drop-zone";

            zone.addEventListener("dragover", event => {
                if (!dragged) {
                    return;
                }

                event.preventDefault();
                event.stopPropagation();

                // Do not allow a block to be dropped directly before itself.
                if (
                    dragged.type === "existing" &&
                    beforeId === dragged.id
                ) {
                    zone.classList.remove("drag-over");
                    return;
                }

                clearDropHighlights();
                zone.classList.add("drag-over");

                event.dataTransfer.dropEffect =
                    dragged.type === "new" ? "copy" : "move";
            });

            zone.addEventListener("dragleave", () => {
                zone.classList.remove("drag-over");
            });

            zone.addEventListener("drop", event => {
                event.preventDefault();
                event.stopPropagation();

                if (
                    dragged &&
                    dragged.type === "existing" &&
                    beforeId === dragged.id
                ) {
                    clearDropHighlights();
                    return;
                }

                clearDropHighlights();
                handleDrop(beforeId);
            });

            return zone;
        }


        // -------------------------
        // CREATE PROGRAM BLOCK
        // -------------------------

        function createSecondsInput(block) {
            const seconds = document.createElement("input");

            seconds.type = "number";
            seconds.min = String(MIN_SECONDS);
            seconds.max = String(MAX_SECONDS);
            seconds.step = "0.1";
            seconds.value = block.seconds;

            seconds.addEventListener("input", () => {
                block.seconds = clampSeconds(seconds.value);
            });

            // Snap the field back into range once the user is done typing.
            seconds.addEventListener("change", () => {
                block.seconds = clampSeconds(seconds.value);
                seconds.value = block.seconds;
            });

            return seconds;
        }


        function createDirectionSelect(block, options) {
            const direction = document.createElement("select");

            direction.innerHTML = options
                .map(option =>
                    `<option value="${option.value}">${t(option.label)}</option>`
                )
                .join("");

            direction.value = block.direction;

            direction.addEventListener("change", () => {
                block.direction = direction.value;
            });

            return direction;
        }


        function createBlockElement(block, number) {
            const wrapper = document.createElement("div");
            wrapper.className = "program-item";

            const element = document.createElement("div");

            element.className = "program-block " + block.type;
            element.draggable = true;

            // Line number
            const lineNumber = document.createElement("span");
            lineNumber.className = "line-number";
            lineNumber.textContent = number;

            element.appendChild(lineNumber);

            // Block label, direction, and duration
            element.appendChild(
                document.createTextNode(t(block.type))
            );

            element.appendChild(
                createDirectionSelect(
                    block,
                    block.type === "drive"
                        ? [
                            { value: "FORWARD", label: "forward" },
                            { value: "BACKWARD", label: "backward" }
                        ]
                        : [
                            { value: "LEFT", label: "left" },
                            { value: "RIGHT", label: "right" }
                        ]
                )
            );

            element.appendChild(
                document.createTextNode(t("for"))
            );

            element.appendChild(createSecondsInput(block));

            element.appendChild(
                document.createTextNode(t("seconds"))
            );

            // -------------------------
            // REMOVE BUTTON
            // -------------------------

            const removeButton = document.createElement("button");

            removeButton.textContent = "✕";
            removeButton.title = t("removeBlock");

            removeButton.addEventListener("click", event => {
                event.stopPropagation();

                removeBlock(block.id);
                renderBlocks();
            });

            element.appendChild(removeButton);


            // -------------------------
            // DRAG START / END
            // -------------------------

            element.addEventListener("dragstart", event => {
                dragged = {
                    type: "existing",
                    id: block.id
                };

                event.dataTransfer.effectAllowed = "move";
                event.dataTransfer.setData("text/plain", String(block.id));

                element.classList.add("dragging");
            });

            element.addEventListener("dragend", () => {
                dragged = null;
                element.classList.remove("dragging");
                clearDropHighlights();
            });


            // -------------------------
            // SNAP TO NEAREST POSITION
            // -------------------------

            element.addEventListener("dragover", event => {
                if (!dragged) {
                    return;
                }

                event.preventDefault();
                event.stopPropagation();

                const rect = element.getBoundingClientRect();

                const isUpperHalf =
                    event.clientY < rect.top + rect.height / 2;

                const beforeId = isUpperHalf
                    ? block.id
                    : getNextBlockId(block.id);

                // Never highlight the position directly before itself.
                if (
                    dragged.type === "existing" &&
                    beforeId === dragged.id
                ) {
                    clearDropHighlights();
                    return;
                }

                const targetZone = isUpperHalf
                    ? wrapper.previousElementSibling
                    : wrapper.nextElementSibling;

                clearDropHighlights();

                if (
                    targetZone &&
                    targetZone.classList.contains("drop-zone")
                ) {
                    targetZone.classList.add("drag-over");
                }

                event.dataTransfer.dropEffect =
                    dragged.type === "new" ? "copy" : "move";
            });


            element.addEventListener("drop", event => {
                if (!dragged) {
                    return;
                }

                event.preventDefault();
                event.stopPropagation();

                const rect = element.getBoundingClientRect();

                const isUpperHalf =
                    event.clientY < rect.top + rect.height / 2;

                const beforeId = isUpperHalf
                    ? block.id
                    : getNextBlockId(block.id);

                clearDropHighlights();

                if (
                    dragged.type === "existing" &&
                    beforeId === dragged.id
                ) {
                    return;
                }

                handleDrop(beforeId);
            });


            wrapper.appendChild(element);

            return wrapper;
        }


        // -------------------------
        // RENDER PROGRAM
        // -------------------------

        function renderBlocks() {
            const program = document.getElementById("program");

            program.innerHTML = "";

            blocks.forEach((block, index) => {
                // Drop zone before this block.
                program.appendChild(createDropZone(block.id));

                // Block itself.
                program.appendChild(createBlockElement(block, index + 1));
            });

            // Drop zone at the end of the list.
            program.appendChild(createDropZone(null));

            updateLimitMessage();
        }


        // -------------------------
        // PALETTE DRAGGING
        // -------------------------

        document.querySelectorAll(".palette-block").forEach(paletteBlock => {
            paletteBlock.addEventListener("dragstart", event => {
                dragged = {
                    type: "new",
                    blockType: paletteBlock.dataset.type
                };

                event.dataTransfer.effectAllowed = "copy";
                event.dataTransfer.setData(
                    "text/plain",
                    paletteBlock.dataset.type
                );
            });

            paletteBlock.addEventListener("dragend", () => {
                dragged = null;
                clearDropHighlights();
            });
        });


        // -------------------------
        // GENERATE JAVA
        // -------------------------

        function generateJava() {
            const lines = [];

            for (const block of blocks) {
                let method;

                if (block.type === "drive") {
                    method = block.direction === "FORWARD"
                        ? "driveForwardInSeconds"
                        : "driveBackwardsInSeconds";
                }

                else if (block.type === "turn") {
                    method = block.direction === "LEFT"
                        ? "turnLeftInSeconds"
                        : "turnRightInSeconds";
                }

                else {
                    continue;
                }

                lines.push(method + "(" + block.seconds + ");");
            }

            return lines.join("\\n");
        }


        // -------------------------
        // SUBMIT CODE
        // -------------------------

        async function submitCode() {
            const status = document.getElementById("status");
            const code = generateJava();

            status.dataset.kind = "";
            status.textContent = t("submitting");

            try {
                const response = await fetch("/submit", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        team: TEAM,
                        code: code
                    })
                });

                const result = await response.json();

                if (!response.ok) {
                    throw new Error(result.error || t("submissionFailed"));
                }

                status.textContent = t("submitted");
                status.style.color = "green";

            } catch (error) {
                status.textContent = "Error: " + error.message;
                status.style.color = "red";
            }
        }


        // Apply saved language and render the editor.
        applyLanguage();

    </script>

</body>
</html>
"""


# -------------------------
# ADMIN PAGE
# -------------------------

@app.route("/admin")
def admin():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">

        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f3f4f6;
                padding: 20px;
            }

            .submission {
                background: white;
                padding: 20px;
                margin-bottom: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 8px #0001;
            }

            pre {
                background: #1f2937;
                color: white;
                padding: 15px;
                border-radius: 6px;
                overflow-x: auto;
                white-space: pre-wrap;
            }

            button {
                padding: 9px 15px;
                background: #2563eb;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }

            button:hover {
                background: #1d4ed8;
            }
        </style>
    </head>

    <body>

        <div style="display:flex;align-items:center;justify-content:space-between;gap:15px">
            <h1 data-i18n="submissionsTitle">Team Submissions</h1>
            <button id="language-toggle" type="button" onclick="toggleLanguage()">עברית</button>
        </div>

        {% if submissions %}
            {% for team, code in submissions.items() %}
                <div class="submission">

                    <h2>Team {{ team }}</h2>

                    <pre>{{ code }}</pre>

                    <button onclick="copyCode(this)">
                        <span data-i18n="copyCode">Copy Code</span>
                    </button>

                </div>
            {% endfor %}
        {% else %}
            <p data-i18n="noSubmissions">No submissions yet.</p>
        {% endif %}

        <script>
            const adminTranslations = {
                en: {
                    submissionsTitle: "Team Submissions",
                    copyCode: "Copy Code",
                    copied: "Copied!",
                    noSubmissions: "No submissions yet."
                },
                he: {
                    submissionsTitle: "הגשות הקבוצות",
                    copyCode: "העתק קוד",
                    copied: "הועתק!",
                    noSubmissions: "אין הגשות עדיין."
                }
            };

            let currentLanguage = localStorage.getItem("athena-language") || "en";

            function applyLanguage() {
                const isHebrew = currentLanguage === "he";
                document.documentElement.lang = currentLanguage;
                document.documentElement.dir = isHebrew ? "rtl" : "ltr";

                document.querySelectorAll("[data-i18n]").forEach(element => {
                    element.textContent = adminTranslations[currentLanguage][element.dataset.i18n];
                });

                document.getElementById("language-toggle").textContent =
                    isHebrew ? "English" : "עברית";
            }

            function toggleLanguage() {
                currentLanguage = currentLanguage === "en" ? "he" : "en";
                localStorage.setItem("athena-language", currentLanguage);
                applyLanguage();
            }

            applyLanguage();

            async function copyCode(button) {
                const code = button.previousElementSibling.textContent;

                try {
                    await navigator.clipboard.writeText(code);
                    button.querySelector("span").textContent = adminTranslations[currentLanguage].copied;
                } catch (error) {
                    const textarea = document.createElement("textarea");
                    textarea.value = code;

                    document.body.appendChild(textarea);
                    textarea.select();

                    document.execCommand("copy");
                    textarea.remove();

                    button.querySelector("span").textContent = adminTranslations[currentLanguage].copied;
                }

                setTimeout(() => {
                    button.querySelector("span").textContent = adminTranslations[currentLanguage].copyCode;
                }, 1500);
            }
        </script>

    </body>
    </html>
    """, submissions=submissions)


# -------------------------
# RUN SERVER
# -------------------------

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )