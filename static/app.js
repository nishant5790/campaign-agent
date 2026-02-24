/**
 * LinkedIn Post Generator - Chat Agent Frontend
 */

class LinkedInPostGenerator {
    constructor() {
        this.sessionId = null;
        this.currentPosts = [];
        this.researchData = {};
        this.currentEditingPost = null;
        this.isLoading = false;

        this.initializeElements();
        this.attachEventListeners();
        this.initSession();
    }

    initializeElements() {
        // Chat elements
        this.chatSection = document.getElementById('chatSection');
        this.chatMessages = document.getElementById('chatMessages');
        this.chatForm = document.getElementById('chatForm');
        this.chatInput = document.getElementById('chatInput');
        this.chatSendBtn = document.getElementById('chatSendBtn');
        this.chatInputBar = document.getElementById('chatInputBar');

        // Processing elements
        this.processingContainer = document.getElementById('processingContainer');
        this.logEntries = document.getElementById('logEntries');
        this.logContent = document.getElementById('logContent');
        this.logToggle = document.getElementById('logToggle');

        // Results elements
        this.resultsSection = document.getElementById('resultsSection');
        this.postsGrid = document.getElementById('postsGrid');
        this.startOverBtn = document.getElementById('startOverBtn');
        this.toggleResearch = document.getElementById('toggleResearch');
        this.researchContent = document.getElementById('researchContent');
        this.trendingTopics = document.getElementById('trendingTopics');
        this.researchReport = document.getElementById('researchReport');

        // Modal elements
        this.refineModal = document.getElementById('refineModal');
        this.modalPostPreview = document.getElementById('modalPostPreview');
        this.feedbackInput = document.getElementById('feedbackInput');
        this.closeModal = document.getElementById('closeModal');
        this.cancelRefine = document.getElementById('cancelRefine');
        this.submitRefine = document.getElementById('submitRefine');

        // Header
        this.newChatBtn = document.getElementById('newChatBtn');

        // Toast
        this.toast = document.getElementById('toast');
    }

    attachEventListeners() {
        // Chat form
        this.chatForm.addEventListener('submit', (e) => this.handleChatSubmit(e));

        // Auto-resize textarea
        this.chatInput.addEventListener('input', () => this.autoResizeInput());

        // Enter to send (Shift+Enter for newline)
        this.chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.chatForm.dispatchEvent(new Event('submit'));
            }
        });

        // Log toggle
        this.logToggle.addEventListener('click', () => this.toggleLog());

        // Start over
        this.startOverBtn.addEventListener('click', () => this.startOver());

        // New chat button in header
        this.newChatBtn.addEventListener('click', () => this.startOver());

        // Research toggle
        this.toggleResearch.addEventListener('click', () => this.toggleResearchPanel());

        // Modal controls
        this.closeModal.addEventListener('click', () => this.hideModal());
        this.cancelRefine.addEventListener('click', () => this.hideModal());
        this.submitRefine.addEventListener('click', () => this.handleRefine());

        // Close modal on overlay click
        this.refineModal.addEventListener('click', (e) => {
            if (e.target === this.refineModal) this.hideModal();
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !this.refineModal.classList.contains('hidden')) {
                this.hideModal();
            }
        });
    }

    // ─── Session Management ────────────────────────────────────

    async initSession() {
        try {
            const response = await fetch('/api/sessions', { method: 'POST' });
            const data = await response.json();
            if (data.success) {
                this.sessionId = data.session_id;
                this.showWelcomeMessage();
                this.chatInput.focus();
            }
        } catch (error) {
            console.error('Failed to create session:', error);
            this.addSystemMessage('⚠️ Failed to connect to the server. Please refresh the page.');
        }
    }

    showWelcomeMessage() {
        this.addAssistantMessage(
            `👋 **Hey there!** I'm your LinkedIn content strategist.\n\n` +
            `Tell me about the LinkedIn post you'd like to create — what topic, who you are, ` +
            `and who you want to reach. I'll put together a research plan and craft the perfect post for you.\n\n` +
            `What would you like to write about?`
        );
    }

    // ─── Chat Messaging ────────────────────────────────────────

    async handleChatSubmit(e) {
        e.preventDefault();
        const message = this.chatInput.value.trim();
        if (!message || this.isLoading) return;

        // Add user message to chat
        this.addUserMessage(message);
        this.chatInput.value = '';
        this.autoResizeInput();

        // Show typing indicator
        this.setChatLoading(true);
        const typingId = this.showTypingIndicator();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    message: message,
                }),
            });

            const data = await response.json();
            this.removeTypingIndicator(typingId);

            if (!data.success) {
                this.addSystemMessage('⚠️ ' + (data.detail || 'Something went wrong.'));
                return;
            }

            // Add AI response
            this.addAssistantMessage(data.response);

            // If a plan was generated, show the plan card
            if (data.plan && data.status === 'plan_pending') {
                this.showPlanCard(data.plan);
            }

        } catch (error) {
            this.removeTypingIndicator(typingId);
            console.error('Chat error:', error);
            this.addSystemMessage('⚠️ Failed to send message. Please try again.');
        } finally {
            this.setChatLoading(false);
        }
    }

    addUserMessage(text) {
        const bubble = document.createElement('div');
        bubble.className = 'chat-bubble user';
        bubble.innerHTML = `
            <div class="bubble-content">
                <div class="bubble-text">${this.escapeHtml(text)}</div>
            </div>
            <div class="bubble-avatar user-avatar">
                <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                </svg>
            </div>
        `;
        this.chatMessages.appendChild(bubble);
        this.scrollToBottom();
    }

    addAssistantMessage(text) {
        const bubble = document.createElement('div');
        bubble.className = 'chat-bubble assistant';
        bubble.innerHTML = `
            <div class="bubble-avatar assistant-avatar">
                <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.32 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.79M6.88 8.56a1.68 1.68 0 0 0 1.68-1.68c0-.93-.75-1.69-1.68-1.69a1.69 1.69 0 0 0-1.69 1.69c0 .93.76 1.68 1.69 1.68m1.39 9.94v-8.37H5.5v8.37h2.77z"/>
                </svg>
            </div>
            <div class="bubble-content">
                <div class="bubble-text">${this.formatMarkdown(text)}</div>
            </div>
        `;
        this.chatMessages.appendChild(bubble);
        this.scrollToBottom();
    }

    addSystemMessage(text) {
        const msg = document.createElement('div');
        msg.className = 'chat-system-message';
        msg.innerHTML = `<span>${text}</span>`;
        this.chatMessages.appendChild(msg);
        this.scrollToBottom();
    }

    showTypingIndicator() {
        const id = 'typing-' + Date.now();
        const indicator = document.createElement('div');
        indicator.className = 'chat-bubble assistant typing-indicator-bubble';
        indicator.id = id;
        indicator.innerHTML = `
            <div class="bubble-avatar assistant-avatar">
                <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.32 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.79M6.88 8.56a1.68 1.68 0 0 0 1.68-1.68c0-.93-.75-1.69-1.68-1.69a1.69 1.69 0 0 0-1.69 1.69c0 .93.76 1.68 1.69 1.68m1.39 9.94v-8.37H5.5v8.37h2.77z"/>
                </svg>
            </div>
            <div class="bubble-content">
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        this.chatMessages.appendChild(indicator);
        this.scrollToBottom();
        return id;
    }

    removeTypingIndicator(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    // ─── Plan Card ─────────────────────────────────────────────

    showPlanCard(planText) {
        const card = document.createElement('div');
        card.className = 'plan-card';
        card.innerHTML = `
            <div class="plan-card-header">
                <div class="plan-card-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"/>
                        <rect x="9" y="3" width="6" height="4" rx="1"/>
                    </svg>
                </div>
                <div>
                    <h3>Content Plan</h3>
                    <p>Review the proposed plan below</p>
                </div>
            </div>
            <div class="plan-card-body">
                <div class="plan-text">${this.formatMarkdown(planText)}</div>
            </div>
            <div class="plan-card-actions">
                <button class="plan-btn plan-btn-approve" id="approvePlanBtn">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="20 6 9 17 4 12"/>
                    </svg>
                    Approve & Generate
                </button>
                <button class="plan-btn plan-btn-edit" id="editPlanBtn">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                    </svg>
                    Request Changes
                </button>
            </div>
        `;

        this.chatMessages.appendChild(card);
        this.scrollToBottom();

        // Attach plan action handlers
        card.querySelector('#approvePlanBtn').addEventListener('click', () => this.handleApprovePlan(card));
        card.querySelector('#editPlanBtn').addEventListener('click', () => this.handleEditPlan(card));
    }

    async handleApprovePlan(planCard) {
        // Disable plan buttons
        const btns = planCard.querySelectorAll('.plan-btn');
        btns.forEach(b => { b.disabled = true; b.classList.add('disabled'); });

        // Update plan card status
        const actionsDiv = planCard.querySelector('.plan-card-actions');
        actionsDiv.innerHTML = `
            <div class="plan-approved-badge">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20 6 9 17 4 12"/>
                </svg>
                Plan Approved — Generating posts...
            </div>
        `;

        // Hide chat input during generation
        this.chatInputBar.classList.add('hidden');

        // Show processing pipeline
        this.processingContainer.classList.remove('hidden');
        this.resetProcessingUI();
        this.scrollToBottom();

        // Show new chat button
        this.newChatBtn.classList.remove('hidden');

        try {
            const response = await fetch('/api/approve-plan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: this.sessionId }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            // Process SSE stream
            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            this.handleStreamEvent(data);
                        } catch (parseError) {
                            console.warn('Failed to parse SSE data:', parseError);
                        }
                    }
                }
            }

        } catch (error) {
            console.error('Generation error:', error);
            this.addLogEntry(`Error: ${error.message}`, 'error');
            this.showToast('Failed to generate posts. Please try again.', 'error');
            this.chatInputBar.classList.remove('hidden');
        }
    }

    handleEditPlan(planCard) {
        // Focus the chat input for the user to type feedback
        this.chatInput.placeholder = "Describe what changes you'd like to the plan...";
        this.chatInput.focus();
        this.scrollToBottom();
    }

    // ─── SSE Stream Handling ───────────────────────────────────

    handleStreamEvent(event) {
        switch (event.type) {
            case 'stage':
                this.handleStageEvent(event);
                break;
            case 'progress':
                this.addLogEntry(event.message, 'info');
                break;
            case 'result':
                this.handleResultEvent(event);
                break;
            case 'complete':
                this.handleComplete(event);
                break;
            case 'error':
                this.addLogEntry(event.message, 'error');
                this.showToast(event.message, 'error');
                break;
        }
    }

    handleStageEvent(event) {
        const stage = event.stage;
        this.addLogEntry(event.message, 'info');

        const steps = document.querySelectorAll('.pipeline-step');
        steps.forEach(stepEl => {
            const stageName = stepEl.dataset.stage;
            if (stageName === stage) {
                stepEl.classList.add('active');
                stepEl.classList.remove('completed');
            }
        });
    }

    handleResultEvent(event) {
        const stage = event.stage;
        this.addLogEntry(event.message, 'success');

        const stepEl = document.querySelector(`.pipeline-step[data-stage="${stage}"]`);
        if (stepEl) {
            stepEl.classList.remove('active');
            stepEl.classList.add('completed');

            const outputEl = stepEl.querySelector('.step-output');
            if (outputEl && event.data) {
                let preview = '';
                if (event.data.topics) {
                    preview = event.data.topics.substring(0, 100) + '...';
                } else if (event.data.report) {
                    preview = event.data.report.substring(0, 100) + '...';
                } else if (event.data.posts) {
                    preview = `Generated ${event.data.posts.length} post variations`;
                }
                outputEl.textContent = preview;
                outputEl.classList.add('visible');
            }
        }

        if (event.data) {
            if (event.data.topics) this.researchData.topics = event.data.topics;
            if (event.data.report) this.researchData.report = event.data.report;
            if (event.data.posts) this.currentPosts = event.data.posts;
        }
    }

    handleComplete(event) {
        this.addLogEntry(event.message, 'success');

        if (event.data) {
            if (event.data.trending_topics) this.researchData.topics = event.data.trending_topics;
            if (event.data.research_report) this.researchData.report = event.data.research_report;
            if (event.data.posts) this.currentPosts = event.data.posts;
        }

        setTimeout(() => {
            this.showResults();
        }, 600);
    }

    // ─── Results ───────────────────────────────────────────────

    showResults() {
        this.trendingTopics.textContent = this.researchData.topics || 'No topics found';
        this.researchReport.textContent = this.researchData.report || 'No report generated';
        this.renderPosts();

        // Hide the chat section
        this.chatSection.classList.add('hidden');
        this.resultsSection.classList.remove('hidden');
        this.resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    renderPosts() {
        this.postsGrid.innerHTML = '';
        this.currentPosts.forEach((post, index) => {
            const postCard = this.createPostCard(post, index);
            this.postsGrid.appendChild(postCard);
        });
    }

    createPostCard(post, index) {
        const card = document.createElement('div');
        card.className = 'post-card';
        card.innerHTML = `
            <div class="post-card-header">
                <div class="post-style">
                    <span class="post-number">${post.id || index + 1}</span>
                    <span class="post-style-name">${post.style || `Post ${index + 1}`}</span>
                </div>
                <div class="post-actions">
                    <button class="post-action-btn copy-btn" title="Copy to clipboard">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                        </svg>
                    </button>
                    <button class="post-action-btn refine-btn" title="Refine this post">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                        </svg>
                    </button>
                </div>
            </div>
            <div class="post-card-content">
                <div class="post-text">${this.escapeHtml(post.content)}</div>
            </div>
        `;

        const copyBtn = card.querySelector('.copy-btn');
        const refineBtn = card.querySelector('.refine-btn');
        copyBtn.addEventListener('click', () => this.copyPost(post.content));
        refineBtn.addEventListener('click', () => this.openRefineModal(post, index));

        return card;
    }

    copyPost(content) {
        navigator.clipboard.writeText(content).then(() => {
            this.showToast('Post copied to clipboard!');
        }).catch(() => {
            this.showToast('Failed to copy', 'error');
        });
    }

    openRefineModal(post, index) {
        this.currentEditingPost = { post, index };
        this.modalPostPreview.textContent = post.content;
        this.feedbackInput.value = '';
        this.refineModal.classList.remove('hidden');
        this.feedbackInput.focus();
    }

    hideModal() {
        this.refineModal.classList.add('hidden');
        this.currentEditingPost = null;
    }

    async handleRefine() {
        if (!this.currentEditingPost) return;

        const feedback = this.feedbackInput.value.trim();
        if (!feedback) {
            this.showToast('Please enter your feedback', 'error');
            return;
        }

        const btn = this.submitRefine;
        btn.classList.add('loading');
        btn.disabled = true;

        try {
            const response = await fetch('/api/refine', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    post_content: this.currentEditingPost.post.content,
                    feedback: feedback,
                }),
            });

            const data = await response.json();

            if (data.success) {
                this.currentPosts[this.currentEditingPost.index].content = data.refined_post;
                this.renderPosts();
                this.hideModal();
                this.showToast('Post refined successfully!');
            } else {
                throw new Error(data.detail || 'Failed to refine post');
            }

        } catch (error) {
            console.error('Refine error:', error);
            this.showToast(error.message, 'error');
        } finally {
            btn.classList.remove('loading');
            btn.disabled = false;
        }
    }

    // ─── UI Helpers ────────────────────────────────────────────

    setChatLoading(loading) {
        this.isLoading = loading;
        this.chatSendBtn.disabled = loading;
        this.chatInput.disabled = loading;
    }

    autoResizeInput() {
        this.chatInput.style.height = 'auto';
        this.chatInput.style.height = Math.min(this.chatInput.scrollHeight, 150) + 'px';
    }

    scrollToBottom() {
        requestAnimationFrame(() => {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        });
    }

    addLogEntry(message, type = 'info') {
        const entry = document.createElement('div');
        entry.className = `log-entry ${type}`;
        entry.textContent = message;
        this.logEntries.appendChild(entry);
        this.logEntries.scrollTop = this.logEntries.scrollHeight;
    }

    toggleLog() {
        this.logContent.classList.toggle('collapsed');
        this.logToggle.classList.toggle('expanded');
    }

    toggleResearchPanel() {
        this.researchContent.classList.toggle('hidden');
        this.toggleResearch.classList.toggle('expanded');
    }

    resetProcessingUI() {
        this.logEntries.innerHTML = '';
        const steps = document.querySelectorAll('.pipeline-step');
        steps.forEach(step => {
            step.classList.remove('active', 'completed');
            const output = step.querySelector('.step-output');
            if (output) {
                output.classList.remove('visible');
                output.textContent = '';
            }
        });
        this.logContent.classList.add('collapsed');
        this.logToggle.classList.remove('expanded');
    }

    async startOver() {
        this.currentPosts = [];
        this.researchData = {};
        this.sessionId = null;

        // Reset UI
        this.chatMessages.innerHTML = '';
        this.processingContainer.classList.add('hidden');
        this.resultsSection.classList.add('hidden');
        this.chatSection.classList.remove('hidden');
        this.chatInputBar.classList.remove('hidden');
        this.researchContent.classList.add('hidden');
        this.toggleResearch.classList.remove('expanded');
        this.chatInput.placeholder = 'Describe the LinkedIn post you\'d like to create...';
        this.newChatBtn.classList.add('hidden');

        // Create new session
        await this.initSession();
    }

    showToast(message, type = 'success') {
        const toast = this.toast;
        const icon = toast.querySelector('.toast-icon');
        const msgEl = toast.querySelector('.toast-message');

        msgEl.textContent = message;
        icon.style.background = type === 'error' ? 'var(--error)' : 'var(--success)';

        toast.classList.remove('hidden');
        setTimeout(() => toast.classList.add('hidden'), 3000);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatMarkdown(text) {
        // Simple markdown-like formatting
        let html = this.escapeHtml(text);

        // Bold: **text**
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

        // Italic: *text*
        html = html.replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, '<em>$1</em>');

        // Numbered lists: 1. item
        html = html.replace(/^(\d+)\.\s+(.+)$/gm, '<div class="md-list-item"><span class="md-list-num">$1.</span> $2</div>');

        // Bullet points: - item
        html = html.replace(/^[-•]\s+(.+)$/gm, '<div class="md-list-item"><span class="md-list-bullet">•</span> $1</div>');

        // Line breaks
        html = html.replace(/\n/g, '<br>');

        return html;
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    window.app = new LinkedInPostGenerator();
});
