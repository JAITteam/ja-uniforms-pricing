document.addEventListener('DOMContentLoaded', () => {
  const $ = s => document.querySelector(s);
  const fmt = n => '$' + (Number(n||0).toFixed(2));
  const set = (sel, val) => { const el = $(sel); if (el) el.value = (val ?? ""); };
  const setText = (sel, txt) => { const el = $(sel); if (el) el.textContent = (txt ?? ""); };

  // Load colors on page load
  loadColors();

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
    const parts=[]; if(base)parts.push(base);
    if(variant && variant.toUpperCase()!=='BASE') parts.push(variant);
    if(fabric && fabric.toUpperCase()!=='F6') parts.push(fabric);
    const auto=parts.join('-'); const input=$('#vendor_style');
    if(input && !input.dataset.touched) input.value=auto;
    setText('#snap_vendor_style', (input?.value || auto || '(vendor style)'));
  }
  ['#base_item_number','#variant_code','#fabric_code'].forEach(sel=> $(sel)?.addEventListener('input',buildVendorStyle));
  $('#vendor_style')?.addEventListener('input',e=> e.target.dataset.touched='1');

  // Fabric dropdown - auto-fill cost when selected (first row only)
  $('[data-fabric-id]')?.addEventListener('change', function() {
    const opt = this.options[this.selectedIndex];
    if (opt.value) {
      const row = this.closest('.kv');
      row.querySelector('[data-fabric-cost]').value = opt.dataset.cost || '';
      row.querySelector('[data-fabric-vendor-id]').value = opt.dataset.vendor || '';
      recalcMaterials();
    }
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
 
  // Garment type - auto-fill cleaning cost
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
    //const sugg = sp ? ((sp-total)/sp)*100 : 0; 
    if (sp > 0 && total > 0) {
      const sugg = Math.max(0, Math.min(95, ((sp - total) / sp) * 100));
      $('#suggested_margin').value = sugg.toFixed(0);
    } else {
      $('#suggested_margin').value = '';
    }
    //if ($('#suggested_margin')) $('#suggested_margin').value = sp ? (sugg.toFixed(0)+'%') : '';
    //if ($('#suggested_margin')) $('#suggested_margin').value = sp && total > 0 ? sugg.toFixed(0) : '';
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
  // KEEP ONLY THIS:
  $('#margin')?.addEventListener('input', recalcTotals);

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
    set('#margin', s.margin || 60);  // NEW
    set('#label_cost', s.label_cost || 0.20);  // NEW
    set('#shipping_cost', s.shipping_cost || 0.00);  // NEW
    set('#suggested_price', s.suggested_price || '');  // NEW

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
        $('[data-fabric-cost]').value = f.cost_per_yard;
        $('[data-fabric-yds]').value = f.yards;
        if (f.vendor_id) $('[data-fabric-vendor-id]').value = f.vendor_id;
      } else {
        $('#addFabric').click();
        const allFabricSelects = document.querySelectorAll('[data-fabric-id]');
        const newRow = allFabricSelects[allFabricSelects.length - 1].closest('.kv');
        newRow.querySelector('[data-fabric-id]').value = f.fabric_id;
        newRow.querySelector('[data-fabric-cost]').value = f.cost_per_yard;
        newRow.querySelector('[data-fabric-yds]').value = f.yards;
        if (f.vendor_id) newRow.querySelector('[data-fabric-vendor-id]').value = f.vendor_id;
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

    // Load colors - NEW
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

    recalcMaterials();
    recalcLabor();
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
        
        fabrics.push({
          vendor: vendorOpt?.text || '',
          name: opt.text,
          cost_per_yard: +(row.querySelector('[data-fabric-cost]')?.value || 0),
          yards: +(row.querySelector('[data-fabric-yds]')?.value || 0),
          primary: fabrics.length === 0
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

    const payload = {
      style: {
        style_name: styleName,
        vendor_style: $('#vendor_style')?.value.trim() || '',
        base_item_number: $('#base_item_number')?.value.trim() || '',
        variant_code: $('#variant_code')?.value.trim() || '',
        gender: $('#gender')?.value || 'MENS',
        garment_type: $('#garment_type')?.value?.trim() || '',
        size_range: $('#size_range')?.value?.trim() || 'XS-4XL',
        margin: parseFloat($('#margin')?.value) || 60.0,  // NEW
        label_cost: parseFloat($('#label_cost')?.value) || 0.20,  // NEW
        shipping_cost: parseFloat($('#shipping_cost')?.value) || 0.00,  // NEW
        suggested_price: parseFloat($('#suggested_price')?.value) || null,  // NEW
      },
      fabrics: fabrics,
      notions: notions,
      labor: labor,
      colors: colors
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
      } else {
        alert('Save failed: ' + (out.error || res.statusText));
      }
    } catch (error) {
      alert('Save failed: ' + error.message);
    }
  });

  $('#addFabric')?.addEventListener('click', () => {
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
        newRow.querySelector('[data-fabric-cost]').value = opt.dataset.cost || '';
        newRow.querySelector('[data-fabric-vendor-id]').value = opt.dataset.vendor || '';
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
    $('#vendor_style').value = vendorStyleParam;
    setTimeout(() => {
      tryLoadByVendorStyle();
    }, 100);
  }
});