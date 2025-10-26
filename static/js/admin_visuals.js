document.addEventListener('DOMContentLoaded', function() {
    // ===== CSRF Token =====
    function getCsrfToken() {
        return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    }
    // ===== ADD VISUAL =====
    const addVisualForm = document.getElementById('add-visual-form');
    const dropZone = document.getElementById('visual-media-dropzone');
    const previewContainer = document.getElementById('visual-media-preview');
    const fileInput = document.getElementById('visual-media');
    let mediaFiles = [];

    // Question sets management for add visual
    const visualQuestionsContainer = document.getElementById('visual-questions-container');
    const addVisualQuestionSetBtn = document.getElementById('add-visual-question-set');

    function updateVisualQuestionSetButtons() {
        const questionSets = visualQuestionsContainer.querySelectorAll('.question-set');
        questionSets.forEach((set, index) => {
            const removeBtn = set.querySelector('.remove-question-set');
            if (questionSets.length > 1) {
                removeBtn.style.display = 'inline-block';
            } else {
                removeBtn.style.display = 'none';
            }
        });
    }

    if (addVisualQuestionSetBtn) {
        addVisualQuestionSetBtn.addEventListener('click', () => {
            const newSet = document.createElement('div');
            newSet.className = 'question-set d-flex align-items-center mb-2';
            newSet.innerHTML = `
                <input type="text" class="form-control question-input" placeholder="e.g. What is the art?, Where is the sculpture?" required>
                <button type="button" class="btn btn-danger btn-sm ms-2 remove-question-set">×</button>
            `;
            visualQuestionsContainer.appendChild(newSet);
            updateVisualQuestionSetButtons();
        });
    }

    if (visualQuestionsContainer) {
        visualQuestionsContainer.addEventListener('click', (e) => {
            if (e.target.classList.contains('remove-question-set')) {
                e.target.closest('.question-set').remove();
                updateVisualQuestionSetButtons();
            }
        });
    }
    function updatePreviews(container, filesArray) {
        container.innerHTML = '';
        filesArray.forEach((file, idx) => {
            const wrapper = document.createElement('div');
            wrapper.className = 'image-preview-wrapper position-relative';
            wrapper.style.position = 'relative';
            wrapper.style.width = '100px';
            wrapper.style.height = '100px';
            wrapper.style.margin = '5px';
            if (file.type.startsWith('image/')) {
                const img = document.createElement('img');
                img.src = URL.createObjectURL(file);
                img.style.width = '100%';
                img.style.height = '100%';
                img.style.objectFit = 'cover';
                wrapper.appendChild(img);
            } else if (file.type.startsWith('video/')) {
                const video = document.createElement('video');
                video.src = URL.createObjectURL(file);
                video.controls = true;
                video.muted = true;
                video.style.width = '100%';
                video.style.height = '100%';
                video.style.objectFit = 'cover';
                wrapper.appendChild(video);
            }
            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.textContent = '×';
            removeBtn.className = 'remove-image-btn';
            removeBtn.style.position = 'absolute';
            removeBtn.style.top = '0';
            removeBtn.style.right = '0';
            removeBtn.style.background = 'rgba(255,0,0,0.8)';
            removeBtn.style.color = 'white';
            removeBtn.style.border = 'none';
            removeBtn.style.borderRadius = '50%';
            removeBtn.style.width = '20px';
            removeBtn.style.height = '20px';
            removeBtn.style.cursor = 'pointer';
            removeBtn.addEventListener('click', () => {
                filesArray.splice(idx, 1);
                updatePreviews(container, filesArray);
            });
            wrapper.appendChild(removeBtn);
            container.appendChild(wrapper);
        });
    }
    if (dropZone) {
        dropZone.addEventListener('click', () => fileInput.click());
        dropZone.addEventListener('dragover', e => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
        dropZone.addEventListener('drop', e => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            Array.from(e.dataTransfer.files)
                .filter(f => f.type.startsWith('image/') || f.type.startsWith('video/'))
                .forEach(f => mediaFiles.push(f));
            updatePreviews(previewContainer, mediaFiles);
        });
        fileInput.addEventListener('change', e => {
            Array.from(e.target.files)
                .filter(f => f.type.startsWith('image/') || f.type.startsWith('video/'))
                .forEach(f => mediaFiles.push(f));
            updatePreviews(previewContainer, mediaFiles);
            e.target.value = '';
        });
    }
    if (addVisualForm) {
        addVisualForm.addEventListener('submit', async e => {
            e.preventDefault();
            const questionInputs = visualQuestionsContainer.querySelectorAll('.question-input');
            const questions = Array.from(questionInputs).flatMap(input => input.value.trim().split(',').map(k => [k.trim()]).filter(k => k[0]));
            const userType = document.getElementById('visual-user-type').value;
            const description = document.getElementById('visual-response').value.trim();
            console.log('Parsed questions:', questions);
            console.log('Description:', description);
            if (!questions.some(set => set.length > 0)) return alert('Please enter at least one question.');
            if (!description) return alert('Please enter description.');
            if (mediaFiles.length === 0) return alert('Please select at least one image or video.');

            const formData = new FormData();
            formData.append('questions', JSON.stringify(questions));
            formData.append('user_type', userType);
            formData.append('description', description);
            mediaFiles.forEach(file => formData.append('images', file));

            try {
                const res = await fetch('/add_visual', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                if (data.status === 'success') location.reload();
                else alert(data.message || 'Failed to add visual');
            } catch (err) {
                console.error(err);
                alert('Error uploading visual.');
            }
        });
    }
    // ===== EDIT VISUAL =====
    function attachVisualEdit() {
        document.querySelectorAll('.edit-visual').forEach(button => {
            button.addEventListener('click', () => {
                const visualId = button.dataset.id;
                const card = button.closest('.futuristic-card');

                // Get current data from the card
                let currentQuestions = [];
                try {
                    currentQuestions = JSON.parse(card.dataset.questions || '[]');
                } catch (e) {
                    console.error('Failed to parse questions for visual edit:', e);
                    // If JSON parse fails, assume it's a comma-separated string of questions
                    const questionString = card.dataset.questions || '';
                    if (questionString.trim()) {
                        currentQuestions = questionString.split(',').map(s => s.trim()).filter(s => s);
                    } else {
                        currentQuestions = [];
                    }
                }
                // Handle case where questions might be stored as array of individual characters
                if (Array.isArray(currentQuestions) && currentQuestions.every(q => typeof q === 'string' && q.length === 1)) {
                    currentQuestions = [currentQuestions.join('')];
                }
                const descP = Array.from(card.querySelectorAll('p')).find(p => p.textContent.trim().startsWith('Description:'));
                const currentDesc = descP ? descP.textContent.replace('Description:', '').trim() : '';
                const currentUserType = card.dataset.userType || 'both';

                // Get all existing images from the DOM elements
                const existingImages = card.querySelectorAll('.visual-media img, .visual-media video, img.img-fluid.rounded.mb-3, video');
                const existingImagesData = Array.from(existingImages).map(img => ({
                    src: img.src || img.dataset.src,
                    type: img.tagName.toLowerCase() === 'video' ? 'video' : 'img'
                }));

                // Create popup modal
                const visualModal = document.createElement('div');
                visualModal.className = 'edit-visual-modal modal fade show';
                visualModal.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0,0,0,0.5);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 10002;
                `;

                // Create question sets container
                const questionSetsContainer = document.createElement('div');

                // Normalize questions: if flat array, wrap in array; if nested, use as is
                let questionSets = [];
                if (currentQuestions.length > 0) {
                    if (Array.isArray(currentQuestions[0])) {
                        questionSets = currentQuestions;
                    } else {
                        questionSets = [currentQuestions];
                    }
                }

                function createQuestionDiv(questionValue = '') {
                    const questionDiv = document.createElement('div');
                    questionDiv.className = 'question-item d-flex align-items-center mr-2';

                    const input = document.createElement('input');
                    input.type = 'text';
                    input.className = 'form-control question-input';
                    input.placeholder = 'e.g. Who is this person?';
                    input.value = questionValue;
                    input.required = false;
                    questionDiv.appendChild(input);

                    const removeBtn = document.createElement('button');
                    removeBtn.type = 'button';
                    removeBtn.className = 'btn btn-danger btn-sm ms-2 remove-question';
                    removeBtn.textContent = '×';
                    questionDiv.appendChild(removeBtn);

                    return questionDiv;
                }

                function createSetDiv(set) {
                    const setDiv = document.createElement('div');
                    setDiv.className = 'question-set-group mb-3 border p-3 rounded';

                    const questionsContainer = document.createElement('div');
                    questionsContainer.className = 'questions-container d-flex flex-wrap';

                    if (Array.isArray(set)) {
                        set.forEach(question => {
                            questionsContainer.appendChild(createQuestionDiv(question));
                        });
                    } else {
                        questionsContainer.appendChild(createQuestionDiv(set));
                    }

                    setDiv.appendChild(questionsContainer);

                    const addQuestionBtn = document.createElement('button');
                    addQuestionBtn.type = 'button';
                    addQuestionBtn.className = 'btn btn-secondary btn-sm mt-2 add-question-to-set';
                    addQuestionBtn.textContent = '+ Add Question to Set';
                    setDiv.appendChild(addQuestionBtn);

                    const removeSetBtn = document.createElement('button');
                    removeSetBtn.type = 'button';
                    removeSetBtn.className = 'btn btn-danger btn-sm ms-2 remove-set';
                    removeSetBtn.textContent = 'Remove Set';
                    setDiv.appendChild(removeSetBtn);

                    return setDiv;
                }

                if (questionSets.length > 0) {
                    questionSets.forEach(set => {
                        questionSetsContainer.appendChild(createSetDiv(set));
                    });
                } else {
                    questionSetsContainer.appendChild(createSetDiv([]));
                }

                function updateSetButtons() {
                    const sets = questionSetsContainer.querySelectorAll('.question-set-group');
                    sets.forEach(set => {
                        const removeSetBtn = set.querySelector('.remove-set');
                        if (sets.length > 1) {
                            removeSetBtn.style.display = 'inline-block';
                        } else {
                            removeSetBtn.style.display = 'none';
                        }
                    });
                }

                function updateQuestionButtons(setDiv) {
                    const questions = setDiv.querySelectorAll('.question-item');
                    questions.forEach(question => {
                        const removeBtn = question.querySelector('.remove-question');
                        if (questions.length > 1) {
                            removeBtn.style.display = 'inline-block';
                        } else {
                            removeBtn.style.display = 'none';
                        }
                    });
                }

                // Initial update
                updateSetButtons();
                questionSetsContainer.querySelectorAll('.question-set-group').forEach(setDiv => {
                    updateQuestionButtons(setDiv);
                });

                visualModal.innerHTML = `
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">Edit Visual</h5>
                                <button type="button" class="btn-close" onclick="this.closest('.modal').remove()" style="background: none; border: none; font-size: 24px; color: #6c757d; cursor: pointer; position: absolute; top: 10px; right: 15px; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center;">&times;</button>
                            </div>
                            <div class="modal-body" style="overflow-y: auto; max-height: 70vh;">
                                <form id="edit-visual-form-${visualId}">
                                    <div class="mb-3">
                                        <label class="form-label" title="Question sets that trigger this visual response">Question Sets <i class="fas fa-info-circle"></i></label>
                                        <div id="edit-visual-questions-container-${visualId}"></div>
                                        <button type="button" class="btn btn-secondary btn-sm mt-2" id="add-edit-question-set-${visualId}">+ Add Question Set</button>
                                        <div class="form-text">Each set is comma-separated questions. Multiple sets allow different combinations to trigger the same response.</div>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">User Type</label>
                                        <select class="form-control" id="edit-user-type-${visualId}" required>
                                            <option value="both" ${currentUserType === 'both' ? 'selected' : ''}>Both Users and Guests</option>
                                            <option value="user" ${currentUserType === 'user' ? 'selected' : ''}>Users Only</option>
                                            <option value="guest" ${currentUserType === 'guest' ? 'selected' : ''}>Guests Only</option>
                                        </select>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">Description</label>
                                        <textarea class="form-control" id="edit-description-${visualId}" rows="3" required>${currentDesc}</textarea>
                                    </div>
                                    ${existingImagesData.length > 0 ? `
                                    <div class="mb-3">
                                        <label class="form-label">Existing Images (Click X to remove)</label>
                                        <div id="existing-images-${visualId}" class="d-flex flex-wrap gap-2"></div>
                                    </div>
                                    ` : ''}
                                    <div class="mb-3">
                                        <label class="form-label">Add New Images</label>
                                        <input type="file" class="form-control" id="edit-images-${visualId}" accept="image/*,video/*" multiple>
                                        <div id="edit-images-preview-${visualId}" class="d-flex flex-wrap gap-2 mt-2"></div>
                                    </div>
                                </form>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" onclick="this.closest('.modal').remove()">Cancel</button>
                                <button type="button" class="btn btn-primary" id="save-edit-${visualId}">Save Changes</button>
                            </div>
                        </div>
                    </div>
                `;

                document.body.appendChild(visualModal);

                // Insert the question sets container into the modal
                const questionsContainerPlaceholder = visualModal.querySelector(`#edit-visual-questions-container-${visualId}`);
                questionsContainerPlaceholder.appendChild(questionSetsContainer);

                // Allow closing modal by clicking outside
                visualModal.addEventListener('click', (e) => {
                    if (e.target === visualModal) {
                        visualModal.remove();
                    }
                });

                // Attach event listeners for sets and questions
                const addEditQuestionSetBtn = visualModal.querySelector(`#add-edit-question-set-${visualId}`);

                if (addEditQuestionSetBtn) {
                    addEditQuestionSetBtn.addEventListener('click', () => {
                        questionSetsContainer.appendChild(createSetDiv([]));
                        updateSetButtons();
                        updateQuestionButtons(questionSetsContainer.lastElementChild);
                    });
                }

                questionSetsContainer.addEventListener('click', (e) => {
                    if (e.target.classList.contains('remove-set')) {
                        e.target.closest('.question-set-group').remove();
                        updateSetButtons();
                    } else if (e.target.classList.contains('add-question-to-set')) {
                        const setDiv = e.target.closest('.question-set-group');
                        const questionsContainer = setDiv.querySelector('.questions-container');
                        questionsContainer.appendChild(createQuestionDiv());
                        updateQuestionButtons(setDiv);
                    } else if (e.target.classList.contains('remove-question')) {
                        const setDiv = e.target.closest('.question-set-group');
                        e.target.closest('.question-item').remove();
                        updateQuestionButtons(setDiv);
                    }
                });

                // Handle existing images display and removal
                const existingImagesContainer = visualModal.querySelector(`#existing-images-${visualId}`);
                const removedImages = new Set();

                if (existingImagesContainer) {
                    existingImagesData.forEach((img, index) => {
                        const wrapper = document.createElement('div');
                        wrapper.className = 'image-preview-wrapper position-relative';
                        wrapper.style.position = 'relative';
                        wrapper.style.width = '100px';
                        wrapper.style.height = '100px';
                        wrapper.style.margin = '5px';

                        const imgElement = document.createElement(img.type);
                        imgElement.src = img.src;
                        imgElement.style.width = '100%';
                        imgElement.style.height = '100%';
                        imgElement.style.objectFit = 'cover';

                        if (img.type === 'video') {
                            imgElement.controls = true;
                            imgElement.muted = true;
                        }

                        wrapper.appendChild(imgElement);

                        const removeBtn = document.createElement('button');
                        removeBtn.type = 'button';
                        removeBtn.textContent = '×';
                        removeBtn.className = 'remove-image-btn';
                        removeBtn.style.position = 'absolute';
                        removeBtn.style.top = '0';
                        removeBtn.style.right = '0';
                        removeBtn.style.background = 'rgba(255,0,0,0.8)';
                        removeBtn.style.color = 'white';
                        removeBtn.style.border = 'none';
                        removeBtn.style.borderRadius = '50%';
                        removeBtn.style.width = '20px';
                        removeBtn.style.height = '20px';
                        removeBtn.style.cursor = 'pointer';
                        removeBtn.title = 'Remove this image';

                        removeBtn.addEventListener('click', () => {
                            // Extract the path after '/static/' to match backend storage format
                            const url = new URL(img.src);
                            const relativeSrc = url.pathname.replace('/static/', '');
                            removedImages.add(relativeSrc);
                            wrapper.remove();
                        });

                        wrapper.appendChild(removeBtn);
                        existingImagesContainer.appendChild(wrapper);
                    });
                }

                // Handle new images preview
                const imagesInput = visualModal.querySelector(`#edit-images-${visualId}`);
                const previewContainer = visualModal.querySelector(`#edit-images-preview-${visualId}`);
                let newImageFiles = [];

                imagesInput.addEventListener('change', (e) => {
                    newImageFiles = Array.from(e.target.files);
                    updatePreviews(previewContainer, newImageFiles);
                });

                // Handle save
                visualModal.querySelector(`#save-edit-${visualId}`).addEventListener('click', async () => {
                    const questionInputs = visualModal.querySelectorAll('.question-input');
                    const updatedQuestions = Array.from(questionInputs).map(input => input.value.trim().split(',').map(k => k.trim()).filter(k => k));
                    const updatedUserType = visualModal.querySelector(`#edit-user-type-${visualId}`).value;
                    const updatedDesc = visualModal.querySelector(`#edit-description-${visualId}`).value.trim();

                    if (!updatedDesc) {
                        alert('Description is required.');
                        return;
                    }

                    const formData = new FormData();
                    formData.append('questions', JSON.stringify(updatedQuestions));
                    formData.append('user_type', updatedUserType);
                    formData.append('description', updatedDesc);
                    formData.append('removedImages', JSON.stringify(Array.from(removedImages)));
                    newImageFiles.forEach(file => formData.append('images', file));

                    try {
                        formData.append('csrf_token', getCsrfToken());
                        const res = await fetch(`/edit_visual/${visualId}`, {
                            method: 'POST',
                            body: formData
                        });
                        const data = await res.json();
                        if (data.status === 'success') {
                            visualModal.remove();
                            location.reload();
                        } else {
                            alert(data.message || 'Failed to update visual');
                        }
                    } catch (err) {
                        console.error(err);
                        alert('Error updating visual.');
                    }
                });
            });
        });
    }

    attachVisualEdit();
    // ===== DELETE VISUAL =====
    document.querySelectorAll('.delete-visual').forEach(btn => {
        btn.addEventListener('click', async () => {
            const visualId = btn.dataset.id;
            if (!confirm('Are you sure you want to delete this visual?')) return;
            try {
                const response = await fetch('/delete_visual', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
                    body: JSON.stringify({ id: visualId })
                });
                const data = await response.json();
                if (data.status === 'success') location.reload();
                else alert('Failed to delete visual');
            } catch (error) {
                console.error(error);
                alert('Error deleting visual');
            }
        });
    });
});

// ===== FULL-SCREEN IMAGE MODAL =====
let currentImageIndex = 0;
let allImages = [];

// Create modal elements
const modal = document.createElement('div');
modal.id = 'image-modal';
modal.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.9);
    display: none;
    z-index: 10001;
    cursor: pointer;
`;

const modalImg = document.createElement('img');
modalImg.style.cssText = `
    max-width: 90%;
    max-height: 90%;
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    object-fit: contain;
`;

const modalVideo = document.createElement('video');
modalVideo.style.cssText = `
    max-width: 90%;
    max-height: 90%;
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    object-fit: contain;
`;
modalVideo.controls = true;

const closeBtn = document.createElement('button');
closeBtn.innerHTML = '×';
closeBtn.style.cssText = `
    position: absolute;
    top: 20px;
    right: 30px;
    color: white;
    font-size: 40px;
    font-weight: bold;
    cursor: pointer;
    background: none;
    border: none;
    z-index: 10000;
`;

const prevBtn = document.createElement('button');
prevBtn.innerHTML = '‹';
prevBtn.style.cssText = `
    position: absolute;
    top: 50%;
    left: 20px;
    color: white;
    font-size: 40px;
    font-weight: bold;
    cursor: pointer;
    background: none;
    border: none;
    transform: translateY(-50%);
    z-index: 10000;
`;

const nextBtn = document.createElement('button');
nextBtn.innerHTML = '›';
nextBtn.style.cssText = `
    position: absolute;
    top: 50%;
    right: 20px;
    color: white;
    font-size: 40px;
    font-weight: bold;
    cursor: pointer;
    background: none;
    border: none;
    transform: translateY(-50%);
    z-index: 10000;
`;

modal.appendChild(modalImg);
modal.appendChild(modalVideo);
modal.appendChild(closeBtn);
modal.appendChild(prevBtn);
modal.appendChild(nextBtn);
document.body.appendChild(modal);

// Modal event listeners
closeBtn.addEventListener('click', closeModal);
prevBtn.addEventListener('click', showPrevImage);
nextBtn.addEventListener('click', showNextImage);
modal.addEventListener('click', (e) => {
    if (e.target === modal) closeModal();
});

document.addEventListener('keydown', (e) => {
    if (modal.style.display === 'block') {
        if (e.key === 'Escape') closeModal();
        else if (e.key === 'ArrowLeft') showPrevImage();
        else if (e.key === 'ArrowRight') showNextImage();
    }
});

// Media item click handler
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('media-item')) {
        e.preventDefault();
        const mediaItem = e.target;
        const container = mediaItem.closest('.visual-media');
        if (container) {
            allImages = Array.from(container.querySelectorAll('.media-item')).map(item => ({
                src: item.dataset.src,
                type: item.dataset.type
            }));
            currentImageIndex = allImages.findIndex(img => img.src === mediaItem.dataset.src);
            showImage(currentImageIndex);
        }
    }
});

// Functions
function showAllImages(visualId) {
    const container = document.querySelector(`.visual-media[data-visual-id="${visualId}"]`);
    if (container) {
        // Get all media items from the visual data attribute (including first 3)
        const card = container.closest('.futuristic-card');
        let visualData = {};
        try {
            visualData = JSON.parse(card.dataset.visual || '{}');
        } catch (e) {
            console.error('Failed to parse visual data:', e);
            visualData = {};
        }
        const visualImages = visualData.urls ? visualData.urls.map(img => ({
            src: '/static/' + img,
            type: img.toLowerCase().includes('.mp4') || img.toLowerCase().includes('.avi') || img.toLowerCase().includes('.mov') || img.toLowerCase().includes('.wmv') || img.toLowerCase().includes('.flv') || img.toLowerCase().includes('.webm') ? 'video' : 'img'
        })) : [];

        // Create popup modal
        const galleryModal = document.createElement('div');
        galleryModal.className = 'modal fade show';
        galleryModal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
        `;

        const modalContent = document.createElement('div');
        modalContent.style.cssText = `
            background: white;
            border-radius: 10px;
            padding: 20px;
            max-width: 90%;
            max-height: 80%;
            overflow: hidden;
            position: relative;
        `;

        const closeBtn = document.createElement('button');
        closeBtn.innerHTML = '×';
        closeBtn.style.cssText = `
            position: absolute;
            top: 10px;
            right: 15px;
            background: none;
            border: none;
            font-size: 24px;
            cursor: pointer;
            color: #666;
            z-index: 10001;
        `;

        const title = document.createElement('h5');
        title.textContent = 'All Images';
        title.style.cssText = `
            margin: 0 0 15px 0;
            color: #333;
            font-weight: bold;
        `;

        // Create horizontal scrollable gallery
        const galleryContainer = document.createElement('div');
        galleryContainer.className = 'gallery-images';
        galleryContainer.style.cssText = `
            display: flex;
            gap: 15px;
            overflow-x: auto;
            padding: 10px 0;
            scrollbar-width: thin;
            scrollbar-color: #888 transparent;
            max-height: 400px;
        `;

        // Add webkit scrollbar styling
        const style = document.createElement('style');
        style.textContent = `
            .gallery-images::-webkit-scrollbar {
                height: 8px;
            }
            .gallery-images::-webkit-scrollbar-thumb {
                background: #888;
                border-radius: 4px;
            }
            .gallery-images::-webkit-scrollbar-track {
                background: transparent;
            }
        `;
        document.head.appendChild(style);

        // Show all images in the horizontal gallery
        visualImages.forEach(media => {
            const mediaElement = document.createElement(media.type);

            mediaElement.src = media.src;
            mediaElement.className = 'img-fluid rounded media-item gallery-image';
            mediaElement.style.cssText = `
                width: 150px;
                height: 150px;
                object-fit: cover;
                cursor: pointer;
                flex-shrink: 0;
                transition: transform 0.2s ease;
                border: 2px solid #eee;
                border-radius: 8px;
            `;
            mediaElement.dataset.src = media.src;
            mediaElement.dataset.type = media.type;

            if (media.type === 'video') {
                mediaElement.controls = true;
                mediaElement.muted = true;
            }

            // Add hover effect
            mediaElement.addEventListener('mouseenter', () => {
                mediaElement.style.transform = 'scale(1.05)';
                mediaElement.style.borderColor = '#007bff';
            });
            mediaElement.addEventListener('mouseleave', () => {
                mediaElement.style.transform = 'scale(1)';
                mediaElement.style.borderColor = '#eee';
            });

            // Click to open full screen
            mediaElement.addEventListener('click', (e) => {
                e.stopPropagation();
                galleryModal.remove();
                // Populate the global allImages array with all images from this visual
                allImages.length = 0; // Clear the array
                allImages.push(...visualImages); // Add all images from the current visual
                currentImageIndex = allImages.findIndex(img => img.src === mediaElement.dataset.src);
                showImage(currentImageIndex);
            });

            galleryContainer.appendChild(mediaElement);
        });

        // Close modal when clicking outside
        galleryModal.addEventListener('click', (e) => {
            if (e.target === galleryModal) {
                galleryModal.remove();
            }
        });

        // Close modal with button
        closeBtn.addEventListener('click', () => {
            galleryModal.remove();
        });

        // Close modal with Escape key
        document.addEventListener('keydown', function closeModal(e) {
            if (e.key === 'Escape') {
                galleryModal.remove();
                document.removeEventListener('keydown', closeModal);
            }
        });

        modalContent.appendChild(closeBtn);
        modalContent.appendChild(title);
        modalContent.appendChild(galleryContainer);
        galleryModal.appendChild(modalContent);
        document.body.appendChild(galleryModal);
    }
}

function showImage(index) {
    if (index < 0 || index >= allImages.length) return;

    const image = allImages[index];
    modalImg.style.display = 'none';
    modalVideo.style.display = 'none';

    if (image.type === 'img') {
        modalImg.src = image.src;
        modalImg.style.display = 'block';
    } else if (image.type === 'video') {
        modalVideo.src = image.src;
        modalVideo.style.display = 'block';
    }

    modal.style.display = 'block';
    updateNavigationButtons();
}

function closeModal() {
    modal.style.display = 'none';
    modalVideo.pause();
}

function showPrevImage() {
    if (currentImageIndex > 0) {
        currentImageIndex--;
        showImage(currentImageIndex);
    }
}

function showNextImage() {
    if (currentImageIndex < allImages.length - 1) {
        currentImageIndex++;
        showImage(currentImageIndex);
    }
}

function updateNavigationButtons() {
    prevBtn.style.display = currentImageIndex > 0 ? 'block' : 'none';
    nextBtn.style.display = currentImageIndex < allImages.length - 1 ? 'block' : 'none';
}

// ===== SEARCH VISUALS =====
const visualSearchInput = document.getElementById('visual-search');
const visualsContainer = document.getElementById('visuals-container');
let visualSearchTimeout;

if (visualSearchInput && visualsContainer) {
    function applyVisualSearch() {
        const searchValue = visualSearchInput.value.toLowerCase().trim();
        const cards = visualsContainer.querySelectorAll('.futuristic-card');

        cards.forEach(card => {
            const keywordsText = card.querySelector('p strong')?.parentElement?.textContent.toLowerCase() || '';
            const descriptionText = card.querySelectorAll('p')[1]?.textContent.toLowerCase() || '';

            const searchMatch = !searchValue ||
                keywordsText.includes(searchValue) ||
                descriptionText.includes(searchValue);

            card.style.display = searchMatch ? '' : 'none';
        });
    }

    visualSearchInput.addEventListener('input', function() {
        clearTimeout(visualSearchTimeout);
        visualSearchTimeout = setTimeout(applyVisualSearch, 300); // Debounce for 300ms
    });
}

// Fix questions display in visual cards
document.querySelectorAll('.futuristic-card').forEach(card => {
    const questionsPs = card.querySelectorAll('p');
    const questionsPsArray = Array.from(questionsPs).filter(p => p.querySelector('strong') && p.querySelector('strong').textContent.trim() === 'Questions:');
    if (questionsPsArray.length > 0) {
        let questions = [];
        try {
            questions = JSON.parse(card.dataset.questions || '[]');
        } catch (e) {
            const questionString = card.dataset.questions || '';
            if (questionString.trim()) {
                questions = questionString.split(',').map(s => s.trim()).filter(s => s);
            } else {
                questions = [];
            }
        }
        // Process questions to handle nested arrays and character arrays
        if (Array.isArray(questions)) {
            questions = questions.map(set => {
                if (Array.isArray(set)) {
                    return set.map(item => {
                        if (Array.isArray(item) && item.every(c => typeof c === 'string' && c.length === 1)) {
                            return item.join('');
                        } else if (typeof item === 'string') {
                            return item;
                        } else {
                            return '';
                        }
                    });
                } else if (typeof set === 'string') {
                    return [set];
                } else {
                    return [];
                }
            });
        }
        // Remove all existing questions p
        questionsPsArray.forEach(p => p.remove());
        // Insert new p for each set at the beginning of visual-card-content
        const content = card.querySelector('.visual-card-content');
        if (content) {
            questions.forEach(set => {
                const displayText = set.join(', ');
                const newP = document.createElement('p');
                newP.innerHTML = '<strong>Questions:</strong> ' + displayText;
                content.insertBefore(newP, content.firstElementChild);
            });
        }
    }
});
