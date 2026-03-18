document.addEventListener('DOMContentLoaded', function () {
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatBox = document.getElementById('chat-box');
    const markBtn = document.getElementById('mark-complete-btn');


    // Only load intro if chatBox is empty (i.e., first load, no chat yet)
    if (chatBox && chatBox.innerHTML.trim() === '') {
        fetch('/chatbot/module_intro', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ module_id: chatForm.dataset.moduleId })
        })
        .then(resp => resp.json())
        .then(data => {
            chatBox.innerHTML += `<div class="mb-2 text-left">
                <span class="inline-block px-3 py-2 bg-yellow-50 rounded-lg">${data.intro}</span>
            </div>`;
            chatBox.scrollTop = chatBox.scrollHeight;
        });
    }
        
    if (chatForm) {
        chatForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            const message = chatInput.value;
            chatBox.innerHTML += `<div class="mb-2 text-right"><span class="inline-block px-3 py-2 bg-blue-100 rounded-lg">${message}</span></div>`;
            chatInput.value = '';
            // Post to backend
            const resp = await fetch('/chatbot/message', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    message: message,
                    module_id: chatForm.dataset.moduleId
                })
            });
            const data = await resp.json();
            chatBox.innerHTML += `<div class="mb-2 text-left"><span class="inline-block px-3 py-2 bg-gray-100 rounded-lg">${data.reply}</span></div>`;
            chatBox.scrollTop = chatBox.scrollHeight;

            // Detect MCQ and user's answer, simulate quiz answer logic
            // After receiving the response from /chatbot/message, handle quiz_passed directly
            // Enable Mark Complete whenever backend reports quiz_passed=true
            if (data.quiz_passed === true && markBtn) {
                markBtn.disabled = false;
            }

        });
    }
    // Initially disable Mark Complete button if not passed
    if (markBtn && !window.quizPassed) {
        markBtn.disabled = true;
    }
});



  
