// ============================================
// MASTER COSTS PAGE JAVASCRIPT
// ============================================

// Load data from JSON script tag (avoids linting errors with Jinja2)
const dataScript = document.getElementById('master-costs-data');
const masterCostsData = dataScript ? JSON.parse(dataScript.textContent) : {
    fabricVendors: [],
    notionVendors: []
};

// Make it globally accessible
window.masterCostsData = masterCostsData;

// Global variables
let currentEditType = '';
let currentEditId = null;

// Get vendor options from injected data
const fabricVendorOptions = masterCostsData.fabricVendors
    .map(v => `<option value="${v.id}">${v.name}</option>`)
    .join('');

const notionVendorOptions = masterCostsData.notionVendors
    .map(v => `<option value="${v.id}">${v.name}</option>`)
    .join('');

// ============================================
// MODAL FUNCTIONS
// ============================================

function openModal(type, id = null) {
    currentEditType = type;
    currentEditId = id;
    
    const modal = document.getElementById('modal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    modal.classList.add('active');
    modal.setAttribute('data-type', type);
    modal.style.display = 'flex';
    
    modalTitle.textContent = id ? 'Edit ' + capitalize(type.replace('_', ' ')) : 'Add ' + capitalize(type.replace('_', ' '));
    
    let formHtml = '';
    
    if (type === 'fabric_vendor') {
        formHtml = `
            <div class="form-group">
                <label>Vendor Name *</label>
                <input type="text" id="name" required placeholder="e.g., CARR TEXTILES">
            </div>
            <div class="form-group">
                <label>Vendor Code *</label>
                <input type="text" id="vendor_code" required placeholder="e.g., F101">
            </div>
        `;
    } else if (type === 'notion_vendor') {
        formHtml = `
            <div class="form-group">
                <label>Vendor Name *</label>
                <input type="text" id="name" required placeholder="e.g., WAWAK">
            </div>
            <div class="form-group">
                <label>Vendor Code *</label>
                <input type="text" id="vendor_code" required placeholder="e.g., N101">
            </div>
        `;
    } else if (type === 'fabric') {
        formHtml = `
            <div class="form-group">
                <label>Fabric Name *</label>
                <input type="text" id="name" required placeholder="e.g., XANADU">
            </div>
            <div class="form-group">
                <label>Fabric Code *</label>
                <input type="text" id="fabric_code" placeholder="e.g., F1">
            </div>
            <div class="form-group">
                <label>Cost per Yard *</label>
                <input type="number" id="cost_per_yard" step="0.01" min="0" required placeholder="e.g., 6.00">
            </div>
            <div class="form-group">
                <label>Vendor *</label>
                <select id="fabric_vendor_id" required>
                    <option value="">Select Vendor</option>
                    ${fabricVendorOptions}
                </select>
            </div>
        `;
    } else if (type === 'notion') {
        formHtml = `
            <div class="form-group">
                <label>Notion Name *</label>
                <input type="text" id="name" required placeholder="e.g., 18L SPORT BUTTON">
            </div>
            <div class="form-group">
                <label>Cost per Unit *</label>
                <input type="number" id="cost_per_unit" step="0.0001" min="0" required placeholder="e.g., 0.04">

            </div>
            <div class="form-group">
                <label>Unit Type *</label>
                <select id="unit_type" required>
                    <option value="each">each</option>
                    <option value="yard">yard</option>
                    <option value="set">set</option>
                </select>
            </div>
            <div class="form-group">
                <label>Vendor *</label>
                <select id="notion_vendor_id" required>
                    <option value="">Select Vendor</option>
                    ${notionVendorOptions}
                </select>
            </div>
        `;
    } else if (type === 'labor') {
        formHtml = `
            <div class="form-group">
                <label>Operation Name *</label>
                <input type="text" id="name" required placeholder="e.g., Sewing">
            </div>
            <div class="form-group">
                <label>Cost Type *</label>
                <select id="cost_type" required onchange="updateLaborFields()">
                    <option value="flat_rate">Flat Rate</option>
                    <option value="hourly">Hourly</option>
                    <option value="per_piece">Per Piece</option>
                </select>
            </div>
            <div class="form-group" id="flat_rate_group">
                <label>Fixed Cost</label>
                <input type="number" id="fixed_cost" step="0.01" placeholder="e.g., 1.50">
            </div>
            <div class="form-group" id="hourly_group" style="display:none;">
                <label>Cost per Hour</label>
                <input type="number" id="cost_per_hour" step="0.01" placeholder="e.g., 19.32">
            </div>
            <div class="form-group" id="per_piece_group" style="display:none;">
                <label>Cost per Piece</label>
                <input type="number" id="cost_per_piece" step="0.01" placeholder="e.g., 0.15">
            </div>
        `;
    } else if (type === 'cleaning') {
        formHtml = `
            <div class="form-group">
                <label>Garment Type *</label>
                <input type="text" id="garment_type" required placeholder="e.g., SS TOP/SS DRESS" style="text-transform: uppercase;">
                <small style="color: #666;">Enter any garment type description</small>
            </div>
            <div class="form-group">
                <label>Average Minutes *</label>
                <input type="number" id="avg_minutes" required placeholder="e.g., 5">
                <small style="color: #666;">Based on $0.32/minute</small>
            </div>
            <div class="form-group">
                <label>Fixed Cost *</label>
                <input type="number" id="fixed_cost" step="0.01" required placeholder="e.g., 1.60">
                <small style="color: #666;">Will be calculated: Minutes × $0.32</small>
            </div>
        `;
    } else if (type === 'color') {
        formHtml = '<div class="form-group"><label>Color Name *</label><input type="text" id="name" required placeholder="e.g., ADMIRAL BLUE" style="text-transform: uppercase;"></div>';
    } else if (type === 'variable') {
        formHtml = '<div class="form-group"><label>Variable Name *</label><input type="text" id="name" required placeholder="e.g., TALL" style="text-transform: uppercase;"></div>';
    } else if (type === 'size_range') {
        formHtml = `
            <div class="form-group">
                <label>Size Range Name * (e.g., XS-6XL, 00-30)</label>
                <input type="text" id="name" required placeholder="e.g., XS-6XL" style="text-transform: uppercase;">
            </div>
            <div class="form-group">
                <label>Regular Sizes * (e.g., XS-XL, 00-18)</label>
                <input type="text" id="regular_sizes" required placeholder="e.g., XS-XL">
            </div>
            <div class="form-group">
                <label>Extended Sizes (e.g., 2XL-6XL, 20-30)</label>
                <input type="text" id="extended_sizes" placeholder="e.g., 2XL-6XL">
            </div>
            <div class="form-group">
                <label>Extended Markup % *</label>
                <input type="number" id="extended_markup_percent" required value="15" step="0.1" min="0" max="100">
            </div>
            <div class="form-group">
                <label>Description (optional)</label>
                <textarea id="description" rows="2" placeholder="Notes about this size range"></textarea>
            </div>
        `;
    } else if (type === 'global_setting') {
        formHtml = `
            <div class="form-group">
                <label>Setting Value *</label>
                <input type="number" id="setting_value" required step="0.01">
            </div>
            <div class="form-group">
                <label>Description</label>
                <textarea id="description" rows="2"></textarea>
            </div>
        `;
    }
    
    modalBody.innerHTML = formHtml;
    
    if (id) {
        loadItemData(type, id);
    } else {
        // AUTO-POPULATE SEQUENTIAL CODES FOR NEW ITEMS
        autoPopulateNextCode(type);
    }
    
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
}
// AUTO-POPULATE SEQUENTIAL CODES
// ============================================

function autoPopulateNextCode(type) {
    if (type === 'fabric_vendor') {
        const codes = [];
        document.querySelectorAll('button[data-type="fabric_vendor"].icon-edit').forEach(btn => {
            const row = btn.closest('tr');
            if (row) {
                const codeCell = row.querySelector('td:nth-child(2)');
                if (codeCell) codes.push(codeCell.textContent.trim());
            }
        });
        const nextCode = getNextSequentialCode(codes, 'F', 101);
        const input = document.getElementById('vendor_code');
        if (input) input.value = nextCode;
        
    } else if (type === 'notion_vendor') {
        const codes = [];
        document.querySelectorAll('button[data-type="notion_vendor"].icon-edit').forEach(btn => {
            const row = btn.closest('tr');
            if (row) {
                const codeCell = row.querySelector('td:nth-child(2)');
                if (codeCell) codes.push(codeCell.textContent.trim());
            }
        });
        const nextCode = getNextSequentialCode(codes, 'N', 101);
        const input = document.getElementById('vendor_code');
        if (input) input.value = nextCode;
        
    } else if (type === 'fabric') {
        const codes = [];
        document.querySelectorAll('#fabricTable tr').forEach(row => {
            const codeCell = row.querySelector('td:nth-child(2)');
            if (codeCell) codes.push(codeCell.textContent.trim());
        });
        const nextCode = getNextSequentialCode(codes, 'F', 1);
        const input = document.getElementById('fabric_code');
        if (input) input.value = nextCode;
    }
}

function getNextSequentialCode(codes, prefix, startNum) {
    let maxNum = startNum - 1;
    
    codes.forEach(code => {
        if (code && code.toUpperCase().startsWith(prefix.toUpperCase())) {
            const numPart = code.substring(prefix.length);
            const num = parseInt(numPart, 10);
            if (!isNaN(num) && num > maxNum) {
                maxNum = num;
            }
        }
    });
    
    return prefix + (maxNum + 1);
}

function closeModal() {
    const modal = document.getElementById('modal');
    modal.classList.remove('active');
    modal.style.display = 'none';
    currentEditType = '';
    currentEditId = null;
}

function saveModal() {
    const formData = {};
    const modalBody = document.getElementById('modalBody');
    const inputs = modalBody.querySelectorAll('input, select, textarea');
    
    let valid = true;
    inputs.forEach(input => {
        if (input.required && !input.value) {
            input.style.borderColor = '#EF4444';
            valid = false;
        } else {
            input.style.borderColor = '';
            formData[input.id] = input.value;
        }
    });
    
    if (!valid) {
        showNotification('Please fill in all required fields', 'error');
        return;
    }
    // Validate numeric fields are positive
    const numericFields = modalBody.querySelectorAll('input[type="number"]');
    numericFields.forEach(input => {
        if (input.value && parseFloat(input.value) < 0) {
            input.style.borderColor = '#EF4444';
            valid = false;
        }
    });

    if (!valid) {
        showNotification('Cost values cannot be negative', 'error');
        return;
    }

    
    const endpoint = currentEditType.replace(/_/g, '-');
    const method = currentEditId ? 'PUT' : 'POST';
    const url = currentEditId 
        ? `/api/${endpoint}s/${currentEditId}`
        : `/api/${endpoint}s`;
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Saved successfully!', 'success');
            closeModal();
            setTimeout(() => location.reload(), 1500);
        } else {
            showNotification('Save failed: ' + (data.error || 'Unknown error'), 'error');
        }
    })
    .catch(error => {
        showNotification('Save failed: ' + error.message, 'error');
    });
}

function loadItemData(type, id) {
    const endpoint = type.replace(/_/g, '-');
    
    fetch(`/api/${endpoint}s/${id}`)
        .then(response => response.json())
        .then(data => {
            Object.keys(data).forEach(key => {
                const input = document.getElementById(key);
                if (input) {
                    input.value = data[key] || '';
                }
            });
            
            if (type === 'labor') {
                updateLaborFields();
            }
        })
        .catch(error => {
            console.error('Error loading data:', error);
            showNotification('Error loading data', 'error');
        });
}

function deleteItem(endpoint, id) {
    const url = `/api/${endpoint}s/${id}`;
    
    fetch(url, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Deleted successfully!', 'success');
            setTimeout(() => location.reload(), 1500);
        } else {
            // Check if styles_using is provided for clickable links
            if (data.styles_using && data.styles_using.length > 0) {
                const styleLinks = data.styles_using.map(s => 
                    `<a href="/style/view?vendor_style=${encodeURIComponent(s.vendor_style)}" target="_blank" style="color: white; text-decoration: underline; font-weight: bold;">${s.vendor_style || s.style_name}</a>`
                ).join(', ');
                const message = `Delete failed: Used in ${data.styles_using.length} style(s): ${styleLinks}`;
                showNotification(message, 'error', true);
            } else {
                showNotification('Delete failed: ' + (data.error || 'Unknown error'), 'error');
            }
        }
    })
    .catch(error => {
        showNotification('Delete failed: ' + error.message, 'error');
    });
}

// ============================================
// CUSTOM CONFIRMATION MODAL INTEGRATION
// ============================================

function showDeleteConfirmation(message, onConfirm, onCancel) {
    // Smart title detection from message
    let title = 'Confirm Action';
    const msgLower = message.toLowerCase();
    
    if (msgLower.includes('notion vendor')) {
        title = 'Delete Notion Vendor?';
    } else if (msgLower.includes('fabric vendor')) {
        title = 'Delete Fabric Vendor?';
    } else if (msgLower.includes('fabric')) {
        title = 'Delete Fabric?';
    } else if (msgLower.includes('notion')) {
        title = 'Delete Notion?';
    } else if (msgLower.includes('labor')) {
        title = 'Delete Labor Cost?';
    } else if (msgLower.includes('cleaning')) {
        title = 'Delete Cleaning Cost?';
    } else if (msgLower.includes('delete')) {
        const match = message.match(/Delete[^?]*/i);
        title = match ? match[0] + '?' : 'Confirm Delete';
    }
    
    // Use new beautiful modal
    confirmDelete({
        title: title,
        message: message,
        onConfirm: onConfirm
    });
}

function showNotification(message, type = 'success', isHtml = false) {
    const notification = document.getElementById('notification');
    const notificationText = document.getElementById('notificationText');
    
    if (notification && notificationText) {
        if (isHtml) {
            notificationText.innerHTML = message;
        } else {
            notificationText.textContent = message;
        }
        notification.classList.remove('error');
        if (type === 'error') {
            notification.classList.add('error');
        }
        notification.classList.add('show');

        // Longer timeout for error messages with links
        const timeout = (type === 'error' && isHtml) ? 10000 : 3000;
        setTimeout(() => {
            notification.classList.remove('show');
        }, timeout);
    }
}
function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function updateLaborFields() {
    const costType = document.getElementById('cost_type')?.value;
    
    document.getElementById('flat_rate_group').style.display = costType === 'flat_rate' ? 'block' : 'none';
    document.getElementById('hourly_group').style.display = costType === 'hourly' ? 'block' : 'none';
    document.getElementById('per_piece_group').style.display = costType === 'per_piece' ? 'block' : 'none';
}

// ============================================
// TABLE FILTER SETUP
// ============================================

function setupTableFilter(searchInputId, rowClass, countElementId) {
    const searchInput = document.getElementById(searchInputId);
    if (!searchInput) return;
    
    const updateCount = () => {
        const rows = document.querySelectorAll('.' + rowClass);
        const visible = Array.from(rows).filter(row => row.style.display !== 'none').length;
        const countEl = document.getElementById(countElementId);
        if (countEl) countEl.textContent = 'Showing ' + visible + ' of ' + rows.length;
    };
    
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const rows = document.querySelectorAll('.' + rowClass);
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(searchTerm) ? '' : 'none';
        });
        
        updateCount();
    });
    
    updateCount();
}

// ============================================
// EVENT DELEGATION FOR BUTTONS
// ============================================

// Handle all "Add" buttons
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('btn-add-modal') || e.target.closest('.btn-add-modal') || 
        e.target.classList.contains('btn-add') || e.target.closest('.btn-add')) {
        const button = e.target.classList.contains('btn-add-modal') || e.target.classList.contains('btn-add') 
            ? e.target 
            : e.target.closest('.btn-add-modal') || e.target.closest('.btn-add');
        const type = button.dataset.type;
        openModal(type);
    }
});

// Handle all "Edit" buttons
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('btn-edit') || e.target.closest('.btn-edit') ||
        e.target.classList.contains('icon-edit') || e.target.closest('.icon-edit')) {
        const button = e.target.classList.contains('btn-edit') || e.target.classList.contains('icon-edit')
            ? e.target 
            : e.target.closest('.btn-edit') || e.target.closest('.icon-edit');
        const type = button.dataset.type;
        const id = button.dataset.id;
        openModal(type, id);
    }
});

// Handle all "Delete" buttons - FIXED VERSION
document.addEventListener('click', function(e) {
    // Prevent event from bubbling
    if (e.target.classList.contains('btn-delete') || e.target.closest('.btn-delete') ||
        e.target.classList.contains('icon-delete') || e.target.closest('.icon-delete')) {
        
        e.preventDefault();
        e.stopPropagation();
        
        const button = e.target.classList.contains('btn-delete') || e.target.classList.contains('icon-delete')
            ? e.target 
            : e.target.closest('.btn-delete') || e.target.closest('.icon-delete');
        const type = button.dataset.type;
        const id = button.dataset.id;
        
        const typeMap = {
            'fabric_vendor': 'fabric vendor',
            'notion_vendor': 'notion vendor',
            'fabric': 'fabric',
            'notion': 'notion',
            'labor': 'labor operation',
            'cleaning': 'cleaning cost',
            'color': 'color',
            'variable': 'variable',
            'size_range': 'size range'
        };
        
        const typeName = typeMap[type] || type;
        const endpoint = type.replace(/_/g, '-');
        
        // CRITICAL FIX: Show confirmation and ONLY delete after OK is clicked
        showDeleteConfirmation(
            `Delete this ${typeName}? This may affect existing styles.`,
            function() {
                // This function ONLY runs when OK is clicked
                deleteItem(endpoint, id);
            },
            function() {
                // This function ONLY runs when Cancel is clicked
                console.log('Delete cancelled');
            }
        );
    }
});

// Handle modal buttons
document.getElementById('modalSaveBtn')?.addEventListener('click', saveModal);
document.getElementById('modalCancelBtn')?.addEventListener('click', closeModal);

// ============================================
// INITIALIZE ON PAGE LOAD
// ============================================

// Initialize all filters
setupTableFilter('fabricSearch', 'fabric-row', 'fabricCount');
setupTableFilter('notionSearch', 'notion-row', 'notionCount');
setupTableFilter('laborSearch', 'labor-row', 'laborCount');
setupTableFilter('cleaningSearch', 'cleaning-row', 'cleaningCount');
setupTableFilter('colorSearch', 'color-row', 'colorCount');
setupTableFilter('variableSearch', 'variable-row', 'variableCount');
setupTableFilter('sizeRangeSearch', 'size-range-row', 'sizeRangeCount');

// Close modal on outside click
window.addEventListener('click', function(event) {
    const modal = document.getElementById('modal');
    if (event.target === modal) {
        closeModal();
    }
});

console.log('✅ Master costs page JavaScript loaded with event delegation');

// ============================================
// NATURAL NUMBER SORTING HELPER
// ============================================

function naturalSort(aValue, bValue, ascending = true) {
    // Extract prefix and number (e.g., F102 -> F, 102)
    const aMatch = aValue.match(/^([A-Za-z]*)(\d+)$/);
    const bMatch = bValue.match(/^([A-Za-z]*)(\d+)$/);
    
    if (aMatch && bMatch) {
        // Compare prefix first
        if (aMatch[1] !== bMatch[1]) {
            const prefixCompare = aMatch[1].localeCompare(bMatch[1]);
            return ascending ? prefixCompare : -prefixCompare;
        }
        // Same prefix - compare numbers
        const aNum = parseInt(aMatch[2], 10);
        const bNum = parseInt(bMatch[2], 10);
        return ascending ? aNum - bNum : bNum - aNum;
    }
    
    // Try numeric comparison for prices
    const aNum = parseFloat(aValue.replace(/[$,%]/g, ''));
    const bNum = parseFloat(bValue.replace(/[$,%]/g, ''));
    
    if (!isNaN(aNum) && !isNaN(bNum)) {
        return ascending ? aNum - bNum : bNum - aNum;
    }
    
    // Fallback to text comparison
    return ascending ? aValue.localeCompare(bValue) : bValue.localeCompare(aValue);
}

// ============================================
// AUTO-SORT TABLE FUNCTION
// ============================================

function autoSortTableByColumn(tableSelector, columnIndex, ascending = true) {
    const table = document.querySelector(tableSelector);
    if (!table) return;
    
    const tbody = table.querySelector('tbody');
    if (!tbody) return;
    
    const rows = Array.from(tbody.querySelectorAll('tr'));
    if (rows.length === 0) return;
    
    rows.sort((a, b) => {
        const aCell = a.cells[columnIndex];
        const bCell = b.cells[columnIndex];
        
        if (!aCell || !bCell) return 0;
        
        const aValue = aCell.textContent.trim();
        const bValue = bCell.textContent.trim();
        
        return naturalSort(aValue, bValue, ascending);
    });
    
    // Re-append sorted rows
    rows.forEach(row => tbody.appendChild(row));
}

// ============================================
// COLUMN SORTING (CLICK HEADERS)
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    
    document.querySelectorAll('.modern-table th[data-sort]').forEach(header => {
        header.addEventListener('click', function() {
            const table = this.closest('table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const columnIndex = Array.from(this.parentElement.children).indexOf(this);
            
            const isAscending = this.classList.contains('sorted-asc');
            
            table.querySelectorAll('th').forEach(th => {
                th.classList.remove('sorted', 'sorted-asc', 'sorted-desc');
            });
            
            if (isAscending) {
                this.classList.add('sorted', 'sorted-desc');
            } else {
                this.classList.add('sorted', 'sorted-asc');
            }
            
            rows.sort((a, b) => {
                let aCell = a.cells[columnIndex];
                let bCell = b.cells[columnIndex];
                
                if (!aCell || !bCell) return 0;
                
                const aValue = aCell.textContent.trim();
                const bValue = bCell.textContent.trim();

                return naturalSort(aValue, bValue, !isAscending);
            });
            
            rows.forEach(row => tbody.appendChild(row));
            
            if (typeof feather !== 'undefined') {
                feather.replace();
            }
        });
    });
    
    // ============================================
    // AUTO-SORT ALL TABLES ON PAGE LOAD
    // ============================================
    
    // Helper function to sort tbody by column
    function sortTbodyByColumn(tbodyId, columnIndex) {
        const tbody = document.getElementById(tbodyId);
        if (!tbody) return false;
        
        const rows = Array.from(tbody.querySelectorAll('tr'));
        if (rows.length === 0) return false;
        
        rows.sort((a, b) => {
            const aCell = a.cells[columnIndex];
            const bCell = b.cells[columnIndex];
            if (!aCell || !bCell) return 0;
            return naturalSort(aCell.textContent.trim(), bCell.textContent.trim(), true);
        });
        rows.forEach(row => tbody.appendChild(row));
        console.log(`✅ Sorted ${tbodyId} by column ${columnIndex}`);
        return true;
    }
    
    // Helper function to sort table in section by column
    function sortSectionTable(sectionId, columnIndex) {
        const section = document.getElementById(sectionId);
        if (!section) return false;
        
        const tbody = section.querySelector('tbody');
        if (!tbody) return false;
        
        const rows = Array.from(tbody.querySelectorAll('tr'));
        if (rows.length === 0) return false;
        
        rows.sort((a, b) => {
            const aCell = a.cells[columnIndex];
            const bCell = b.cells[columnIndex];
            if (!aCell || !bCell) return 0;
            return naturalSort(aCell.textContent.trim(), bCell.textContent.trim(), true);
        });
        rows.forEach(row => tbody.appendChild(row));
        console.log(`✅ Sorted ${sectionId} by column ${columnIndex}`);
        return true;
    }
    
    // Sort Fabric Vendors by CODE (column 1)
    sortSectionTable('fabric-vendors', 1);
    
    // Sort Notion Vendors by CODE (column 1)
    // Notion Vendors doesn't have an ID, so find it by position (second vendor-card)
    const vendorCards = document.querySelectorAll('.vendor-card');
    if (vendorCards.length >= 2) {
        const notionVendorCard = vendorCards[1]; // Second card is Notion Vendors
        const tbody = notionVendorCard.querySelector('tbody');
        if (tbody) {
            const rows = Array.from(tbody.querySelectorAll('tr'));
            rows.sort((a, b) => {
                const aCell = a.cells[1]; // CODE column
                const bCell = b.cells[1];
                if (!aCell || !bCell) return 0;
                return naturalSort(aCell.textContent.trim(), bCell.textContent.trim(), true);
            });
            rows.forEach(row => tbody.appendChild(row));
            console.log('✅ Notion Vendors sorted');
        }
    }
    
    // Sort Fabrics by FABRIC CODE (column 1)
    sortTbodyByColumn('fabricTable', 1);
    
    // Sort Notions by NAME (column 0)
    sortTbodyByColumn('notionTable', 0);
    
    // Sort other sections
    sortSectionTable('labor-section', 0);
    sortSectionTable('cleaning-section', 0);
    sortSectionTable('size-ranges-section', 0);
    sortSectionTable('colors-section', 0);
    sortSectionTable('variables-section', 0);
    
    console.log('✅ Tables auto-sorted by code/name on page load');
});

function refreshIcons() {
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
}

// ============================================
// SEARCH ICON TOGGLE
// ============================================

document.querySelectorAll('.search-box').forEach(searchBox => {
    searchBox.addEventListener('click', function(e) {
        // Don't toggle if clicking inside input
        if (e.target.tagName === 'INPUT') return;
        
        this.classList.toggle('active');
        const input = this.querySelector('input');
        
        if (this.classList.contains('active')) {
            input.focus();
        } else {
            input.value = '';
            input.dispatchEvent(new Event('input')); // Trigger filter reset
        }
    });
    
    // Close search when clicking outside
    document.addEventListener('click', function(e) {
        if (!searchBox.contains(e.target)) {
            searchBox.classList.remove('active');
        }
    });
});