(function () {
  const root = document.querySelector("[data-assistant-root]");
  if (!root) return;

  const sessionList = root.querySelector("[data-session-list]");
  const sessionTitle = root.querySelector("[data-session-title]");
  const sessionMeta = root.querySelector("[data-session-meta]");
  const messageList = root.querySelector("[data-message-list]");
  const form = root.querySelector("[data-message-form]");
  const textarea = form.querySelector("textarea");
  const status = root.querySelector("[data-chat-status]");
  const newSessionButton = root.querySelector("[data-new-session]");

  let activeSessionId = null;

  const renderStatus = (message, isError = false) => {
    status.textContent = message;
    status.classList.toggle("text-danger", isError);
  };

  const escapeHtml = (value) =>
    value
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;");

  const createMessageMarkup = (message) => {
    const speakButton = message.role === "assistant"
      ? `<button class="btn btn-sm btn-link p-0 text-decoration-none ms-2 speak-msg-btn" type="button" title="Read aloud" data-speak-content="${escapeHtml(message.content)}">🔊</button>`
      : "";
    return `
      <article class="assistant-message assistant-message-${message.role}">
        <div class="d-flex justify-content-between align-items-center mb-1">
          <div class="assistant-role">${message.role === "assistant" ? "AI Assistant" : "You"}</div>
          ${speakButton}
        </div>
        <div class="assistant-content">${escapeHtml(message.content).replaceAll("\n", "<br>")}</div>
      </article>
    `;
  };

  // Text-To-Speech for assistant chat bubbles
  let currentUtterance = null;
  const speakText = (text, button) => {
    window.speechSynthesis.cancel();

    // Reset all buttons visual state
    messageList.querySelectorAll(".speak-msg-btn").forEach(btn => {
      btn.textContent = "🔊";
      btn.classList.remove("speaking-pulse");
    });

    currentUtterance = new SpeechSynthesisUtterance(text);

    currentUtterance.onstart = () => {
      button.textContent = "⏹";
      button.classList.add("speaking-pulse");
    };

    const stopSpeaking = () => {
      button.textContent = "🔊";
      button.classList.remove("speaking-pulse");
    };

    currentUtterance.onend = stopSpeaking;
    currentUtterance.onerror = stopSpeaking;

    // Toggle stop behavior if clicked again
    button.addEventListener("click", function handler() {
      window.speechSynthesis.cancel();
      button.removeEventListener("click", handler);
    }, { once: true });

    window.speechSynthesis.speak(currentUtterance);
  };

  // Delegate click events on messageList for speak buttons
  messageList.addEventListener("click", (event) => {
    const btn = event.target.closest(".speak-msg-btn");
    if (btn) {
      const text = btn.dataset.speakContent;
      if (text) {
        speakText(text, btn);
      }
    }
  });

  const applyAssistantDifficultyLevel = (level) => {
    const standardLabels = root.querySelectorAll(".standard-label");
    const kidLabels = root.querySelectorAll(".kid-label");
    const expertLabels = root.querySelectorAll(".expert-label");

    const standardBtnTexts = root.querySelectorAll(".standard-btn-text");
    const kidBtnTexts = root.querySelectorAll(".kid-btn-text");
    const expertBtnTexts = root.querySelectorAll(".expert-btn-text");

    const textarea = form.querySelector("textarea");

    // Hide all first
    standardLabels.forEach(el => el.style.display = "none");
    kidLabels.forEach(el => el.style.display = "none");
    expertLabels.forEach(el => el.style.display = "none");

    standardBtnTexts.forEach(el => el.style.display = "none");
    kidBtnTexts.forEach(el => el.style.display = "none");
    expertBtnTexts.forEach(el => el.style.display = "none");

    if (level === "kid") {
      kidLabels.forEach(el => el.style.display = "inline");
      kidBtnTexts.forEach(el => el.style.display = "inline");
      if (textarea) textarea.placeholder = "Hello! Ask me something fun, like: 'Why is the sky blue?' 🌟🎈";
    } else if (level === "expert") {
      expertLabels.forEach(el => el.style.display = "inline");
      expertBtnTexts.forEach(el => el.style.display = "inline");
      if (textarea) textarea.placeholder = "Enter technical query, e.g. 'Explain SGD optimization convergence rate O(1/T)'…";
    } else {
      // Intermediate / default
      standardLabels.forEach(el => el.style.display = "inline");
      standardBtnTexts.forEach(el => el.style.display = "inline");
      if (textarea) textarea.placeholder = "Type your question here…";
    }
  };

  // Listen for level changes
  window.addEventListener("difficultyLevelChanged", (e) => {
    applyAssistantDifficultyLevel(e.detail.level);
  });

  // Initial Level application
  const initialLevel = localStorage.getItem("difficultyLevel") || "intermediate";
  applyAssistantDifficultyLevel(initialLevel);

  const renderMessages = (messages) => {
    if (!messages.length) {
      const level = localStorage.getItem("difficultyLevel") || "intermediate";
      let placeholderText = "Start a conversation about analytics, machine learning results, or product decisions.";
      if (level === "kid") {
        placeholderText = "Hello there, little explorer! 🦖 Ask me any question, and let's learn together!";
      } else if (level === "expert") {
        placeholderText = "System initialized. Enter query parameters for advanced analytical modeling details.";
      }
      messageList.innerHTML = `
        <div class="assistant-empty">
          ${placeholderText}
        </div>
      `;
      return;
    }
    messageList.innerHTML = messages.map(createMessageMarkup).join("");
    messageList.scrollTop = messageList.scrollHeight;
  };

  const renderSessions = (sessions) => {
    if (!sessions.length) {
      sessionList.innerHTML = `<div class="assistant-empty small">No conversations yet.</div>`;
      return;
    }
    sessionList.innerHTML = sessions
      .map(
        (session) => `
          <button class="assistant-session-item ${session.id === activeSessionId ? "active" : ""}" data-session-id="${session.id}">
            <span class="assistant-session-title">${escapeHtml(session.title)}</span>
            <span class="assistant-session-model">${escapeHtml(session.model_name)}</span>
          </button>
        `
      )
      .join("");

    sessionList.querySelectorAll("[data-session-id]").forEach((button) => {
      button.addEventListener("click", () => {
        window.speechSynthesis.cancel();
        loadSession(Number(button.dataset.sessionId));
      });
    });
  };

  const fetchJson = async (url, options = {}) => {
    const response = await fetch(url, {
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      credentials: "same-origin",
      ...options,
    });
    const payload = await response.json();
    if (!response.ok || payload.success === false) {
      const errorMessage = payload?.error?.message || "Request failed.";
      throw new Error(errorMessage);
    }
    return payload.data;
  };

  const loadSessionList = async () => {
    const data = await fetchJson("/api/v1/chat/sessions");
    renderSessions(data.sessions);
    if (!activeSessionId && data.sessions.length) {
      await loadSession(data.sessions[0].id);
    }
  };

  const loadSession = async (sessionId) => {
    const data = await fetchJson(`/api/v1/chat/sessions/${sessionId}`);
    const session = data.session;
    activeSessionId = session.id;
    sessionTitle.textContent = session.title;
    sessionMeta.textContent = `${session.provider} | ${session.model_name}`;
    renderMessages(session.messages || []);
    await loadSessionList();
  };

  const createSession = async () => {
    renderStatus("Creating conversation...");
    const level = localStorage.getItem("difficultyLevel") || "intermediate";
    let title = "New Conversation";
    let systemPrompt = null;

    if (level === "kid") {
      title = "🧒 Fun Learning Chat";
      systemPrompt = "You are a super friendly, fun, and warm AI tutor and companion. Explain everything like you are talking to a 5-year-old child! Use very simple words, fun analogies, short sentences, and lots of happy emojis (like 🎈, 🐶, 🦖, 🌟). Keep answers short, positive, and easy to understand. Never use complex terms without explaining them simply first!";
    } else if (level === "expert") {
      title = "🧠 Advanced Expert Session";
      systemPrompt = "You are an advanced AI research and analytics assistant. Provide extremely detailed, technically rigorous explanations. Include mathematical formulas (in LaTeX format where appropriate), algorithmic steps, complexity analysis, and performance considerations. Skip simple introductory fluff and get straight to low-level engineering details, optimization strategies, and code implementations.";
    }

    const payload = { title };
    if (systemPrompt) {
      payload.system_prompt = systemPrompt;
    }

    const data = await fetchJson("/api/v1/chat/sessions", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    activeSessionId = data.session.id;
    await loadSession(activeSessionId);
    renderStatus("Conversation ready.");
  };

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const content = textarea.value.trim();
    if (!content) return;

    if (!activeSessionId) {
      await createSession();
    }

    textarea.disabled = true;
    renderStatus("Assistant is thinking...");
    try {
      const data = await fetchJson(`/api/v1/chat/sessions/${activeSessionId}/messages`, {
        method: "POST",
        body: JSON.stringify({ content }),
      });
      textarea.value = "";
      sessionTitle.textContent = data.session.title;
      sessionMeta.textContent = `${data.provider} | ${data.model_name}`;
      renderMessages(data.session.messages || []);
      await loadSessionList();
      renderStatus("Response received.");
    } catch (error) {
      renderStatus(error.message, true);
    } finally {
      textarea.disabled = false;
      textarea.focus();
    }
  });

  newSessionButton.addEventListener("click", async () => {
    try {
      await createSession();
    } catch (error) {
      renderStatus(error.message, true);
    }
  });

  loadSessionList()
    .catch(async () => {
      try {
        await createSession();
      } catch (error) {
        renderStatus(error.message, true);
      }
    });
})();
