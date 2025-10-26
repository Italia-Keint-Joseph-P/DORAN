document.addEventListener('DOMContentLoaded', function() {
    const showFinishedFeedbackBtn = document.getElementById('showFinishedFeedbackBtn');
    const finishedFeedbackModal = new bootstrap.Modal(document.getElementById('finishedFeedbackModal'));
    const finishedFeedbackContent = document.getElementById('finishedFeedbackContent');

    function groupFeedbackByDate(feedbacks) {
        const grouped = {};
        feedbacks.forEach(fb => {
            const date = fb.timestamp.split(' ')[0]; // Extract date part
            if (!grouped[date]) {
                grouped[date] = [];
            }
            grouped[date].push(fb);
        });
        return grouped;
    }

    function createDateSection(date, feedbacks) {
        const section = document.createElement('div');
        section.classList.add('finished-feedback-date-section');

        const header = document.createElement('h5');
        header.classList.add('finished-feedback-date-header');
        header.textContent = date;
        header.style.cursor = 'pointer';

        const feedbackList = document.createElement('div');
        feedbackList.classList.add('finished-feedback-list');
        feedbackList.style.maxHeight = '200px';
        feedbackList.style.overflowY = 'auto';
        feedbackList.style.marginBottom = '1rem';
        feedbackList.style.display = 'none'; // Hide feedback list initially

        feedbacks.forEach(fb => {
            const fbDiv = document.createElement('div');
            fbDiv.classList.add('finished-feedback-item');
            fbDiv.style.padding = '0.5rem';
            fbDiv.style.borderBottom = '1px solid #ccc';

            const user = fb.user_id ? `User ID: ${fb.user_id}` : 'Guest';
            fbDiv.innerHTML = `
                <strong>${user}</strong><br>
                <small>${fb.timestamp}</small>
                <pre style="white-space: pre-wrap; margin-top: 0.25rem;">${fb.message}</pre>
            `;
            feedbackList.appendChild(fbDiv);
        });

        header.addEventListener('click', () => {
            if (feedbackList.style.display === 'none') {
                feedbackList.style.display = 'block';
                feedbackList.scrollIntoView({ behavior: 'smooth' });
            } else {
                feedbackList.style.display = 'none';
            }
        });

        section.appendChild(header);
        section.appendChild(feedbackList);

        return section;
    }

    async function loadFinishedFeedback() {
        finishedFeedbackContent.innerHTML = '<p>Loading finished feedback...</p>';
        try {
            const response = await fetch('/admin/feedback/finished');
            const data = await response.json();
            if (data.status === 'success') {
                const grouped = groupFeedbackByDate(data.finished_feedback);
                finishedFeedbackContent.innerHTML = '';
                for (const date in grouped) {
                    const section = createDateSection(date, grouped[date]);
                    finishedFeedbackContent.appendChild(section);
                }
            } else {
                finishedFeedbackContent.innerHTML = `<p>Error loading finished feedback: ${data.message}</p>`;
            }
        } catch (error) {
            finishedFeedbackContent.innerHTML = `<p>Error loading finished feedback.</p>`;
            console.error('Error loading finished feedback:', error);
        }
    }

    showFinishedFeedbackBtn.addEventListener('click', () => {
        loadFinishedFeedback();
        finishedFeedbackModal.show();
    });
});
