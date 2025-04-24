// Auto-scroll chat box to bottom
document.addEventListener('DOMContentLoaded', function() {
    const chatBox = document.querySelector('.chat-box');
    if (chatBox) {
        chatBox.scrollTop = chatBox.scrollHeight;
    }
});