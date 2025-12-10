// ============================================
// CSRF TOKEN HELPER (MUST BE GLOBAL)
// ============================================
function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
}

// ============================================
// FRONTEND VALIDATION HELPERS
// ============================================
function validateRequired(value, fieldName) {
  const val = (value || '').trim();
  if (!val) {
    return { valid: false, error: `${fieldName} is required` };
  }
  return { valid: true, value: val };
}

function validateStringLength(value, fieldName, maxLength) {
  const val = String(value || '');
  if (val.length > maxLength) {
    return { valid: false, error: `${fieldName} too long (max ${maxLength} characters)` };
  }
  return { valid: true, value: val };
}

function validatePositiveNumber(value, fieldName, allowZero = false) {
  const num = parseFloat(value);
  if (isNaN(num)) {
    return { valid: false, error: `${fieldName} must be a valid number` };
  }
  if (allowZero && num < 0) {
    return { valid: false, error: `${fieldName} cannot be negative` };
  }
  if (!allowZero && num <= 0) {
    return { valid: false, error: `${fieldName} must be greater than 0` };
  }
  return { valid: true, value: num };
}

function validatePercentage(value, fieldName) {
  const num = parseFloat(value);
  if (isNaN(num)) {
    return { valid: false, error: `${fieldName} must be a valid number` };
  }
  if (num < 0 || num > 100) {
    return { valid: false, error: `${fieldName} must be between 0 and 100` };
  }
  return { valid: true, value: num };
}
// ============================================
// CUSTOM ALERT MODAL (REPLACES BROWSER ALERTS)
// ============================================
window.customAlert = function(message, type = 'info') {
    return new Promise((resolve) => {
        const modal = document.getElementById('customAlertModal');
        const messageEl = document.getElementById('alertMessage');
        const iconEl = document.getElementById('alertIcon');
        const okBtn = document.getElementById('alertOkBtn');
        const cancelBtn = document.getElementById('alertCancelBtn');
        
        messageEl.textContent = message;
        iconEl.className = 'custom-alert-icon ' + type;
        cancelBtn.style.display = 'none';
        
        modal.classList.add('active');
        
        const handleOk = () => {
            modal.classList.remove('active');
            okBtn.removeEventListener('click', handleOk);
            resolve(true);
        };
        
        okBtn.addEventListener('click', handleOk);
        
        // Close on Escape
        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                modal.classList.remove('active');
                document.removeEventListener('keydown', handleEscape);
                resolve(true);
            }
        };
        document.addEventListener('keydown', handleEscape);
    });
};

window.customConfirm = function(message, type = 'question') {
    return new Promise((resolve) => {
        const modal = document.getElementById('customAlertModal');
        const messageEl = document.getElementById('alertMessage');
        const iconEl = document.getElementById('alertIcon');
        const okBtn = document.getElementById('alertOkBtn');
        const cancelBtn = document.getElementById('alertCancelBtn');
        
        messageEl.textContent = message;
        iconEl.className = 'custom-alert-icon ' + type;
        okBtn.textContent = 'OK';
        cancelBtn.textContent = 'Cancel';
        cancelBtn.style.display = 'inline-block';
        
        modal.classList.add('active');
        
        const handleOk = () => {
            modal.classList.remove('active');
            okBtn.removeEventListener('click', handleOk);
            cancelBtn.removeEventListener('click', handleCancel);
            resolve(true);
        };
        
        const handleCancel = () => {
            modal.classList.remove('active');
            okBtn.removeEventListener('click', handleOk);
            cancelBtn.removeEventListener('click', handleCancel);
            resolve(false);
        };
        
        okBtn.addEventListener('click', handleOk);
        cancelBtn.addEventListener('click', handleCancel);
        
        // Close on Escape = Cancel
        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                modal.classList.remove('active');
                document.removeEventListener('keydown', handleEscape);
                resolve(false);
            }
        };
        document.addEventListener('keydown', handleEscape);
    });
};

// Override default alert and confirm
window.alert = window.customAlert;
window.confirm = window.customConfirm;




// ============================================
// HANDLE DUPLICATION FROM EXISTING STYLE
// ============================================
(function() {
    const urlParams = new URLSearchParams(window.location.search);
    const duplicateFromId = urlParams.get('duplicate_from_id');

    if (duplicateFromId && window.location.pathname === '/style/new') {
        // Wait for page to load, then load style for duplication
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => loadStyleForDuplication(duplicateFromId));
        } else {
            loadStyleForDuplication(duplicateFromId);
        }
    }

    async function loadStyleForDuplication(styleId) {
        try {
            const response = await fetch(`/api/style/load-for-duplicate/${styleId}`);
            const data = await response.json();
            if (!data.success) {
                alert('Error loading style for duplication: ' + (data.error || 'Unknown error'));
                return;
            }
            
            // Store original values for validation
            window.originalVendorStyle = data.style.original_vendor_style;
            window.originalStyleName = data.style.original_style_name;
            window.isDuplicating = true;
            
            // Wait for page to fully load
            setTimeout(() => {
                const $ = s => document.querySelector(s);
                const set = (sel, val) => { const el = $(sel); if (el) el.value = (val ?? ""); };
                
                // Add warning banner
                const container = document.querySelector('.container-fluid') || document.querySelector('.row.g-3');
                if (container) {
                    const banner = document.createElement('div');
                    banner.id = 'duplication-warning';
                    banner.style.cssText = 'background: #fef3c7; border: 2px solid #f59e0b; padding: 1rem; margin-bottom: 1.5rem; border-radius: 8px; text-align: center; position: sticky; top: 0; z-index: 100; grid-column: 1 / -1;';
                    banner.innerHTML = `
                        <strong style="font-size: 1.1rem;">⚠️ Duplicating Style</strong><br>
                        <span style="color: #92400e;">You MUST change the Vendor Style and Style Name before saving to avoid conflicts.</span>
                    `;
                    container.insertBefore(banner, container.firstChild);
                }
                
                // Populate form fields directly (don't trigger auto-load)
                const s = data.style;
                set('#vendor_style', s.vendor_style);
                set('#base_item_number', s.base_item_number);
                set('#variant_code', s.variant_code);
                set('#style_name', s.style_name);
                set('#gender', s.gender);
                set('#garment_type', s.garment_type);
                set('#margin', 60);  // Always default to 60% for estimation
                set('#suggested_price', s.suggested_price);
                set('#notes', s.notes);
                
                // Set size range
                const sizeRangeSelect = $('#size_range_id');
                if (sizeRangeSelect && s.size_range) {
                    Array.from(sizeRangeSelect.options).forEach(option => {
                        if (option.dataset.name === s.size_range) {
                            option.selected = true;
                        }
                    });
                }
                
                // Clear existing rows
                document.querySelectorAll('[data-fabric-id]').forEach((el, i) => {
                    if (i > 0) el.closest('.kv').remove();
                });
                document.querySelectorAll('[data-notion-id]').forEach((el, i) => {
                    if (i > 0) el.closest('.kv').remove();
                });
                
                // Load fabrics
                const fabrics = data.fabrics || [];
                fabrics.forEach((f, index) => {
                    if (index > 0) {
                        // Click add button to create new row
                        $('#addFabric')?.click();
                    }
                    
                    const allFabricRows = document.querySelectorAll('[data-fabric-id]');
                    const targetRow = allFabricRows[index]?.closest('.kv');
                    
                    if (targetRow) {
                        const fabricSelect = targetRow.querySelector('[data-fabric-id]');
                        const vendorSelect = targetRow.querySelector('[data-fabric-vendor-id]');
                        const yardsInput = targetRow.querySelector('[data-fabric-yds]');
                        const costInput = targetRow.querySelector('[data-fabric-cost]');
                        const sublimationCheckbox = targetRow.querySelector('[data-fabric-sublimation]');
                        
                        if (vendorSelect && f.vendor) {
                            Array.from(vendorSelect.options).forEach(opt => {
                                if (opt.text === f.vendor) vendorSelect.value = opt.value;
                            });
                        }
                        
                        if (fabricSelect && f.name) {
                            Array.from(fabricSelect.options).forEach(opt => {
                                if (opt.text === f.name) fabricSelect.value = opt.value;
                            });
                        }
                        
                        if (yardsInput) yardsInput.value = f.yards || '';
                        if (costInput) costInput.value = f.cost_per_yard || '';
                        if (sublimationCheckbox) sublimationCheckbox.checked = f.sublimation || false;
                    }
                });
                
                // Load notions
                const notions = data.notions || [];
                notions.forEach((n, index) => {
                    if (index > 0) {
                        $('#addNotion')?.click();
                    }
                    
                    const allNotionRows = document.querySelectorAll('[data-notion-id]');
                    const targetRow = allNotionRows[index]?.closest('.kv');
                    
                    if (targetRow) {
                        const notionSelect = targetRow.querySelector('[data-notion-id]');
                        const vendorSelect = targetRow.querySelector('[data-notion-vendor-id]');
                        const qtyInput = targetRow.querySelector('[data-notion-qty]');
                        const costInput = targetRow.querySelector('[data-notion-cost]');
                        
                        if (vendorSelect && n.vendor) {
                            Array.from(vendorSelect.options).forEach(opt => {
                                if (opt.text === n.vendor) vendorSelect.value = opt.value;
                            });
                        }
                        
                        if (notionSelect && n.name) {
                            Array.from(notionSelect.options).forEach(opt => {
                                if (opt.text === n.name) notionSelect.value = opt.value;
                            });
                        }
                        
                        if (qtyInput) qtyInput.value = n.qty || '';
                        if (costInput) costInput.value = n.cost_per_unit || '';
                    }
                });
                
                // Load labor
                const labor = data.labor || [];
                document.querySelectorAll('[data-labor-row]').forEach((row, i) => {
                    const l = labor[i] || {};
                    const qInput = row.querySelector('[data-labor-qoh]');
                    if (qInput && l.qty_or_hours) qInput.value = l.qty_or_hours;
                });
                
                // Load colors
                if (data.colors && data.colors.length > 0) {
                    const colorList = $('#color_list');
                    if (colorList) {
                        colorList.innerHTML = '';
                        data.colors.forEach(color => {
                            const option = document.createElement('option');
                            option.value = color.color_id;
                            option.text = color.name;
                            colorList.add(option);
                        });
                    }
                }
                
                // Load variables
                if (data.variables && data.variables.length > 0) {
                    const variableList = $('#variable_list');
                    if (variableList) {
                        variableList.innerHTML = '';
                        data.variables.forEach(variable => {
                            const option = document.createElement('option');
                            option.value = variable.variable_id;
                            option.text = variable.name;
                            variableList.add(option);
                        });
                    }
                }
                
                // Trigger calculations
                const recalcEvent = new Event('input', { bubbles: true });
                $('#margin')?.dispatchEvent(recalcEvent);
                document.querySelector('[data-fabric-yds]')?.dispatchEvent(recalcEvent);
                
                alert('✅ Style data loaded for duplication!\n\nPlease change the Vendor Style and Style Name before saving.');
                
            }, 1500); // Increased timeout to ensure page is fully loaded
            
        } catch (error) {
            console.error('Duplication error:', error);
            alert('Error loading style for duplication: ' + error.message);
        }
    }
})();

// ============================================
// ENABLE COPY/PASTE EVERYWHERE
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    // Remove any copy/paste blockers
    document.addEventListener('copy', function(e) {
        // Allow copy
    }, true);
    
    document.addEventListener('paste', function(e) {
        // Allow paste
    }, true);
    
    document.addEventListener('cut', function(e) {
        // Allow cut
    }, true);
    
    // Enable text selection
    document.body.style.userSelect = 'text';
    document.body.style.webkitUserSelect = 'text';
    document.body.style.mozUserSelect = 'text';
    document.body.style.msUserSelect = 'text';
});

// Allow copy/paste on all input fields
window.addEventListener('load', function() {
    const inputs = document.querySelectorAll('input, textarea');
    inputs.forEach(input => {
        input.removeAttribute('oncopy');
        input.removeAttribute('onpaste');
        input.removeAttribute('oncut');
        input.style.userSelect = 'text';
    });
});

document.addEventListener('DOMContentLoaded', () => {
  const $ = s => document.querySelector(s);
  const fmt = n => '$' + (Number(n||0).toFixed(2));
  const set = (sel, val) => { const el = $(sel); if (el) el.value = (val ?? ""); };
  const setText = (sel, txt) => { const el = $(sel); if (el) el.textContent = (txt ?? ""); };

  // Load colors on page load
  loadColors();
  loadVariables(); 

  // Function to prevent negative values - REUSABLE FOR DYNAMIC ROWS
  function preventNegativeValues(input) {
    // Prevent typing negative sign, 'e', and 'E'
    input.addEventListener('keydown', function(e) {
      if (e.key === '-' || e.key === 'e' || e.key === 'E' || e.key === '+') {
        e.preventDefault();
      }
    });
    
    // Check on every input change
    input.addEventListener('input', function() {
      const value = parseFloat(this.value);
      if (this.value && value < 0) {
        this.value = 0;
      }
    });
    
    // Final check when user leaves the field
    input.addEventListener('blur', function() {
      const value = parseFloat(this.value);
      if (this.value && value < 0) {
        this.value = 0;
      }
    });
    
    // Prevent paste of negative numbers
    input.addEventListener('paste', function(e) {
      setTimeout(() => {
        const value = parseFloat(this.value);
        if (!isNaN(value) && value < 0) {
          this.value = 0;
          this.dispatchEvent(new Event('input', { bubbles: true }));
        }
      }, 10);
    });
  }

  // Apply to all existing number inputs on page load
  document.querySelectorAll('input[type="number"]').forEach(input => {
    preventNegativeValues(input);
  });


  // Capture dropdown options once at page load for dynamic row creation
  const fabricVendorSelect = document.querySelector('[data-fabric-vendor-id]');
  const fabricVendorOptions = fabricVendorSelect 
    ? Array.from(fabricVendorSelect.options).map(opt => ({
        value: opt.value,
        text: opt.text
      }))
    : [];

  const notionVendorSelect = document.querySelector('[data-notion-vendor-id]');
  const notionVendorOptions = notionVendorSelect
    ? Array.from(notionVendorSelect.options).map(opt => ({
        value: opt.value,
        text: opt.text
      }))
    : [];

  const fabricSelect = document.querySelector('[data-fabric-id]');
  const fabricOptions = fabricSelect
    ? Array.from(fabricSelect.options).map(opt => ({
        value: opt.value,
        text: opt.text,
        cost: opt.dataset.cost || '',
        vendor: opt.dataset.vendor || '',
        fabricCode: opt.dataset.fabricCode || ''
      }))
    : [];

  const notionSelect = document.querySelector('[data-notion-id]');
  const notionOptions = notionSelect
    ? Array.from(notionSelect.options).map(opt => ({
        value: opt.value,
        text: opt.text,
        cost: opt.dataset.cost || '',
        vendor: opt.dataset.vendor || ''
      }))
    : [];

  // Auto Vendor Style
  function buildVendorStyle(){
    const base=$('#base_item_number')?.value.trim() || '';
    const variant=$('#variant_code')?.value.trim() || '';
    
    // Get fabric code from first fabric row
    const firstFabricSelect = document.querySelector('[data-fabric-id]');
    let fabricCode = '';
    if (firstFabricSelect && firstFabricSelect.value) {
      const selectedOption = firstFabricSelect.options[firstFabricSelect.selectedIndex];
      fabricCode = selectedOption.dataset.fabricCode || '';
    }
    
    // Check sublimation checkbox on first row
    const firstSublimationCheckbox = document.querySelector('[data-fabric-sublimation]');
    const hasSublimation = firstSublimationCheckbox?.checked || false;
    
    // Build vendor style: BASE-VARIANT+FABRICCODE+P (no hyphen after variant)
    const parts = [];
    if (base) parts.push(base);
    if (variant) parts.push(variant);
    
    let vendorStyle = parts.join('-');
    if (fabricCode) {
      vendorStyle += fabricCode;
      if (hasSublimation) {
        vendorStyle += 'P';
      }
    }
    
    // Update fields
    const input = $('#vendor_style');
    if (input) {
      input.value = vendorStyle;
      input.dataset.touched = '0';
    }
    
    $('#fabric_code').value = fabricCode || 'Auto';
    setText('#snap_vendor_style', vendorStyle || '(vendor style)');
  }

  // Bidirectional: Parse vendor style back to components
  function parseVendorStyle() {
    const vendorStyle = $('#vendor_style')?.value.trim() || '';
    if (!vendorStyle) return;
    
    const parts = vendorStyle.split('-');
    
    if (parts.length >= 1 && parts[0]) {
      $('#base_item_number').value = parts[0];
    }
    if (parts.length >= 2 && parts[1]) {
      $('#variant_code').value = parts[1];
    }
    if (parts.length >= 3 && parts[2]) {
      $('#fabric_code').value = parts[2];
    }
    
    // Update snapshot
    setText('#snap_vendor_style', vendorStyle);
  }
  // Auto-build vendor style when components change
  ['#base_item_number','#variant_code'].forEach(sel=> 
    $(sel)?.addEventListener('input', buildVendorStyle)
  );
  // Watch first fabric row for vendor style changes
  document.querySelector('[data-fabric-id]')?.addEventListener('change', buildVendorStyle);
  document.querySelector('[data-fabric-sublimation]')?.addEventListener('change', buildVendorStyle);

  // Parse vendor style back to components when manually edited
  $('#vendor_style')?.addEventListener('blur', function() {
    parseVendorStyle();
  });

  // Fabric dropdown - auto-fill cost when selected (first row only)
  $('[data-fabric-id]')?.addEventListener('change', function() {
    const opt = this.options[this.selectedIndex];
    if (opt.value) {
      const row = this.closest('.kv');
      const baseCost = parseFloat(opt.dataset.cost || 0);
      const sublimationCheckbox = row.querySelector('[data-fabric-sublimation]');
      const sublimationCost = sublimationCheckbox?.checked ? 6.00 : 0;
    
      row.querySelector('[data-fabric-cost]').value = (baseCost + sublimationCost).toFixed(2);
      row.querySelector('[data-fabric-vendor-id]').value = opt.dataset.vendor || '';
      recalcMaterials();
      buildVendorStyle();
    }
  });
  
  // Handle sublimation checkbox on the first fabric row
  document.querySelector('[data-fabric-sublimation]')?.addEventListener('change', function() {
    const row = this.closest('.kv');
    const fabricSelect = row.querySelector('[data-fabric-id]');
    const costInput = row.querySelector('[data-fabric-cost]');
  
    if (fabricSelect && fabricSelect.value && costInput) {
      const opt = fabricSelect.options[fabricSelect.selectedIndex];
      const baseCost = parseFloat(opt.dataset.cost || 0);
      const sublimationCost = this.checked ? 6.00 : 0;
      costInput.value = (baseCost + sublimationCost).toFixed(2);
      recalcMaterials();
    }
  });

  // Filter fabrics by vendor 
  document.querySelector('[data-fabric-vendor-id]')?.addEventListener('change', function() {
    const vendorId = this.value;
    const fabricSelect = document.querySelector('[data-fabric-id]');
    
    if (!fabricSelect) return;
    
    Array.from(fabricSelect.options).forEach(option => {
      if (option.value === '') {
        option.style.display = '';
      } else if (!vendorId) {
        option.style.display = '';
      } else {
        option.style.display = option.dataset.vendor === vendorId ? '' : 'none';
      }
    });
    
    fabricSelect.value = '';
    document.querySelector('[data-fabric-cost]').value = '';
  });

  // Notion dropdown - auto-fill cost when selected (first row only)
  $('[data-notion-id]')?.addEventListener('change', function() {
    const opt = this.options[this.selectedIndex];
    if (opt.value) {
      const row = this.closest('.kv');
      row.querySelector('[data-notion-cost]').value = opt.dataset.cost || '';
      row.querySelector('[data-notion-vendor-id]').value = opt.dataset.vendor || '';
      recalcMaterials();
    }
  });

  // Filter notions by vendor - ADD HERE (around line 110)
  document.querySelector('[data-notion-vendor-id]')?.addEventListener('change', function() {
    const vendorId = this.value;
    const notionSelect = document.querySelector('[data-notion-id]');
    
    if (!notionSelect) return;
    
    Array.from(notionSelect.options).forEach(option => {
      if (option.value === '') {
        option.style.display = '';
      } else if (!vendorId) {
        option.style.display = '';
      } else {
        option.style.display = option.dataset.vendor === vendorId ? '' : 'none';
      }
    });
    
    notionSelect.value = '';
    document.querySelector('[data-notion-cost]').value = '';
  });
 
  // Garment type - auto-fill cleaning cost
  // Garment type - auto-fill cleaning cost
  $('#garment_type')?.addEventListener('change', async function() {
    const garmentType = this.value;
    
    if (!garmentType) {
      $('#cleaning_cost').value = '0.00';
      recalcLabor();
      return;
    }
    
    try {
      const url = `/api/cleaning-cost?type=${encodeURIComponent(garmentType)}`;
      const res = await fetch(url);
      
      if (res.ok) {
        const data = await res.json();
        const cleaningInput = $('#cleaning_cost');
        if (cleaningInput && data.fixed_cost !== undefined) {
          cleaningInput.value = parseFloat(data.fixed_cost).toFixed(2);
          recalcLabor();
        }
      } else {
        console.error('API returned error status:', res.status);
        $('#cleaning_cost').value = '0.00';
        recalcLabor();
      }
    } catch (e) {
      console.error('Failed to fetch cleaning cost:', e);
      $('#cleaning_cost').value = '0.00';
      recalcLabor();
    }
  });

  // Calculations
  function recalcMaterials(){
    let fabricTotal = 0;
    let notionTotal = 0;
    
    document.querySelectorAll('[data-fabric-cost]').forEach(costInput => {
      const row = costInput.closest('.kv');
      const cost = +(costInput.value || 0);
      const yds = +(row.querySelector('[data-fabric-yds]')?.value || 0);
      const total = cost * yds;
      const totalInput = row.querySelector('[data-fabric-total]');
      if (totalInput) totalInput.value = total ? fmt(total) : '';
      fabricTotal += total;
    });
    
    document.querySelectorAll('[data-notion-cost]').forEach(costInput => {
      const row = costInput.closest('.kv');
      const cost = +(costInput.value || 0);
      const qty = +(row.querySelector('[data-notion-qty]')?.value || 0);
      const total = cost * qty;
      const totalInput = row.querySelector('[data-notion-total]');
      if (totalInput) totalInput.value = total ? fmt(total) : '';
      notionTotal += total;
    });
    
    const labels = +($('#label_cost')?.value || 0);
    const shipping = +($('#shipping_cost')?.value || 0);
    const materials = fabricTotal + notionTotal + labels;
    
    setText('#sumMaterials', fmt(materials));
    setText('#snap_mat', fmt(materials));
    setText('#snap_lbl', fmt(labels));
    setText('#snap_ship', fmt(shipping));
    recalcTotals();
  }

  function recalcLabor(){
    let sum=0;
    document.querySelectorAll('[data-labor-row]').forEach(r=>{
      const rate=+(r.querySelector('[data-labor-rate]')?.value||0);
      const q=+(r.querySelector('[data-labor-qoh]')?.value||0);
      const tot=rate*q; 
      const out=r.querySelector('[data-labor-total]');
      if (out) out.value = tot ? fmt(tot) : '';
      sum+=tot;
    });
    sum+=+( $('#cleaning_cost')?.value || 0 );
    setText('#sumLabor', fmt(sum));
    setText('#snap_lab', fmt(sum));
    recalcTotals();
  }

  function recalcTotals(){
    const mat=parseFloat((($('#sumMaterials')?.textContent)||'').replace('$',''))||0;
    const lab=parseFloat((($('#sumLabor')?.textContent)||'').replace('$',''))||0;
    //const labels=+( $('#label_cost')?.value || 0 );
    const ship=+( $('#shipping_cost')?.value || 0 );
    const total=mat+lab+ship;
    setText('#snap_total', fmt(total));

    if ($('#total_reg')) $('#total_reg').value = total ? fmt(total) : '';
    // Get dynamic markup from selected size range
    const sizeRangeSelect = $('#size_range_id');
    let extendedMarkup = 1.15; // default 15%
    if (sizeRangeSelect && sizeRangeSelect.value) {
      const selectedOption = sizeRangeSelect.options[sizeRangeSelect.selectedIndex];
      const markupPercent = parseFloat(selectedOption.dataset.markup || 15);
      extendedMarkup = 1 + (markupPercent / 100);
    }
    if ($('#total_ext')) $('#total_ext').value = total ? fmt(total * extendedMarkup) : '';

    const m=Math.max(0,Math.min(95,+($('#margin')?.value||60)));
    const retail= total ? (total/(1-(m/100))) : 0; 
    if ($('#retail_price')) $('#retail_price').value = retail ? fmt(retail) : '';
    const sp=+($('#suggested_price')?.value||0);
    if (sp > 0 && total > 0) {
      const sugg = Math.max(0, Math.min(95, ((sp - total) / sp) * 100));
      $('#suggested_margin').value = sugg.toFixed(1);
    } else {
      $('#suggested_margin').value = '';
    }
  }

  function updateSizeRangeDisplay() {
    const sizeRangeSelect = $('#size_range_id');
    if (!sizeRangeSelect || !sizeRangeSelect.value) {
      $('#regular_sizes_display').value = '';
      $('#extended_sizes_display').value = '';
      $('#extended_label').textContent = 'Extended Sizes (+15%)';
      return;
    }
    
    const selectedOption = sizeRangeSelect.options[sizeRangeSelect.selectedIndex];
    const regularSizes = selectedOption.dataset.regular || '';
    const extendedSizes = selectedOption.dataset.extended || '';
    const markup = selectedOption.dataset.markup || '15';
    
    $('#regular_sizes_display').value = regularSizes;
    $('#extended_sizes_display').value = extendedSizes || 'N/A';
    $('#extended_label').textContent = `Extended Sizes (+${markup}%)`;
    
    recalcTotals();
  }
  
  // Bidirectional: Change suggested price → calculate margin
  $('#suggested_price')?.addEventListener('input', function() {
    const sp = parseFloat(this.value) || 0;
    const total = parseFloat((($('#snap_total')?.textContent)||'').replace('$',''))||0;
  
    if (sp > 0 && total > 0) {
      const margin = ((sp - total) / sp) * 100;
      $('#suggested_margin').value = Math.max(0, Math.min(95, margin)).toFixed(1);
    }
  });
  
  // Bidirectional: Change margin → calculate suggested price
  $('#suggested_margin')?.addEventListener('input', function() {
    const margin = parseFloat(this.value) || 0;
    const total = parseFloat((($('#snap_total')?.textContent)||'').replace('$',''))||0;
  
    if (margin > 0 && total > 0) {
      const sp = total / (1 - (margin / 100));
      $('#suggested_price').value = sp.toFixed(2);
    }
  });

  document.querySelectorAll('[data-fabric-cost],[data-fabric-yds],[data-notion-cost],[data-notion-qty],#label_cost,#shipping_cost')
    .forEach(i=> i?.addEventListener('input',recalcMaterials));
  document.querySelectorAll('[data-labor-rate],[data-labor-qoh],#cleaning_cost')
    .forEach(i=> i?.addEventListener('input',recalcLabor));
  $('#margin')?.addEventListener('input', recalcTotals);
  $('#size_range_id')?.addEventListener('change', updateSizeRangeDisplay);

  // ADD VALIDATION FUNCTIONS HERE - START
  function validateFirstFabricRow() {
    const firstVendor = document.querySelector('[data-fabric-vendor-id]')?.value;
    const firstFabric = document.querySelector('[data-fabric-id]')?.value;
    const firstYards = document.querySelector('[data-fabric-yds]')?.value;
    
    const addBtn = $('#addFabric');
    if (addBtn) {
      if (firstVendor && firstFabric && firstYards) {
        addBtn.style.opacity = '1';
        addBtn.style.pointerEvents = 'auto';
        addBtn.style.cursor = 'pointer';
      } else {
        addBtn.style.opacity = '0.5';
        addBtn.style.pointerEvents = 'none';
        addBtn.style.cursor = 'not-allowed';
      }
    }
  }

  function validateFirstNotionRow() {
    const firstVendor = document.querySelector('[data-notion-vendor-id]')?.value;
    const firstNotion = document.querySelector('[data-notion-id]')?.value;
    const firstQty = document.querySelector('[data-notion-qty]')?.value;
    
    const addBtn = $('#addNotion');
    if (addBtn) {
      if (firstVendor && firstNotion && firstQty) {
        addBtn.style.opacity = '1';
        addBtn.style.pointerEvents = 'auto';
        addBtn.style.cursor = 'pointer';
      } else {
        addBtn.style.opacity = '0.5';
        addBtn.style.pointerEvents = 'none';
        addBtn.style.cursor = 'not-allowed';
      }
    }
  }

  // Validate fabric row on input
  document.querySelector('[data-fabric-vendor-id]')?.addEventListener('change', validateFirstFabricRow);
  document.querySelector('[data-fabric-id]')?.addEventListener('change', validateFirstFabricRow);
  document.querySelector('[data-fabric-yds]')?.addEventListener('input', validateFirstFabricRow);

  // Validate notion row on input
  document.querySelector('[data-notion-vendor-id]')?.addEventListener('change', validateFirstNotionRow);
  document.querySelector('[data-notion-id]')?.addEventListener('change', validateFirstNotionRow);
  document.querySelector('[data-notion-qty]')?.addEventListener('input', validateFirstNotionRow);

  
  // ADD VALIDATION FUNCTIONS HERE - END

  //$('#vendor_style')?.addEventListener('blur', tryLoadByVendorStyle);
  $('#vendor_style')?.addEventListener('keydown', e => { 
    if (e.key === 'Enter') { e.preventDefault(); tryLoadByVendorStyle(); } 
  });

  async function tryLoadByVendorStyle() {
    const vendorStyle = ($('#vendor_style')?.value || '').trim();
    if (!vendorStyle) return;

    const url = `/api/style/by-vendor-style?vendor_style=${encodeURIComponent(vendorStyle)}`;
    const res = await fetch(url);
    
    const data = await res.json().catch(() => ({}));
    
    if (!data.found) {
      const createNew = confirm(
        `Style "${vendorStyle}" not found in the system.\n\n` +
        `Would you like to create it as a new style?`
      );
      
      if (createNew) {
        set('#base_item_number', '');
        set('#variant_code', '');
        set('#style_name', '');
        set('#gender', 'MENS');
        set('#garment_type', '');
        set('#size_range', 'XS-4XL');
        $('#style_name')?.focus();
        if ($('#saveBtn')) $('#saveBtn').disabled = false;
      } else {
        window.location.href = '/';
      }
      return;
    }

    const s = data.style || {};
    set('#base_item_number', s.base_item_number);
    set('#variant_code', s.variant_code);
    set('#style_name', s.style_name);
    set('#gender', s.gender || 'MENS');
    set('#garment_type', s.garment_type);
    //set('#size_range', s.size_range);
    set('#margin', 60);  // Always default to 60% for estimation purposes
    set('#label_cost', s.label_cost || 0.20);
    set('#shipping_cost', s.shipping_cost || 0.00);
    set('#suggested_price', s.suggested_price || '');
    set('#notes', s.notes || '');
    setText('#snap_vendor_style', s.vendor_style || $('#vendor_style')?.value || '(vendor style)');
    // Find and select the size range option by name
    const sizeRangeSelect = $('#size_range_id');
    if (sizeRangeSelect && s.size_range) {
      Array.from(sizeRangeSelect.options).forEach(option => {
        if (option.dataset.name === s.size_range) {
          option.selected = true;
        }
      });
    }
updateSizeRangeDisplay();

    // Clear existing dynamic rows
    document.querySelectorAll('[data-fabric-id]').forEach((el, i) => {
      if (i > 0) el.closest('.kv').remove();
    });
    document.querySelectorAll('[data-notion-id]').forEach((el, i) => {
      if (i > 0) el.closest('.kv').remove();
    });

    // Load fabrics
    const fabrics = data.fabrics || [];
    fabrics.forEach((f, index) => {
      if (index === 0) {
        $('[data-fabric-id]').value = f.fabric_id;
        if (f.vendor_id) $('[data-fabric-vendor-id]').value = f.vendor_id;
        $('[data-fabric-yds]').value = f.yards;
        
        // Set sublimation checkbox first
        const sublimationCheckbox = document.querySelector('[data-fabric-sublimation]');
        if (sublimationCheckbox) sublimationCheckbox.checked = f.sublimation || false;
        
        // Calculate cost including sublimation
        const baseCost = parseFloat(f.cost_per_yard || 0);
        const sublimationCost = (sublimationCheckbox && sublimationCheckbox.checked) ? 6.00 : 0;
        $('[data-fabric-cost]').value = (baseCost + sublimationCost).toFixed(2);
      } else {
        $('#addFabric').click();
        const allFabricSelects = document.querySelectorAll('[data-fabric-id]');
        const newRow = allFabricSelects[allFabricSelects.length - 1].closest('.kv');
        newRow.querySelector('[data-fabric-id]').value = f.fabric_id;
        if (f.vendor_id) newRow.querySelector('[data-fabric-vendor-id]').value = f.vendor_id;
        newRow.querySelector('[data-fabric-yds]').value = f.yards;
        
        // Set sublimation checkbox first
        const sublimationCheckbox = newRow.querySelector('[data-fabric-sublimation]');
        if (sublimationCheckbox) sublimationCheckbox.checked = f.sublimation || false;
        
        // Calculate cost including sublimation
        const baseCost = parseFloat(f.cost_per_yard || 0);
        const sublimationCost = (sublimationCheckbox && sublimationCheckbox.checked) ? 6.00 : 0;
        newRow.querySelector('[data-fabric-cost]').value = (baseCost + sublimationCost).toFixed(2);
      }
    });

    // Load notions
    const notions = data.notions || [];
    notions.forEach((n, index) => {
      if (index === 0) {
        $('[data-notion-id]').value = n.notion_id;
        $('[data-notion-cost]').value = n.cost_per_unit;
        $('[data-notion-qty]').value = n.qty;
        if (n.vendor_id) $('[data-notion-vendor-id]').value = n.vendor_id;
      } else {
        $('#addNotion').click();
        const allNotionSelects = document.querySelectorAll('[data-notion-id]');
        const newRow = allNotionSelects[allNotionSelects.length - 1].closest('.kv');
        newRow.querySelector('[data-notion-id]').value = n.notion_id;
        newRow.querySelector('[data-notion-cost]').value = n.cost_per_unit;
        newRow.querySelector('[data-notion-qty]').value = n.qty;
        if (n.vendor_id) newRow.querySelector('[data-notion-vendor-id]').value = n.vendor_id;
      }
    });

    // Load labor
    const ops = data.labor || [];
    document.querySelectorAll('[data-labor-row]').forEach((row, i) => {
      const l = ops[i] || {};
      const qInput = row.querySelector('[data-labor-qoh]');
      if (qInput && l.qty_or_hours) qInput.value = l.qty_or_hours;
    });

    // Load cleaning
    if (data.cleaning) set('#cleaning_cost', data.cleaning.cost);

    // Load colors
    if (data.colors && data.colors.length > 0) {
      const colorList = $('#color_list');
      if (colorList) {
        colorList.innerHTML = '';
        data.colors.forEach(color => {
          const option = document.createElement('option');
          option.value = color.color_id;
          option.text = color.name;
          colorList.add(option);
        });
      }
    }

    // Load variables - ADD THIS ENTIRE BLOCK
    if (data.variables && data.variables.length > 0) {
      const variableList = $('#variable_list');
      if (variableList) {
        variableList.innerHTML = '';
        data.variables.forEach(variable => {
          const option = document.createElement('option');
          option.value = variable.variable_id;
          option.text = variable.name;
          variableList.add(option);
        });
      }
    }

    // Load images - ADD THIS
    if (data.style && data.style.id) {
      currentStyleId = data.style.id;
      console.log('✅ Style loaded! currentStyleId set to:', currentStyleId); 
      await loadStyleImages(data.style.id);
    }

    recalcMaterials();
    recalcLabor();
    // Run validation on page load
    validateFirstFabricRow();
    validateFirstNotionRow();
    if ($('#saveBtn')) $('#saveBtn').disabled = false;
  }

  const saveBtn = $('#saveBtn');
  function toggleSave(){ 
    if (saveBtn) saveBtn.disabled = !($('#style_name')?.value.trim()); 
  }
  $('#style_name')?.addEventListener('input', toggleSave); 
  toggleSave();
  
  saveBtn?.addEventListener('click', async () => {
    // ========================================
    // ENHANCED SAVE VALIDATION
    // ========================================
    
    // Get values
    const styleName = ($('#style_name')?.value || '').trim();
    const vendorStyle = ($('#vendor_style')?.value || '').trim();
    
    // ===== STEP 1: VALIDATE STYLE NAME =====
    let validation = validateRequired(styleName, 'Style Name');
    if (!validation.valid) {
      await customAlert(validation.error, 'error');
      $('#style_name')?.focus();
      return;
    }
    
    validation = validateStringLength(styleName, 'Style Name', 200);
    if (!validation.valid) {
      await customAlert(validation.error, 'error');
      $('#style_name')?.focus();
      return;
    }
    
    // ===== STEP 2: VALIDATE VENDOR STYLE =====
    if (vendorStyle) {
      validation = validateStringLength(vendorStyle, 'Vendor Style', 50);
      if (!validation.valid) {
        await customAlert(validation.error, 'error');
        $('#vendor_style')?.focus();
        return;
      }
    }
    

    // ===== STEP 3: VALIDATE MARGIN =====
    const marginValue = $('#margin')?.value;
    validation = validatePercentage(marginValue, 'Margin');
    if (!validation.valid) {
      await customAlert(validation.error, 'error');
      $('#margin')?.focus();
      return;
    }

    
    // ===== STEP 4: VALIDATE FIRST FABRIC ROW =====
    
    // ===== STEP 4: VALIDATE FIRST FABRIC ROW =====
    const firstVendor = document.querySelector('[data-fabric-vendor-id]')?.value;
    const firstFabric = document.querySelector('[data-fabric-id]')?.value;
    const firstYards = document.querySelector('[data-fabric-yds]')?.value;
    
    if (!firstVendor || !firstFabric || !firstYards) {
      await customAlert(
        'Cannot save! Missing required fields:\n\n• FIRST FABRIC ROW (Vendor, Fabric, and Yards)\n\nPlease complete these fields before saving.',
        'error'
      );
      return;
    }
    
    // Validate yards is positive
    validation = validatePositiveNumber(firstYards, 'Fabric yards', false);
    if (!validation.valid) {
      await customAlert(validation.error, 'error');
      document.querySelector('[data-fabric-yds]')?.focus();
      return;
    }
    
    // ===== STEP 5: VALIDATE ALL FABRIC YARDS =====
    const allFabricYards = document.querySelectorAll('[data-fabric-yds]');
    for (let i = 0; i < allFabricYards.length; i++) {
      const yards = allFabricYards[i].value;
      if (yards) {
        validation = validatePositiveNumber(yards, `Fabric row ${i+1} yards`, false);
        if (!validation.valid) {
          await customAlert(validation.error, 'error');
          allFabricYards[i].focus();
          return;
        }
      }
    }
    
    // ===== STEP 6: VALIDATE ALL NOTION QUANTITIES =====
    const allNotionQty = document.querySelectorAll('[data-notion-qty]');
    for (let i = 0; i < allNotionQty.length; i++) {
      const qty = allNotionQty[i].value;
      if (qty) {
        validation = validatePositiveNumber(qty, `Notion row ${i+1} quantity`, false);
        if (!validation.valid) {
          await customAlert(validation.error, 'error');
          allNotionQty[i].focus();
          return;
        }
      }
    }
    
    console.log('✅ All validations passed, preparing to save...');
    
    // ========================================
    // DUPLICATION VALIDATION
  
    // ========================================
    // DUPLICATION VALIDATION
    // ========================================
    if (window.isDuplicating) {
        const currentVendorStyle = $('#vendor_style')?.value.trim();
        
        if (!currentVendorStyle) {
            alert('❌ Vendor Style is required!');
            return;
        }
        
        if (currentVendorStyle === window.originalVendorStyle) {
            alert('❌ You must change the Vendor Style!\n\nThe Vendor Style cannot be the same as the original style ("' + window.originalVendorStyle + '").');
            return;
        }
        
        // Check if vendor_style already exists
        try {
            const checkResponse = await fetch(`/api/style/check-vendor-style?vendor_style=${encodeURIComponent(currentVendorStyle)}`);
            const checkData = await checkResponse.json();
            
            if (checkData.exists) {
                alert('❌ This Vendor Style already exists!\n\nPlease choose a different Vendor Style.');
                return;
            }
        } catch (error) {
            console.error('Error checking vendor style:', error);
        }
        
        // Clear duplication flag after validation passes
        window.isDuplicating = false;
    }

    // ========================================
    // COLLECT DATA FOR SAVE
    // ========================================
    
    const labor = [];
    document.querySelectorAll('[data-labor-row]').forEach(row => {
      const name = row.getAttribute('data-labor-name') || row.querySelector('label')?.textContent.trim();
      const rate = +(row.querySelector('[data-labor-rate]')?.value || 0);
      const qty = +(row.querySelector('[data-labor-qoh]')?.value || 0);
      
      if (name && (rate > 0 || qty > 0)) {
        labor.push({
          name: name,
          cost_type: /hour/i.test(name) ? 'hourly' : 'flat_rate',
          rate: rate,
          qty_or_hours: qty
        });
      }
    });

    const fabrics = [];
    document.querySelectorAll('[data-fabric-id]').forEach(select => {
      if (select.value) {
        const row = select.closest('.kv');
        const opt = select.options[select.selectedIndex];
        const vendorSelect = row.querySelector('[data-fabric-vendor-id]');
        const vendorOpt = vendorSelect?.options[vendorSelect.selectedIndex];
        const sublimationCheckbox = row.querySelector('[data-fabric-sublimation]');
    
        fabrics.push({
          vendor: vendorOpt?.text || '',
          name: opt.text,
          cost_per_yard: +(row.querySelector('[data-fabric-cost]')?.value || 0),
          yards: +(row.querySelector('[data-fabric-yds]')?.value || 0),
          primary: fabrics.length === 0,
          sublimation: sublimationCheckbox?.checked || false
        });
      }
    });

    const notions = [];
    document.querySelectorAll('[data-notion-id]').forEach(select => {
      if (select.value) {
        const row = select.closest('.kv');
        const opt = select.options[select.selectedIndex];
        const vendorSelect = row.querySelector('[data-notion-vendor-id]');
        const vendorOpt = vendorSelect?.options[vendorSelect.selectedIndex];
        
        notions.push({
          vendor: vendorOpt?.text || '',
          name: opt.text,
          cost_per_unit: +(row.querySelector('[data-notion-cost]')?.value || 0),
          qty: +(row.querySelector('[data-notion-qty]')?.value || 0)
        });
      }
    });

    const colors = [];
    const colorList = $('#color_list');
    if (colorList) {
      Array.from(colorList.options).forEach(opt => {
        colors.push({
          color_id: opt.value,
          name: opt.text
        });
      });
    }

    const variables = [];
    const variableList = $('#variable_list');
    if (variableList) {
      Array.from(variableList.options).forEach(opt => {
        variables.push({
          variable_id: opt.value,
          name: opt.text
        });
      });
    }
    console.log('🔍 Saving... currentStyleId =', currentStyleId);

    const payload = {
      style: {
        style_id: currentStyleId,
        style_name: styleName,
        vendor_style: vendorStyle,
        base_item_number: $('#base_item_number')?.value.trim() || '',
        variant_code: $('#variant_code')?.value.trim() || '',
        gender: $('#gender')?.value || 'MENS',
        garment_type: $('#garment_type')?.value?.trim() || '',
        size_range: $('#size_range_id')?.options[$('#size_range_id')?.selectedIndex]?.dataset.name || '',
        margin: parseFloat($('#margin')?.value) || 60.0,
        label_cost: parseFloat($('#label_cost')?.value) || 0.20,
        shipping_cost: parseFloat($('#shipping_cost')?.value) || 0.00,
        suggested_price: parseFloat($('#suggested_price')?.value) || null,
        notes: $('#notes')?.value || '',
      },
      fabrics: fabrics,
      notions: notions,
      labor: labor,
      colors: colors,
      variables: variables
    };
    console.log('📦 Full payload:', JSON.stringify(payload, null, 2));


    // ========================================
    // SEND SAVE REQUEST
    // ========================================
    try {
      const res = await fetch('/api/style/save', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(payload)
      });
      
      const out = await res.json().catch(() => ({}));
  
      if (res.ok && out.success) {
        alert(out.new ? '✅ New style created successfully!' : '✅ Style updated successfully!');
        // Set current style ID and load images
        if (out.style_id) {
          currentStyleId = out.style_id;
          await loadStyleImages(out.style_id);
        }
        // UPDATE URL WITH VENDOR_STYLE PARAMETER (without reloading page)
        const savedVendorStyle = $('#vendor_style')?.value.trim();
        if (savedVendorStyle) {
            const newUrl = new URL(window.location.href);
            newUrl.searchParams.set('vendor_style', savedVendorStyle);
            window.history.pushState({}, '', newUrl);
            
            console.log('✅ URL updated with vendor_style:', savedVendorStyle);
        }
      } else {
        alert('❌ Save failed: ' + (out.error || res.statusText));
      }
    } catch (error) {
      alert('❌ Save failed: ' + error.message);
    }
});

  $('#addFabric')?.addEventListener('click', () => {
    // Validate first row before allowing new row
    const firstVendor = document.querySelector('[data-fabric-vendor-id]')?.value;
    const firstFabric = document.querySelector('[data-fabric-id]')?.value;
    const firstYards = document.querySelector('[data-fabric-yds]')?.value;
    
    if (!firstVendor || !firstFabric || !firstYards) {
      alert('Please complete the first fabric row (Vendor, Fabric, and Yards) before adding another.');
      return;
    }
    const newRow = document.createElement('div');
    newRow.className = 'kv';
    
    const vendorOptionsHtml = fabricVendorOptions.map(opt => 
      `<option value="${opt.value}">${opt.text}</option>`
    ).join('');
    
    const fabricOptionsHtml = fabricOptions.map(opt => 
      `<option value="${opt.value}" data-cost="${opt.cost}" data-vendor="${opt.vendor}" data-fabric-code="${opt.fabricCode || ''}">${opt.text}</option>`
    ).join('');
    
    newRow.innerHTML = `
      <label>Vendor</label>
      <select class="form-select md" data-fabric-vendor-id>
        ${vendorOptionsHtml}
      </select>
      <label>Fabric</label>
      <select class="form-select md" data-fabric-id>
        ${fabricOptionsHtml}
      </select>
      <label style="display: flex; align-items: center; gap: 5px; white-space: nowrap;">
        <input type="checkbox" data-fabric-sublimation style="width: auto; margin: 0;">
        Sub.
      </label>
      <label>Cost/yd</label><input class="form-control w-110 text-end" type="number" step="0.01" value="" data-fabric-cost readonly>
      <label>Yards</label><input class="form-control w-110 text-end" type="number" step="0.01" value="" data-fabric-yds>
      <label>Total</label><input class="form-control w-110 text-end" value="" disabled data-fabric-total>
      <button type="button" class="btn btn-sm btn-danger" data-remove-btn>Remove</button>
    `;
    
    const addBtn = $('#addFabric').parentElement;
    addBtn.parentElement.insertBefore(newRow, addBtn);
    // Apply negative prevention to new row's number inputs
    newRow.querySelectorAll('input[type="number"]').forEach(input => {
      preventNegativeValues(input);
    });
    
    const fabricSelect = newRow.querySelector('[data-fabric-id]');
    fabricSelect?.addEventListener('change', function() {
      const opt = this.options[this.selectedIndex];
      if (opt.value) {
        const baseCost = parseFloat(opt.dataset.cost || 0);
        const sublimationCheckbox = newRow.querySelector('[data-fabric-sublimation]');
        const sublimationCost = sublimationCheckbox?.checked ? 6.00 : 0;
    
        newRow.querySelector('[data-fabric-cost]').value = (baseCost + sublimationCost).toFixed(2);
        newRow.querySelector('[data-fabric-vendor-id]').value = opt.dataset.vendor || '';
        recalcMaterials();
      }
    });

    // Add vendor filter for dynamic fabric row - ADD HERE
    const fabricVendorSelect = newRow.querySelector('[data-fabric-vendor-id]');
    fabricVendorSelect?.addEventListener('change', function() {
      const vendorId = this.value;
      const fabricSelect = newRow.querySelector('[data-fabric-id]');
      
      Array.from(fabricSelect.options).forEach(option => {
        if (option.value === '') {
          option.style.display = '';
        } else if (!vendorId) {
          option.style.display = '';
        } else {
          option.style.display = option.dataset.vendor === vendorId ? '' : 'none';
        }
      });
      
      fabricSelect.value = '';
      newRow.querySelector('[data-fabric-cost]').value = '';
    });

    // Sublimation checkbox handler for dynamically added rows
    const sublimationCheckbox = newRow.querySelector('[data-fabric-sublimation]');
    sublimationCheckbox?.addEventListener('change', function() {
      const fabricSelect = newRow.querySelector('[data-fabric-id]');
      const costInput = newRow.querySelector('[data-fabric-cost]');
      
      if (fabricSelect && fabricSelect.value && costInput) {
        const opt = fabricSelect.options[fabricSelect.selectedIndex];
        const baseCost = parseFloat(opt.dataset.cost || 0);
        const sublimationCost = this.checked ? 6.00 : 0;
        costInput.value = (baseCost + sublimationCost).toFixed(2);
        recalcMaterials();
      }
    });

    newRow.querySelector('[data-fabric-yds]')?.addEventListener('input', recalcMaterials);
    
    const removeBtn = newRow.querySelector('[data-remove-btn]');
    removeBtn?.addEventListener('click', function() {
      newRow.remove();
      recalcMaterials();
    });
  });

  $('#addNotion')?.addEventListener('click', () => {
    // Validate first row before allowing new row
    const firstVendor = document.querySelector('[data-notion-vendor-id]')?.value;
    const firstNotion = document.querySelector('[data-notion-id]')?.value;
    const firstQty = document.querySelector('[data-notion-qty]')?.value;
    
    if (!firstVendor || !firstNotion || !firstQty) {
      alert('Please complete the first notion row (Vendor, Notion, and Qty) before adding another.');
      return;
    }
    const newRow = document.createElement('div');
    newRow.className = 'kv';
    
    const vendorOptionsHtml = notionVendorOptions.map(opt => 
      `<option value="${opt.value}">${opt.text}</option>`
    ).join('');
    
    const notionOptionsHtml = notionOptions.map(opt => 
      `<option value="${opt.value}" data-cost="${opt.cost}" data-vendor="${opt.vendor}">${opt.text}</option>`
    ).join('');
    
    newRow.innerHTML = `
      <label>Vendor</label>
      <select class="form-select md" data-notion-vendor-id>
        ${vendorOptionsHtml}
      </select>
      <label>Notion</label>
      <select class="form-select md" data-notion-id>
        ${notionOptionsHtml}
      </select>
      <label>Cost</label><input class="form-control w-110 text-end" type="number" step="0.01" value="" data-notion-cost readonly>
      <label>Qty</label><input class="form-control qty text-end" type="number" step="1" value="" data-notion-qty>
      <label>Total</label><input class="form-control w-110 text-end" value="" disabled data-notion-total>
      <button type="button" class="btn btn-sm btn-danger" data-remove-btn>Remove</button>
    `;
    
    const addBtn = $('#addNotion').parentElement;
    addBtn.parentElement.insertBefore(newRow, addBtn);
    // Apply negative prevention to new row's number inputs
    newRow.querySelectorAll('input[type="number"]').forEach(input => {
      preventNegativeValues(input);
    });
    
    const notionSelect = newRow.querySelector('[data-notion-id]');
    notionSelect?.addEventListener('change', function() {
      const opt = this.options[this.selectedIndex];
      if (opt.value) {
        newRow.querySelector('[data-notion-cost]').value = opt.dataset.cost || '';
        newRow.querySelector('[data-notion-vendor-id]').value = opt.dataset.vendor || '';
        recalcMaterials();
      }
    });

    // Add vendor filter for dynamic notion row - ADD HERE
    const notionVendorSelect = newRow.querySelector('[data-notion-vendor-id]');
    notionVendorSelect?.addEventListener('change', function() {
      const vendorId = this.value;
      const notionSelect = newRow.querySelector('[data-notion-id]');
      
      Array.from(notionSelect.options).forEach(option => {
        if (option.value === '') {
          option.style.display = '';
        } else if (!vendorId) {
          option.style.display = '';
        } else {
          option.style.display = option.dataset.vendor === vendorId ? '' : 'none';
        }
      });
      
      notionSelect.value = '';
      newRow.querySelector('[data-notion-cost]').value = '';
    });
    
    newRow.querySelector('[data-notion-qty]')?.addEventListener('input', recalcMaterials);
    
    const removeBtn = newRow.querySelector('[data-remove-btn]');
    removeBtn?.addEventListener('click', function() {
      newRow.remove();
      recalcMaterials();
    });
  });

  // COLOR MANAGEMENT FUNCTIONS
  async function loadColors() {
    try {
      const res = await fetch('/api/colors');
      const colors = await res.json();
      
      const dropdown = $('#color_dropdown');
      if (dropdown) {
        dropdown.innerHTML = '<option value="">Select Color</option>';
        colors.forEach(color => {
          const opt = document.createElement('option');
          opt.value = color.id;
          opt.textContent = color.name;
          dropdown.appendChild(opt);
        });
      }
    } catch (e) {
      console.error('Failed to load colors:', e);
    }
  }

  window.addSelectedColor = function() {
    const dropdown = $('#color_dropdown');
    if (!dropdown || !dropdown.value) return;
    
    const selectedOption = dropdown.options[dropdown.selectedIndex];
    const colorName = selectedOption.text;
    const colorId = selectedOption.value;
    
    const colorList = $('#color_list');
    const existing = Array.from(colorList.options).find(opt => opt.value === colorId);
    if (existing) {
      alert('Color already added');
      return;
    }
    
    const option = document.createElement('option');
    option.text = colorName;
    option.value = colorId;
    colorList.add(option);
    
    dropdown.value = '';
  };

  window.addNewColor = async function() {
    const input = $('#new_color_input');
    const colorName = input.value.trim().toUpperCase();
    
    if (!colorName) {
      alert('Please enter a color name');
      return;
    }
    
    try {
      const res = await fetch('/api/colors', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name: colorName})
    });
      
      const data = await res.json();
      
      if (data.success) {
        const dropdown = $('#color_dropdown');
        const opt = document.createElement('option');
        opt.value = data.id;
        opt.textContent = data.name;
        dropdown.appendChild(opt);
        
        const colorList = $('#color_list');
        const existing = Array.from(colorList.options).find(o => o.value === data.id.toString());
        
        if (!existing) {
          const listOpt = document.createElement('option');
          listOpt.text = data.name;
          listOpt.value = data.id;
          colorList.add(listOpt);
        }
        
        input.value = '';
        
        if (data.existed) {
          alert('Color already existed in master list - added to selection');
        } else {
          alert('New color created and added!');
        }
      }
    } catch (e) {
      alert('Failed to create color: ' + e.message);
    }
  };

  window.removeSelectedColors = function() {
    const colorList = $('#color_list');
    if (!colorList) return;
    
    const selected = Array.from(colorList.selectedOptions);
    if (selected.length === 0) {
      alert('Please select colors to remove');
      return;
    }
    
    selected.forEach(opt => opt.remove());
  };


  // VARIABLE MANAGEMENT FUNCTIONS - ADD THIS ENTIRE BLOCK HERE
  async function loadVariables() {
    try {
      const res = await fetch('/api/variables');
      const variables = await res.json();
      
      const dropdown = $('#variable_dropdown');
      if (dropdown) {
        dropdown.innerHTML = '<option value="">Select Variable</option>';
        variables.forEach(variable => {
          const opt = document.createElement('option');
          opt.value = variable.id;
          opt.textContent = variable.name;
          dropdown.appendChild(opt);
        });
      }
    } catch (e) {
      console.error('Failed to load variables:', e);
    }
  }

  window.addSelectedVariable = function() {
    const dropdown = $('#variable_dropdown');
    if (!dropdown || !dropdown.value) return;
    
    const selectedOption = dropdown.options[dropdown.selectedIndex];
    const variableName = selectedOption.text;
    const variableId = selectedOption.value;
    
    const variableList = $('#variable_list');
    const existing = Array.from(variableList.options).find(opt => opt.value === variableId);
    if (existing) {
      alert('Variable already added');
      return;
    }
    
    const option = document.createElement('option');
    option.text = variableName;
    option.value = variableId;
    variableList.add(option);
    
    dropdown.value = '';
  };

  window.addNewVariable = async function() {
    const input = $('#new_variable_input');
    const variableName = input.value.trim().toUpperCase();
    
    if (!variableName) {
      alert('Please enter a variable name');
      return;
    }
    
    try {
      const res = await fetch('/api/variables', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({name: variableName})
      });
  
      const data = await res.json();
      
      if (data.success) {
        const dropdown = $('#variable_dropdown');
        const opt = document.createElement('option');
        opt.value = data.id;
        opt.textContent = data.name;
        dropdown.appendChild(opt);
        
        const variableList = $('#variable_list');
        const existing = Array.from(variableList.options).find(o => o.value === data.id.toString());
        
        if (!existing) {
          const listOpt = document.createElement('option');
          listOpt.text = data.name;
          listOpt.value = data.id;
          variableList.add(listOpt);
        }
        
        input.value = '';
        
        if (data.existed) {
          alert('Variable already existed in master list - added to selection');
        } else {
          alert('New variable created and added!');
        }
      }
    } catch (e) {
      alert('Failed to create variable: ' + e.message);
    }
  };

  window.removeSelectedVariables = function() {
    const variableList = $('#variable_list');
    if (!variableList) return;
    
    const selected = Array.from(variableList.selectedOptions);
    if (selected.length === 0) {
      alert('Please select variables to remove');
      return;
    }
    
    selected.forEach(opt => opt.remove());
  };

  // ============================================
  // IMAGE MANAGEMENT - BACKEND INTEGRATION
  // ============================================

  let currentStyleId = null;
  let isUploading = false;

  // Initialize image gallery with add button inside
  function initializeImageGallery() {
    const gallery = $('#imageGallery');
    if (!gallery) return;
    
    // Clear gallery first
    gallery.innerHTML = '';
    
    // Create add button inside gallery
    const addButton = document.createElement('div');
    addButton.className = 'add-image-box';
    addButton.id = 'addImageBox';
    addButton.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
      </svg>
      <span>Add Images</span>
    `;
    
    addButton.onclick = () => {
      if (!currentStyleId) {
        alert('Please save the style first before uploading images');
        return;
      }
      $('#imageUpload').click();
    };
    
    gallery.appendChild(addButton);
  }

  // Load images from backend
  async function loadStyleImages(styleId) {
    if (!styleId) return;
    
    currentStyleId = styleId;
    
    try {
      const res = await fetch(`/api/style/${styleId}/images`);
      if (!res.ok) throw new Error('Failed to load images');
      
      const images = await res.json();
      const gallery = $('#imageGallery');
      
      if (!gallery) return;
      
      // Remove all existing image items (keep add button)
      const imageItems = gallery.querySelectorAll('.image-item');
      imageItems.forEach(item => item.remove());
      
      // Add images after the add button
      images.forEach(img => {
        addImageToGallery(img.url, img.id, img.is_primary);
      });
      
    } catch (e) {
      console.error('Failed to load images:', e);
    }
  }

  // Add image to gallery (DOM only)
  function addImageToGallery(url, imageId, isPrimary = false) {
    const gallery = $('#imageGallery');
    if (!gallery) return;
    
    const imageItem = document.createElement('div');
    imageItem.className = 'image-item';
    imageItem.dataset.imageId = imageId;
    
    imageItem.innerHTML = `
      <img src="${url}" alt="Style image" onclick="openImageModal('${url}')">
      <button class="delete-btn" onclick="deleteImage(${imageId})" title="Delete image">×</button>
      ${isPrimary ? '<span class="primary-badge">Primary</span>' : ''}
    `;
    
    // Add to gallery (after add button)
    gallery.appendChild(imageItem);
  }

  // Upload image to backend
  async function uploadImageToBackend(file) {
    if (!currentStyleId) {
      alert('Please save the style first before uploading images');
      return false;
    }
    
    if (isUploading) {
      console.log('Already uploading...');
      return false;
    }
    
    isUploading = true;
    
    const gallery = $('#imageGallery');
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'image-item';
    loadingDiv.innerHTML = '<div class="image-loading"></div>';
    gallery.appendChild(loadingDiv);
    
    try {
      const formData = new FormData();

      // Ensure file has a proper name
      let fileToUpload = file;
      if (!file.name || file.name === 'blob' || file.name === '') {
        const timestamp = Date.now();
        const ext = file.type.split('/')[1] || 'png';
        fileToUpload = new File([file], `image-${timestamp}.${ext}`, { 
          type: file.type || 'image/png',
          lastModified: Date.now()
        });
        console.log('🔧 Created proper file object:', fileToUpload.name, fileToUpload.type, fileToUpload.size);
      }

      formData.append('image', fileToUpload);
      formData.append('csrf_token', getCsrfToken());

      // Debug: Check FormData contents
      console.log('📦 FormData prepared:');
      console.log('  - File name:', fileToUpload.name);
      console.log('  - File type:', fileToUpload.type);
      console.log('  - File size:', fileToUpload.size);
      for (let pair of formData.entries()) {
        console.log(`  - ${pair[0]}:`, pair[1]);
      }
      
      const res = await fetch(`/api/style/${currentStyleId}/upload-image`, {
        method: 'POST',
        // Don't set Content-Type header - let browser set it automatically for FormData
        body: formData
      });
      
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.error || 'Upload failed');
      }
      
      const data = await res.json();
      
      if (data.success) {
        loadingDiv.remove();
        addImageToGallery(data.url, data.id, data.is_primary);
        showNotification('Image uploaded successfully', 'success');
        return true;
      }
      
    } catch (e) {
      console.error('Upload failed:', e);
      loadingDiv.remove();
      showNotification('Failed to upload image: ' + e.message, 'error');
      return false;
    } finally {
      isUploading = false;
    }
  }
  // Delete image from backend
  window.deleteImage = async function(imageId) {
    if (!confirm('Delete this image?')) return;
    
    try {
      const res = await fetch(`/api/style-image/${imageId}`, {
        method: 'DELETE'
      });
      
      if (!res.ok) throw new Error('Failed to delete image');
      
      // Remove from DOM
      const imageItem = document.querySelector(`.image-item[data-image-id="${imageId}"]`);
      if (imageItem) imageItem.remove();
      
      showNotification('Image deleted', 'success');
      
    } catch (e) {
      console.error('Delete failed:', e);
      showNotification('Failed to delete image', 'error');
    }
  };

  // Handle file input change
  $('#imageUpload')?.addEventListener('change', async function(e) {
    const files = e.target.files;
    
    if (!currentStyleId) {
      alert('Please save the style first before uploading images');
      e.target.value = '';
      return;
    }
    
    for (let file of files) {
      if (file.type.startsWith('image/')) {
        await uploadImageToBackend(file);
      }
    }
    
    e.target.value = ''; // Reset input
  });

  // Enable paste functionality
  // ===== ENHANCED CLIPBOARD PASTE - WORKS WITH EXCEL =====
  document.addEventListener('paste', async function(e) {
    // Only handle paste when on the style page
    if (!currentStyleId) {
      console.log('No style loaded, ignoring paste');
      return;
    }
    
    const items = e.clipboardData?.items;
    if (!items) {
      console.log('No clipboard items');
      return;
    }
    
    console.log('📋 Clipboard items:', items.length);
    
    let imageFile = null;
    
    // Try to find image in clipboard items
    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      console.log(`Item ${i}: type=${item.type}, kind=${item.kind}`);
      
      // Check for any image type
      if (item.type.startsWith('image/')) {
        e.preventDefault(); // Prevent default paste
        
        console.log('✅ Found image in clipboard:', item.type);
        
        // ===== CRITICAL: Get blob and convert to File =====
        const blob = item.getAsFile();
        
        if (blob) {
          console.log('📦 Blob received:', blob.type, blob.size, 'bytes');
          
          // Create proper File object with filename
          const timestamp = Date.now();
          const ext = blob.type.split('/')[1] || 'png';
          const filename = `pasted-image-${timestamp}.${ext}`;
          
          // Convert Blob to File
          imageFile = new File([blob], filename, { 
            type: blob.type,
            lastModified: Date.now()
          });
          
          console.log('✅ Created File object:', imageFile.name, imageFile.type, imageFile.size);
          // ===== END CRITICAL =====
          
          break; // Found image, stop looking
        }
      }
    }
    
    if (imageFile) {
      // Show notification
      showNotification('Uploading pasted image...', 'info');
      
      try {
        // Upload the image
        const success = await uploadImageToBackend(imageFile);
        
        if (success) {
          showNotification('✅ Image pasted and uploaded successfully!', 'success');
        } else {
          showNotification('❌ Failed to upload pasted image', 'error');
        }
      } catch (error) {
        console.error('Paste upload error:', error);
        showNotification('❌ Error: ' + error.message, 'error');
      }
    } else {
      console.log('⚠️ No image data found in clipboard');
      
      // Debug: Show what was in clipboard
      for (let i = 0; i < items.length; i++) {
        console.log(`Clipboard item ${i}:`, items[i].type, items[i].kind);
      }
    }
  });

  console.log('✅ Enhanced clipboard paste enabled (Excel compatible)');
  // ===== END ENHANCED CLIPBOARD PASTE =====

  // ============================================
// PREVENT NEGATIVE NUMBERS IN REAL-TIME
// ============================================
function preventNegativeValues(input) {
  input.addEventListener('input', function() {
    if (this.value < 0) {
      this.value = 0;
    }
  });
  
  input.addEventListener('keydown', function(e) {
    if (e.key === '-' || e.key === 'Subtract') {
      e.preventDefault();
    }
  });
}

// Apply on page load
document.addEventListener('DOMContentLoaded', function() {
  const numberInputs = document.querySelectorAll(
    '[data-fabric-yds], [data-fabric-cost], [data-notion-qty], [data-notion-cost], [data-labor-qoh], #margin, #label_cost, #shipping_cost, #suggested_price'
  );
  
  numberInputs.forEach(input => {
    if (input.type === 'number') {
      preventNegativeValues(input);
    }
  });
  
  console.log('✅ Negative number prevention enabled on', numberInputs.length, 'fields');
});

  // Enable drag and drop on gallery
  const imageGallery = $('#imageGallery');
  if (imageGallery) {
    imageGallery.addEventListener('dragover', function(e) {
      e.preventDefault();
      this.style.borderColor = '#3b82f6';
      this.style.background = '#f0f7ff';
    });
    
    imageGallery.addEventListener('dragleave', function(e) {
      this.style.borderColor = '';
      this.style.background = '';
    });
    
    imageGallery.addEventListener('drop', async function(e) {
      e.preventDefault();
      this.style.borderColor = '';
      this.style.background = '';
      
      if (!currentStyleId) {
        alert('Please save the style first before uploading images');
        return;
      }
      
      const files = e.dataTransfer.files;
      for (let file of files) {
        if (file.type.startsWith('image/')) {
          await uploadImageToBackend(file);
        }
      }
    });
  }

  // Image zoom modal functions
  window.openImageModal = function(src) {
    const modal = $('#imageModal');
    const modalImg = $('#modalImage');
    if (modal && modalImg) {
      modal.classList.add('active');
      modalImg.src = src;
    }
  };

  window.closeImageModal = function() {
    const modal = $('#imageModal');
    if (modal) {
      modal.classList.remove('active');
    }
  };

  // Close modal on click outside
  $('#imageModal')?.addEventListener('click', function(e) {
    if (e.target === this) {
      closeImageModal();
    }
  });

  // Close modal on Escape key
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      closeImageModal();
    }
  });

  // Notification helper
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

  // Initialize gallery on page load
  initializeImageGallery();

  $('#add_var')?.addEventListener('click', ()=>{
    const v=$('#var_input')?.value.trim(); 
    if(!v) return;
    const o=document.createElement('option'); 
    o.text=v; 
    $('#var_list')?.add(o); 
    $('#var_input').value='';
  });

  const urlParams = new URLSearchParams(window.location.search);
  const vendorStyleParam = urlParams.get('vendor_style');
  if (vendorStyleParam) {
    const vendorStyleInput = $('#vendor_style');
    if (vendorStyleInput) {
      vendorStyleInput.dataset.touched = '1';
      vendorStyleInput.value = vendorStyleParam;
    }
    tryLoadByVendorStyle();
  }


  // STYLE SEARCH FUNCTIONALITY - ADD THIS ENTIRE BLOCK HERE
  const styleSearch = $('#styleSearch');
  const searchResults = $('#searchResults');
  let searchTimeout;

  styleSearch?.addEventListener('input', function() {
    const query = this.value.trim();
    
    clearTimeout(searchTimeout);
    
    if (query.length < 2) {
      searchResults.style.display = 'none';
      return;
    }
    
    searchTimeout = setTimeout(async () => {
      try {
        const res = await fetch(`/api/styles/search?q=${encodeURIComponent(query)}`);
        const styles = await res.json();
        
        if (styles.length === 0) {
          searchResults.innerHTML = '<div style="padding: 10px; color: #999;">No styles found</div>';
          searchResults.style.display = 'block';
          return;
        }
        
        searchResults.innerHTML = styles.map(s => `
          <div class="search-result-item" data-vendor-style="${s.vendor_style}" style="padding: 10px; cursor: pointer; border-bottom: 1px solid #eee;">
            <div style="font-weight: 600; color: #333;">${s.vendor_style}</div>
            <div style="font-size: 12px; color: #666;">${s.style_name}</div>
          </div>
        `).join('');
        
        searchResults.style.display = 'block';
        
        document.querySelectorAll('.search-result-item').forEach(item => {
          item.addEventListener('click', function() {
            const vendorStyle = this.dataset.vendorStyle;
            $('#vendor_style').value = vendorStyle;
            styleSearch.value = '';
            searchResults.style.display = 'none';
            tryLoadByVendorStyle();
          });
          
          item.addEventListener('mouseenter', function() {
            this.style.backgroundColor = '#f0f0f0';
          });
          
          item.addEventListener('mouseleave', function() {
            this.style.backgroundColor = 'white';
          });
        });
        
      } catch (e) {
        console.error('Search failed:', e);
      }
    }, 300);
  });

  // Only add event listeners if search elements exist
  if (styleSearch && searchResults) {
    document.addEventListener('click', function(e) {
      if (e.target !== styleSearch && e.target !== searchResults) {
        searchResults.style.display = 'none';
      }
    });

    styleSearch.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') {
        this.value = '';
        searchResults.style.display = 'none';
      }
    });
  }

});