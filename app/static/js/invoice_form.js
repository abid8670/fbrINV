document.addEventListener('DOMContentLoaded', function () {
    const customerSelect = document.getElementById('customerSelect');
    const buyerBadge = document.getElementById('buyerTypeBadge');
    const buyerDetailsText = document.getElementById('buyerDetailsText');
    const itemsTableBody = document.getElementById('invoiceItemsBody');
    const addRowBtn = document.getElementById('addRowBtn');

    // Summary elements
    const summarySubtotal = document.getElementById('summarySubtotal');
    const summarySalesTax = document.getElementById('summarySalesTax');
    const summaryFurtherTax = document.getElementById('summaryFurtherTax');
    const summaryDiscount = document.getElementById('summaryDiscount');
    const summaryGrandTotal = document.getElementById('summaryGrandTotal');

    let defaultTaxRate = parseFloat(document.getElementById('defaultTaxRate')?.value || 18.0);
    let defaultFurtherRate = parseFloat(document.getElementById('defaultFurtherRate')?.value || 4.0);
    let currentBuyerType = 'Registered';

    // Catalog items cache passed via data attribute or fetched
    let catalogItems = [];
    try {
        const catalogEl = document.getElementById('catalogData');
        if (catalogEl) {
            catalogItems = JSON.parse(catalogEl.textContent);
        }
    } catch (e) {
        console.error('Failed to parse catalog items', e);
    }

    // Customer Selection Listener
    if (customerSelect) {
        customerSelect.addEventListener('change', function () {
            const customerId = this.value;
            if (!customerId) {
                buyerBadge.textContent = 'Select Buyer';
                buyerBadge.className = 'badge bg-secondary';
                buyerDetailsText.textContent = 'Please choose a customer to view tax credentials.';
                currentBuyerType = 'Registered';
                recalculateAll();
                return;
            }

            fetch(`/customers/api/${customerId}`)
                .then(res => res.json())
                .then(data => {
                    currentBuyerType = data.buyer_type;
                    if (data.buyer_type === 'Registered') {
                        buyerBadge.textContent = 'Registered Taxpayer';
                        buyerBadge.className = 'badge bg-success-subtle text-success border border-success-subtle';
                        buyerDetailsText.innerHTML = `<strong>NTN:</strong> ${data.ntn || 'N/A'} &nbsp;|&nbsp; <strong>STRN:</strong> ${data.strn || 'N/A'} &nbsp;|&nbsp; <strong>City:</strong> ${data.city || 'N/A'}`;
                    } else {
                        buyerBadge.textContent = 'Unregistered (4% Further Tax)';
                        buyerBadge.className = 'badge bg-warning-subtle text-warning-emphasis border border-warning-subtle';
                        buyerDetailsText.innerHTML = `<strong>CNIC:</strong> ${data.cnic || 'Not provided'} &nbsp;|&nbsp; <strong>Address:</strong> ${data.address || 'N/A'}`;
                    }
                    recalculateAll();
                })
                .catch(err => console.error('Error fetching customer details:', err));
        });
    }

    // Generate Item Dropdown HTML
    function getItemOptionsHtml(selectedId = '') {
        let options = '<option value="">-- Choose Catalog Item (or type manually) --</option>';
        catalogItems.forEach(item => {
            options += `<option value="${item.id}" ${item.id == selectedId ? 'selected' : ''} data-code="${item.item_code}" data-name="${item.name}" data-hs="${item.hs_code}" data-uom="${item.uom}" data-price="${item.unit_price}" data-rate="${item.sales_tax_rate}">
                [${item.item_code}] ${item.name} (${item.hs_code}) - PKR ${item.unit_price}
            </option>`;
        });
        return options;
    }

    // Add Row function
    function addRow(prefill = null) {
        const rowId = Date.now() + Math.random().toString(36).substring(2, 6);
        const tr = document.createElement('tr');
        tr.className = 'item-row';
        tr.id = `row-${rowId}`;

        tr.innerHTML = `
            <td style="min-width: 200px;">
                <select class="form-select form-select-sm mb-1 item-picker">
                    ${getItemOptionsHtml(prefill ? prefill.item_id : '')}
                </select>
                <input type="hidden" name="item_id[]" class="item-id-input" value="${prefill ? prefill.item_id : ''}">
                <input type="text" name="description[]" class="form-control form-control-sm item-desc-input" placeholder="Item description" value="${prefill ? prefill.description : ''}" required>
            </td>
            <td style="width: 130px;">
                <input type="text" name="hs_code[]" class="form-control form-control-sm font-mono item-hs-input" placeholder="8471.3010" value="${prefill ? prefill.hs_code : '8471.3010'}" required>
            </td>
            <td style="width: 90px;">
                <select name="uom[]" class="form-select form-select-sm font-mono item-uom-input">
                    <option value="NOS">NOS</option>
                    <option value="KG">KG</option>
                    <option value="LTR">LTR</option>
                    <option value="MTR">MTR</option>
                    <option value="PKT">PKT</option>
                    <option value="SET">SET</option>
                    <option value="BAG">BAG</option>
                    <option value="TON">TON</option>
                </select>
            </td>
            <td style="width: 100px;">
                <input type="number" step="any" min="0.01" name="quantity[]" class="form-control form-control-sm text-end item-qty-input" value="${prefill ? prefill.quantity : '1.0'}" required>
            </td>
            <td style="width: 120px;">
                <input type="number" step="0.01" min="0" name="unit_price[]" class="form-control form-control-sm text-end font-mono item-price-input" placeholder="0.00" value="${prefill ? prefill.unit_price : '0.00'}" required>
            </td>
            <td style="width: 130px;" class="text-end font-mono align-middle">
                <span class="row-value-supply">0.00</span>
            </td>
            <td style="width: 100px;">
                <div class="input-group input-group-sm">
                    <input type="number" step="0.01" min="0" name="sales_tax_rate[]" class="form-control form-control-sm text-end item-tax-rate" value="${prefill ? prefill.tax_rate : defaultTaxRate}">
                    <span class="input-group-text p-1">%</span>
                </div>
                <div class="fs-xs text-muted text-end row-tax-amount">PKR 0.00</div>
            </td>
            <td style="width: 100px;">
                <input type="number" step="0.01" min="0" name="discount[]" class="form-control form-control-sm text-end item-discount-input" value="0.00">
            </td>
            <td style="width: 140px;" class="text-end font-mono fw-bold align-middle">
                <span class="row-total-amount">0.00</span>
            </td>
            <td style="width: 50px;" class="text-center align-middle">
                <button type="button" class="btn btn-sm btn-light border text-danger p-1 remove-row-btn" title="Remove row">
                    <i class="bi bi-x-lg"></i>
                </button>
            </td>
        `;

        itemsTableBody.appendChild(tr);

        // Bind events for newly added row
        bindRowEvents(tr);
        calculateRow(tr);
        recalculateTotals();
    }

    function bindRowEvents(tr) {
        const picker = tr.querySelector('.item-picker');
        const descInput = tr.querySelector('.item-desc-input');
        const hsInput = tr.querySelector('.item-hs-input');
        const uomInput = tr.querySelector('.item-uom-input');
        const priceInput = tr.querySelector('.item-price-input');
        const taxRateInput = tr.querySelector('.item-tax-rate');
        const itemIdInput = tr.querySelector('.item-id-input');
        const qtyInput = tr.querySelector('.item-qty-input');
        const discountInput = tr.querySelector('.item-discount-input');
        const removeBtn = tr.querySelector('.remove-row-btn');

        picker.addEventListener('change', function () {
            const selectedOpt = this.options[this.selectedIndex];
            if (this.value) {
                itemIdInput.value = this.value;
                descInput.value = selectedOpt.dataset.name || '';
                hsInput.value = selectedOpt.dataset.hs || '8471.3010';
                uomInput.value = selectedOpt.dataset.uom || 'NOS';
                priceInput.value = selectedOpt.dataset.price || '0.00';
                taxRateInput.value = selectedOpt.dataset.rate || defaultTaxRate;
            } else {
                itemIdInput.value = '';
            }
            calculateRow(tr);
            recalculateTotals();
        });

        [qtyInput, priceInput, taxRateInput, discountInput].forEach(inp => {
            inp.addEventListener('input', function () {
                calculateRow(tr);
                recalculateTotals();
            });
        });

        removeBtn.addEventListener('click', function () {
            if (document.querySelectorAll('.item-row').length > 1) {
                tr.remove();
                recalculateTotals();
            } else {
                alert('An invoice must have at least one line item.');
            }
        });
    }

    function calculateRow(tr) {
        const qty = parseFloat(tr.querySelector('.item-qty-input').value) || 0;
        const price = parseFloat(tr.querySelector('.item-price-input').value) || 0;
        const taxRate = parseFloat(tr.querySelector('.item-tax-rate').value) || 0;
        const discount = parseFloat(tr.querySelector('.item-discount-input').value) || 0;

        const valOfSupply = qty * price;
        const salesTaxAmt = valOfSupply * (taxRate / 100.0);
        
        // 4% further tax if unregistered buyer
        const furtherRate = currentBuyerType === 'Unregistered' ? defaultFurtherRate : 0.0;
        const furtherTaxAmt = valOfSupply * (furtherRate / 100.0);

        const netTotal = valOfSupply + salesTaxAmt + furtherTaxAmt - discount;

        tr.querySelector('.row-value-supply').textContent = valOfSupply.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        tr.querySelector('.row-tax-amount').textContent = `Tax: PKR ${salesTaxAmt.toFixed(2)}`;
        tr.querySelector('.row-total-amount').textContent = netTotal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

        tr.dataset.valSupply = valOfSupply;
        tr.dataset.taxAmt = salesTaxAmt;
        tr.dataset.furtherAmt = furtherTaxAmt;
        tr.dataset.discount = discount;
        tr.dataset.grandAmt = netTotal;
    }

    function recalculateAll() {
        document.querySelectorAll('.item-row').forEach(row => {
            calculateRow(row);
        });
        recalculateTotals();
    }

    function recalculateTotals() {
        let totalValSupply = 0;
        let totalSalesTax = 0;
        let totalFurtherTax = 0;
        let totalDiscount = 0;
        let grandTotal = 0;

        document.querySelectorAll('.item-row').forEach(row => {
            totalValSupply += parseFloat(row.dataset.valSupply || 0);
            totalSalesTax += parseFloat(row.dataset.taxAmt || 0);
            totalFurtherTax += parseFloat(row.dataset.furtherAmt || 0);
            totalDiscount += parseFloat(row.dataset.discount || 0);
            grandTotal += parseFloat(row.dataset.grandAmt || 0);
        });

        summarySubtotal.textContent = `PKR ${totalValSupply.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        summarySalesTax.textContent = `PKR ${totalSalesTax.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        summaryFurtherTax.textContent = `PKR ${totalFurtherTax.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        summaryDiscount.textContent = `- PKR ${totalDiscount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        summaryGrandTotal.textContent = `PKR ${grandTotal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }

    if (addRowBtn) {
        addRowBtn.addEventListener('click', function () {
            addRow();
        });
    }

    // Initialize first row
    if (itemsTableBody && itemsTableBody.children.length === 0) {
        addRow();
    }

    // Trigger customer select once if already pre-selected
    if (customerSelect && customerSelect.value) {
        customerSelect.dispatchEvent(new Event('change'));
    }
});
