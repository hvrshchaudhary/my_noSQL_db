// src/static/js/scripts.js

// Example: Add confirmation dialog before deleting a record
document.addEventListener('DOMContentLoaded', function() {
    const deleteForms = document.querySelectorAll('form[action*="?action=delete"]');
    deleteForms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            const confirmDelete = confirm('Are you sure you want to delete this record?');
            if (!confirmDelete) {
                event.preventDefault();
            }
        });
    });
});
