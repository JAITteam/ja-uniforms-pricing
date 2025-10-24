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
    modal.classList.add('active'); // Add this line!
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
                <input type="text" id="vendor_code" required placeholder="e.g., V100">
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
                <input type="text" id="vendor_code" required placeholder="e.g., N100">
            </div>
        `;
    } else if (type === 'fabric') {
        formHtml = `
            <div class="form-group">
                <label>Fabric Name *</label>
                <input type="text" id="name" required placeholder="e.g., XANADU">
            </div>
            <div class="form-group">
                <label>Fabric Code</label>
                <input type="text" id="fabric_code" placeholder="e.g., 3202">
            </div>
            <div class="form-group">
                <label>Cost per Yard *</label>
                <input type="number" id="cost_per_yard" step="0.01" required placeholder="e.g., 6.00">
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
                <input type="number" id="cost_per_unit" step="0.0001" required placeholder="e.g., 0.04">
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
                <input type="number" id="setting_value" step="0.01" required placeholder="e.g., 0.20">
            </div>
            <div class="form-group">
                <label>Description</label>
                <textarea id="description" rows="2" placeholder="Description of this setting"></textarea>
            </div>
        `;
    }

    modalBody.innerHTML = formHtml;
    
    // If editing, load current values
    if (id) {
        const endpoint = type.replace(/_/g, '-');
        const pluralMap = {
            'size-range': 'size-ranges',
            'fabric-vendor': 'fabric-vendors',
            'notion-vendor': 'notion-vendors',
            'global-setting': 'global-settings'
        };
        const apiEndpoint = pluralMap[endpoint] || endpoint + 's';
        
        fetch(`/api/${apiEndpoint}/${id}`)
            .then(response => response.json())
            .then(data => {
                // Populate form fields with existing data
                Object.keys(data).forEach(key => {
                    const field = document.getElementById(key);
                    if (field) {
                        if (field.type === 'checkbox') {
                            field.checked = data[key];
                        } else {
                            field.value = data[key] || '';
                        }
                    }
                });
                
                // For labor, show the correct cost type group
                if (type === 'labor' && data.cost_type) {
                    updateLaborFields();
                }
            })
            .catch(error => {
                console.error('Error loading data:', error);
                showNotification('Error loading data: ' + error.message, 'error');
            });
    }
    
    modal.style.display = 'block';
}

function closeModal() {
    const modal = document.getElementById('modal');
    modal.classList.remove('active');
    modal.removeAttribute('data-type');
    modal.style.display = 'none';
    currentEditType = '';
    currentEditId = null;
}

function updateLaborFields() {
    const costType = document.getElementById('cost_type').value;
    document.getElementById('flat_rate_group').style.display = costType === 'flat_rate' ? 'block' : 'none';
    document.getElementById('hourly_group').style.display = costType === 'hourly' ? 'block' : 'none';
    document.getElementById('per_piece_group').style.display = costType === 'per_piece' ? 'block' : 'none';
}

function saveModal() {
    const formData = {};
    const modalBody = document.getElementById('modalBody');
    const inputs = modalBody.querySelectorAll('input, select, textarea');
    
    inputs.forEach(input => {
        if (input.type === 'checkbox') {
            formData[input.id] = input.checked;
        } else if (input.value) {
            formData[input.id] = input.value;
        }
    });
    
    const endpoint = currentEditType.replace(/_/g, '-');
    const pluralMap = {
        'size-range': 'size-ranges',
        'fabric-vendor': 'fabric-vendors',
        'notion-vendor': 'notion-vendors',
        'global-setting': 'global-settings'
    };
    const apiEndpoint = pluralMap[endpoint] || endpoint + 's';
    
    const url = currentEditId ? `/api/${apiEndpoint}/${currentEditId}` : `/api/${apiEndpoint}`;
    const method = currentEditId ? 'PUT' : 'POST';
    
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    const headers = {'Content-Type': 'application/json'};
    if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken;
    }
    
    fetch(url, {
        method: method,
        headers: headers,
        body: JSON.stringify(formData)
    })
    .then(response => {
        console.log('Response status:', response.status);
        if (!response.ok) {
            return response.text().then(text => {
                throw new Error(`HTTP ${response.status}: ${text}`);
            });
        }
        return response.json();
    })
    .then(() => {
        showNotification('Saved successfully!', 'success');
        closeModal();
        setTimeout(() => location.reload(), 1000);
    })
    .catch(error => {
        console.error('Save error:', error);
        showNotification('Error saving: ' + error.message, 'error');
    });
}

// ============================================
// EDIT/DELETE FUNCTIONS - Now handled by event delegation above
// ============================================
// All edit/delete functionality is now handled by event listeners
// No individual functions needed anymore!

function deleteItem(type, id) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    const headers = {};
    if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken;
    }
    
    fetch(`/api/${type}s/${id}`, {
        method: 'DELETE',
        headers: headers
    })
    .then(response => response.json())
    .then(() => {
        showNotification('Deleted successfully!', 'success');
        setTimeout(() => location.reload(), 500);
    })
    .catch(error => {
        showNotification('Error deleting: ' + error, 'error');
    });
}

// ============================================
// UTILITY FUNCTIONS
// ============================================

function showNotification(message, type) {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = 'notification ' + type;
    notification.style.display = 'block';
    
    setTimeout(() => {
        notification.style.display = 'none';
    }, 3000);
}

function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

// ============================================
// TABLE FILTER FUNCTION
// ============================================

function setupTableFilter(searchId, rowClass, countId) {
    const searchInput = document.getElementById(searchId);
    if (!searchInput) return;
    
    const updateCount = () => {
        const rows = document.querySelectorAll('.' + rowClass);
        const visible = Array.from(rows).filter(r => r.style.display !== 'none').length;
        const countEl = document.getElementById(countId);
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

// Handle all "Delete" buttons
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('btn-delete') || e.target.closest('.btn-delete') ||
        e.target.classList.contains('icon-delete') || e.target.closest('.icon-delete')) {
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
        
        if (confirm(`Delete this ${typeName}? This may affect existing styles.`)) {
            const endpoint = type.replace(/_/g, '-');
            deleteItem(endpoint, id);
        }
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
// COLUMN SORTING (NEW FEATURE)
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
                
                const aNum = parseFloat(aValue.replace(/[$,%]/g, ''));
                const bNum = parseFloat(bValue.replace(/[$,%]/g, ''));
                
                if (!isNaN(aNum) && !isNaN(bNum)) {
                    return isAscending ? bNum - aNum : aNum - bNum;
                }
                
                return isAscending ? 
                    bValue.localeCompare(aValue) : 
                    aValue.localeCompare(bValue);
            });
            
            rows.forEach(row => tbody.appendChild(row));
            
            if (typeof feather !== 'undefined') {
                feather.replace();
            }
        });
    });
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
