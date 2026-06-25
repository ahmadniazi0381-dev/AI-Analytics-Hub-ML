(function () {
  // Helpers
  const fetchJson = async (url, options = {}) => {
    const response = await fetch(url, {
      credentials: "same-origin",
      ...options,
    });
    const payload = await response.json();
    if (!response.ok || payload.success === false) {
      throw new Error(payload?.error?.message || "Request failed.");
    }
    return payload.data;
  };

  const escapeHtml = (value) =>
    String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;");

  // ════════════════════════════════════════════════════════════════
  // 1. Question Answering (Voice In + Voice Out)
  // ════════════════════════════════════════════════════════════════
  const qaForm = document.getElementById("qaForm");
  if (qaForm) {
    const micBtn = document.getElementById("qaVoiceInput");
    const voiceStatus = document.getElementById("voiceInputStatus");
    const questionInput = document.getElementById("qaQuestion");
    const qaSpinner = document.getElementById("qaSpinner");
    const qaResultPanel = document.getElementById("qaResultPanel");
    const qaAnswerText = document.getElementById("qaAnswerText");
    const qaAnswerMeta = document.getElementById("qaAnswerMeta");

    const readAnswerBtn = document.getElementById("readAnswerBtn");
    const stopSpeechBtn = document.getElementById("stopSpeechBtn");
    const speakingStatus = document.getElementById("speakingStatus");

    // Speech Recognition Setup
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition = null;
    let isRecording = false;

    if (SpeechRecognition) {
      recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = "en-US";

      recognition.onstart = () => {
        isRecording = true;
        micBtn.classList.add("recording");
        voiceStatus.style.display = "block";
      };

      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        questionInput.value = transcript;
      };

      recognition.onerror = (event) => {
        console.error("Speech recognition error", event.error);
        voiceStatus.style.display = "none";
        micBtn.classList.remove("recording");
        isRecording = false;
      };

      recognition.onend = () => {
        voiceStatus.style.display = "none";
        micBtn.classList.remove("recording");
        isRecording = false;
      };

      micBtn.addEventListener("click", () => {
        if (isRecording) {
          recognition.stop();
        } else {
          recognition.start();
        }
      });
    } else {
      micBtn.addEventListener("click", () => {
        alert("Your browser does not support Speech Recognition. Please try Chrome, Edge, or Safari.");
      });
    }

    // Speech Synthesis (Read aloud)
    let currentUtterance = null;

    const speak = (text) => {
      window.speechSynthesis.cancel(); // cancel any active speech
      currentUtterance = new SpeechSynthesisUtterance(text);

      currentUtterance.onstart = () => {
        speakingStatus.style.display = "inline";
        readAnswerBtn.style.display = "none";
        stopSpeechBtn.style.display = "inline-block";
        qaAnswerText.classList.add("speaking-pulse");
      };

      currentUtterance.onend = () => {
        speakingStatus.style.display = "none";
        readAnswerBtn.style.display = "inline-block";
        stopSpeechBtn.style.display = "none";
        qaAnswerText.classList.remove("speaking-pulse");
      };

      currentUtterance.onerror = () => {
        speakingStatus.style.display = "none";
        readAnswerBtn.style.display = "inline-block";
        stopSpeechBtn.style.display = "none";
        qaAnswerText.classList.remove("speaking-pulse");
      };

      window.speechSynthesis.speak(currentUtterance);
    };

    readAnswerBtn.addEventListener("click", () => {
      if (qaAnswerText.textContent) {
        speak(qaAnswerText.textContent);
      }
    });

    stopSpeechBtn.addEventListener("click", () => {
      window.speechSynthesis.cancel();
      speakingStatus.style.display = "none";
      readAnswerBtn.style.display = "inline-block";
      stopSpeechBtn.style.display = "none";
    });

    // --- MULTI-LEVEL DIFFICULTY MODE FOR QUESTION ANSWERING ---
    const storiesData = {
      dino: {
        context: "Dino is a friendly green dinosaur who loves eating yummy yellow bananas and playing hide-and-seek in the jungle.",
        questions: [
          "What does Dino love eating?",
          "What color is Dino?",
          "What game does Dino love playing?"
        ]
      },
      space: {
        context: "Sparky is a shiny red space rocket. Sparky flies up to the silver Moon to visit friendly blue star monsters.",
        questions: [
          "What color is Sparky?",
          "Where does Sparky fly to?",
          "Who does Sparky visit?"
        ]
      },
      puppy: {
        context: "Pippin is a fluffy brown puppy who lives in a cozy blue house. Pippin loves chasing round red balls in the backyard.",
        questions: [
          "What color is Pippin?",
          "Where does Pippin live?",
          "What does Pippin love chasing?"
        ]
      }
    };

    const selectStory = (key) => {
      const story = storiesData[key];
      if (!story) return;

      document.getElementById("qaContext").value = story.context;
      document.getElementById("qaQuestion").value = story.questions[0];

      // Mark active story preset card
      document.querySelectorAll(".story-preset-card").forEach(card => {
        if (card.dataset.story === key) {
          card.style.borderColor = "#ff6b6b";
          card.style.background = "#fff0f2";
        } else {
          card.style.borderColor = "";
          card.style.background = "";
        }
      });

      // Populate preset questions list
      const qList = document.getElementById("presetQuestionsList");
      if (qList) {
        qList.innerHTML = story.questions
          .map(q => `<button type="button" class="btn btn-sm preset-q-btn" data-question="${escapeHtml(q)}">${escapeHtml(q)}</button>`)
          .join("");

        qList.querySelectorAll("[data-question]").forEach(btn => {
          btn.addEventListener("click", () => {
            questionInput.value = btn.dataset.question;
            // Submit the form automatically for a seamless child-friendly experience!
            qaForm.dispatchEvent(new Event("submit"));
          });
        });
      }
    };

    const applyQaDifficultyLevel = (level) => {
      const presetsContainer = document.getElementById("storyPresetsContainer");
      const presetQContainer = document.getElementById("presetQuestionsContainer");
      const metricsPanel = document.getElementById("expertMetricsPanel");
      
      const standardLabels = qaForm.querySelectorAll(".standard-label");
      const kidLabels = qaForm.querySelectorAll(".kid-label");
      const expertLabels = qaForm.querySelectorAll(".expert-label");

      const standardBtnText = qaForm.querySelector(".standard-btn-text");
      const kidBtnText = qaForm.querySelector(".kid-btn-text");
      const expertBtnText = qaForm.querySelector(".expert-btn-text");

      // Reset visibilities
      if (presetsContainer) presetsContainer.style.display = "none";
      if (presetQContainer) presetQContainer.style.display = "none";
      if (metricsPanel) metricsPanel.style.display = "none";

      standardLabels.forEach(el => el.style.display = "none");
      kidLabels.forEach(el => el.style.display = "none");
      expertLabels.forEach(el => el.style.display = "none");

      if (standardBtnText) standardBtnText.style.display = "none";
      if (kidBtnText) kidBtnText.style.display = "none";
      if (expertBtnText) expertBtnText.style.display = "none";

      if (level === "kid") {
        if (presetsContainer) presetsContainer.style.display = "block";
        if (presetQContainer) presetQContainer.style.display = "block";
        kidLabels.forEach(el => el.style.display = "inline");
        if (kidBtnText) kidBtnText.style.display = "inline";

        // Auto-select first story if context is default/empty
        const currentContext = document.getElementById("qaContext").value;
        if (!currentContext || currentContext.includes("Lahore is the capital city")) {
          selectStory("dino");
        }
      } else if (level === "expert") {
        if (metricsPanel) metricsPanel.style.display = "block";
        expertLabels.forEach(el => el.style.display = "inline");
        if (expertBtnText) expertBtnText.style.display = "inline";
      } else {
        // Intermediate
        standardLabels.forEach(el => el.style.display = "inline");
        if (standardBtnText) standardBtnText.style.display = "inline";
      }
    };

    // Attach story card listeners
    document.querySelectorAll(".story-preset-card").forEach(card => {
      card.addEventListener("click", () => {
        selectStory(card.dataset.story);
      });
    });

    // Listen for level changes
    window.addEventListener("difficultyLevelChanged", (e) => {
      applyQaDifficultyLevel(e.detail.level);
    });

    // Initial state load
    const initialLevel = localStorage.getItem("difficultyLevel") || "intermediate";
    applyQaDifficultyLevel(initialLevel);

    // Form Submit
    qaForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const formData = new FormData(qaForm);
      const payload = Object.fromEntries(formData.entries());

      qaSpinner.style.display = "block";
      qaResultPanel.style.display = "none";
      window.speechSynthesis.cancel(); // Stop talking if currently playing

      try {
        const data = await fetchJson("/api/v1/qa/ask", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        qaSpinner.style.display = "none";
        
        const answer = data.answer || "No answer found.";
        qaAnswerText.textContent = answer;
        
        const latency = data.latency_ms || 0;
        const confidence = data.score !== undefined ? data.score : 0;

        const score = data.score !== undefined ? `Confidence Score: ${(data.score * 100).toFixed(1)}%` : "";
        const time = data.latency_ms ? `Latency: ${data.latency_ms.toFixed(0)}ms` : "";
        qaAnswerMeta.textContent = [score, time].filter(Boolean).join(" | ");

        // Populate expert panel metrics
        const latTag = document.getElementById("metricLatency");
        const confTag = document.getElementById("metricConfidence");
        if (latTag) latTag.textContent = `Latency: ${latency.toFixed(2)} ms`;
        if (confTag) confTag.textContent = `Confidence: ${confidence.toFixed(4)} (probability)`;

        readAnswerBtn.style.display = "inline-block";
        qaResultPanel.style.display = "block";

        // Automatically speak the answer ONLY in Kid Mode
        if (localStorage.getItem("difficultyLevel") === "kid") {
          speak(answer);
        }
      } catch (err) {
        qaSpinner.style.display = "none";
        alert(`QA Error: ${err.message}`);
      }
    });
  }

  // ════════════════════════════════════════════════════════════════
  // 2. Text Generation
  // ════════════════════════════════════════════════════════════════
  const genForm = document.getElementById("genForm");
  if (genForm) {
    const genSpinner = document.getElementById("genSpinner");
    const genResultPanel = document.getElementById("genResultPanel");
    const genOutputText = document.getElementById("genOutputText");

    genForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const formData = new FormData(genForm);
      const payload = Object.fromEntries(formData.entries());

      // Parse parameters
      if (payload.max_new_tokens) payload.max_new_tokens = parseInt(payload.max_new_tokens, 10);
      if (payload.temperature) payload.temperature = parseFloat(payload.temperature);

      genSpinner.style.display = "block";
      genResultPanel.style.display = "none";

      try {
        const data = await fetchJson("/api/v1/text-generation/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        genSpinner.style.display = "none";
        genOutputText.textContent = data.generated_text || "No text generated.";
        genResultPanel.style.display = "block";
      } catch (err) {
        genSpinner.style.display = "none";
        alert(`Generation Error: ${err.message}`);
      }
    });
  }

  // ════════════════════════════════════════════════════════════════
  // 3. Named Entity Recognition (NER)
  // ════════════════════════════════════════════════════════════════
  const nerForm = document.getElementById("nerForm");
  if (nerForm) {
    const nerSpinner = document.getElementById("nerSpinner");
    const nerResultPanel = document.getElementById("nerResultPanel");
    const nerHighlighted = document.getElementById("nerHighlighted");
    const nerEntityTable = document.getElementById("nerEntityTable");

    nerForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const formData = new FormData(nerForm);
      const payload = Object.fromEntries(formData.entries());

      nerSpinner.style.display = "block";
      nerResultPanel.style.display = "none";

      try {
        const data = await fetchJson("/api/v1/ner/extract", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        nerSpinner.style.display = "none";
        const entities = data.entities || [];

        // Build highlighting
        const rawText = payload.text;
        let highlightedHtml = "";
        let lastIdx = 0;

        // Sort entities by start index to process sequentially
        const sortedEntities = [...entities].sort((a, b) => a.start - b.start);

        for (const entity of sortedEntities) {
          const start = entity.start;
          const end = entity.end;
          
          if (start >= lastIdx) {
            highlightedHtml += escapeHtml(rawText.substring(lastIdx, start));
            const entityText = rawText.substring(start, end);
            const badgeClass = `entity-${entity.entity_group || "default"}`;
            highlightedHtml += `<span class="entity-tag ${badgeClass}">${escapeHtml(entityText)} <small class="opacity-75">${escapeHtml(entity.entity_group)}</small></span>`;
            lastIdx = end;
          }
        }
        highlightedHtml += escapeHtml(rawText.substring(lastIdx));
        nerHighlighted.innerHTML = highlightedHtml;

        // Build table
        if (entities.length) {
          nerEntityTable.innerHTML = entities
            .map(
              (ent) => `
              <tr>
                <td><code class="text-info">${escapeHtml(rawText.substring(ent.start, ent.end))}</code></td>
                <td><span class="badge text-bg-secondary text-uppercase">${escapeHtml(ent.entity_group)}</span></td>
                <td>${(ent.score * 100).toFixed(1)}%</td>
              </tr>
            `
            )
            .join("");
        } else {
          nerEntityTable.innerHTML = `<tr><td colspan="3" class="text-center text-light-emphasis py-3">No entities identified.</td></tr>`;
        }

        nerResultPanel.style.display = "block";
      } catch (err) {
        nerSpinner.style.display = "none";
        alert(`NER Error: ${err.message}`);
      }
    });
  }
})();
