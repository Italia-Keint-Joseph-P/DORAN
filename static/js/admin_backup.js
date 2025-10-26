    document.addEventListener('DOMContentLoaded', function() {
        const addRuleForm = document.getElementById('add-rule-form');
        const keywordsInput = document.getElementById('keywords');
        const responseInput = document.getElementById('response');
        const rulesTable = document.getElementById('rules-table');
        const guestRulesTable = document.getElementById('guest-rules-table');
        const ruleFilter = document.getElementById('rule-filter');

        const addEmailForm = document.getElementById('add-email-form');
        const schoolInput = document.getElementById('school');
        const emailInput = document.getElementById('email');
        const emailTable = document.getElementById('email-table');

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

                const keywords = keywordsInput.value.trim();
                const response = responseInput.value.trim();
                const userTypeSelect = document.getElementById('rule-category');
                const user_type = userTypeSelect ? userTypeSelect.value : 'user';
                const categorySelect = document.getElementById('category');
                const category = categorySelect ? categorySelect.value : 'soict';

                if (!keywords || !response) {
                    alert('Please enter both keywords and response');
                    return;
                }

                try {
                    const result = await fetch('/add_rule', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCsrfToken()
                        },
                        body: JSON.stringify({
                            keywords,
                            response,
                            user_type,
                            category
                        }),
                    });

                    const data = await result.json();

                    if (data.status === 'success') {
                        // Close the modal using our cleanup function
                        closeCategoryModal();
                        // Redirect to the admin dashboard
                        window.location.href = data.redirect;
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



        // Edit and delete locations
        function attachLocationEventListeners() {
            const editButtons = document.querySelectorAll('.edit-location');
            editButtons.forEach(button => {
                // Remove existing listeners to avoid duplicates
                button.replaceWith(button.cloneNode(true));
            });
            // Re-query after cloning
            const freshEditButtons = document.querySelectorAll('.edit-location');
            freshEditButtons.forEach(button => {
                button.addEventListener('click', function() {
                    const locationId = this.getAttribute('data-id');
                    const locationCard = this.closest('.futuristic-card');

                    if (!locationCard) {
                        console.error('Location card element not found for edit button.');
                        return;
                    }

                    if (locationCard.classList.contains('editing')) {
                        return;
                    }

                    // Hide the edit and delete buttons when in edit mode
                    const editButton = this;
                    const deleteButton = locationCard.querySelector('.delete-location');
                    editButton.style.display = 'none';
                    deleteButton.style.display = 'none';

                    locationCard.classList.add('editing');

                    // Get current values
                    const paragraphs = locationCard.querySelectorAll('p');
                    let keywordsP = null;
                    let descriptionP = null;
                    paragraphs.forEach(p => {
                        if (p.textContent.includes('Keywords:')) {
                            keywordsP = p;
                        } else if (p.textContent.includes('Description:')) {
                            descriptionP = p;
                        }
                    });

                    const imagesContainer = document.createElement('div');
                    imagesContainer.classList.add('d-flex', 'flex-wrap', 'gap-2', 'mb-3');

                    // Track removed images
                    const removedImages = new Set();

                    // Get all existing images
                    const existingImages = locationCard.querySelectorAll('.location-images img, img.img-fluid.rounded.mb-3');
                    existingImages.forEach(img => {
                        const imgWrapper = document.createElement('div');
                        imgWrapper.style.position = 'relative';
                        imgWrapper.style.display = 'inline-block';

                        const removeBtn = document.createElement('button');
                        removeBtn.textContent = '×';
                        removeBtn.style.position = 'absolute';
                        removeBtn.style.top = '0';
                        removeBtn.style.right = '0';
                        removeBtn.style.background = 'rgba(255, 0, 0, 0.7)';
                        removeBtn.style.color = 'white';
                        removeBtn.style.border = 'none';
                        removeBtn.style.borderRadius = '50%';
                        removeBtn.style.width = '20px';
                        removeBtn.style.height = '20px';
                        removeBtn.style.cursor = 'pointer';
                        removeBtn.title = 'Remove image';

                        removeBtn.addEventListener('click', () => {
                            removedImages.add(img.getAttribute('src'));
                            imgWrapper.style.display = 'none';
                        });

                        imgWrapper.appendChild(img.cloneNode(true));
                        imgWrapper.appendChild(removeBtn);
                        imagesContainer.appendChild(imgWrapper);
                    });

                    // Replace images section with editable images container
                    const oldImagesSection = locationCard.querySelector('.location-images') || locationCard.querySelector('img.img-fluid.rounded.mb-3');
                    if (oldImagesSection) {
                        // Remove original images container or original single image to avoid duplication
                        if (oldImagesSection.classList && oldImagesSection.classList.contains('location-images')) {
                            oldImagesSection.remove();
                        } else {
                            // It's a single image element, remove it to avoid duplication
                            oldImagesSection.remove();
                        }
                    }
                    locationCard.insertBefore(imagesContainer, keywordsP);

                    // Replace keywords with individual input boxes for each keyword
                    // Replace this line:
// keywordsP.innerHTML = `<input type="text" class="form-control form-control-sm edit-keywords" value="${currentKeywords}">`;

// With this:
if (keywordsP) {
    const currentKeywords = keywordsP.textContent.replace('Keywords:', '').trim();
    const keywordsArray = currentKeywords.split(',').map(k => k.trim()).filter(k => k.length > 0);

    const container = document.createElement('div');
    container.classList.add('d-flex', 'flex-wrap', 'gap-2', 'mb-2');

    keywordsArray.forEach(kw => {
        const inputWrapper = document.createElement('div');
        inputWrapper.style.display = 'flex';
        inputWrapper.style.alignItems = 'center';
        inputWrapper.style.gap = '2px';

        const input = document.createElement('input');
        input.type = 'text';
        input.value = kw;
        input.className = 'form-control form-control-sm';
        inputWrapper.appendChild(input);

        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.textContent = '×';
        removeBtn.className = 'btn btn-sm btn-outline-danger';
        removeBtn.addEventListener('click', () => inputWrapper.remove());
        inputWrapper.appendChild(removeBtn);

        container.appendChild(inputWrapper);
    });

    keywordsP.innerHTML = '';
    keywordsP.appendChild(container);
}



                    // Replace description with textarea
                    if (descriptionP) {
                        descriptionP.innerHTML = `<textarea class="form-control form-control-sm edit-description" rows="3">${descriptionP.textContent.replace('Description:', '').trim()}</textarea>`;
                    }

                    // Add image file input for editing
                    const btnContainer = document.createElement('div');
                    btnContainer.classList.add('mt-2');

                    // Label for new image upload input
                    const imageInputLabel = document.createElement('label');
                    imageInputLabel.textContent = 'Upload New Image(s)';
                    imageInputLabel.classList.add('form-label', 'mt-2');
                    btnContainer.appendChild(imageInputLabel);

                    const imageInput = document.createElement('input');
                    imageInput.type = 'file';
                    imageInput.accept = 'image/*';
                    imageInput.multiple = true;
                    imageInput.className = 'form-control form-control-sm';
                    btnContainer.appendChild(imageInput);

                    // Add save and cancel buttons
                    const saveBtn = document.createElement('button');
                    saveBtn.className = 'btn btn-sm btn-success me-2 mt-3';
                    saveBtn.textContent = 'Save';
                    btnContainer.appendChild(saveBtn);

                    const cancelBtn = document.createElement('button');
                    cancelBtn.className = 'btn btn-sm btn-secondary mt-3';
                    cancelBtn.textContent = 'Cancel';
                    btnContainer.appendChild(cancelBtn);

                    locationCard.appendChild(btnContainer);

                    saveBtn.addEventListener('click', async () => {
                        // Collect keywords from individual input boxes
                        const keywordInputs = keywordsP.querySelectorAll('.edit-keywords-container input[type="text"]');
                        const keywordsList = [];
                        keywordInputs.forEach(input => {
                            const value = input.value.trim();
                            if (value) {
                                keywordsList.push(value);
                            }
                        });
                        const newKeywords = keywordsList.join(', ');

                        const newDescription = descriptionP.querySelector('.edit-description').value.trim();
                        const imageFile = imageInput.files[0];

                        if (!newKeywords || !newDescription) {
                            alert('Keywords and description cannot be empty.');
                            return;
                        }

                        try {
                            let imageUrl = null;
                            if (imageFile) {
                                // Upload new image
                                const formData = new FormData();
                                formData.append('image', imageFile);

                                const uploadResult = await fetch('/upload_location_image', {
                                    method: 'POST',
                                    headers: {
                                        'X-CSRFToken': getCsrfToken()
                                    },
                                    body: formData
                                });

                                const uploadData = await uploadResult.json();

                                if (uploadData.status !== 'success') {
                                    alert(uploadData.message || 'Failed to upload image');
                                    return;
                                }

                                imageUrl = uploadData.url;
                            }

                            // Send edit location request with optional image URL and removed images list
                            const response = await fetch('/edit_location', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'X-CSRFToken': getCsrfToken()
                                },
                                body: JSON.stringify({
                                    id: locationId,
                                    keywords: newKeywords,
                                    description: newDescription,
                                    image_url: imageUrl,
                                    removed_images: Array.from(removedImages)
                                }),
                            });

                            const data = await response.json();

                            if (data.status === 'success') {
                                alert('Location updated successfully.');
                                location.reload();
                            } else {
                                alert(data.message || 'Failed to update location.');
                            }
                        } catch (error) {
                            console.error('Error:', error);
                            alert('An error occurred. Please try again.');
                        }
                    });

                    cancelBtn.addEventListener('click', () => {
                        location.reload();
                    });
                });
            });

            const deleteButtons = document.querySelectorAll('.delete-location');
            deleteButtons.forEach(button => {
                button.addEventListener('click', async function() {
                    const locationId = this.getAttribute('data-id');
                    if (confirm('Are you sure you want to delete this location?')) {
                        try {
                            const response = await fetch('/delete_location', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'X-CSRFToken': getCsrfToken()
                                },
                                body: JSON.stringify({ id: locationId }),
                            });

                            const data = await response.json();

                            if (data.status === 'success') {
                                alert('Location deleted successfully.');
                                location.reload();
                            } else {
                                alert(data.message || 'Failed to delete location.');
                            }
                        } catch (error) {
                            console.error('Error:', error);
                            alert('An error occurred. Please try again.');
                        }
                    }
                });
            });
        }

        // Attach location event listeners on DOMContentLoaded and after reloads
        attachLocationEventListeners();

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
                    console.log(`Delete button clicked for rule id: ${ruleId}`);

                    if (confirm('Are you sure you want to delete this rule?')) {
                        try {
                            const result = await fetch('/delete_rule', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'X-CSRFToken': getCsrfToken()
                                },
                                body: JSON.stringify({
                                    rule_id: ruleId
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
                                    keywords: newKeywords,
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

        // Search rules by keywords or response
        const ruleSearchInput = document.getElementById('rule-search');
        const searchTypeSelect = document.getElementById('search-type');

        if (ruleSearchInput) {
            ruleSearchInput.addEventListener('input', function() {
                console.log("Rule search input changed"); // Log the change
                applyFilters();
            });
        } else {
            console.error("Rule search input element not found");
        }

        if (searchTypeSelect) {
            searchTypeSelect.addEventListener('change', function() {
                console.log("Search type changed"); // Log the change
                applyFilters();
            });
        } else {
            console.error("Search type select element not found");
        }

        function applyFilters() {
            console.log("applyFilters called"); // Log when the function is called
            
            // Get the current active table (user or guest rules)
            const activeTable = document.querySelector('#rules-table[style*="display: table"], #guest-rules-table[style*="display: table"]');
            if (!activeTable) {
                console.error("No active rules table found");
                return;
            }
            
            const searchValue = ruleSearchInput.value.toLowerCase();
            const searchType = searchTypeSelect.value;
            const rows = activeTable.querySelectorAll('tbody tr');

            console.log("Search value:", searchValue, "Search type:", searchType);

            rows.forEach(row => {
                // If the row is the "No rules defined yet." message, always show it
                if (row.querySelector('td').colSpan === 3) {
                    row.style.display = '';
                    return;
                }

                const keywordBadges = row.querySelectorAll('.keyword-badge');
                const keywords = Array.from(keywordBadges).map(badge => badge.textContent.toLowerCase());
                const responseText = row.querySelector('td:nth-child(2)').textContent.toLowerCase();

                // Filter by search
                let searchMatch = false;
                if (!searchValue) {
                    searchMatch = true;
                } else {
                    if (searchType === 'keywords') {
                        searchMatch = keywords.some(keyword => keyword.includes(searchValue));
                        console.log("Keywords search:", keywords, "Match:", searchMatch);
                    } else if (searchType === 'response') {
                        searchMatch = responseText.includes(searchValue);
                        console.log("Response search:", responseText, "Match:", searchMatch);
                    }
                }

                if (searchMatch) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        }

        // Load email directory entries
        async function loadEmailDirectory() {
            try {
                const response = await fetch('/email_directory');
                const data = await response.json();
                if (data.status === 'success') {
                    const emails = data.emails;
                    const tbody = emailTable.querySelector('tbody');
                    tbody.innerHTML = '';
                    if (emails.length === 0) {
                        const emptyRow = document.createElement('tr');
                        emptyRow.innerHTML = '<td colspan="3" class="text-center">No email entries yet.</td>';
                        tbody.appendChild(emptyRow);
                    } else {
                        emails.forEach((entry, index) => {
                            const row = document.createElement('tr');
                            row.dataset.index = index;
                            row.innerHTML = `
                                <td contenteditable="true" class="editable-school">${entry.school}</td>
                                <td contenteditable="true" class="editable-email">${entry.email}</td>
                                <td>
                                    <button class="btn btn-sm btn-success save-email" data-index="${index}">
                                        <i class="fas fa-save"></i>
                                    </button>
                                    <button class="btn btn-sm btn-danger delete-email" data-index="${index}">
                                        <i class="fas fa-trash-alt"></i>
                                    </button>
                                </td>
                            `;
                            tbody.appendChild(row);
                        });
                        attachEmailEventListeners();
                    }
                } else {
                    alert('Failed to load email directory.');
                }
            } catch (error) {
                console.error('Error loading email directory:', error);
                alert('An error occurred while loading email directory.');
            }
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
                        // Reload email directory
                        loadEmailDirectory();
                    } else {
                        alert(data.message || 'Failed to add email.');
                    }
                } catch (error) {
                    console.error('Error adding email:', error);
                    alert('An error occurred. Please try again.');
                }
            });
        } else {
            console.error("Add email form element not found");
        }

        // Initial load of email directory
        // Commented out to avoid redundant fetch since emails are server-rendered
        // loadEmailDirectory();

        // Attach event listeners to server-rendered email directory buttons
        attachEmailEventListeners();

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

        // New code to toggle between user and guest rules tables
        const showUserRulesBtn = document.getElementById('show-user-rules');
        const showGuestRulesBtn = document.getElementById('show-guest-rules');

        function showUserRules() {
            rulesTable.style.display = '';
            guestRulesTable.style.display = 'none';
            showUserRulesBtn.classList.add('btn-primary');
            showUserRulesBtn.classList.remove('btn-secondary');
            showGuestRulesBtn.classList.add('btn-secondary');
            showGuestRulesBtn.classList.remove('btn-primary');
            attachRuleEventListeners(rulesTable);
        }

        function showGuestRules() {
            rulesTable.style.display = 'none';
            guestRulesTable.style.display = '';
            showGuestRulesBtn.classList.add('btn-primary');
            showGuestRulesBtn.classList.remove('btn-secondary');
            showUserRulesBtn.classList.add('btn-secondary');
            showUserRulesBtn.classList.remove('btn-primary');
            attachRuleEventListeners(guestRulesTable);
        }

        if (showUserRulesBtn) {
            showUserRulesBtn.addEventListener('click', showUserRules);
        } else {
            console.error("Show user rules button not found");
        }

        if (showGuestRulesBtn) {
            showGuestRulesBtn.addEventListener('click', showGuestRules);
        } else {
            console.error("Show guest rules button not found");
        }

        // Initialize with user rules shown
        if (showUserRulesBtn) {
            showUserRules();
        }

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
