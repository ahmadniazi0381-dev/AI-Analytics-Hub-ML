(function () {
  const root = document.querySelector("[data-workbench-root]");
  if (!root) return;

  const uploadList = root.querySelector("[data-upload-list]");
  const uploadStatus = root.querySelector("[data-upload-status]");
  const uploadForm = root.querySelector("[data-upload-form]");
  const uploadSelects = Array.from(root.querySelectorAll("[data-upload-select]"));

  const escapeHtml = (value) =>
    String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;");

  const setResult = (selector, value) => {
    const element = root.querySelector(selector);
    element.textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
  };

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
              <article class="upload-item">
                <div class="upload-item-name">${escapeHtml(upload.original_filename)}</div>
                <div class="upload-item-meta">ID ${upload.id} | ${(upload.file_size_bytes / 1024).toFixed(1)} KB</div>
              </article>
            `
          )
          .join("")
      : `<div class="assistant-empty small">No datasets uploaded yet.</div>`;

    const options = uploads.length
      ? uploads
          .map(
            (upload) =>
              `<option value="${upload.id}">${escapeHtml(upload.original_filename)} (ID ${upload.id})</option>`
          )
          .join("")
      : `<option value="">Upload a dataset first</option>`;

    uploadSelects.forEach((select) => {
      select.innerHTML = options;
    });
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
      uploadStatus.classList.add("text-danger");
    }
  });

  const bindAsyncJobForm = (selector, endpoint, resultSelector) => {
    const form = root.querySelector(selector);
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const formData = new FormData(form);
      const payload = Object.fromEntries(formData.entries());
      Object.keys(payload).forEach((key) => {
        const value = payload[key];
        if (!Number.isNaN(Number(value)) && value !== "") {
          payload[key] = value.includes?.(".") ? Number.parseFloat(value) : Number.parseInt(value, 10);
        }
      });
      setResult(resultSelector, "Processing...");
      try {
        const data = await fetchJson(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const completedJob = await pollJob(data.job.id);
        setResult(resultSelector, completedJob);
      } catch (error) {
        setResult(resultSelector, error.message);
      }
    });
  };

  const bindInferenceForm = (selector, endpoint, resultSelector) => {
    const form = root.querySelector(selector);
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const formData = new FormData(form);
      const payload = Object.fromEntries(formData.entries());
      Object.keys(payload).forEach((key) => {
        const value = payload[key];
        if (!Number.isNaN(Number(value)) && value !== "") {
          payload[key] = value.includes?.(".") ? Number.parseFloat(value) : Number.parseInt(value, 10);
        }
      });
      setResult(resultSelector, "Processing...");
      try {
        const data = await fetchJson(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        setResult(resultSelector, data);
      } catch (error) {
        setResult(resultSelector, error.message);
      }
    });
  };

  bindAsyncJobForm("[data-apriori-form]", "/api/v1/apriori/jobs", "[data-apriori-result]");
  bindAsyncJobForm("[data-classifier-form]", "/api/v1/classifier/jobs", "[data-classifier-result]");
  bindInferenceForm("[data-qa-form]", "/api/v1/qa/ask", "[data-qa-result]");
  bindInferenceForm("[data-generation-form]", "/api/v1/text-generation/generate", "[data-generation-result]");
  bindInferenceForm("[data-ner-form]", "/api/v1/ner/extract", "[data-ner-result]");

  loadUploads().catch((error) => {
    uploadStatus.textContent = error.message;
    uploadStatus.classList.add("text-danger");
  });
})();
