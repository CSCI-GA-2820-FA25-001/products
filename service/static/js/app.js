async function fetchJSON(url, opts = {}) {
    const resp = await fetch(url, { headers: { "Content-Type": "application/json" }, ...opts });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}: ${await resp.text()}`);
    return resp.status === 204 ? null : resp.json();
}
const api = (p) => `${window.BASE_URL || ""}${p}`;

function renderRows(items) {
    const tbody = document.querySelector("#results tbody");
    tbody.innerHTML = "";
    (items || []).forEach(p => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
        <td>${p.id ?? ""}</td>
        <td>${p.name ?? ""}</td>
        <td>${p.price ?? ""}</td>
        <td>${p.category ?? ""}</td>`;
        tbody.appendChild(tr);
    });
}

/** Load list only when explicitly asked */
async function loadList(q = {}) {
    const params = new URLSearchParams(q);
    const url = params.toString() ? api(`/products?${params.toString()}`) : api("/products");
    const data = await fetchJSON(url);
    renderRows(data);
}

/* ========== CREATE (no auto-list) ========== */
document.getElementById("create-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
        id: document.getElementById("create-id").value.trim(),
        name: document.getElementById("name").value.trim(),
        price: parseFloat(document.getElementById("price").value),
        category: document.getElementById("category").value.trim(),
    };
    const invEl = document.getElementById("inventory");
    const availEl = document.getElementById("available");
    if (invEl) {
        const inv = parseInt(invEl.value || "0", 10);
        if (!Number.isNaN(inv)) payload.inventory = inv;
    }
    if (availEl) payload.available = !!availEl.checked;

    await fetchJSON(api("/products"), { method: "POST", body: JSON.stringify(payload) });
    // Intentionally NOT calling loadList() here
});

/* ========== SEARCH (only if filters provided) ========== */
document.getElementById("search-btn").addEventListener("click", async () => {
    const name = document.getElementById("search-name").value.trim();
    const min = document.getElementById("search-min").value;
    const max = document.getElementById("search-max").value;

    // If no filters, do nothing (don’t list)
    if (!name && !min && !max) return;

    const q = {};
    if (name) q.name = name;
    if (min) q.min_price = min;
    if (max) q.max_price = max;
    await loadList(q);
});

/* ========== LIST ALL (explicit) ========== */
document.getElementById("list-btn").addEventListener("click", () => loadList());

/* ========== READ (no auto-list) ========== */
document.getElementById("read-btn").addEventListener("click", async () => {
    const id = document.getElementById("prod-id").value.trim();
    if (!id) return;
    const p = await fetchJSON(api(`/products/${id}`));
    document.getElementById("upd-name").value = p.name ?? "";
    document.getElementById("upd-price").value = p.price ?? "";
    document.getElementById("upd-category").value = p.category ?? "";
});

/* ========== UPDATE (no auto-list) ========== */
document.getElementById("update-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = document.getElementById("prod-id").value.trim();
    if (!id) return;
    const payload = {
        name: document.getElementById("upd-name").value.trim(),
        price: parseFloat(document.getElementById("upd-price").value),
        category: document.getElementById("upd-category").value.trim(),
    };
    await fetchJSON(api(`/products/${id}`), { method: "PUT", body: JSON.stringify(payload) });
    // Intentionally NOT calling loadList() here
});

/* ========== DELETE (no auto-list) ========== */
document.getElementById("delete-btn").addEventListener("click", async () => {
    const id = document.getElementById("prod-id").value.trim();
    if (!id) return;
    await fetch(api(`/products/${id}`), { method: "DELETE" });
    // Intentionally NOT calling loadList() here
});

/* ========== ACTION (purchase 1; no auto-list) ========== */
document.getElementById("action-btn").addEventListener("click", async () => {
    const id = document.getElementById("prod-id").value.trim();
    if (!id) return;
    await fetchJSON(api(`/products/${id}/purchase`), { method: "POST", body: JSON.stringify({ quantity: 1 }) });
    // Intentionally NOT calling loadList() here
});

/* No DOMContentLoaded fetch — table stays empty until "List All" or a filtered "Search" */
