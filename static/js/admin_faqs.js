 document.addEventListener('DOMContentLoaded', function() {
  const addInfoForm = document.getElementById('add-info-form');
  const questionInput = document.getElementById('question');
  const answerInput = document.getElementById('answer');
  const infoTable = document.getElementById('info-table');
  const infoSearchInput = document.getElementById('info-search');

  // Function to get CSRF token from meta tag
  function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
  }

  // Add new FAQ entry
  addInfoForm.addEventListener('submit', async function(e) {
    e.preventDefault();

    const question = questionInput.value.trim();
    const answer = answerInput.value.trim();
    const userType = document.getElementById('faq-user-type').value;

    if (!question || !answer) {
      alert('Please enter both question and answer.');
      return;
    }

    try {
      const response = await fetch('/add_info', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ question, answer, user_type: userType })
      });

      const data = await response.json();

      if (data.status === 'success') {
        // Reload page to show updated FAQ list
        window.location.reload();
      } else {
        alert(data.message || 'Failed to add FAQ.');
      }
    } catch (error) {
      console.error('Error adding FAQ:', error);
      alert('An error occurred. Please try again.');
    }
  });

  // Attach event listeners for edit and delete buttons
  function attachInfoEventListeners() {
    // Delete buttons
    const deleteButtons = document.querySelectorAll('.delete-info');
    deleteButtons.forEach(button => {
      button.replaceWith(button.cloneNode(true));
    });
    const freshDeleteButtons = document.querySelectorAll('.delete-info');
    freshDeleteButtons.forEach(button => {
      button.addEventListener('click', async function() {
        const infoId = this.getAttribute('data-info-id');
        if (confirm('Are you sure you want to delete this FAQ entry?')) {
          try {
            const response = await fetch('/delete_info', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
              },
              body: JSON.stringify({ info_id: parseInt(infoId) })
            });
            const data = await response.json();
            if (data.status === 'success') {
              window.location.reload();
            } else {
              alert(data.message || 'Failed to delete FAQ.');
            }
          } catch (error) {
            console.error('Error deleting info:', error);
            alert('An error occurred. Please try again.');
          }
        }
      });
    });

    // Edit buttons
    const editButtons = document.querySelectorAll('.edit-info');
    editButtons.forEach(button => {
      button.replaceWith(button.cloneNode(true));
    });
    const freshEditButtons = document.querySelectorAll('.edit-info');
    freshEditButtons.forEach(button => {
      button.addEventListener('click', function() {
        const row = this.closest('tr');
        const infoId = this.getAttribute('data-info-id');

        if (row.classList.contains('editing')) {
          return;
        }
        row.classList.add('editing');

        const questionCell = row.querySelector('.info-question');
        const answerCell = row.querySelector('.info-answer');

        const currentQuestion = questionCell.innerHTML.trim();
        const currentAnswer = answerCell.innerHTML.trim();

        questionCell.innerHTML = `<textarea class="form-control form-control-sm edit-question" rows="3">${currentQuestion}</textarea>`;
        answerCell.innerHTML = `<textarea class="form-control form-control-sm edit-answer" rows="5">${currentAnswer}</textarea>`;

        const actionsCell = this.parentElement;
        actionsCell.innerHTML = `
          <button class="btn btn-sm btn-success save-edit" data-info-id="${infoId}" title="Save">
            <i class="fas fa-save"></i>
          </button>
          <button class="btn btn-sm btn-secondary cancel-edit" title="Cancel">
            <i class="fas fa-times"></i>
          </button>
        `;

        // Save edit
        actionsCell.querySelector('.save-edit').addEventListener('click', async () => {
          const newQuestion = row.querySelector('.edit-question').value.trim();
          const newAnswer = row.querySelector('.edit-answer').value.trim();

          if (!newQuestion || !newAnswer) {
            alert('Question and answer cannot be empty.');
            return;
          }

          try {
            const response = await fetch('/edit_info', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
              },
              body: JSON.stringify({
                info_id: parseInt(infoId),
                question: newQuestion,
                answer: newAnswer
              })
            });
            const data = await response.json();
            if (data.status === 'success') {
              window.location.reload();
            } else {
              alert(data.message || 'Failed to update info.');
            }
          } catch (error) {
            console.error('Error updating info:', error);
            alert('An error occurred. Please try again.');
          }
        });

        // Cancel edit
        actionsCell.querySelector('.cancel-edit').addEventListener('click', () => {
          window.location.reload();
        });
      });
    });
  }

  attachInfoEventListeners();

  // Search filter with debouncing
  const searchTypeSelect = document.getElementById('search-type');
  let searchTimeout;

  function applySearch() {
    const searchValue = infoSearchInput.value.toLowerCase().trim();
    const searchType = searchTypeSelect.value;
    const rows = infoTable.querySelectorAll('tbody tr');

    rows.forEach(row => {
      if (row.querySelector('td').colSpan === 3) {
        row.style.display = '';
        return;
      }
      const questionText = row.querySelector('.info-question').textContent.toLowerCase();
      const answerText = row.querySelector('.info-answer').textContent.toLowerCase();

      let searchMatch = false;

      if (!searchValue) {
        searchMatch = true;
      } else {
        if (searchType === 'both') {
          searchMatch = questionText.includes(searchValue) || answerText.includes(searchValue);
        } else if (searchType === 'question') {
          searchMatch = questionText.includes(searchValue);
        } else if (searchType === 'answer') {
          searchMatch = answerText.includes(searchValue);
        }
      }

      if (searchMatch) {
        row.style.display = '';
      } else {
        row.style.display = 'none';
      }
    });
  }

  infoSearchInput.addEventListener('input', function() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(applySearch, 300); // Debounce for 300ms
  });

  searchTypeSelect.addEventListener('change', applySearch);
});
