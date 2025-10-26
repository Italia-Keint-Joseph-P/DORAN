document.addEventListener('DOMContentLoaded', function() {
    // Function to get CSRF token from meta tag
    function getCsrfToken() {
        return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    }

    // Attach event listeners for edit, save, and delete buttons in email directory
    function attachEmailEventListeners() {
        // Edit email buttons
        const editButtons = document.querySelectorAll('.edit-email');
        editButtons.forEach(button => {
            // Remove existing listeners to avoid duplicates
            button.replaceWith(button.cloneNode(true));
        });
        // Re-query after cloning
        const freshEditButtons = document.querySelectorAll('.edit-email');
        freshEditButtons.forEach(button => {
            button.addEventListener('click', function() {
                const row = this.closest('tr');
                const id = this.getAttribute('data-id');
                
                // Get current values
                const schoolCell = row.querySelector('.editable-school');
                const emailCell = row.querySelector('.editable-email');
                
                const currentSchool = schoolCell.textContent.trim();
                const currentEmail = emailCell.textContent.trim();
                
                // Make cells editable
                schoolCell.contentEditable = 'true';
                emailCell.contentEditable = 'true';
                
                // Add styling to indicate editable state
                schoolCell.style.border = '1px solid #007bff';
                emailCell.style.border = '1px solid #007bff';
                schoolCell.style.padding = '2px';
                emailCell.style.padding = '2px';
                
                // Hide edit button and show save/cancel buttons
                const editBtn = row.querySelector('.edit-email');
                const saveBtn = row.querySelector('.save-email');
                const cancelBtn = row.querySelector('.cancel-edit');
                const deleteBtn = row.querySelector('.delete-email');
                
                editBtn.style.display = 'none';
                saveBtn.style.display = 'inline-block';
                cancelBtn.style.display = 'inline-block';
                deleteBtn.style.display = 'none';
                
                // Add event listener for save button
                saveBtn.addEventListener('click', async function() {
                    const newSchool = schoolCell.textContent.trim();
                    const newEmail = emailCell.textContent.trim();
                    
                    if (!newSchool || !newEmail) {
                        alert('School and email cannot be empty.');
                        return;
                    }
                    
                    try {
                        const result = await fetch('/update_email', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': getCsrfToken()
                            },
                            body: JSON.stringify({ id, school: newSchool, email: newEmail }),
                        });
                        
                        const data = await result.json();
                        if (data.status === 'success') {
                            alert('Email updated successfully.');
                            // Reset to non-editable state
                            schoolCell.contentEditable = 'false';
                            emailCell.contentEditable = 'false';
                            schoolCell.style.border = 'none';
                            emailCell.style.border = 'none';
                            schoolCell.style.padding = '0';
                            emailCell.style.padding = '0';
                            
                            // Show edit/delete buttons and hide save/cancel buttons
                            editBtn.style.display = 'inline-block';
                            saveBtn.style.display = 'none';
                            cancelBtn.style.display = 'none';
                            deleteBtn.style.display = 'inline-block';
                        } else {
                            alert(data.message || 'Failed to update email.');
                        }
                    } catch (error) {
                        console.error('Error updating email:', error);
                        alert('An error occurred. Please try again.');
                    }
                });
                
                // Add event listener for cancel button
                cancelBtn.addEventListener('click', function() {
                    // Reset values to original
                    schoolCell.textContent = currentSchool;
                    emailCell.textContent = currentEmail;
                    
                    // Reset to non-editable state
                    schoolCell.contentEditable = 'false';
                    emailCell.contentEditable = 'false';
                    schoolCell.style.border = 'none';
                    emailCell.style.border = 'none';
                    schoolCell.style.padding = '0';
                    emailCell.style.padding = '0';
                    
                    // Show edit/delete buttons and hide save/cancel buttons
                    editBtn.style.display = 'inline-block';
                    saveBtn.style.display = 'none';
                    cancelBtn.style.display = 'none';
                    deleteBtn.style.display = 'inline-block';
                });
            });
        });

        // Delete email buttons
        const deleteButtons = document.querySelectorAll('.delete-email');
        deleteButtons.forEach(button => {
            // Remove existing listeners to avoid duplicates
            button.replaceWith(button.cloneNode(true));
        });
        // Re-query after cloning
        const freshDeleteButtons = document.querySelectorAll('.delete-email');
        freshDeleteButtons.forEach(button => {
            button.addEventListener('click', async function() {
                const id = this.getAttribute('data-id');
                if (confirm('Are you sure you want to delete this email entry?')) {
                    try {
                        const result = await fetch('/delete_email', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': getCsrfToken()
                            },
                            body: JSON.stringify({ id }),
                        });

                        const data = await result.json();
                        if (data.status === 'success') {
                            // Remove the row from the table
                            const row = this.closest('tr');
                            row.remove();
                        } else {
                            alert(data.message || 'Failed to delete email.');
                        }
                    } catch (error) {
                        console.error('Error deleting email:', error);
                        alert('An error occurred. Please try again.');
                    }
                }
            });
        });
    }

    // Handle add email form submission
    const addEmailForm = document.getElementById('add-email-form');
    const schoolInput = document.getElementById('school');
    const emailInput = document.getElementById('email');
    
    if (addEmailForm) {
        addEmailForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const school = schoolInput.value.trim();
            const email = emailInput.value.trim();

            if (!school || !email) {
                alert('Please enter both school and email.');
                return;
            }

            try {
                const result = await fetch('/add_email', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify({ school, email }),
                });

                const data = await result.json();

                if (data.status === 'success') {
                    // Clear inputs
                    schoolInput.value = '';
                    emailInput.value = '';
                    // Reload the page to show the new entry
                    location.reload();
                } else {
                    alert(data.message || 'Failed to add email.');
                }
            } catch (error) {
                console.error('Error adding email:', error);
                alert('An error occurred. Please try again.');
            }
        });
    }

    // Attach event listeners when the page loads
    attachEmailEventListeners();

    // ===== SEARCH EMAILS =====
    const emailSearchInput = document.getElementById('email-search');
    const emailTable = document.getElementById('email-table');
    let emailSearchTimeout;

    if (emailSearchInput && emailTable) {
        function applyEmailSearch() {
            const searchValue = emailSearchInput.value.toLowerCase().trim();
            const rows = emailTable.querySelectorAll('tbody tr');

            rows.forEach(row => {
                // Skip the "No email entries yet." row
                if (row.querySelector('td[colspan="3"]')) {
                    row.style.display = '';
                    return;
                }

                const positionText = row.querySelector('.editable-school')?.textContent.toLowerCase() || '';
                const emailText = row.querySelector('.editable-email')?.textContent.toLowerCase() || '';

                const searchMatch = !searchValue ||
                    positionText.includes(searchValue) ||
                    emailText.includes(searchValue);

                row.style.display = searchMatch ? '' : 'none';
            });
        }

        emailSearchInput.addEventListener('input', function() {
            clearTimeout(emailSearchTimeout);
            emailSearchTimeout = setTimeout(applyEmailSearch, 300); // Debounce for 300ms
        });
    }
});
