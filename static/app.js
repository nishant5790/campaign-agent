/**
 * LinkedIn Post Generator - Frontend Application
 */

class LinkedInPostGenerator {
    constructor() {
        this.currentPosts = [];
        this.researchData = {};
        this.currentEditingPost = null;
        
        this.initializeElements();
        this.attachEventListeners();
    }
    
    initializeElements() {
        // Sections
        this.inputSection = document.getElementById('inputSection');
        this.processingContainer = document.getElementById('processingContainer');
        this.resultsSection = document.getElementById('resultsSection');
        
        // Form elements
        this.generateForm = document.getElementById('generateForm');
        this.fieldInput = document.getElementById('fieldInput');
        this.contextInput = document.getElementById('contextInput');
        this.generateBtn = document.getElementById('generateBtn');
        
        // Processing elements
        this.logEntries = document.getElementById('logEntries');
        this.logContent = document.getElementById('logContent');
        this.logToggle = document.getElementById('logToggle');
        
        // Results elements
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
        
        // Toast
        this.toast = document.getElementById('toast');
    }
    
    attachEventListeners() {
        // Form submission
        this.generateForm.addEventListener('submit', (e) => this.handleGenerate(e));
        
        // Log toggle
        this.logToggle.addEventListener('click', () => this.toggleLog());
        
        // Start over
        this.startOverBtn.addEventListener('click', () => this.startOver());
        
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
    
    async handleGenerate(e) {
        e.preventDefault();
        
        const field = this.fieldInput.value.trim();
        const context = this.contextInput.value.trim();
        
        if (!field) {
            this.showToast('Please enter a professional field', 'error');
            return;
        }
        
        // Show processing container in same page
        this.showProcessing();
        this.resetProcessingUI();
        this.setLoading(true);
        
        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    field: field,
                    additional_context: context
                })
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
            this.setLoading(false);
        }
    }
    
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
                this.setLoading(false);
                break;
        }
    }
    
    handleStageEvent(event) {
        const stage = event.stage;
        this.addLogEntry(event.message, 'info');
        
        // Update pipeline visualization
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
        
        // Mark stage as completed
        const stepEl = document.querySelector(`.pipeline-step[data-stage="${stage}"]`);
        if (stepEl) {
            stepEl.classList.remove('active');
            stepEl.classList.add('completed');
            
            // Show output preview
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
        
        // Store research data
        if (event.data) {
            if (event.data.topics) this.researchData.topics = event.data.topics;
            if (event.data.report) this.researchData.report = event.data.report;
            if (event.data.posts) this.currentPosts = event.data.posts;
        }
    }
    
    handleComplete(event) {
        this.addLogEntry(event.message, 'success');
        this.setLoading(false);
        
        // Store final data
        if (event.data) {
            this.researchData.topics = event.data.trending_topics;
            this.researchData.report = event.data.research_report;
            this.currentPosts = event.data.posts;
        }
        
        // Short delay before showing results
        setTimeout(() => {
            this.showResults();
        }, 600);
    }
    
    showProcessing() {
        this.processingContainer.classList.remove('hidden');
        this.resultsSection.classList.add('hidden');
        
        // Scroll to processing container
        this.processingContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    
    showResults() {
        // Populate research content
        this.trendingTopics.textContent = this.researchData.topics || 'No topics found';
        this.researchReport.textContent = this.researchData.report || 'No report generated';
        
        // Render posts
        this.renderPosts();
        
        // Hide processing completely and clear log entries
        this.processingContainer.classList.add('hidden');
        this.logEntries.innerHTML = '';
        
        // Show results
        this.resultsSection.classList.remove('hidden');
        
        // Scroll to results
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
        
        // Attach event listeners
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
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    post_content: this.currentEditingPost.post.content,
                    feedback: feedback
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update the post
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
    
    addLogEntry(message, type = 'info') {
        const entry = document.createElement('div');
        entry.className = `log-entry ${type}`;
        entry.textContent = message;
        this.logEntries.appendChild(entry);
        
        // Auto-scroll to bottom
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
    
    setLoading(loading) {
        if (loading) {
            this.generateBtn.classList.add('loading');
            this.generateBtn.disabled = true;
            this.fieldInput.disabled = true;
            this.contextInput.disabled = true;
        } else {
            this.generateBtn.classList.remove('loading');
            this.generateBtn.disabled = false;
            this.fieldInput.disabled = false;
            this.contextInput.disabled = false;
        }
    }
    
    resetProcessingUI() {
        // Clear log entries
        this.logEntries.innerHTML = '';
        
        // Reset pipeline steps
        const steps = document.querySelectorAll('.pipeline-step');
        steps.forEach(step => {
            step.classList.remove('active', 'completed');
            const output = step.querySelector('.step-output');
            if (output) {
                output.classList.remove('visible');
                output.textContent = '';
            }
        });
        
        // Collapse log by default
        this.logContent.classList.add('collapsed');
        this.logToggle.classList.remove('expanded');
    }
    
    startOver() {
        this.currentPosts = [];
        this.researchData = {};
        this.fieldInput.value = '';
        this.contextInput.value = '';
        
        // Hide sections
        this.processingContainer.classList.add('hidden');
        this.resultsSection.classList.add('hidden');
        
        // Hide research content
        this.researchContent.classList.add('hidden');
        this.toggleResearch.classList.remove('expanded');
        
        // Scroll to top
        this.inputSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        
        // Focus input
        this.fieldInput.focus();
    }
    
    showToast(message, type = 'success') {
        const toast = this.toast;
        const icon = toast.querySelector('.toast-icon');
        const msgEl = toast.querySelector('.toast-message');
        
        msgEl.textContent = message;
        
        // Update icon color based on type
        if (type === 'error') {
            icon.style.background = 'var(--error)';
        } else {
            icon.style.background = 'var(--success)';
        }
        
        toast.classList.remove('hidden');
        
        // Auto-hide after 3 seconds
        setTimeout(() => {
            toast.classList.add('hidden');
        }, 3000);
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    window.app = new LinkedInPostGenerator();
});
