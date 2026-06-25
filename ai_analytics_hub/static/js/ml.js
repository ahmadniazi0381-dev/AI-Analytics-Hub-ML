(function () {
  const root = document.querySelector("[data-ml-root]");
  if (!root) return;

  const uploadList = root.querySelector("[data-upload-list]");
  const uploadStatus = root.querySelector("[data-upload-status]");
  const uploadForm = root.querySelector("[data-upload-form]");
  const uploadSelect = root.querySelector("[data-upload-select]");

  const aprioriForm = root.querySelector("[data-apriori-form]");
  const aprioriStatus = root.querySelector("[data-apriori-status]");
  const aprioriStatusText = root.querySelector("[data-apriori-status-text]");
  const aprioriResults = root.querySelector("[data-apriori-results]");
  const aprioriSummary = root.querySelector("[data-apriori-summary]");
  const itemsetsBody = root.querySelector("[data-itemsets-body]");
  const rulesBody = root.querySelector("[data-rules-body]");
  const aprioriResultRaw = root.querySelector("[data-apriori-result]");

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

  aprioriForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(aprioriForm);
    const payload = Object.fromEntries(formData.entries());

    // Parse numeric inputs
    Object.keys(payload).forEach((key) => {
      const value = payload[key];
      if (!Number.isNaN(Number(value)) && value !== "") {
        payload[key] = value.includes(".") ? Number.parseFloat(value) : Number.parseInt(value, 10);
      }
    });

    aprioriStatus.style.display = "block";
    aprioriStatusText.textContent = "Creating mining job...";
    aprioriResults.style.display = "none";
    aprioriResultRaw.style.display = "none";

    try {
      const data = await fetchJson("/api/v1/apriori/jobs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      aprioriStatusText.textContent = "Job queued. Mining frequent itemsets...";
      const completedJob = await pollJob(data.job.id);

      aprioriStatus.style.display = "none";

      if (completedJob.status === "failed") {
        aprioriStatusText.textContent = `Mining failed: ${completedJob.error || "Unknown error"}`;
        aprioriStatus.style.display = "block";
        return;
      }

      const results = completedJob.result;
      if (!results) {
        throw new Error("No results payload found in job response.");
      }

      // Populate summary
      const itemsetsCount = results.frequent_itemsets ? results.frequent_itemsets.length : 0;
      const rulesCount = results.association_rules ? results.association_rules.length : 0;
      const txCount = results.transaction_count || 0;

      aprioriSummary.innerHTML = `
        <div class="col-md-4">
          <div class="p-3 rounded bg-light bg-opacity-5 border border-light border-opacity-10 text-center">
            <div class="text-light-emphasis small mb-1">Transactions Parsed</div>
            <div class="h5 mb-0 fw-semibold">${txCount}</div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="p-3 rounded bg-light bg-opacity-5 border border-light border-opacity-10 text-center">
            <div class="text-light-emphasis small mb-1">Frequent Itemsets</div>
            <div class="h5 mb-0 fw-semibold">${itemsetsCount}</div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="p-3 rounded bg-light bg-opacity-5 border border-light border-opacity-10 text-center">
            <div class="text-light-emphasis small mb-1">Rules Generated</div>
            <div class="h5 mb-0 fw-semibold">${rulesCount}</div>
          </div>
        </div>
      `;

      // Render frequent itemsets table
      if (results.frequent_itemsets && results.frequent_itemsets.length) {
        itemsetsBody.innerHTML = results.frequent_itemsets
          .map(
            (item) => `
            <tr>
              <td><code class="text-info">${item.itemsets.map(escapeHtml).join(", ")}</code></td>
              <td>${item.support.toFixed(4)}</td>
            </tr>
          `
          )
          .join("");
      } else {
        itemsetsBody.innerHTML = `<tr><td colspan="2" class="text-center text-light-emphasis py-3">No frequent itemsets found matching support threshold.</td></tr>`;
      }

      // Render association rules table
      if (results.association_rules && results.association_rules.length) {
        rulesBody.innerHTML = results.association_rules
          .map(
            (rule) => `
            <tr>
              <td><code class="text-info">${rule.antecedents.map(escapeHtml).join(", ")}</code></td>
              <td><code class="text-success">${rule.consequents.map(escapeHtml).join(", ")}</code></td>
              <td>${rule.support.toFixed(4)}</td>
              <td>${rule.confidence.toFixed(4)}</td>
              <td>${rule.lift.toFixed(2)}</td>
            </tr>
          `
          )
          .join("");
      } else {
        rulesBody.innerHTML = `<tr><td colspan="5" class="text-center text-light-emphasis py-3">No association rules found matching confidence/lift thresholds.</td></tr>`;
      }

      aprioriResults.style.display = "block";
    } catch (error) {
      aprioriStatus.style.display = "none";
      aprioriResultRaw.style.display = "block";
      aprioriResultRaw.textContent = `Error: ${error.message}`;
    }
  });

  loadUploads().catch((error) => {
    uploadStatus.textContent = error.message;
    uploadStatus.className = "small text-danger mt-3";
  });
})();
