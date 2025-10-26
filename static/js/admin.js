document.addEventListener('DOMContentLoaded', function() {
    const addRuleForm = document.getElementById('add-rule-form');
    const keywordsInput = document.getElementById('keywords');
    const responseInput = document.getElementById('response');

    const ruleFilter = document.getElementById('rule-filter');

    // Function to get CSRF token from meta tag and log it
    function getCsrfToken() {
        return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    }

    const addRuleFormElement = document.getElementById('add-rule-form');
    if (addRuleFormElement) {
        const keywordsInput = document.getElementById('keywords');
        const responseInput = document.getElementById('response');

        addRuleFormElement.addEventListener('submit', async function(e) {
            e.preventDefault();

            const question = keywordsInput.value.trim();  // The input field is labeled as keywords but contains the question
            const response = responseInput.value.trim();
            const userTypeSelect = document.getElementById('rule-category');
            const user_type = userTypeSelect ? userTypeSelect.value : '';
            const categorySelect = document.getElementById('category-select');
            const category = categorySelect ? categorySelect.value : '';

            // Validation with detailed warnings
            if (!question) {
                alert('Please enter a question. This field cannot be left blank.');
                keywordsInput.focus();
                return;
            }

            if (!response) {
                alert('Please enter a response. This field cannot be left blank.');
                responseInput.focus();
                return;
            }

            if (!user_type) {
                alert('Please select a user type. This field cannot be left blank.');
                userTypeSelect.focus();
                return;
            }

            if (!category) {
                alert('Please select a category. This field cannot be left blank.');
                categorySelect.focus();
                return;
            }

            try {
                // Create FormData to send form data instead of JSON
                const formData = new FormData();
                formData.append('keywords', question);  // Send question as 'keywords' field for backward compatibility
                formData.append('response', response);
                formData.append('user_type', user_type);
                formData.append('category', category);

                const result = await fetch('/add_rule', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: formData,
                });

                const data = await result.json();

                if (data.status === 'success') {
                    // Close the modal using our cleanup function
                    closeCategoryModal();
                    // Refresh the page to show the new rule
                    location.reload();
                } else {
                    alert(data.message || 'Failed to add rule');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('An error occurred. Please try again.');
            }
        });
    }

// Cleanup function for category modal
function closeCategoryModal(redirectUrl) {
    const modalElement = document.getElementById('addCategoryModal');
    const modal = bootstrap.Modal.getInstance(modalElement);
    
    if (modal) {
        // Hide the modal first
        modal.hide();
        
        // Wait for the modal to be fully hidden before redirecting
        modalElement.addEventListener('hidden.bs.modal', function() {
            console.log("Category modal closed");
            // Redirect to the specified URL or fallback to admin dashboard
            window.location.href = redirectUrl || '/admin';
        }, { once: true });
    } else {
        // If modal instance doesn't exist, redirect immediately
        console.log("Category modal closed");
        window.location.href = redirectUrl || '/admin';
    }
}

    // Expose closeCategoryModal globally for inline onclick handlers
    window.closeCategoryModal = closeCategoryModal;

    // Expose attachRuleEventListeners globally for inline scripts
    window.attachRuleEventListeners = attachRuleEventListeners;





    // Function to attach event listeners for edit and delete buttons in a given table
    function attachRuleEventListeners(tableElement) {
        if (!tableElement) return;

        // Delete rule buttons
        const deleteButtons = tableElement.querySelectorAll('.delete-rule');
        deleteButtons.forEach(button => {
            // Remove existing listeners to avoid duplicates
            button.replaceWith(button.cloneNode(true));
        });
        // Re-query after cloning
        const freshDeleteButtons = tableElement.querySelectorAll('.delete-rule');
        freshDeleteButtons.forEach(button => {
            button.addEventListener('click', async function() {
                const ruleId = this.getAttribute('data-rule-id');
                const user_type = tableElement.id === 'guest-rules-table' ? 'guest' : 'user';
                console.log(`Delete button clicked for rule id: ${ruleId}, user_type: ${user_type}`);

                if (confirm('Are you sure you want to delete this rule?')) {
                    try {
                        const result = await fetch('/delete_rule', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': getCsrfToken()
                            },
                            body: JSON.stringify({
                                rule_id: ruleId,
                                user_type: user_type
                            }),
                        });

                        const data = await result.json();

                        if (data.status === 'success') {
                            console.log(`Rule with id ${ruleId} deleted successfully.`);
                            // Remove the row from the table
                            const row = this.closest('tr');
                            row.remove();

                            // Check if the table is empty and show empty message
                            const tbody = tableElement.querySelector('tbody');
                            if (tbody.querySelectorAll('tr').length === 0) {
                                const emptyRow = document.createElement('tr');
                                emptyRow.innerHTML = '<td colspan="3" class="text-center">No rules defined yet.</td>';
                                tbody.appendChild(emptyRow);
                            }
                        } else {
                            console.error(`Failed to delete rule with id ${ruleId}: ${data.message}`);
                            alert(data.message || 'Failed to delete rule');
                        }
                    } catch (error) {
                        console.error('Error:', error);
                        alert('An error occurred. Please try again.');
                    }
                }
            });
        });

        // Edit rule buttons
        const editButtons = tableElement.querySelectorAll('.edit-rule');
        console.log(`Attaching edit-rule listeners: found ${editButtons.length} buttons`);
        editButtons.forEach(button => {
            // Remove existing listeners to avoid duplicates
            button.replaceWith(button.cloneNode(true));
        });
        // Re-query after cloning
        const freshEditButtons = tableElement.querySelectorAll('.edit-rule');
        freshEditButtons.forEach(button => {
            console.log('edit-rule button listener attached');
            button.addEventListener('click', function() {
                console.log('edit-rule button clicked');
                const row = this.closest('tr');
                const ruleId = this.getAttribute('data-rule-id');
                const user_type = tableElement.id === 'guest-rules-table' ? 'guest' : 'user';

                // If already in edit mode, do nothing
                if (row.classList.contains('editing')) {
                    console.log('Row already in editing mode, ignoring click');
                    return;
                }

                row.classList.add('editing');

                // Get current keywords and response
                const keywordsCell = row.querySelector('td:nth-child(1) div');
                const responseCell = row.querySelector('td:nth-child(2)');

                const currentKeywords = Array.from(keywordsCell.querySelectorAll('.keyword-badge'))
                    .map(badge => badge.textContent).join(', ');
                const currentResponse = responseCell.textContent.trim();

                // Replace keywords cell content with input
                keywordsCell.innerHTML = `<input type="text" class="form-control form-control-sm edit-keywords" value="${currentKeywords}">`;

                // Replace response cell content with textarea
                responseCell.innerHTML = `<textarea class="form-control form-control-sm edit-response" rows="3">${currentResponse}</textarea>`;

                // Replace actions cell buttons
                const actionsCell = row.querySelector('td:nth-child(3)');
                actionsCell.innerHTML = `
                    <button class="btn btn-sm btn-success save-edit" data-rule-id="${ruleId}">
                        <i class="fas fa-save"></i>
                    </button>
                    <button class="btn btn-sm btn-secondary cancel-edit">
                        <i class="fas fa-times"></i>
                    </button>
                `;

                // Capture ruleId in local variable for closure
                const capturedRuleId = ruleId;

                // Add event listener for save button
                actionsCell.querySelector('.save-edit').addEventListener('click', async () => {
                    const newQuestion = actionsCell.closest('tr').querySelector('.edit-keywords').value.trim();
                    const newResponse = actionsCell.closest('tr').querySelector('.edit-response').value.trim();

                    if (!newQuestion || !newResponse) {
                        alert('Question and response cannot be empty.');
                        return;
                    }

                    try {
                        const result = await fetch('/edit_rule', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': getCsrfToken()
                            },
                            body: JSON.stringify({
                                rule_id: capturedRuleId,
                                keywords: newQuestion,  // Send question as 'keywords' field for backward compatibility
                                response: newResponse
                            }),
                        });

                        const data = await result.json();

                        if (data.status === 'success') {
                            // Reload the page to reflect changes
                            location.reload();
                        } else {
                            alert(data.message || 'Failed to update rule');
                        }
                    } catch (error) {
                        console.error('Error:', error);
                        alert('An error occurred. Please try again.');
                    }
                });

                // Add event listener for cancel button
                actionsCell.querySelector('.cancel-edit').addEventListener('click', () => {
                    // Reload the page to cancel editing
                    location.reload();
                });
            });
        });
    }

    // Search functionality removed to avoid conflicts with admin_categorized.js
    // The search is now handled by admin_categorized.js for categorized rules

    // Function to handle category button clicks
    function handleCategoryButtonClick(category) {
        const ruleFilter = document.getElementById('rule-filter');
        if (ruleFilter) {
            ruleFilter.value = category; // Set the filter value
            applyFilters(); // Call the filtering function
        }
    }

    // Attach event listeners to category buttons in the modal
    const categoryButtons = document.querySelectorAll('.category-btn');
    categoryButtons.forEach(button => {
        button.addEventListener('click', function() {
            const category = this.getAttribute('data-category'); // Assuming data-category attribute holds the category
            handleCategoryButtonClick(category);
        });
    });

    // Toggle functionality is handled by admin_categorized.js
    // The admin_categorized.js file already contains the correct implementation
    // for toggling between user and guest rules containers

    // ===== Category Selection and Reordering =====
    function handleCategorySelection(category, buttonElement) {
        // Update the hidden input value
        const categoryInput = document.getElementById('category');
        if (categoryInput) {
            categoryInput.value = category;
        }

        // Reorder category buttons - move selected category to first position
        const categoryButtonsContainer = document.getElementById('category-buttons');
        if (categoryButtonsContainer && buttonElement) {
            // Remove the button from its current position
            buttonElement.remove();
            // Add it back at the beginning
            categoryButtonsContainer.prepend(buttonElement);
        }

        // Add active class for visual feedback
        document.querySelectorAll('.category-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        if (buttonElement) {
            buttonElement.classList.add('active');
        }

        // Store the selected category in localStorage for persistence
        localStorage.setItem('selectedCategory', category);

        // Apply category filter
        filterByCategory(category);
    }

    // Function to filter by category (from admin_rules.html)
    function filterByCategory(category) {
        const allRows = [...rulesTable.querySelectorAll('tbody tr'), ...guestRulesTable.querySelectorAll('tbody tr')];
        
        allRows.forEach(row => {
            // If the row is the "No rules defined yet." message, always show it
            if (row.querySelector('td').colSpan === 3) {
                row.style.display = '';
                return;
            }

            const rowCategory = row.dataset.category ? row.dataset.category.toLowerCase() : '';
            if (rowCategory === category.toLowerCase()) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }

    // Update category button click handlers to include reordering
    document.querySelectorAll('.category-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const category = this.dataset.category;
            handleCategorySelection(category, this);
        });
    });

    // On page load, check for previously selected category and reorder buttons
    const savedCategory = localStorage.getItem('selectedCategory');
    if (savedCategory) {
        const savedButton = document.querySelector(`.category-btn[data-category="${savedCategory}"]`);
        if (savedButton) {
            handleCategorySelection(savedCategory, savedButton);
        }
    }

});
  const userBtn = document.getElementById('show-user-rules');
  const guestBtn = document.getElementById('show-guest-rules');

  if (userBtn && guestBtn) {
    function setActive(button) {
      // remove active from both
      userBtn.classList.remove('active');
      guestBtn.classList.remove('active');

      // add active to the clicked one
      button.classList.add('active');
    }

    userBtn.addEventListener('click', () => {
      setActive(userBtn);
      // your logic to show user rules
    });

    guestBtn.addEventListener('click', () => {
      setActive(guestBtn);
      // your logic to show guest rules
    });
  }
