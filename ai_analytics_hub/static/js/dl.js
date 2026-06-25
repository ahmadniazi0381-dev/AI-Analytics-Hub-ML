(function () {
  const root = document.querySelector("[data-dl-root]");
  if (!root) return;

  const uploadList = root.querySelector("[data-upload-list]");
  const uploadStatus = root.querySelector("[data-upload-status]");
  const uploadForm = root.querySelector("[data-upload-form]");
  const uploadSelect = root.querySelector("[data-upload-select]");

  const classifierForm = root.querySelector("[data-classifier-form]");
  const classifierStatus = root.querySelector("[data-classifier-status]");
  const classifierStatusText = root.querySelector("[data-classifier-status-text]");
  const classifierResults = root.querySelector("[data-classifier-results]");
  const metricsSummary = root.querySelector("[data-metrics-summary]");
  const classLabelsContainer = root.querySelector("[data-class-labels]");
  const confusionMatrixBody = root.querySelector("[data-confusion-matrix]");

  const escapeHtml = (value) =>
    String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;");

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

  const renderUploads = (uploads) => {
    uploadList.innerHTML = uploads.length
      ? uploads
          .map(
            (upload) => `
              <article class="upload-item p-2 mb-2 rounded bg-light bg-opacity-10 d-flex justify-content-between align-items-center">
                <div>
                  <div class="upload-item-name fw-semibold small text-truncate" style="max-width: 180px;">${escapeHtml(upload.original_filename)}</div>
                  <div class="upload-item-meta text-light-emphasis" style="font-size: 0.75rem;">ID ${upload.id} | ${(upload.file_size_bytes / 1024).toFixed(1)} KB</div>
                </div>
              </article>
            `
          )
          .join("")
      : `<div class="text-light-emphasis small py-2">No datasets uploaded yet.</div>`;

    const options = uploads.length
      ? uploads
          .map(
            (upload) =>
              `<option value="${upload.id}">${escapeHtml(upload.original_filename)} (ID ${upload.id})</option>`
          )
          .join("")
      : `<option value="">Upload a dataset first</option>`;

    if (uploadSelect) {
      uploadSelect.innerHTML = options;
    }
  };

  const loadUploads = async () => {
    const data = await fetchJson("/api/v1/uploads");
    renderUploads(data.uploads);
  };

  const pollJob = async (jobId) => {
    let attempts = 0;
    while (attempts < 60) {
      const data = await fetchJson(`/api/v1/jobs/${jobId}`);
      const job = data.job;
      if (job.status === "completed" || job.status === "failed") {
        return job;
      }
      attempts += 1;
      await new Promise((resolve) => setTimeout(resolve, 1500));
    }
    throw new Error("Timed out waiting for job completion.");
  };

  uploadForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(uploadForm);
    uploadStatus.textContent = "Uploading dataset...";
    uploadStatus.className = "small text-light-emphasis mt-3";
    try {
      const response = await fetch("/api/v1/uploads", {
        method: "POST",
        body: formData,
        credentials: "same-origin",
      });
      const payload = await response.json();
      if (!response.ok || payload.success === false) {
        throw new Error(payload?.error?.message || "Upload failed.");
      }
      uploadStatus.textContent = `Uploaded: ${payload.data.upload.original_filename}`;
      uploadForm.reset();
      await loadUploads();
    } catch (error) {
      uploadStatus.textContent = error.message;
      uploadStatus.className = "small text-danger mt-3";
    }
  });

  classifierForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(classifierForm);
    const payload = Object.fromEntries(formData.entries());

    if (typeof payload.target_column === "string") {
      payload.target_column = payload.target_column.trim();
    }

    // Parse numeric inputs
    Object.keys(payload).forEach((key) => {
      const value = payload[key];
      if (!Number.isNaN(Number(value)) && value !== "") {
        payload[key] = value.includes(".") ? Number.parseFloat(value) : Number.parseInt(value, 10);
      }
    });

    classifierStatus.style.display = "block";
    classifierStatusText.textContent = "Starting neural network training job...";
    classifierResults.style.display = "none";

    try {
      const data = await fetchJson("/api/v1/classifier/jobs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      classifierStatusText.textContent = "Job queued. Preprocessing & training model...";
      const completedJob = await pollJob(data.job.id);

      classifierStatus.style.display = "none";

      if (completedJob.status === "failed") {
        classifierStatusText.textContent = `Training failed: ${completedJob.error || "Unknown error"}`;
        classifierStatus.style.display = "block";
        return;
      }

      const results = completedJob.result;
      if (!results) {
        throw new Error("No results payload found in job response.");
      }

      // Populate metrics
      const metrics = results.metrics || {};
      metricsSummary.innerHTML = `
        <div class="col-md-3">
          <div class="p-3 rounded bg-light bg-opacity-5 border border-light border-opacity-10 text-center">
            <div class="text-light-emphasis small mb-1">Accuracy</div>
            <div class="h5 mb-0 fw-semibold text-success">${(metrics.accuracy * 100).toFixed(2)}%</div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="p-3 rounded bg-light bg-opacity-5 border border-light border-opacity-10 text-center">
            <div class="text-light-emphasis small mb-1">Precision</div>
            <div class="h5 mb-0 fw-semibold text-info">${(metrics.precision * 100).toFixed(2)}%</div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="p-3 rounded bg-light bg-opacity-5 border border-light border-opacity-10 text-center">
            <div class="text-light-emphasis small mb-1">Recall</div>
            <div class="h5 mb-0 fw-semibold text-warning">${(metrics.recall * 100).toFixed(2)}%</div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="p-3 rounded bg-light bg-opacity-5 border border-light border-opacity-10 text-center">
            <div class="text-light-emphasis small mb-1">F1 Score</div>
            <div class="h5 mb-0 fw-semibold text-danger">${(metrics.f1_score * 100).toFixed(2)}%</div>
          </div>
        </div>
      `;

      // Render class labels
      if (results.class_labels && results.class_labels.length) {
        classLabelsContainer.innerHTML = results.class_labels
          .map((label) => `<span class="badge text-bg-secondary me-2 text-uppercase">${escapeHtml(label)}</span>`)
          .join("");
      } else {
        classLabelsContainer.innerHTML = `<span class="text-light-emphasis small">None detected</span>`;
      }

      // Render confusion matrix
      if (results.confusion_matrix && results.confusion_matrix.length) {
        const matrix = results.confusion_matrix;
        const labels = results.class_labels || [];
        
        let headerRow = "<tr><th>Actual \\ Predicted</th>";
        labels.forEach((l) => {
          headerRow += `<th>${escapeHtml(l)}</th>`;
        });
        headerRow += "</tr>";

        let matrixRows = "";
        matrix.forEach((row, i) => {
          let rowHtml = `<tr><td class="fw-semibold">${escapeHtml(labels[i] || i)}</td>`;
          row.forEach((cell) => {
            rowHtml += `<td>${cell}</td>`;
          });
          rowHtml += "</tr>";
          matrixRows += rowHtml;
        });

        confusionMatrixBody.innerHTML = `<thead>${headerRow}</thead><tbody>${matrixRows}</tbody>`;
      } else {
        confusionMatrixBody.innerHTML = `<tr><td class="text-center text-light-emphasis py-3">No confusion matrix generated.</td></tr>`;
      }

      classifierResults.style.display = "block";
    } catch (error) {
      classifierStatus.style.display = "none";
      alert(`Error: ${error.message}`);
    }
  });

  loadUploads().catch((error) => {
    uploadStatus.textContent = error.message;
    uploadStatus.className = "small text-danger mt-3";
  });
})();
