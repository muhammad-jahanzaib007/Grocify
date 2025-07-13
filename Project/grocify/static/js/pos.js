let cart = [];

// Add product to cart
function addToCart(product) {
  const existing = cart.find(item => item.product_id === product.product_id);
  if (existing) {
    existing.qty += 1;
  } else {
    // Defensive check before adding
    if (isNaN(product.price) || product.price <= 0) {
      alert(`🚫 Price is invalid for ${product.name}. Cannot add to cart.`);
      return;
    }
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
  let qty = parseFloat(value);
  if (isNaN(qty) || qty <= 0) {
    qty = 1;
  }
  cart[index].qty = qty;
  renderCart();
}

// Update discount
function updateDiscount(index, value) {
  let disc = parseFloat(value);
  if (isNaN(disc) || disc < 0) {
    disc = 0;
  }
  cart[index].discount = disc;
  renderCart();
}

// Render cart table
function renderCart() {
  const tbody = document.getElementById('cart-body');
  const cartInput = document.getElementById('cart-input');
  const totalEl = document.getElementById('cart-total');
  const paidInput = document.querySelector('input[name="amount_paid"]');
  const pointsInput = document.querySelector('input[name="points_used"]');
  const changeBox = document.getElementById('change-due');
  const customerSelect = document.getElementById('customer-select');

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

  const selectedId = customerSelect?.value;
  const maxPoints = customerPoints[selectedId] || 0;
  const pointsUsed = Math.min(parseInt(pointsInput?.value || 0), maxPoints, grand);
  if (pointsInput) pointsInput.value = pointsUsed;

  const totalAfterPoints = grand - pointsUsed;

  if (paidInput && changeBox) {
    const paidAmount = parseFloat(paidInput.value) || 0;
    const changeDue = paidAmount - totalAfterPoints;
    changeBox.value = changeDue >= 0 ? changeDue.toFixed(2) : '0.00';
  }
}

// Product search
function searchProducts(term) {
  fetch(`/api/products/?q=${encodeURIComponent(term)}`)
    .then(res => res.json())
    .then(data => {
      const list = document.getElementById('search-results');
      list.innerHTML = '';

      if (data.length === 1 && term.length >= 4) {
        const p = data[0];
        const priceValue = Number(p.price); // ✅ expects 'price' field from backend
        if (!isNaN(priceValue) && priceValue > 0) {
          addToCart({
            product_id: p.id,
            name: p.name,
            price: priceValue,
            discount: 0
          });
          document.getElementById('product-search').value = '';
          document.getElementById('product-search').focus();
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

// DOM Ready
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

  document.querySelector('input[name="amount_paid"]')?.addEventListener('input', renderCart);
  document.querySelector('input[name="points_used"]')?.addEventListener('input', renderCart);

  const customerSelect = document.getElementById('customer-select');
  const pointsPreview = document.getElementById('customer-points-preview');
  if (customerSelect && pointsPreview) {
    customerSelect.addEventListener('change', () => {
      const selectedId = customerSelect.value;
      const points = customerPoints[selectedId] || 0;
      pointsPreview.textContent = selectedId ? `Points Available: ${points}` : 'Points Available: —';
      renderCart();
    });
  }

  // 💡 Optional: Cart sanity check before form submit
  document.getElementById('pos-form')?.addEventListener('submit', e => {
    const hasInvalid = cart.some(item => item.qty <= 0 || item.price <= 0);
    if (hasInvalid) {
      e.preventDefault();
      alert("🚫 Cart contains invalid items. Please check price and quantity.");
    }
  });
});
/* Analytics integration and POS UI enhancement */
/* Add this snippet to enable analytics tracking for completed sales */

function sendAnalyticsEvent(eventName, eventData) {
    fetch('/api/analytics/event/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event: eventName, data: eventData })
    })
    .then(response => response.json())
    .then(data => console.log('Analytics event sent:', data))
    .catch(error => console.error('Error sending analytics event:', error));
}

// Enhance the POS sale completion: If a completeSale function exists, wrap it to include analytics tracking.
if (typeof completeSale === 'function') {
    var originalCompleteSale = completeSale;
    completeSale = function() {
        originalCompleteSale.apply(this, arguments);
        // Capture sale value from a UI element (e.g., an element with id "sale-amount")
        var saleValue = document.getElementById('sale-amount') ? parseFloat(document.getElementById('sale-amount').innerText) : 0;
        sendAnalyticsEvent('sale_completed', { amount: saleValue });
    };
} else {
    // Alternatively, attach an event listener to a button with id "complete-sale" if completeSale is not defined.
    var completeSaleButton = document.getElementById('complete-sale');
    if (completeSaleButton) {
        completeSaleButton.addEventListener('click', function() {
            // You can include POS sale completion logic here if needed.
            var saleValue = document.getElementById('sale-amount') ? parseFloat(document.getElementById('sale-amount').innerText) : 0;
            sendAnalyticsEvent('sale_completed', { amount: saleValue });
        });
    }
}