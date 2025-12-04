// Helper function to make API calls
async function fetchJSON(url, opts = {}) {
    const resp = await fetch(url, { headers: { "Content-Type": "application/json" }, ...opts });
    if (!resp.ok) {
        const text = await resp.text();
        
        try {
            const errorData = JSON.parse(text);
            const errorMsg = errorData.message || errorData.error || text;
            throw new Error(errorMsg);
        } catch (e) {
            if (e instanceof SyntaxError) {
                throw new Error(text || `HTTP ${resp.status}`);
            }
            throw e;
        }
    }
    return resp.status === 204 ? null : resp.json();
}

// Build API URL
const api = (p) => `${window.BASE_URL || ""}${p}`;

// Show flash message
function showMessage(message, type = "success") {
    const flashDiv = document.getElementById("flash-message");
    flashDiv.className = `alert alert-${type}`;
    flashDiv.textContent = message;
    flashDiv.style.display = "block";
}

// Render table rows
function renderRows(items) {
    const tbody = document.querySelector("#results tbody");
    tbody.innerHTML = "";

    document.getElementById("result-count").textContent = items.length;

    if (!items || items.length === 0) {
        const tr = document.createElement("tr");
        tr.innerHTML = '<td colspan="8" class="text-center text-muted">No products found</td>';
        tbody.appendChild(tr);
        return;
    }

    items.forEach(p => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${p.id || ""}</td>
            <td>${p.name || ""}</td>
            <td>${p.description || ""}</td>
            <td>$${p.price || ""}</td>
            <td>${p.image_url ? '<a href="' + p.image_url + '" target="_blank">View</a>' : ""}</td>
            <td>${p.available ? '<span class="badge bg-success">Yes</span>' : '<span class="badge bg-secondary">No</span>'}</td>
            <td>${p.inventory !== undefined ? p.inventory : ""}</td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="loadProductToEdit('${p.id}')">Edit</button>
            </td>`;
        tbody.appendChild(tr);
    });
}

// Load list with optional query parameters
async function loadList(q = {}, showMsg = true, fillSearchForm = false) {
    try {
        const params = new URLSearchParams(q);
        const url = params.toString() ? api(`/products?${params.toString()}`) : api("/products");
        const data = await fetchJSON(url);
        renderRows(data);
        
        if (showMsg) {
            showMessage(`Loaded ${data.length} product(s)`, "info");
        }
        
        if (fillSearchForm && data.length === 1) {
            fillSearchFormWithProduct(data[0]);
        }
    } catch (error) {
        showMessage(`Error loading products: ${error.message}`, "danger");
    }
}
function fillSearchFormWithProduct(product) {
    document.getElementById("search-id").value = product.id || "";
    document.getElementById("search-name").value = product.name || "";
    document.getElementById("search-description").value = product.description || "";
    document.getElementById("search-price").value = product.price || "";
    document.getElementById("search-image-url").value = product.image_url || "";
    document.getElementById("search-available").value = product.available ? "true" : (product.available === false ? "false" : "");
    document.getElementById("search-min-price").value = "";
    document.getElementById("search-max-price").value = "";
}



// CREATE PRODUCT
document.getElementById("create-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
        const payload = {
            id: document.getElementById("create-id").value.trim(),
            name: document.getElementById("create-name").value.trim(),
            price: parseFloat(document.getElementById("create-price").value),
            description: document.getElementById("create-description").value.trim() || null,
            image_url: document.getElementById("create-image-url").value.trim() || null,
            inventory: parseInt(document.getElementById("create-inventory").value, 10),
            available: document.getElementById("create-available").checked,
        };

        await fetchJSON(api("/products"), { method: "POST", body: JSON.stringify(payload) });
        showMessage(`Product "${payload.name}" created successfully!`, "success");
        document.getElementById("create-form").reset();
        document.getElementById("create-available").checked = true;

        await loadList({}, false);
    } catch (error) {
        showMessage(`Error creating product: ${error.message}`, "danger");
    }
});

// SEARCH WITH FILTERS
// SEARCH WITH FILTERS
document.getElementById("search-btn").addEventListener("click", async () => {
    const id = document.getElementById("search-id").value.trim();
    const name = document.getElementById("search-name").value.trim();
    const description = document.getElementById("search-description").value.trim();
    const available = document.getElementById("search-available").value;
    const price = document.getElementById("search-price").value;
    const minPrice = document.getElementById("search-min-price").value;
    const maxPrice = document.getElementById("search-max-price").value;
    const imageUrl = document.getElementById("search-image-url").value.trim();

    const q = {};
    if (id) q.id = id;
    if (name) q.name = name;
    if (description) q.description = description;
    if (available) q.available = available;
    if (price) q.price = price;
    if (minPrice) q.min_price = minPrice;
    if (maxPrice) q.max_price = maxPrice;
    if (imageUrl) q.image_url = imageUrl;

    await loadList(q, true, true);  // fill search form if exactly one result
});

// LIST ALL PRODUCTS
document.getElementById("list-all-btn").addEventListener("click", () => loadList());

// CLEAR SEARCH FILTERS
document.getElementById("clear-search-btn").addEventListener("click", () => {
    document.getElementById("search-id").value = "";
    document.getElementById("search-name").value = "";
    document.getElementById("search-description").value = "";
    document.getElementById("search-available").value = "";
    document.getElementById("search-price").value = "";
    document.getElementById("search-min-price").value = "";
    document.getElementById("search-max-price").value = "";
    document.getElementById("search-image-url").value = "";
});

// READ PRODUCT (display only)
document.getElementById("read-btn").addEventListener("click", async () => {
    const id = document.getElementById("product-id-read").value.trim();
    if (!id) {
        showMessage("Please enter a Product ID", "warning");
        return;
    }

    try {
        const p = await fetchJSON(api(`/products/${id}`));

        // Display product details in read-only view
        document.getElementById("display-id").textContent = p.id || "";
        document.getElementById("display-name").textContent = p.name || "";
        document.getElementById("display-price").textContent = p.price ? `$${p.price}` : "";
        document.getElementById("display-inventory").textContent = p.inventory !== undefined ? p.inventory : "";
        document.getElementById("display-description").textContent = p.description || "N/A";
        document.getElementById("display-image-url").innerHTML = p.image_url ? `<a href="${p.image_url}" target="_blank">View Image</a>` : "N/A";
        document.getElementById("display-available").textContent = p.available ? "Yes" : "No";

        // Show the details section
        document.getElementById("read-product-details").style.display = "block";

        showMessage(`Product "${p.name}" loaded successfully!`, "info");
    } catch (error) {
        let errorMsg = error.message || "";

        if (errorMsg.includes("Product with id")) {
            const match = errorMsg.match(/id '([^']+)'/);
            const productId = match ? match[1] : id;
            errorMsg = `Product '${productId}' not found`;
        }
        else if (errorMsg.toLowerCase().includes("not found")) {
            errorMsg = `Product '${id}' not found`;
        }

        showMessage(errorMsg, "danger");
    }
});

// UPDATE PRODUCT
document.getElementById("update-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = document.getElementById("product-id-update").value.trim();
    if (!id) {
        showMessage("Please enter a Product ID and load the product first", "warning");
        return;
    }

    try {
        const payload = {
            id: id,
            name: document.getElementById("update-name").value.trim(),
            price: parseFloat(document.getElementById("update-price").value),
            description: document.getElementById("update-description").value.trim() || null,
            image_url: document.getElementById("update-image-url").value.trim() || null,
            available: document.getElementById("update-available").checked,
            inventory: parseInt(document.getElementById("update-inventory").value, 10),
        };

        await fetchJSON(api(`/products/${id}`), { method: "PUT", body: JSON.stringify(payload) });
        showMessage(`Product "${payload.name}" updated successfully!`, "success");

        // Reset the form and allow new ID entry
        document.getElementById("update-form").reset();
        const idField = document.getElementById("product-id-update");
        idField.readOnly = false;
        idField.style.cursor = "text";
        idField.classList.remove("bg-light");

        // Auto-refresh the product list
        await loadList({}, false);
    } catch (error) {
        showMessage(`Error updating product: ${error.message}`, "danger");
    }
});

// LOAD PRODUCT TO UPDATE (helper button to fetch and fill update form)
document.getElementById("load-to-update-btn").addEventListener("click", async () => {
    const idField = document.getElementById("product-id-update");
    const id = idField.value.trim();
    if (!id) {
        showMessage("Please enter a Product ID first", "warning");
        return;
    }

    try {
        const p = await fetchJSON(api(`/products/${id}`));
        document.getElementById("update-name").value = p.name || "";
        document.getElementById("update-price").value = p.price || "";
        document.getElementById("update-description").value = p.description || "";
        document.getElementById("update-image-url").value = p.image_url || "";
        document.getElementById("update-available").checked = p.available || false;
        document.getElementById("update-inventory").value = p.inventory || 0;

        // Make ID field truly readonly after loading
        idField.readOnly = true;
        idField.style.cursor = "not-allowed";
        idField.classList.add("bg-light");

        showMessage(`Product "${p.name}" loaded into form for editing!`, "info");
    } catch (error) {
        showMessage(`Error loading product: ${error.message}`, "danger");
    }
});

// DELETE PRODUCT
document.getElementById("delete-btn").addEventListener("click", async () => {
    const id = document.getElementById("product-id-read").value.trim();
    if (!id) {
        showMessage("Please enter a Product ID", "warning");
        return;
    }

    try {
        await fetchJSON(api(`/products/${id}`));
        
        if (!confirm(`Are you sure you want to delete product ${id}?`)) {
            return;
        }
        
        await fetchJSON(api(`/products/${id}`), { method: "DELETE" });
        showMessage(`Product ${id} deleted successfully!`, "success");
        document.getElementById("product-id-read").value = "";
        document.getElementById("read-product-details").style.display = "none";

        await loadList({}, false);
    } catch (error) {
        let errorMsg = error.message;
        
        if (errorMsg.includes("Product with id")) {
            const match = errorMsg.match(/id '([^']+)'/);
            const productId = match ? match[1] : id;
            errorMsg = `Product with id '${productId}' was not found`;
        } else if (errorMsg.toLowerCase().includes("not found")) {
            errorMsg = `Product with id '${id}' was not found`;
        }
        
        showMessage(errorMsg, "danger");
    }
});

// PURCHASE PRODUCT (Action)
document.getElementById("purchase-btn").addEventListener("click", async () => {
    const id = document.getElementById("purchase-id").value.trim();
    const quantityStr = document.getElementById("purchase-quantity").value.trim();

    if (!id) {
        showMessage("Please enter a Product ID", "warning");
        return;
    }

    const quantity = parseInt(quantityStr, 10);
    if (!Number.isInteger(quantity) || quantity <= 0) {
        showMessage("Quantity must be a positive integer", "warning");
        return;
    }

    try {
        const payload = { quantity: quantity };
        const product = await fetchJSON(
            api(`/products/${id}/purchase`),
            {
                method: "POST",
                body: JSON.stringify(payload),
            }
        );

        showMessage(
            `Successfully purchased ${quantity} unit(s) of ${product.name}`,
            "success"
        );

        await loadList({}, false);
    } catch (error) {
        let errorMsg = error.message || "Error purchasing product";

        if (errorMsg.includes("Insufficient inventory")) {
            errorMsg = "Insufficient inventory";
        } else if (errorMsg.includes("404 Not Found: Product with id")) {
            const match = errorMsg.match(/id '([^']+)'/);
            const productId = match ? match[1] : id;
            errorMsg = `Product with id '${productId}' was not found`;
        }

        showMessage(errorMsg, "danger");
    }
});

// Helper function to load product into edit form from table
window.loadProductToEdit = async function (id) {
    document.getElementById("product-id-update").value = id;
    document.getElementById("load-to-update-btn").click();
    window.scrollTo({ top: document.getElementById("product-id-update").offsetTop - 100, behavior: "smooth" });
};