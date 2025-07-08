// pos.js

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
  cart[index].qty = parseFloat(value);
  renderCart();
}

// Update discount
function updateDiscount(index, value) {
  cart[index].discount = parseFloat(value);
  renderCart();
}

// Render the cart to table
function renderCart() {
  const tbody = document.getElementById('cart-body');
  const input = document.getElementById('cart-input');
  const totalEl = document.getElementById('cart-total');

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
          <input type="number" class="form-control form-control-sm" min="0" value="${disc}" onchange="updateDiscount(${i}, this.value)">
        </td>
        <td>${lineTotal.toFixed(2)}</td>
        <td><button class="btn btn-sm btn-danger" onclick="removeFromCart(${i})">×</button></td>
      </tr>
    `;
  });

  totalEl.innerText = grand.toFixed(2);
  input.value = JSON.stringify(cart);
}

// Live search for products
function searchProducts(term) {
  fetch(`/api/products/?q=${encodeURIComponent(term)}`)
    .then(res => res.json())
    .then(data => {
      const list = document.getElementById('search-results');
      list.innerHTML = '';

      data.forEach(product => {
        const div = document.createElement('div');
        div.className = 'product-result';
        div.textContent = `${product.name} – ${product.price} PKR`;
        div.onclick = () => addToCart({
          product_id: product.id,
          name: product.name,
          price: parseFloat(product.price),
          discount: 0
        });
        list.appendChild(div);
      });
    });
}

// Attach search input handler
document.addEventListener('DOMContentLoaded', () => {
  const searchBox = document.getElementById('product-search');
  if (searchBox) {
    searchBox.addEventListener('input', () => {
      const term = searchBox.value.trim();
      if (term.length >= 2) searchProducts(term);
    });
  }

  // Set Receipt ID if it wasn’t set in template
  const now = new Date();
  const receiptId = now.toISOString().slice(0,19).replace(/[-T:]/g, '');
  const receiptSpan = document.getElementById('receipt-id');
  const receiptInput = document.getElementById('receipt-id-input');
  if (receiptSpan) receiptSpan.textContent = `Receipt ID: ${receiptId}`;
  if (receiptInput) receiptInput.value = receiptId;
});