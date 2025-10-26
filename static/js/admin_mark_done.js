document.addEventListener('DOMContentLoaded', function() {
    // Function to get CSRF token from meta tag
    function getCsrfToken() {
        return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    }

    // Add event listener for "Mark as Done" buttons on admin feedback page
    function attachMarkDoneEventListeners() {
        const markDoneButtons = document.querySelectorAll('.mark-done-btn');
        markDoneButtons.forEach(button => {
            button.addEventListener('click', function() {
                const row = this.closest('tr');
                const feedbackId = row.getAttribute('data-feedback-id');
                const feedbackMessage = row.getAttribute('data-feedback-message');
                const feedbackTimestamp = row.getAttribute('data-feedback-timestamp');

                // Populate modal content
                const modal = new bootstrap.Modal(document.getElementById('markDoneModal'));
                document.getElementById('markDoneFeedbackMessage').textContent = feedbackMessage;
                document.getElementById('markDoneFeedbackTimestamp').textContent = feedbackTimestamp;
                document.getElementById('confirmMarkDoneBtn').setAttribute('data-feedback-id', feedbackId);

                modal.show();
            });
        });
    }

    // Add event listener for "View" buttons on admin feedback page
    function attachViewEventListeners() {
        const viewButtons = document.querySelectorAll('.view-feedback-btn');
        viewButtons.forEach(button => {
            button.addEventListener('click', function() {
                const row = this.closest('tr');
                const feedbackMessage = row.getAttribute('data-feedback-message');
                const feedbackTimestamp = row.getAttribute('data-feedback-timestamp');

                // Populate modal content
                const modal = new bootstrap.Modal(document.getElementById('feedbackModal'));
                document.getElementById('modal-feedback-message').textContent = feedbackMessage;
                document.getElementById('modal-feedback-timestamp').textContent = feedbackTimestamp;

                modal.show();
            });
        });
    }

    // Confirm mark as done button click handler
    const confirmMarkDoneBtn = document.getElementById('confirmMarkDoneBtn');
    if (confirmMarkDoneBtn) {
        confirmMarkDoneBtn.addEventListener('click', async function() {
            const feedbackId = this.getAttribute('data-feedback-id');
            if (!feedbackId) {
                alert('Feedback ID not found.');
                return;
            }

            try {
                const response = await fetch('/admin/feedback/mark_done', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify({ feedback_id: feedbackId })
                });

                const data = await response.json();

                if (data.status === 'success') {
                    // Remove the feedback row from the table
                    const row = document.querySelector(`tr[data-feedback-id="${feedbackId}"]`);
                    if (row) {
                        row.remove();
                    }
                    // Hide the modal
                    const modalEl = document.getElementById('markDoneModal');
                    const modal = bootstrap.Modal.getInstance(modalEl);
                    modal.hide();

                    alert('Feedback marked as done successfully.');
                } else {
                    alert(data.message || 'Failed to mark feedback as done.');
                }
            } catch (error) {
                console.error('Error marking feedback as done:', error);
                alert('An error occurred. Please try again.');
            }
        });
    }

    // Call the function to attach event listeners
    attachMarkDoneEventListeners();
    attachViewEventListeners();
});
