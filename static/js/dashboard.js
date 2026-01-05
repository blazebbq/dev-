// Dashboard JavaScript
let currentUser = null;
let currentPage = 'dashboard';

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    await loadCurrentUser();
    setupNavigation();
    loadPage('dashboard');
});

// Load current user info
async function loadCurrentUser() {
    try {
        const response = await fetch('/api/auth/current-user');
        if (response.ok) {
            currentUser = await response.json();
            document.getElementById('userInfo').textContent = `Welcome, ${currentUser.full_name || currentUser.username}`;
            
            // Show users link for admins
            if (currentUser.role === 'ADMIN') {
                document.getElementById('usersLink').style.display = 'flex';
            }
        } else {
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('Error loading user:', error);
        window.location.href = '/login';
    }
}

// Setup navigation
function setupNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = item.dataset.page;
            if (page) {
                // Update active state
                document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
                item.classList.add('active');
                
                // Load page
                loadPage(page);
            }
        });
    });
}

// Load page content
async function loadPage(page) {
    currentPage = page;
    const contentArea = document.getElementById('contentArea');
    const pageTitle = document.getElementById('pageTitle');
    
    // Set page title
    const titles = {
        'dashboard': 'Dashboard',
        'products': 'Products',
        'warehouses': 'Warehouses & Bins',
        'stock': 'Stock Management',
        'workorders': 'Work Orders',
        'suppliers': 'Suppliers',
        'purchase-orders': 'Purchase Orders',
        'reports': 'Reports',
        'units': 'Units of Measure',
        'users': 'Users'
    };
    pageTitle.textContent = titles[page] || 'Dashboard';
    
    // Load page content
    contentArea.innerHTML = '<div class="loading">Loading...</div>';
    
    try {
        switch (page) {
            case 'dashboard':
                await loadDashboard();
                break;
            case 'products':
                await loadProducts();
                break;
            case 'warehouses':
                await loadWarehouses();
                break;
            case 'stock':
                await loadStock();
                break;
            case 'workorders':
                await loadWorkOrders();
                break;
            case 'suppliers':
                await loadSuppliers();
                break;
            case 'purchase-orders':
                await loadPurchaseOrders();
                break;
            case 'reports':
                await loadReports();
                break;
            case 'units':
                await loadUnits();
                break;
            case 'users':
                if (currentUser.role === 'ADMIN') {
                    await loadUsers();
                }
                break;
        }
    } catch (error) {
        console.error('Error loading page:', error);
        contentArea.innerHTML = '<div class="error">Error loading page. Please try again.</div>';
    }
}

// Logout
async function logout() {
    try {
        await fetch('/api/auth/logout', { method: 'POST' });
    } catch (error) {
        console.error('Error logging out:', error);
    }
    window.location.href = '/login';
}

// Dashboard
async function loadDashboard() {
    const [products, warehouses, stock, suppliers] = await Promise.all([
        fetch('/api/products').then(r => r.json()),
        fetch('/api/warehouses').then(r => r.json()),
        fetch('/api/stock/levels').then(r => r.json()),
        fetch('/api/suppliers').then(r => r.json())
    ]);
    
    const lowStock = stock.filter(s => s.needs_reorder);
    
    document.getElementById('contentArea').innerHTML = `
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Total Products</h3>
                <div class="value">${products.length}</div>
            </div>
            <div class="stat-card">
                <h3>Active Warehouses</h3>
                <div class="value">${warehouses.length}</div>
            </div>
            <div class="stat-card">
                <h3>Stock Items</h3>
                <div class="value">${stock.length}</div>
            </div>
            <div class="stat-card">
                <h3>Low Stock Items</h3>
                <div class="value">${lowStock.length}</div>
                ${lowStock.length > 0 ? '<div class="change negative">⚠️ Attention needed</div>' : ''}
            </div>
        </div>
        
        <div class="data-table-container">
            <div class="table-header">
                <h2>Low Stock Alert</h2>
            </div>
            ${lowStock.length > 0 ? `
                <table>
                    <thead>
                        <tr>
                            <th>Product SKU</th>
                            <th>Product Name</th>
                            <th>Current Stock</th>
                            <th>Reorder Point</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${lowStock.map(item => `
                            <tr>
                                <td>${item.product_sku}</td>
                                <td>${item.product_name}</td>
                                <td><span class="badge badge-danger">${item.current_stock}</span></td>
                                <td>${item.reorder_point}</td>
                                <td>
                                    <button class="btn btn-primary btn-small" onclick="createPOForProduct('${item.product_sku}')">
                                        Create PO
                                    </button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            ` : '<div class="empty-state"><div class="empty-state-icon">✅</div><p>All stock levels are healthy!</p></div>'}
        </div>
    `;
}

// Products
async function loadProducts() {
    const [products, units] = await Promise.all([
        fetch('/api/products').then(r => r.json()),
        fetch('/api/units').then(r => r.json()).catch(() => [])
    ]);
    
    document.getElementById('contentArea').innerHTML = `
        <div class="data-table-container">
            <div class="table-header">
                <h2>Products</h2>
                <div class="table-actions">
                    <button class="btn btn-primary" onclick="showProductModal()">➕ Add Product</button>
                </div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>SKU</th>
                        <th>Name</th>
                        <th>Description</th>
                        <th>Category</th>
                        <th>Unit</th>
                        <th>Price</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${products.map(p => `
                        <tr>
                            <td><strong>${p.sku}</strong></td>
                            <td>${p.name}</td>
                            <td>${p.description || '-'}</td>
                            <td>${p.category || '-'}</td>
                            <td>${p.custom_unit_name || p.unit_of_measure}</td>
                            <td>$${p.unit_price.toFixed(2)}</td>
                            <td><span class="badge badge-success">${p.status}</span></td>
                            <td>
                                <button class="btn btn-secondary btn-small" onclick="editProduct('${p.sku}')">Edit</button>
                                <button class="btn btn-danger btn-small" onclick="deleteProduct('${p.sku}')">Delete</button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
        
        <div id="productModal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2 id="productModalTitle">Add Product</h2>
                    <button class="btn-close" onclick="closeModal('productModal')">×</button>
                </div>
                <form id="productForm" onsubmit="saveProduct(event)">
                    <div class="form-grid">
                        <div class="form-group">
                            <label>SKU *</label>
                            <input type="text" name="sku" class="form-control" required>
                        </div>
                        <div class="form-group">
                            <label>Name *</label>
                            <input type="text" name="name" class="form-control" required>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Description</label>
                        <textarea name="description" class="form-control"></textarea>
                    </div>
                    <div class="form-grid">
                        <div class="form-group">
                            <label>Category</label>
                            <input type="text" name="category" class="form-control">
                        </div>
                        <div class="form-group">
                            <label>Unit of Measure</label>
                            <select name="unit_of_measure_id" class="form-control">
                                <option value="">Default (EA)</option>
                                ${units.map(u => `<option value="${u.id}">${u.name} (${u.code})</option>`).join('')}
                            </select>
                        </div>
                    </div>
                    <div class="form-grid">
                        <div class="form-group">
                            <label>Unit Price</label>
                            <input type="number" step="0.01" name="unit_price" class="form-control" value="0">
                        </div>
                        <div class="form-group">
                            <label>Reorder Point</label>
                            <input type="number" name="reorder_point" class="form-control" value="0">
                        </div>
                        <div class="form-group">
                            <label>Reorder Quantity</label>
                            <input type="number" name="reorder_quantity" class="form-control" value="0">
                        </div>
                    </div>
                    <button type="submit" class="btn btn-primary">Save Product</button>
                </form>
            </div>
        </div>
    `;
}

function showProductModal(sku = null) {
    const modal = document.getElementById('productModal');
    const form = document.getElementById('productForm');
    
    if (sku) {
        // Edit mode
        document.getElementById('productModalTitle').textContent = 'Edit Product';
        fetch(`/api/products/${sku}`)
            .then(r => r.json())
            .then(product => {
                form.elements.sku.value = product.sku;
                form.elements.sku.readOnly = true;
                form.elements.name.value = product.name;
                form.elements.description.value = product.description || '';
                form.elements.category.value = product.category || '';
                form.elements.unit_of_measure_id.value = product.unit_of_measure_id || '';
                form.elements.unit_price.value = product.unit_price;
                form.elements.reorder_point.value = product.reorder_point;
                form.elements.reorder_quantity.value = product.reorder_quantity;
            });
    } else {
        // Add mode
        document.getElementById('productModalTitle').textContent = 'Add Product';
        form.reset();
        form.elements.sku.readOnly = false;
    }
    
    modal.classList.add('show');
}

async function saveProduct(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    
    // Convert empty string to null for unit_of_measure_id
    if (!data.unit_of_measure_id) {
        data.unit_of_measure_id = null;
    }
    
    const isEdit = form.elements.sku.readOnly;
    const url = isEdit ? `/api/products/${data.sku}` : '/api/products';
    const method = isEdit ? 'PUT' : 'POST';
    
    try {
        const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            closeModal('productModal');
            loadProducts();
        } else {
            const error = await response.json();
            alert('Error: ' + (error.error || 'Failed to save product'));
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

function editProduct(sku) {
    showProductModal(sku);
}

async function deleteProduct(sku) {
    if (!confirm(`Are you sure you want to delete product ${sku}?`)) return;
    
    try {
        const response = await fetch(`/api/products/${sku}`, { method: 'DELETE' });
        if (response.ok) {
            loadProducts();
        } else {
            alert('Error deleting product');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Warehouses & Bins
async function loadWarehouses() {
    const warehouses = await fetch('/api/warehouses').then(r => r.json());
    
    document.getElementById('contentArea').innerHTML = `
        <div class="data-table-container">
            <div class="table-header">
                <h2>Warehouses</h2>
                <div class="table-actions">
                    <button class="btn btn-primary" onclick="showWarehouseModal()">➕ Add Warehouse</button>
                </div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Code</th>
                        <th>Name</th>
                        <th>Location</th>
                        <th>Manager</th>
                        <th>Capacity</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${warehouses.map(w => `
                        <tr>
                            <td><strong>${w.code}</strong></td>
                            <td>${w.name}</td>
                            <td>${w.location || '-'}</td>
                            <td>${w.manager || '-'}</td>
                            <td>${w.capacity || '-'}</td>
                            <td><span class="badge badge-success">${w.status}</span></td>
                            <td>
                                <button class="btn btn-secondary btn-small" onclick="viewBins('${w.code}')">View Bins</button>
                                <button class="btn btn-secondary btn-small" onclick="editWarehouse('${w.code}')">Edit</button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

async function viewBins(warehouseCode) {
    const bins = await fetch(`/api/bins?warehouse=${warehouseCode}`).then(r => r.json()).catch(() => []);
    
    const modal = document.createElement('div');
    modal.className = 'modal show';
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 800px;">
            <div class="modal-header">
                <h2>Bins in ${warehouseCode}</h2>
                <button class="btn-close" onclick="this.closest('.modal').remove()">×</button>
            </div>
            <button class="btn btn-primary" onclick="showBinModal('${warehouseCode}')">➕ Add Bin</button>
            <br><br>
            <table>
                <thead>
                    <tr>
                        <th>Bin Code</th>
                        <th>Aisle</th>
                        <th>Rack</th>
                        <th>Level</th>
                        <th>Type</th>
                        <th>Capacity</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${bins.length > 0 ? bins.map(b => `
                        <tr>
                            <td><strong>${b.code}</strong></td>
                            <td>${b.aisle || '-'}</td>
                            <td>${b.rack || '-'}</td>
                            <td>${b.level || '-'}</td>
                            <td>${b.bin_type || '-'}</td>
                            <td>${b.capacity || '-'}</td>
                            <td>
                                <button class="btn btn-secondary btn-small" onclick="viewBinStock(${b.id})">Stock</button>
                                <button class="btn btn-danger btn-small" onclick="deleteBin(${b.id})">Delete</button>
                            </td>
                        </tr>
                    `).join('') : '<tr><td colspan="7" style="text-align:center;">No bins found. Add bins to organize stock.</td></tr>'}
                </tbody>
            </table>
        </div>
    `;
    document.body.appendChild(modal);
}

function showBinModal(warehouseCode) {
    const modal = document.createElement('div');
    modal.className = 'modal show';
    modal.id = 'binModal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>Add Bin</h2>
                <button class="btn-close" onclick="this.closest('.modal').remove()">×</button>
            </div>
            <form onsubmit="saveBin(event, '${warehouseCode}')">
                <div class="form-grid">
                    <div class="form-group">
                        <label>Bin Code *</label>
                        <input type="text" name="code" class="form-control" required>
                    </div>
                    <div class="form-group">
                        <label>Aisle</label>
                        <input type="text" name="aisle" class="form-control">
                    </div>
                    <div class="form-group">
                        <label>Rack</label>
                        <input type="text" name="rack" class="form-control">
                    </div>
                    <div class="form-group">
                        <label>Level</label>
                        <input type="text" name="level" class="form-control">
                    </div>
                    <div class="form-group">
                        <label>Bin Type</label>
                        <select name="bin_type" class="form-control">
                            <option value="STORAGE">Storage</option>
                            <option value="PICKING">Picking</option>
                            <option value="RECEIVING">Receiving</option>
                            <option value="SHIPPING">Shipping</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Capacity</label>
                        <input type="number" name="capacity" class="form-control">
                    </div>
                </div>
                <button type="submit" class="btn btn-primary">Save Bin</button>
            </form>
        </div>
    `;
    document.body.appendChild(modal);
}

async function saveBin(event, warehouseCode) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData.entries());
    data.warehouse_code = warehouseCode;
    
    try {
        const response = await fetch('/api/bins', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            event.target.closest('.modal').remove();
            // Reload bins view
            viewBins(warehouseCode);
        } else {
            const error = await response.json();
            alert('Error: ' + (error.error || 'Failed to save bin'));
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Stock Management
async function loadStock() {
    const stock = await fetch('/api/stock/levels').then(r => r.json());
    
    document.getElementById('contentArea').innerHTML = `
        <div class="data-table-container">
            <div class="table-header">
                <h2>Current Stock Levels</h2>
                <div class="table-actions">
                    <button class="btn btn-primary" onclick="showStockReceiptModal()">📥 Receive Stock</button>
                    <button class="btn btn-secondary" onclick="showStockIssueModal()">📤 Issue Stock</button>
                    <button class="btn btn-secondary" onclick="showStockTransferModal()">🔄 Transfer Stock</button>
                </div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Product SKU</th>
                        <th>Product Name</th>
                        <th>On Hand</th>
                        <th>Available</th>
                        <th>Reserved</th>
                        <th>Reorder Point</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${stock.map(s => `
                        <tr>
                            <td><strong>${s.product_sku}</strong></td>
                            <td>${s.product_name}</td>
                            <td>${s.total_on_hand}</td>
                            <td>${s.total_available}</td>
                            <td>${s.total_reserved}</td>
                            <td>${s.reorder_point}</td>
                            <td>
                                <span class="badge ${s.needs_reorder ? 'badge-danger' : 'badge-success'}">
                                    ${s.needs_reorder ? '⚠️ Reorder' : '✓ OK'}
                                </span>
                            </td>
                            <td>
                                <button class="btn btn-secondary btn-small" onclick="viewStockDetails('${s.product_sku}')">Details</button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

// Work Orders
async function loadWorkOrders() {
    const workOrders = await fetch('/api/work-orders').then(r => r.json()).catch(() => []);
    
    document.getElementById('contentArea').innerHTML = `
        <div class="data-table-container">
            <div class="table-header">
                <h2>Work Orders</h2>
                <div class="table-actions">
                    <button class="btn btn-primary" onclick="showWorkOrderModal()">➕ Create Work Order</button>
                </div>
            </div>
            ${workOrders.length > 0 ? `
                <table>
                    <thead>
                        <tr>
                            <th>Order #</th>
                            <th>Type</th>
                            <th>Warehouse</th>
                            <th>Status</th>
                            <th>Priority</th>
                            <th>Assigned To</th>
                            <th>Created</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${workOrders.map(wo => `
                            <tr>
                                <td><strong>${wo.order_number}</strong></td>
                                <td>${wo.order_type}</td>
                                <td>${wo.warehouse_code || '-'}</td>
                                <td><span class="badge badge-info">${wo.status}</span></td>
                                <td><span class="badge ${wo.priority === 'URGENT' ? 'badge-danger' : 'badge-info'}">${wo.priority}</span></td>
                                <td>${wo.assigned_user_name || '-'}</td>
                                <td>${new Date(wo.created_at).toLocaleDateString()}</td>
                                <td>
                                    <button class="btn btn-secondary btn-small" onclick="viewWorkOrder('${wo.order_number}')">View</button>
                                    <button class="btn btn-success btn-small" onclick="printPickList('${wo.order_number}')">🖨️ Print</button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            ` : '<div class="empty-state"><div class="empty-state-icon">📝</div><p>No work orders yet. Create one to get started!</p></div>'}
        </div>
    `;
}

// Units of Measure
async function loadUnits() {
    const units = await fetch('/api/units').then(r => r.json()).catch(() => []);
    
    document.getElementById('contentArea').innerHTML = `
        <div class="data-table-container">
            <div class="table-header">
                <h2>Units of Measure</h2>
                <div class="table-actions">
                    <button class="btn btn-primary" onclick="showUnitModal()">➕ Add Unit</button>
                </div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Code</th>
                        <th>Name</th>
                        <th>Description</th>
                        <th>Type</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${units.length > 0 ? units.map(u => `
                        <tr>
                            <td><strong>${u.code}</strong></td>
                            <td>${u.name}</td>
                            <td>${u.description || '-'}</td>
                            <td>${u.unit_type || '-'}</td>
                            <td><span class="badge badge-success">${u.is_active ? 'Active' : 'Inactive'}</span></td>
                            <td>
                                <button class="btn btn-secondary btn-small" onclick="editUnit(${u.id})">Edit</button>
                                <button class="btn btn-danger btn-small" onclick="deleteUnit(${u.id})">Delete</button>
                            </td>
                        </tr>
                    `).join('') : '<tr><td colspan="6" style="text-align:center;">No custom units defined. Add units like grams, liters, etc.</td></tr>'}
                </tbody>
            </table>
        </div>
        
        <div id="unitModal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2 id="unitModalTitle">Add Unit of Measure</h2>
                    <button class="btn-close" onclick="closeModal('unitModal')">×</button>
                </div>
                <form id="unitForm" onsubmit="saveUnit(event)">
                    <div class="form-grid">
                        <div class="form-group">
                            <label>Code *</label>
                            <input type="text" name="code" class="form-control" required placeholder="e.g., G, KG, L">
                        </div>
                        <div class="form-group">
                            <label>Name *</label>
                            <input type="text" name="name" class="form-control" required placeholder="e.g., Grams, Kilograms">
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Description</label>
                        <input type="text" name="description" class="form-control" placeholder="Description of the unit">
                    </div>
                    <div class="form-grid">
                        <div class="form-group">
                            <label>Unit Type</label>
                            <select name="unit_type" class="form-control">
                                <option value="">Select type</option>
                                <option value="WEIGHT">Weight</option>
                                <option value="VOLUME">Volume</option>
                                <option value="LENGTH">Length</option>
                                <option value="COUNT">Count</option>
                                <option value="TIME">Time</option>
                                <option value="OTHER">Other</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Base Unit (for conversions)</label>
                            <input type="text" name="base_unit" class="form-control" placeholder="e.g., G for grams">
                        </div>
                        <div class="form-group">
                            <label>Conversion Factor</label>
                            <input type="number" step="0.000001" name="conversion_factor" class="form-control" placeholder="e.g., 1000 for KG to G">
                        </div>
                    </div>
                    <button type="submit" class="btn btn-primary">Save Unit</button>
                </form>
            </div>
        </div>
    `;
}

function showUnitModal(unitId = null) {
    const modal = document.getElementById('unitModal');
    const form = document.getElementById('unitForm');
    
    if (unitId) {
        document.getElementById('unitModalTitle').textContent = 'Edit Unit of Measure';
        fetch(`/api/units/${unitId}`)
            .then(r => r.json())
            .then(unit => {
                form.elements.code.value = unit.code;
                form.elements.code.readOnly = true;
                form.elements.name.value = unit.name;
                form.elements.description.value = unit.description || '';
                form.elements.unit_type.value = unit.unit_type || '';
                form.elements.base_unit.value = unit.base_unit || '';
                form.elements.conversion_factor.value = unit.conversion_factor || '';
            });
    } else {
        document.getElementById('unitModalTitle').textContent = 'Add Unit of Measure';
        form.reset();
        form.elements.code.readOnly = false;
    }
    
    modal.classList.add('show');
}

async function saveUnit(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    
    const isEdit = form.elements.code.readOnly;
    const url = isEdit ? `/api/units/${data.code}` : '/api/units';
    const method = isEdit ? 'PUT' : 'POST';
    
    try {
        const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            closeModal('unitModal');
            loadUnits();
        } else {
            const error = await response.json();
            alert('Error: ' + (error.error || 'Failed to save unit'));
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

function editUnit(unitId) {
    showUnitModal(unitId);
}

async function deleteUnit(unitId) {
    if (!confirm('Are you sure you want to delete this unit?')) return;
    
    try {
        const response = await fetch(`/api/units/${unitId}`, { method: 'DELETE' });
        if (response.ok) {
            loadUnits();
        } else {
            alert('Error deleting unit');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Reports (placeholder)
async function loadReports() {
    document.getElementById('contentArea').innerHTML = `
        <div class="stats-grid">
            <div class="stat-card" style="cursor:pointer;" onclick="generateReport('inventory-valuation')">
                <h3>📊 Inventory Valuation</h3>
                <p>View total inventory value</p>
            </div>
            <div class="stat-card" style="cursor:pointer;" onclick="generateReport('stock-movement')">
                <h3>📈 Stock Movement</h3>
                <p>Transaction history</p>
            </div>
            <div class="stat-card" style="cursor:pointer;" onclick="generateReport('abc-analysis')">
                <h3>🎯 ABC Analysis</h3>
                <p>Product classification</p>
            </div>
            <div class="stat-card" style="cursor:pointer;" onclick="generateReport('warehouse-utilization')">
                <h3>🏢 Warehouse Utilization</h3>
                <p>Space usage report</p>
            </div>
        </div>
    `;
}

async function generateReport(reportType) {
    const response = await fetch(`/api/reports/${reportType}`);
    const data = await response.json();
    
    const modal = document.createElement('div');
    modal.className = 'modal show';
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 900px;">
            <div class="modal-header">
                <h2>${reportType.replace(/-/g, ' ').toUpperCase()}</h2>
                <button class="btn-close" onclick="this.remove()">×</button>
            </div>
            <pre style="background:#f5f5f5;padding:20px;border-radius:5px;overflow:auto;">${JSON.stringify(data, null, 2)}</pre>
        </div>
    `;
    document.body.appendChild(modal);
}

// Suppliers & Purchase Orders (placeholder functions)
async function loadSuppliers() {
    document.getElementById('contentArea').innerHTML = '<div class="empty-state"><div class="empty-state-icon">🤝</div><p>Supplier management interface coming soon!</p></div>';
}

async function loadPurchaseOrders() {
    document.getElementById('contentArea').innerHTML = '<div class="empty-state"><div class="empty-state-icon">💼</div><p>Purchase order management interface coming soon!</p></div>';
}

async function loadUsers() {
    document.getElementById('contentArea').innerHTML = '<div class="empty-state"><div class="empty-state-icon">👥</div><p>User management interface coming soon!</p></div>';
}

// Helper functions
function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('show');
}

function showStockReceiptModal() {
    alert('Stock receipt modal coming soon!');
}

function showStockIssueModal() {
    alert('Stock issue modal coming soon!');
}

function showStockTransferModal() {
    alert('Stock transfer modal coming soon!');
}

function viewStockDetails(sku) {
    alert(`Stock details for ${sku} coming soon!`);
}

function showWorkOrderModal() {
    alert('Work order creation modal coming soon!');
}

function viewWorkOrder(orderNumber) {
    alert(`Work order ${orderNumber} details coming soon!`);
}

function printPickList(orderNumber) {
    window.open(`/api/work-orders/${orderNumber}/pick-list`, '_blank');
}

function showWarehouseModal() {
    alert('Warehouse management modal coming soon!');
}

function editWarehouse(code) {
    alert(`Edit warehouse ${code} coming soon!`);
}

function createPOForProduct(sku) {
    alert(`Create PO for ${sku} coming soon!`);
}
