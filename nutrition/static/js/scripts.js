/**
 * ByteBites - Nutrition App JS
 * Common JavaScript functionality for the ByteBites application
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            // Use Bootstrap's dismiss method if available
            if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } else {
                // Fallback to simple display:none
                alert.style.display = 'none';
            }
        });
    }, 5000);
    
    // Image preview functionality for file inputs
    const fileInputs = document.querySelectorAll('input[type="file"][accept*="image"]');
    fileInputs.forEach(function(input) {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(event) {
                    // Check if there's a preview container next to the input
                    let previewContainer = input.nextElementSibling;
                    if (!previewContainer || !previewContainer.classList.contains('image-preview')) {
                        // Create one if it doesn't exist
                        previewContainer = document.createElement('div');
                        previewContainer.classList.add('image-preview', 'mt-2', 'text-center');
                        input.parentNode.insertBefore(previewContainer, input.nextSibling);
                    }
                    
                    previewContainer.innerHTML = `
                        <img src="${event.target.result}" class="img-fluid rounded" style="max-height: 200px;">
                    `;
                };
                reader.readAsDataURL(file);
            }
        });
    });
});

/**
 * Format a number with commas as thousands separators
 * @param {number} num - The number to format
 * @returns {string} - Formatted number
 */
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

/**
 * Scroll to an element smoothly
 * @param {string} elementId - ID of the element to scroll to
 */
function scrollToElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}
