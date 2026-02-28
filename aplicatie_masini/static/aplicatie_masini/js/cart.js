const CART_STORAGE_KEY = 'virtual_cart';

function initCart() {
    const cart = localStorage.getItem(CART_STORAGE_KEY);
    return cart ? JSON.parse(cart) : {};
}

function saveCart(cart) {
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(cart));
}

function getCart() {
    return initCart();
}

function addToCart(productId, price, productName, maxStock) {
    let quantity = 1;

    const quantityInput = document.getElementById(`qty-${productId}`);
    if (quantityInput) {
        quantity = parseInt(quantityInput.value) || 1;
    }

    if (quantity > maxStock) {
        alert(`⚠️ Nu puteți adăuga mai mult decât stocul disponibil (${maxStock} unități)`);
        return;
    }
    
    if (quantity <= 0) {
        alert('Cantitatea trebuie să fie mai mare decât 0');
        return;
    }
    
    const cart = getCart();
    
    if (!cart[productId]) {
        cart[productId] = {
            name: productName,
            price: price,
            quantity: quantity,
            maxStock: maxStock 
        };
    } else {
        const newQuantity = cart[productId].quantity + quantity;
        if (newQuantity > maxStock) {
            alert(`⚠️ Nu puteți adăuga mai mult decât stocul disponibil (${maxStock} unități). Deja aveți ${cart[productId].quantity} articole în coș.`);
            return;
        }
        cart[productId].quantity = newQuantity;
    }
    
    saveCart(cart);
    updateCartUI();

    if (quantityInput) {
        quantityInput.value = 1;
    }

    showNotification(`✓ ${productName} adăugat în coș!`);
}

function removeFromCart(productId) {
    const cart = getCart();
    if (cart[productId]) {
        const productName = cart[productId].name;
        delete cart[productId];
        saveCart(cart);
        updateCartUI();
        showNotification(`✓ ${productName} șters din coș!`);
    }
}

function setCartQuantity(productId, quantity) {
    const cart = getCart();
    
    if (!cart[productId]) {
        return;
    }
    
    const maxStock = cart[productId].maxStock;
    
    if (quantity > maxStock) {
        alert(`⚠️ Nu puteți adăuga mai mult decât stocul disponibil (${maxStock} unități)`);
        return;
    }
    
    if (quantity <= 0) {
        removeFromCart(productId);
        return;
    }
    
    cart[productId].quantity = quantity;
    saveCart(cart);
    updateCartUI();
}

function incrementQuantity(productId, maxStock = null) {
    const quantityInput = document.getElementById(`qty-${productId}`);
    let currentValue = parseInt(quantityInput.value) || 1;
    
    const limit = maxStock || parseInt(quantityInput.max);
    
    if (currentValue < limit) {
        quantityInput.value = currentValue + 1;
    } else {
        alert(`⚠️ Nu puteți adăuga mai mult decât stocul disponibil (${limit} unități)`);
    }
}

function decrementQuantity(productId) {
    const quantityInput = document.getElementById(`qty-${productId}`);
    let currentValue = parseInt(quantityInput.value) || 1;
    
    if (currentValue > 1) {
        quantityInput.value = currentValue - 1;
    }
}

function validateQuantity(productId, maxStock) {
    const quantityInput = document.getElementById(`qty-${productId}`);
    let value = parseInt(quantityInput.value) || 1;
    
    if (value > maxStock) {
        alert(`⚠️ Nu puteți adăuga mai mult decât stocul disponibil (${maxStock} unități)`);
        quantityInput.value = maxStock;
    } else if (value < 1) {
        quantityInput.value = 1;
    }
    
    const cart = getCart();
    if (cart[productId]) {
        setCartQuantity(productId, value);
    }
}

function updateCartUI() {
    const cart = getCart();

    document.querySelectorAll('[data-product-id]').forEach(card => {
        const productId = parseInt(card.dataset.productId);
        const inCartMarker = card.querySelector('.in-cos-marker');
        const addButton = card.querySelector('.btn-add-to-cart');
        const removeButton = card.querySelector('.btn-remove');
        const removeButtonDetail = card.querySelector('.btn-remove-detail');
        
        if (cart[productId]) {
            if (inCartMarker) {
                inCartMarker.style.display = 'block';
            }
            if (addButton) {
                addButton.style.display = 'none';
            }
            if (removeButton) {
                removeButton.style.display = 'inline-block';
            }
            if (removeButtonDetail) {
                removeButtonDetail.style.display = 'inline-block';
            }

            const qtyInput = card.querySelector(`#qty-${productId}`);
            if (qtyInput) {
                qtyInput.value = cart[productId].quantity;
            }
        } else {
            if (inCartMarker) {
                inCartMarker.style.display = 'none';
            }
            if (addButton) {
                addButton.style.display = 'inline-block';
            }
            if (removeButton) {
                removeButton.style.display = 'none';
            }
            if (removeButtonDetail) {
                removeButtonDetail.style.display = 'none';
            }

            const qtyInput = card.querySelector(`#qty-${productId}`);
            if (qtyInput) {
                qtyInput.value = 1;
            }
        }
    });
}

function showNotification(message) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background-color: #4CAF50;
        color: white;
        padding: 16px;
        border-radius: 4px;
        z-index: 10000;
        animation: slideIn 0.3s ease-out;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
if (!document.querySelector('style[data-cart-animations]')) {
    style.setAttribute('data-cart-animations', 'true');
    document.head.appendChild(style);
}
