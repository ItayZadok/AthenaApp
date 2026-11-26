from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# Team submissions (stored in memory)
submissions = {}

MAX_CODE_LENGTH = 100_000


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

        html[dir="rtl"] .children {
            margin-left: 0;
            margin-right: 30px;
            padding-left: 0;
            padding-right: 12px;
            border-left: none;
            border-right: 3px solid #9333ea;
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

        .repeat {
            background: #9333ea;
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
           NESTED BLOCKS
        ------------------------- */

        .children {
            margin-left: 30px;
            padding-left: 12px;
            border-left: 3px solid #9333ea;
            min-height: 15px;
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

            <div class="palette-block repeat"
                 draggable="true"
                 data-type="repeat"
                 onclick="addBlock('repeat')">
                <span data-i18n="repeat">Repeat</span>
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
                repeat: "Repeat",
                startBlock: "When program starts",
                submitCode: "Submit Code",
                forward: "Forward",
                backward: "Backward",
                left: "Left",
                right: "Right",
                for: "for",
                seconds: "seconds",
                times: "times",
                removeBlock: "Remove block",
                submitting: "Submitting...",
                submitted: "Code submitted successfully!",
                submissionFailed: "Submission failed"
            },
            he: {
                editorTitle: "פרויקט אתנה - " + TEAM,
                availableBlocks: "בלוקים זמינים",
                drive: "נסיעה",
                turn: "סיבוב",
                repeat: "חזור",
                startBlock: "כאשר התוכנית מתחילה",
                submitCode: "שלח קוד",
                forward: "קדימה",
                backward: "אחורה",
                left: "שמאלה",
                right: "ימינה",
                for: "במשך",
                seconds: "שניות",
                times: "פעמים",
                removeBlock: "הסר בלוק",
                submitting: "שולח...",
                submitted: "הקוד נשלח בהצלחה!",
                submissionFailed: "שליחת הקוד נכשלה"
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
                count: 3,
                direction: type === "drive"
                    ? "FORWARD"
                    : "LEFT",
                children: []
            };

            return block;
        }


        // -------------------------
        // ADD BLOCK
        // -------------------------

        function addBlock(type) {
            blocks.push(createBlock(type));
            renderBlocks();
        }


        // -------------------------
        // TREE HELPERS
        // -------------------------

        function findList(ownerId, list = blocks) {
            if (ownerId === null) {
                return list;
            }

            for (const block of list) {
                if (block.id === ownerId) {
                    return block.children;
                }

                const result = findList(ownerId, block.children);

                if (result !== null) {
                    return result;
                }
            }

            return null;
        }


        function findBlock(id, list = blocks) {
            for (const block of list) {
                if (block.id === id) {
                    return block;
                }

                const result = findBlock(id, block.children);

                if (result) {
                    return result;
                }
            }

            return null;
        }


        function containsBlock(block, id) {
            if (block.id === id) {
                return true;
            }

            return block.children.some(child =>
                containsBlock(child, id)
            );
        }


        function removeBlockFromList(id, list = blocks) {
            const index = list.findIndex(block => block.id === id);

            if (index !== -1) {
                return list.splice(index, 1)[0];
            }

            for (const block of list) {
                const result = removeBlockFromList(id, block.children);

                if (result) {
                    return result;
                }
            }

            return null;
        }


        function getNextBlockId(ownerId, blockId) {
            const list = findList(ownerId);

            if (!list) {
                return null;
            }

            const index = list.findIndex(block => block.id === blockId);

            if (index === -1 || index + 1 >= list.length) {
                return null;
            }

            return list[index + 1].id;
        }


        // -------------------------
        // DRAG AND DROP
        // -------------------------

        function clearDropHighlights() {
            document.querySelectorAll(".drag-over").forEach(zone => {
                zone.classList.remove("drag-over");
            });
        }


        function handleDrop(ownerId, beforeId) {
            if (!dragged) {
                return;
            }

            const targetList = findList(ownerId);

            if (!targetList) {
                return;
            }

            // Create a new block from the palette.
            if (dragged.type === "new") {
                const newBlock = createBlock(dragged.blockType);

                const index = beforeId === null
                    ? targetList.length
                    : targetList.findIndex(block => block.id === beforeId);

                targetList.splice(
                    index === -1 ? targetList.length : index,
                    0,
                    newBlock
                );

                renderBlocks();
                return;
            }

            // Move an existing block.
            if (dragged.type === "existing") {
                const movingBlock = findBlock(dragged.id);

                if (!movingBlock) {
                    return;
                }

                // Do not move a block into itself or one of its children.
                if (ownerId !== null && containsBlock(movingBlock, ownerId)) {
                    return;
                }

                // Do not drop a block directly before itself.
                if (beforeId === dragged.id) {
                    return;
                }

                const removed = removeBlockFromList(dragged.id);

                if (!removed) {
                    return;
                }

                const index = beforeId === null
                    ? targetList.length
                    : targetList.findIndex(block => block.id === beforeId);

                targetList.splice(
                    index === -1 ? targetList.length : index,
                    0,
                    removed
                );

                renderBlocks();
            }
        }


        function createDropZone(ownerId, beforeId) {
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
                handleDrop(ownerId, beforeId);
            });

            return zone;
        }


        // -------------------------
        // CREATE PROGRAM BLOCK
        // -------------------------

        function createBlockElement(block, lineCounter, ownerId) {
            const wrapper = document.createElement("div");
            wrapper.className = "program-item";

            const element = document.createElement("div");

            element.className = "program-block " + block.type;
            element.draggable = true;

            // Line number
            const lineNumber = document.createElement("span");
            lineNumber.className = "line-number";
            lineNumber.textContent = lineCounter.value++;

            element.appendChild(lineNumber);

            // -------------------------
            // DRIVE BLOCK
            // -------------------------

            if (block.type === "drive") {
                element.appendChild(
                    document.createTextNode(t("drive"))
                );

                const direction = document.createElement("select");

                direction.innerHTML = `
                    <option value="FORWARD">${t("forward")}</option>
                    <option value="BACKWARD">${t("backward")}</option>
                `;

                direction.value = block.direction;

                direction.addEventListener("change", () => {
                    block.direction = direction.value;
                });

                element.appendChild(direction);

                element.appendChild(
                    document.createTextNode(t("for"))
                );

                const seconds = document.createElement("input");

                seconds.type = "number";
                seconds.min = "0";
                seconds.step = "0.1";
                seconds.value = block.seconds;

                seconds.addEventListener("input", () => {
                    block.seconds = Math.max(0, Number(seconds.value) || 0);
                });

                element.appendChild(seconds);

                element.appendChild(
                    document.createTextNode(t("seconds"))
                );
            }


            // -------------------------
            // TURN BLOCK
            // -------------------------

            else if (block.type === "turn") {
                element.appendChild(
                    document.createTextNode(t("turn"))
                );

                const direction = document.createElement("select");

                direction.innerHTML = `
                    <option value="LEFT">${t("left")}</option>
                    <option value="RIGHT">${t("right")}</option>
                `;

                direction.value = block.direction;

                direction.addEventListener("change", () => {
                    block.direction = direction.value;
                });

                element.appendChild(direction);

                element.appendChild(
                    document.createTextNode(t("for"))
                );

                const seconds = document.createElement("input");

                seconds.type = "number";
                seconds.min = "0";
                seconds.step = "0.1";
                seconds.value = block.seconds;

                seconds.addEventListener("input", () => {
                    block.seconds = Math.max(0, Number(seconds.value) || 0);
                });

                element.appendChild(seconds);

                element.appendChild(
                    document.createTextNode(t("seconds"))
                );
            }


            // -------------------------
            // REPEAT BLOCK
            // -------------------------

            else if (block.type === "repeat") {
                element.appendChild(
                    document.createTextNode(t("repeat"))
                );

                const count = document.createElement("input");

                count.type = "number";
                count.min = "0";
                count.step = "1";
                count.value = block.count;

                count.addEventListener("input", () => {
                    block.count = Math.max(
                        0,
                        Math.floor(Number(count.value) || 0)
                    );
                });

                element.appendChild(count);

                element.appendChild(
                    document.createTextNode(t("times"))
                );
            }


            // -------------------------
            // REMOVE BUTTON
            // -------------------------

            const removeButton = document.createElement("button");

            removeButton.textContent = "✕";
            removeButton.title = t("removeBlock");

            removeButton.addEventListener("click", event => {
                event.stopPropagation();

                removeBlockFromList(block.id);
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
                    : getNextBlockId(ownerId, block.id);

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
                    : getNextBlockId(ownerId, block.id);

                clearDropHighlights();

                if (
                    dragged.type === "existing" &&
                    beforeId === dragged.id
                ) {
                    return;
                }

                handleDrop(ownerId, beforeId);
            });


            wrapper.appendChild(element);


            // -------------------------
            // NESTED CHILDREN
            // -------------------------

            if (block.type === "repeat") {
                const childList = document.createElement("div");
                childList.className = "children";

                renderList(
                    block.children,
                    childList,
                    block.id,
                    lineCounter
                );

                wrapper.appendChild(childList);
            }

            return wrapper;
        }


        // -------------------------
        // RENDER LIST
        // -------------------------

        function renderList(list, container, ownerId, lineCounter) {
            container.innerHTML = "";

            list.forEach(block => {
                // Drop zone before this block.
                container.appendChild(
                    createDropZone(ownerId, block.id)
                );

                // Block itself.
                container.appendChild(
                    createBlockElement(block, lineCounter, ownerId)
                );
            });

            // Drop zone at the end of this list.
            container.appendChild(
                createDropZone(ownerId, null)
            );
        }


        // -------------------------
        // RENDER PROGRAM
        // -------------------------

        function renderBlocks() {
            const program = document.getElementById("program");

            const lineCounter = {
                value: 1
            };

            renderList(
                blocks,
                program,
                null,
                lineCounter
            );
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

            function emit(list, indent) {
                const pad = "    ".repeat(indent);

                for (const block of list) {

                    if (block.type === "drive") {
                        const method = block.direction === "FORWARD"
                            ? "driveForwardInSeconds"
                            : "driveBackwardInSeconds";

                        lines.push(
                            pad + method + "(" + block.seconds + ");"
                        );
                    }

                    else if (block.type === "turn") {
                        const method = block.direction === "LEFT"
                            ? "turnLeftInSeconds"
                            : "turnRightInSeconds";

                        lines.push(
                            pad + method + "(" + block.seconds + ");"
                        );
                    }

                    else if (block.type === "repeat") {
                        lines.push(
                            pad + "for (int i = 0; i < " +
                            block.count + "; i++) {"
                        );

                        emit(block.children, indent + 1);

                        lines.push(pad + "}");
                    }
                }
            }

            emit(blocks, 0);

            return lines.join("\\n");
        }


        // -------------------------
        // SUBMIT CODE
        // -------------------------

        async function submitCode() {
            const status = document.getElementById("status");
            const code = generateJava();

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