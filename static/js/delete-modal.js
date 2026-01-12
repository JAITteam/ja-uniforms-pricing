// ============================================
// DELETE VENDOR MODAL - Vanilla JS Version
// For Flask/Jinja2 Projects
// ============================================

class DeleteModal {
    constructor() {
        this.modal = null;
        this.onConfirmCallback = null;
        this.init();
    }

    init() {
        // Create modal HTML
        const modalHTML = `
            <div id="deleteVendorModal" class="delete-modal" style="display: none;">
                <!-- Overlay -->
                <div class="delete-modal-overlay"></div>
                
                <!-- Modal Content -->
                <div class="delete-modal-content">
                    <!-- Header with Gradient -->
                    <div class="delete-modal-header">
                        <div class="delete-modal-header-left">
                            <div class="delete-modal-icon">
                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                                    <line x1="12" y1="9" x2="12" y2="13"></line>
                                    <line x1="12" y1="17" x2="12.01" y2="17"></line>
                                </svg>
                            </div>
                            <h3 class="delete-modal-title" id="deleteModalTitle">Delete Notion Vendor?</h3>
                        </div>
                        <button class="delete-modal-close" id="deleteModalClose">
                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <line x1="18" y1="6" x2="6" y2="18"></line>
                                <line x1="6" y1="6" x2="18" y2="18"></line>
                            </svg>
                        </button>
                    </div>

                    <!-- Body -->
                    <div class="delete-modal-body">
                        <p id="deleteModalMessage">
                            This may affect existing styles and configurations. 
                            This action <strong>cannot be undone</strong>.
                        </p>
                    </div>

                    <!-- Footer -->
                    <div class="delete-modal-footer">
                        <button class="delete-modal-btn delete-modal-btn-cancel" id="deleteModalCancel">
                            Cancel
                        </button>
                        <button class="delete-modal-btn delete-modal-btn-delete" id="deleteModalConfirm">
                            Delete Vendor
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Inject into DOM
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.modal = document.getElementById('deleteVendorModal');

        // Attach event listeners
        this.attachEvents();
    }

    attachEvents() {
        // Close buttons
        document.getElementById('deleteModalClose').addEventListener('click', () => this.hide());
        document.getElementById('deleteModalCancel').addEventListener('click', () => this.hide());
        
        // Overlay click
        this.modal.querySelector('.delete-modal-overlay').addEventListener('click', () => this.hide());
        
        // Confirm button
        document.getElementById('deleteModalConfirm').addEventListener('click', () => {
            if (this.onConfirmCallback) {
                this.onConfirmCallback();
            }
            this.hide();
        });

        // ESC key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal.style.display === 'flex') {
                this.hide();
            }
        });
    }

    show(options = {}) {
        const {
            title = 'Delete Notion Vendor?',
            message = 'This may affect existing styles and configurations. This action <strong>cannot be undone</strong>.',
            onConfirm = null
        } = options;

        document.getElementById('deleteModalTitle').textContent = title;
        document.getElementById('deleteModalMessage').innerHTML = message;
        this.onConfirmCallback = onConfirm;

        // Detect type from title and set data-type for gradient
        const modalContent = this.modal.querySelector('.delete-modal-content');
        const titleLower = title.toLowerCase();
        
        if (titleLower.includes('fabric vendor')) {
            modalContent.setAttribute('data-type', 'fabric_vendor');
        } else if (titleLower.includes('notion vendor')) {
            modalContent.setAttribute('data-type', 'notion_vendor');
        } else if (titleLower.includes('fabric')) {
            modalContent.setAttribute('data-type', 'fabric');
        } else if (titleLower.includes('notion')) {
            modalContent.setAttribute('data-type', 'notion');
        } else if (titleLower.includes('labor')) {
            modalContent.setAttribute('data-type', 'labor');
        } else if (titleLower.includes('cleaning')) {
            modalContent.setAttribute('data-type', 'cleaning');
        } else if (titleLower.includes('color')) {
            modalContent.setAttribute('data-type', 'color');
        } else if (titleLower.includes('variable')) {
            modalContent.setAttribute('data-type', 'variable');
        } else if (titleLower.includes('size')) {
            modalContent.setAttribute('data-type', 'size_range');
        } else if (titleLower.includes('client')) {
            modalContent.setAttribute('data-type', 'client');
        } else {
            modalContent.setAttribute('data-type', 'default');
        }

        this.modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }

    hide() {
        this.modal.style.display = 'none';
        document.body.style.overflow = '';
        this.onConfirmCallback = null;
        
        // Clear the data-type attribute
        const modalContent = this.modal.querySelector('.delete-modal-content');
        if (modalContent) {
            modalContent.removeAttribute('data-type');
        }
    }
}

// Initialize on page load
let deleteModal;
document.addEventListener('DOMContentLoaded', () => {
    deleteModal = new DeleteModal();
});

// Helper function for easy usage
function confirmDelete(options) {
    if (!deleteModal) {
        console.error('DeleteModal not initialized');
        return;
    }
    deleteModal.show(options);
}