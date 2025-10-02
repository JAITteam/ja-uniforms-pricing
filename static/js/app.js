document.addEventListener('DOMContentLoaded', () => {
  const $ = s => document.querySelector(s);
  const fmt = n => '$' + (Number(n||0).toFixed(2));
  const set = (sel, val) => { const el = $(sel); if (el) el.value = (val ?? ""); };
  const setText = (sel, txt) => { const el = $(sel); if (el) el.textContent = (txt ?? ""); };

  // Load colors on page load
  loadColors();
  loadVariables(); 

  // Capture dropdown options once at page load for dynamic row creation
  const fabricVendorOptions = Array.from($('[data-fabric-vendor-id]').options).map(opt => ({
    value: opt.value,
    text: opt.text
  }));

  const notionVendorOptions = Array.from($('[data-notion-vendor-id]').options).map(opt => ({
    value: opt.value,
    text: opt.text
  }));

  const fabricOptions = Array.from($('[data-fabric-id]').options).map(opt => ({
    value: opt.value,
    text: opt.text,
    cost: opt.dataset.cost || '',
    vendor: opt.dataset.vendor || ''
  }));

  const notionOptions = Array.from($('[data-notion-id]').options).map(opt => ({
    value: opt.value,
    text: opt.text,
    cost: opt.dataset.cost || '',
    vendor: opt.dataset.vendor || ''
  }));

  // Auto Vendor Style
  function buildVendorStyle(){
    const base=$('#base_item_number')?.value.trim() || '';
    const variant=$('#variant_code')?.value.trim() || '';
    const fabric=$('#fabric_code')?.value.trim() || '';
    // Always concatenate all parts that exist
    const parts = [];
    if (base) parts.push(base);
    if (variant) parts.push(variant);
    if (fabric) parts.push(fabric);
    
    const auto = parts.join('-');
    const input = $('#vendor_style');
    
    // Always update vendor style with concatenation
    if (input) {
      input.value = auto;
      input.dataset.touched = '0'; // Reset touched flag
    }
    
    // Update snapshot
    setText('#snap_vendor_style', auto || '(vendor style)');
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
  ['#base_item_number','#variant_code','#fabric_code'].forEach(sel=> 
    $(sel)?.addEventListener('input', buildVendorStyle)
  );

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
  $('#garment_type')?.addEventListener('change', async function() {
    const garmentType = this.value;
    
    if (!garmentType) {
      $('#cleaning_cost').value = '';
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
        $('#cleaning_cost').value = '';
        recalcLabor();
      }
    } catch (e) {
      console.error('Failed to fetch cleaning cost:', e);
      $('#cleaning_cost').value = '';
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
    const labels=+( $('#label_cost')?.value || 0 );
    const ship=+( $('#shipping_cost')?.value || 0 );
    const total=mat+lab+labels+ship;
    setText('#snap_total', fmt(total));
    if ($('#total_reg')) $('#total_reg').value = total ? fmt(total) : '';
    if ($('#total_ext')) $('#total_ext').value = total ? fmt(total*1.15) : '';
    const m=Math.max(0,Math.min(95,+($('#margin')?.value||60)));
    const retail= total ? (total/(1-(m/100))) : 0; 
    if ($('#retail_price')) $('#retail_price').value = retail ? fmt(retail) : '';
    const sp=+($('#suggested_price')?.value||0);
    if (sp > 0 && total > 0) {
      const sugg = Math.max(0, Math.min(95, ((sp - total) / sp) * 100));
      $('#suggested_margin').value = sugg.toFixed(0);
    } else {
      $('#suggested_margin').value = '';
    }
  }
  
  // Bidirectional: Change suggested price → calculate margin
  $('#suggested_price')?.addEventListener('input', function() {
    const sp = parseFloat(this.value) || 0;
    const total = parseFloat((($('#snap_total')?.textContent)||'').replace('$',''))||0;
  
    if (sp > 0 && total > 0) {
      const margin = ((sp - total) / sp) * 100;
      $('#suggested_margin').value = Math.max(0, Math.min(95, margin)).toFixed(0);
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

  $('#vendor_style')?.addEventListener('blur', tryLoadByVendorStyle);
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
    set('#size_range', s.size_range);
    set('#margin', s.margin || 60);
    set('#label_cost', s.label_cost || 0.20);
    set('#shipping_cost', s.shipping_cost || 0.00);
    set('#suggested_price', s.suggested_price || '');
    setText('#snap_vendor_style', s.vendor_style || $('#vendor_style')?.value || '(vendor style)');

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
    const styleName = $('#style_name')?.value.trim();
    if (!styleName) { 
      alert('Enter a Style Name before saving.'); 
      return; 
    }

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

    // Collect variables - ADD THIS ENTIRE BLOCK
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

    const payload = {
      style: {
        style_name: styleName,
        vendor_style: $('#vendor_style')?.value.trim() || '',
        base_item_number: $('#base_item_number')?.value.trim() || '',
        variant_code: $('#variant_code')?.value.trim() || '',
        gender: $('#gender')?.value || 'MENS',
        garment_type: $('#garment_type')?.value?.trim() || '',
        size_range: $('#size_range')?.value?.trim() || 'XS-4XL',
        margin: parseFloat($('#margin')?.value) || 60.0,
        label_cost: parseFloat($('#label_cost')?.value) || 0.20,
        shipping_cost: parseFloat($('#shipping_cost')?.value) || 0.00,
        suggested_price: parseFloat($('#suggested_price')?.value) || null,
      },
      fabrics: fabrics,
      notions: notions,
      labor: labor,
      colors: colors,
      variables: variables
    };

    try {
      const res = await fetch('/api/style/save', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
      });
      
      const out = await res.json().catch(() => ({}));
      
      if (res.ok && out.ok) {
        alert(out.new ? 'Created new style!' : 'Updated style.');
        // Set current style ID and load images
        if (out.style_id) {
          currentStyleId = out.style_id;
          await loadStyleImages(out.style_id);
        }
      } else {
        alert('Save failed: ' + (out.error || res.statusText));
    }
  } catch (error) {
    alert('Save failed: ' + error.message);
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
      `<option value="${opt.value}" data-cost="${opt.cost}" data-vendor="${opt.vendor}">${opt.text}</option>`
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

  // IMAGE MANAGEMENT - ADD THIS ENTIRE BLOCK HERE
  let currentStyleId = null;

  async function loadStyleImages(styleId) {
    currentStyleId = styleId;
    const res = await fetch(`/api/style/${styleId}/images`);
    const images = await res.json();
    
    const gallery = $('#imageGallery');
    if (!gallery) return;
    
    gallery.innerHTML = '';
    
    if (images.length === 0) {
      gallery.innerHTML = '<div style="grid-column: 1/-1; text-align: center; color: #999;">No images yet</div>';
      return;
    }
    
    images.forEach(img => {
      const imgDiv = document.createElement('div');
      imgDiv.style.position = 'relative';
      imgDiv.innerHTML = `
        <img src="${img.url}" style="width: 100%; height: 120px; object-fit: cover; border-radius: 4px; border: 2px solid #ddd;">
        <button onclick="deleteImage(${img.id})" style="position: absolute; top: 2px; right: 2px; background: #dc3545; color: white; border: none; border-radius: 50%; width: 22px; height: 22px; cursor: pointer; font-weight: bold;">×</button>
        ${img.is_primary ? '<span style="position: absolute; bottom: 2px; left: 2px; background: #28a745; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px; font-weight: bold;">Primary</span>' : ''}
      `;
      gallery.appendChild(imgDiv);
    });
  }

$('#imageUpload')?.addEventListener('change', async function(e) {
  const file = e.target.files[0];
  if (!file || !currentStyleId) {
    alert('Please save the style first before uploading images');
    e.target.value = '';
    return;
  }
  
  const formData = new FormData();
  formData.append('image', file);
  
  const res = await fetch(`/api/style/${currentStyleId}/upload-image`, {
    method: 'POST',
    body: formData
  });
  
  if (res.ok) {
    await loadStyleImages(currentStyleId);
    e.target.value = '';
  } else {
    const error = await res.json();
    alert('Failed to upload image: ' + (error.error || 'Unknown error'));
  }
});

window.deleteImage = async function(imageId) {
  if (!confirm('Delete this image?')) return;
  
  const res = await fetch(`/api/style-image/${imageId}`, {
    method: 'DELETE'
  });
  
  if (res.ok) {
    await loadStyleImages(currentStyleId);
  } else {
    alert('Failed to delete image');
  }
};
  



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

  document.addEventListener('click', function(e) {
    if (e.target !== styleSearch && e.target !== searchResults) {
      searchResults.style.display = 'none';
    }
  });

  styleSearch?.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      this.value = '';
      searchResults.style.display = 'none';
    }
  });

});