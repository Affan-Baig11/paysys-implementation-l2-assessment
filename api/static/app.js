const state = { apiKey: sessionStorage.getItem("minipayApiKey") || "" };
const loginCard = document.getElementById("login-card");
const workspace = document.getElementById("workspace");
const connectionStatus = document.getElementById("connection-status");
const notice = document.getElementById("notice");

function setSignedIn(signedIn) {
  loginCard.classList.toggle("hidden", signedIn);
  workspace.classList.toggle("hidden", !signedIn);
  connectionStatus.textContent = signedIn ? "Connected" : "Signed out";
  connectionStatus.classList.toggle("online", signedIn);
}

function showNotice(message, isError = false) {
  notice.textContent = message;
  notice.classList.toggle("hidden", !message);
  notice.classList.toggle("error", isError);
}

async function api(path, options = {}) {
  const headers = { "X-API-Key": state.apiKey, ...(options.headers || {}) };
  if (options.body) headers["Content-Type"] = "application/json";
  const response = await fetch(path, { ...options, headers });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || "Request failed (" + response.status + ")");
  return body;
}

function showDetails(target, payment) {
  target.replaceChildren();
  target.classList.remove("hidden", "error");
  const title = document.createElement("p");
  title.className = "result-title";
  title.textContent = payment.transaction_ref + " · " + payment.status;
  target.append(title);
  const values = [
    "Payment ID: " + payment.id,
    "Customer: " + ((payment.customer && payment.customer.name) || payment.customer_id),
    "Amount: " + payment.amount,
    "Created: " + payment.created_at,
    payment.completed_at ? "Completed: " + payment.completed_at : "Completion time: pending",
    "Callback attempts: " + ((payment.callbacks || []).length),
  ];
  for (const value of values) {
    const line = document.createElement("p");
    line.className = "result-line";
    line.textContent = value;
    target.append(line);
  }
}

function showError(target, message) {
  target.replaceChildren();
  target.classList.remove("hidden");
  target.classList.add("error");
  target.textContent = message;
}

document.getElementById("login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  state.apiKey = document.getElementById("api-key").value.trim();
  try {
    await api("/api/ops/health");
    sessionStorage.setItem("minipayApiKey", state.apiKey);
    setSignedIn(true);
    showNotice("Connected to the MiniPay API and database.");
  } catch (error) {
    sessionStorage.removeItem("minipayApiKey");
    state.apiKey = "";
    setSignedIn(false);
    showNotice(error.message, true);
  }
});

document.getElementById("signout").addEventListener("click", () => {
  sessionStorage.removeItem("minipayApiKey");
  state.apiKey = "";
  setSignedIn(false);
  showNotice("");
});

document.getElementById("customer-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const target = document.getElementById("customer-result");
  try {
    const customer = await api("/api/customers", {
      method: "POST",
      body: JSON.stringify({
        customer_ref: document.getElementById("customer-ref").value.trim(),
        name: document.getElementById("customer-name").value.trim(),
      }),
    });
    target.classList.remove("hidden", "error");
    target.textContent = "Created " + customer.customer_ref + " with customer ID " + customer.id + ".";
    document.getElementById("payment-customer").value = customer.id;
    showNotice("Customer created.");
  } catch (error) {
    showError(target, error.message);
  }
});

document.getElementById("payment-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const target = document.getElementById("payment-result");
  try {
    const submitted = await api("/api/payments", {
      method: "POST",
      headers: { "Idempotency-Key": crypto.randomUUID() },
      body: JSON.stringify({
        customer_id: Number(document.getElementById("payment-customer").value),
        amount: document.getElementById("payment-amount").value,
      }),
    });
    const payment = await api("/api/payments/" + encodeURIComponent(submitted.transaction_ref));
    showDetails(target, payment);
    showNotice("Test payment submitted. The local mock processor marked it complete.");
  } catch (error) {
    showError(target, error.message);
    showNotice(error.message, true);
  }
});

document.getElementById("search-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const target = document.getElementById("search-result");
  const ref = document.getElementById("transaction-ref").value.trim();
  try {
    const payment = await api("/api/payments/" + encodeURIComponent(ref));
    showDetails(target, payment);
    showNotice("Payment found.");
  } catch (error) {
    showError(target, error.message);
    showNotice(error.message, true);
  }
});

if (state.apiKey) {
  document.getElementById("api-key").value = state.apiKey;
  api("/api/ops/health").then(() => setSignedIn(true)).catch(() => {
    sessionStorage.removeItem("minipayApiKey");
    state.apiKey = "";
    setSignedIn(false);
  });
} else {
  setSignedIn(false);
}
