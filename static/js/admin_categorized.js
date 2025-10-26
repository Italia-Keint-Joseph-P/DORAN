// JavaScript for handling categorized rules in admin interface

document.addEventListener('DOMContentLoaded', function() {
    // Function to get CSRF token from meta tag
    function getCsrfToken() {
        return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    }

    // Function to attach event listeners for edit and delete buttons in categorized tables
    function attachRuleEventListenersToContainers() {
        // Delete rule buttons
        const deleteButtons = document.querySelectorAll('.delete-rule');
        deleteButtons.forEach(button => {
            // Remove existing listeners to avoid duplicates
            button.replaceWith(button.cloneNode(true));
        });
        // Re-query after cloning
        const freshDeleteButtons = document.querySelectorAll('.delete-rule');
        freshDeleteButtons.forEach(button => {
            button.addEventListener('click', async function() {
                const ruleId = this.getAttribute('data-rule-id');
                const user_type = document.getElementById('user-rules-container').style.display !== 'none' ? 'user' : 'guest';
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

                            // Check if the category table is empty and show empty message
                            const tbody = row.closest('tbody');
                            const categorySection = row.closest('.category-section');
                            if (tbody.querySelectorAll('tr').length === 0) {
                                const emptyRow = document.createElement('tr');
                                emptyRow.innerHTML = '<td colspan="3" class="text-center">No rules defined yet.</td>';
                                tbody.appendChild(emptyRow);
                            }

                            // If the entire category is empty, remove the category section
                            const categoryTables = categorySection.querySelectorAll('tbody tr');
                            const hasRules = Array.from(categoryTables).some(tr => tr.cells.length > 1);
                            if (!hasRules) {
                                categorySection.remove();
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
        const editButtons = document.querySelectorAll('.edit-rule');
        editButtons.forEach(button => {
            // Remove existing listeners to avoid duplicates
            button.replaceWith(button.cloneNode(true));
        });
        // Re-query after cloning
        const freshEditButtons = document.querySelectorAll('.edit-rule');
        freshEditButtons.forEach(button => {
            button.addEventListener('click', function() {
                console.log('edit-rule button clicked');
                const row = this.closest('tr');
                const ruleId = this.getAttribute('data-rule-id');
                const user_type = document.getElementById('user-rules-container').style.display !== 'none' ? 'user' : 'guest';

                // If already in edit mode, do nothing
                if (row.classList.contains('editing')) {
                    console.log('Row already in editing mode, ignoring click');
                    return;
                }

                row.classList.add('editing');

                // Get current keywords and response
                const keywordsCell = row.querySelector('td:nth-child(1) div');
                const responseCell = row.querySelector('td:nth-child(2)');

                const currentKeywords = keywordsCell.textContent.trim();
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
                    const newKeywords = actionsCell.closest('tr').querySelector('.edit-keywords').value.trim();
                    const newResponse = actionsCell.closest('tr').querySelector('.edit-response').value.trim();

                    if (!newKeywords || !newResponse) {
                        alert('Keywords and response cannot be empty.');
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
                                question: newKeywords,
                                response: newResponse,
                                user_type: user_type
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

    // Add rule to category buttons
    document.querySelectorAll('.add-rule-to-category').forEach(button => {
        button.addEventListener('click', function() {
            const category = this.getAttribute('data-category');
            const categoryInput = document.getElementById('category');
            const selectedCategoryDisplay = document.getElementById('selected-category-display');
            const selectedCategoryText = document.getElementById('selected-category-text');

            if (categoryInput && selectedCategoryDisplay && selectedCategoryText) {
                categoryInput.value = category;
                selectedCategoryText.textContent = category;
                selectedCategoryDisplay.style.display = 'block';

                // Add active styling
                selectedCategoryDisplay.classList.remove('btn-outline-primary');
                selectedCategoryDisplay.classList.add('btn-primary', 'text-white');

                // Scroll to the form
                document.querySelector('.futuristic-card').scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    // Remove category buttons
    document.querySelectorAll('.remove-category').forEach(button => {
        button.addEventListener('click', async function() {
            const category = this.getAttribute('data-category');
            if (confirm(`Are you sure you want to remove the category "${category}"? This will delete all associated rules.`)) {
                try {
                    const response = await fetch('/remove_category', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCsrfToken()
                        },
                        body: JSON.stringify({ category_name: category })
                    });

                    const data = await response.json();

                    if (data.status === 'success') {
                        alert(data.message);
                        location.reload();
                    } else {
                        alert(data.message || 'Failed to remove category');
                    }
                } catch (error) {
                    console.error('Error removing category:', error);
                    alert('An error occurred while removing the category. Please try again.');
                }
            }
        });
    });

    // Search functionality for categorized rules
    const ruleSearchInput = document.getElementById('rule-search');
    const searchTypeSelect = document.getElementById('search-type');

    let searchTimeout;

    function applySearch() {
        const searchValue = ruleSearchInput ? ruleSearchInput.value.toLowerCase().trim() : '';
        const searchType = searchTypeSelect ? searchTypeSelect.value : 'question';

        // Get all category sections in the currently visible container
        const activeContainer = document.getElementById('user-rules-container').style.display !== 'none'
            ? document.getElementById('user-rules-container')
            : document.getElementById('guest-rules-container');

        if (!activeContainer) return;

        const categorySections = activeContainer.querySelectorAll('.category-section');

        categorySections.forEach(section => {
            // Skip sections hidden by category filter
            if (section.style.display === 'none') return;

            const rows = section.querySelectorAll('tbody tr');
            let sectionHasVisibleRows = false;

            rows.forEach(row => {
                // Skip the "No rules defined yet" message row
                if (row.cells.length === 1 && row.cells[0].colSpan === 3) {
                    row.style.display = '';
                    return;
                }

                let searchMatch = false;

                if (!searchValue) {
                    searchMatch = true;
                } else {
                    const questionText = row.querySelector('td:nth-child(1) div')?.textContent.toLowerCase() || '';
                    const responseText = row.querySelector('td:nth-child(2)')?.textContent.toLowerCase() || '';

                    if (searchType === 'question') {
                        searchMatch = questionText.includes(searchValue);
                    } else if (searchType === 'response') {
                        searchMatch = responseText.includes(searchValue);
                    }
                }

                if (searchMatch) {
                    row.style.display = '';
                    sectionHasVisibleRows = true;
                } else {
                    row.style.display = 'none';
                }
            });

            // Show/hide the entire category section based on whether it has visible rows
            section.style.display = sectionHasVisibleRows ? 'block' : 'none';
        });
    }

    // Add search event listeners with debouncing
    if (ruleSearchInput) {
        ruleSearchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(applySearch, 300); // Debounce for 300ms
        });
    }

    if (searchTypeSelect) {
        searchTypeSelect.addEventListener('change', applySearch);
    }

    // Initialize event listeners
    attachRuleEventListenersToContainers();

    // Populate category filter dropdown
    const categoryFilter = document.getElementById('category-filter');
    if (categoryFilter) {
        // Fetch categories from the server
        fetch('/get_categories')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Clear existing options except "All Categories"
                    categoryFilter.innerHTML = '<option value="all" selected>All Categories</option>';

                    // Add categories to dropdown
                    data.categories.forEach(category => {
                        const option = document.createElement('option');
                        option.value = category.toLowerCase();
                        option.textContent = category.toUpperCase();
                        categoryFilter.appendChild(option);
                    });
                } else {
                    console.error('Failed to load categories:', data.message);
                }
            })
            .catch(error => {
                console.error('Error fetching categories:', error);
            });

        // Handle category filter change
        categoryFilter.addEventListener('change', function() {
            const selectedCategory = this.value;
            applyCategoryFilter(selectedCategory);
        });
    }

    // Populate category selection dropdown for adding rules
    const categorySelect = document.getElementById('category-select');
    if (categorySelect) {
        // Fetch categories from the server
        fetch('/get_categories')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Clear existing options except the default
                    categorySelect.innerHTML = '<option value="" disabled selected>Select a category</option>';

                    // Add categories to dropdown
                    data.categories.forEach(category => {
                        const option = document.createElement('option');
                        option.value = category;
                        option.textContent = category.toUpperCase();
                        categorySelect.appendChild(option);
                    });
                } else {
                    console.error('Failed to load categories:', data.message);
                }
            })
            .catch(error => {
                console.error('Error fetching categories:', error);
            });
    }

    // Handle Remove Category button click
    const removeCategoryBtn = document.getElementById('remove-category-btn');
    if (removeCategoryBtn) {
        removeCategoryBtn.addEventListener('click', function() {
            // Fetch categories and populate the remove modal
            fetch('/get_categories')
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        const removeCategoryList = document.getElementById('remove-category-list');
                        removeCategoryList.innerHTML = ''; // Clear existing categories

                        data.categories.forEach(category => {
                            const categoryDiv = document.createElement('div');
                            categoryDiv.className = 'd-flex justify-content-between align-items-center mb-2 p-2 border rounded';

                            const categoryName = document.createElement('span');
                            categoryName.textContent = category.toUpperCase();

                            const removeBtn = document.createElement('button');
                            removeBtn.type = 'button';
                            removeBtn.className = 'btn btn-sm btn-danger';
                            removeBtn.innerHTML = '&times;';
                            removeBtn.title = 'Remove Category';
                            removeBtn.addEventListener('click', async function() {
                                if (confirm(`Are you sure you want to remove the category "${category}"? This will delete all associated rules.`)) {
                                    try {
                                        const response = await fetch('/remove_category', {
                                            method: 'POST',
                                            headers: {
                                                'Content-Type': 'application/json',
                                                'X-CSRFToken': getCsrfToken()
                                            },
                                            body: JSON.stringify({ category_name: category })
                                        });

                                        const data = await response.json();

                                        if (data.status === 'success') {
                                            alert(data.message);
                                            location.reload();
                                        } else {
                                            alert(data.message || 'Failed to remove category');
                                        }
                                    } catch (error) {
                                        console.error('Error removing category:', error);
                                        alert('An error occurred while removing the category. Please try again.');
                                    }
                                }
                            });

                            categoryDiv.appendChild(categoryName);
                            categoryDiv.appendChild(removeBtn);
                            removeCategoryList.appendChild(categoryDiv);
                        });
                    } else {
                        alert(data.message || 'Failed to load categories');
                    }
                })
                .catch(error => {
                    console.error('Error fetching categories:', error);
                    alert('An error occurred while fetching categories. Please try again.');
                });
        });
    }

    // Handle user/guest rules toggle buttons
    const showUserRulesBtn = document.getElementById('show-user-rules');
    const showGuestRulesBtn = document.getElementById('show-guest-rules');

    if (showUserRulesBtn && showGuestRulesBtn) {
        showUserRulesBtn.addEventListener('click', function() {
            showUserRules();
        });

        showGuestRulesBtn.addEventListener('click', function() {
            showGuestRules();
        });
    }

    function showUserRules() {
        const userContainer = document.getElementById('user-rules-container');
        const guestContainer = document.getElementById('guest-rules-container');

        if (userContainer && guestContainer) {
            userContainer.style.display = 'block';
            guestContainer.style.display = 'none';
            showUserRulesBtn.classList.add('btn-primary');
            showUserRulesBtn.classList.remove('btn-secondary');
            showGuestRulesBtn.classList.add('btn-secondary');
            showGuestRulesBtn.classList.remove('btn-primary');
        }
    }

    function showGuestRules() {
        const userContainer = document.getElementById('user-rules-container');
        const guestContainer = document.getElementById('guest-rules-container');

        if (userContainer && guestContainer) {
            userContainer.style.display = 'none';
            guestContainer.style.display = 'block';
            showGuestRulesBtn.classList.add('btn-primary');
            showGuestRulesBtn.classList.remove('btn-secondary');
            showUserRulesBtn.classList.add('btn-secondary');
            showUserRulesBtn.classList.remove('btn-primary');
        }
    }

    function applyCategoryFilter(selectedCategory) {
        const userContainer = document.getElementById('user-rules-container');
        const guestContainer = document.getElementById('guest-rules-container');

        // Determine which container is active
        const activeContainer = userContainer && userContainer.style.display !== 'none' ? userContainer : guestContainer;

        if (!activeContainer) return;

        const categorySections = activeContainer.querySelectorAll('.category-section');

        categorySections.forEach(section => {
            const sectionCategory = section.dataset.category ? section.dataset.category.toLowerCase() : '';

            if (selectedCategory === 'all') {
                section.style.display = 'block';
            } else if (sectionCategory === selectedCategory.toLowerCase()) {
                section.style.display = 'block';
            } else {
                section.style.display = 'none';
            }
        });
    }

    // Handle Add Category button click
    const saveCategoryBtn = document.getElementById('save-category-btn');
    if (saveCategoryBtn) {
        saveCategoryBtn.addEventListener('click', async function() {
            const categoryNameInput = document.getElementById('new-category-name');
            const categoryName = categoryNameInput ? categoryNameInput.value.trim() : '';

            if (!categoryName) {
                alert('Please enter a category name');
                return;
            }

            try {
                const result = await fetch('/add_category', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify({
                        category_name: categoryName
                    }),
                });

                const data = await result.json();

                if (data.status === 'success') {
                    alert(data.message || 'Category added successfully');
                    // Close the modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('addCategoryModal'));
                    if (modal) {
                        modal.hide();
                    }
                    // Clear the input field
                    if (categoryNameInput) {
                        categoryNameInput.value = '';
                    }
                    // Reload the page to update category dropdowns
                    location.reload();
                } else {
                    alert(data.message || 'Failed to add category');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('An error occurred. Please try again.');
            }
        });
    }
});
