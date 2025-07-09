let cart = [];

// Add product to cart
function addToCart(product) {
  const existing = cart.find(item => item.product_id === product.product_id);
  if (existing) {
    existing.qty += 1;
  } else {
    cart.push({ ...product, qty: 1, discount: 0 });
  }
  renderCart();
}

// Remove item from cart
function removeFromCart(index) {
  cart.splice(index, 1);
  renderCart();
}

// Update quantity
function updateQuantity(index, value) {
  const qty = Math.max(1, parseFloat(value));
  cart[index].qty = qty;
  renderCart();
}

// Update discount
function updateDiscount(index, value) {
  const disc = Math.max(0, parseFloat(value));
  cart[index].discount = disc;
  renderCart();
}

// Render cart table
function renderCart() {
  const tbody = document.getElementById('cart-body');
  const cartInput = document.getElementById('cart-input');
  const totalEl = document.getElementById('cart-total');
  const paidInput = document.querySelector('input[name="amount_paid"]');
  const changeBox = document.getElementById('change-due');

  tbody.innerHTML = '';
  let grand = 0;

  cart.forEach((item, i) => {
    const disc = item.discount || 0;
    const lineTotal = (item.price - disc) * item.qty;
    grand += lineTotal;

    tbody.innerHTML += `
      <tr>
        <td>${item.name}</td>
        <td>
          <input type="number" class="form-control form-control-sm" min="1" value="${item.qty}" onchange="updateQuantity(${i}, this.value)">
        </td>
        <td>${item.price.toFixed(2)}</td>
        <td>
          <input type="number" class="form-control form-control-sm" min="0" value="${disc.toFixed(2)}" onchange="updateDiscount(${i}, this.value)">
        </td>
        <td>${lineTotal.toFixed(2)}</td>
        <td><button class="btn btn-sm btn-danger" onclick="removeFromCart(${i})">×</button></td>
      </tr>
    `;
  });

  totalEl.innerText = grand.toFixed(2);
  cartInput.value = JSON.stringify(cart);

  // Calculate change due
  if (paidInput && changeBox) {
    const paidAmount = parseFloat(paidInput.value) || 0;
    const changeDue = paidAmount - grand;
    changeBox.value = changeDue >= 0 ? changeDue.toFixed(2) : '0.00';
  }
}

// Fetch products matching search term
function searchProducts(term) {
  fetch(`/api/products/?q=${encodeURIComponent(term)}`)
    .then(res => res.json())
    .then(data => {
      const list = document.getElementById('search-results');
      list.innerHTML = '';

      if (data.length === 1 && term.length >= 4) {
        const p = data[0];
        const priceValue = Number(p.price);
        if (!isNaN(priceValue) && priceValue > 0) {
          addToCart({
            product_id: p.id,
            name: p.name,
            price: priceValue,
            discount: 0
          });

          const searchBox = document.getElementById('product-search');
          searchBox.value = '';
          searchBox.focus();
        }
        return;
      }

      data.forEach(product => {
        const priceValue = Number(product.price);
        if (isNaN(priceValue) || priceValue <= 0) return;

        const div = document.createElement('div');
        div.className = 'product-result';
        div.textContent = `${product.name} – ${priceValue.toFixed(2)} PKR`;
        div.onclick = () => {
          addToCart({
            product_id: product.id,
            name: product.name,
            price: priceValue,
            discount: 0
          });
          document.getElementById('product-search').value = '';
          document.getElementById('product-search').focus();
          list.innerHTML = '';
        };
        list.appendChild(div);
      });
    })
    .catch(err => {
      console.error("🔴 Product search error:", err);
    });
}

// DOM Ready Setup
document.addEventListener('DOMContentLoaded', () => {
  const searchBox = document.getElementById('product-search');
  if (searchBox) {
    searchBox.addEventListener('input', () => {
      const term = searchBox.value.trim();
      if (term.length >= 2) searchProducts(term);
    });

    searchBox.addEventListener('keydown', e => {
      if (e.key === 'Enter') {
        e.preventDefault();
        const term = searchBox.value.trim();
        if (term.length >= 2) searchProducts(term);
      }
    });
  }

  const paidInput = document.querySelector('input[name="amount_paid"]');
  if (paidInput) {
    paidInput.addEventListener('input', () => renderCart());
  }

  const now = new Date();
  const receiptId = now.toISOString().slice(0, 19).replace(/[-T:]/g, '');
  const receiptSpan = document.getElementById('receipt-id');
  const receiptInput = document.getElementById('receipt-id-input');

  if (receiptSpan) receiptSpan.textContent = `Receipt ID: ${receiptId}`;
  if (receiptInput) receiptInput.value = receiptId;
});
const customerSelect = document.getElementById('customer-select');
const pointsPreview = document.getElementById('customer-points-preview');

if (customerSelect && pointsPreview) {
  customerSelect.addEventListener('change', () => {
    const selectedId = customerSelect.value;
    const points = customerPoints[selectedId] || 0;
    pointsPreview.textContent = selectedId ? `Points Available: ${points}` : 'Points Available: —';
  });
}
