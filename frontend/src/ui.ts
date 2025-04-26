import { marked } from 'marked';
import { stateManager } from './state';
import { api } from './api';

// DOM Elements
const elements = {
    landingSection: document.getElementById('landing-section') as HTMLElement,
    dashboardSection: document.getElementById('dashboard-section') as HTMLElement,
    companyHeaderContainer: document.getElementById('company-header-container') as HTMLElement,
    competitorsContainer: document.getElementById('competitors-container') as HTMLElement,
    newsContainer: document.getElementById('news-container') as HTMLElement,
    insightsContainer: document.getElementById('insights-container') as HTMLElement,
    chatContainer: document.getElementById('chat-container') as HTMLElement,
    modalContainer: document.getElementById('modal-container') as HTMLElement,
    modalTitle: document.getElementById('modal-title') as HTMLElement,
    modalBody: document.getElementById('modal-body') as HTMLElement,
    modalCloseButton: document.querySelector('.modal-close-button') as HTMLElement,
};

// View Management
export function showView(viewId: string) {
    const sections = document.querySelectorAll('.view-section');
    sections.forEach(section => {
        (section as HTMLElement).style.display = 'none';
    });
    const targetSection = document.getElementById(viewId);
    if (targetSection) {
        targetSection.style.display = 'block';
    }
}

// Loading States
export function setLoading(elementId: string, isLoading: boolean, message = 'Loading...') {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = isLoading ? 'block' : 'none';
        element.textContent = message;
    }
}

// Error States
export function setError(elementId: string, message: string | null) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = message ? 'block' : 'none';
        if (message) {
            element.textContent = message;
        }
    }
}

// Company Header
export function renderCompanyHeader(companyData: any) {
    elements.companyHeaderContainer.innerHTML = `
        <div class="card">
            <h2>${companyData.name}</h2>
            <p>${companyData.description || 'No description available'}</p>
            <p>Industry: ${companyData.industry || 'N/A'}</p>
            <p>Founded: ${companyData.founded || 'N/A'}</p>
        </div>
    `;
}

// Competitors Section
export function renderCompetitorSection(competitors: any[], companyId: string) {
    elements.competitorsContainer.innerHTML = `
        <h3>Competitors</h3>
        <div class="competitors-grid">
            ${competitors.map(competitor => createCompetitorCardHTML(competitor, companyId)).join('')}
        </div>
    `;
}

function createCompetitorCardHTML(competitor: any, companyId: string): string {
    return `
        <div class="card competitor-card">
            <h4>${competitor.name}</h4>
            <p>${competitor.description || 'No description available'}</p>
            <div class="competitor-actions">
                ${competitor.deep_research_status === 'completed' ? 
                    `<button onclick="window.open('${api.getDeepResearchDownloadUrl(competitor.id)}', '_blank')">Download Report</button>
                     <button onclick="viewReport('${competitor.id}')">View Report</button>` :
                    `<button onclick="triggerResearch('${competitor.id}')" ${competitor.deep_research_status === 'pending' ? 'disabled' : ''}>
                        ${competitor.deep_research_status === 'pending' ? 'Research in Progress...' : 'Trigger Research'}
                    </button>`
                }
            </div>
        </div>
    `;
}

// News Section
export function renderNewsSection(news: any[]) {
    elements.newsContainer.innerHTML = `
        <h3>Latest News</h3>
        <div class="news-grid">
            ${news.map(article => createNewsArticleCardHTML(article)).join('')}
        </div>
    `;
}

function createNewsArticleCardHTML(article: any): string {
    return `
        <div class="card news-card">
            <h4>${article.title}</h4>
            <p>${article.summary}</p>
            <a href="${article.url}" target="_blank">Read More</a>
            <p class="news-meta">Source: ${article.source} | Date: ${new Date(article.date).toLocaleDateString()}</p>
        </div>
    `;
}

// Insights Section
export function renderInsightsSection(insights: any[], companyId: string) {
    elements.insightsContainer.innerHTML = `
        <div class="insights-header">
            <h3>Insights</h3>
            <button onclick="refreshInsights('${companyId}')">Refresh Insights</button>
        </div>
        <div class="insights-grid">
            ${insights.map(insight => createInsightCardHTML(insight)).join('')}
        </div>
    `;
}

function createInsightCardHTML(insight: any): string {
    return `
        <div class="card insight-card">
            <h4>${insight.title}</h4>
            <p>${insight.content}</p>
            <p class="insight-meta">Generated: ${new Date(insight.generated_at).toLocaleString()}</p>
        </div>
    `;
}

// Chat Section
export function renderChatSection(companyId: string) {
    elements.chatContainer.innerHTML = `
        <h3>Chat</h3>
        <div class="chat-messages" id="chat-messages"></div>
        <div class="chat-input">
            <input type="text" id="chat-input" placeholder="Ask a question...">
            <button onclick="sendChatMessage('${companyId}')">Send</button>
        </div>
    `;
}

export function addChatMessage(message: string, isUser: boolean) {
    const messagesContainer = document.getElementById('chat-messages');
    if (messagesContainer) {
        const messageElement = document.createElement('div');
        messageElement.className = `chat-message ${isUser ? 'user-message' : 'ai-message'}`;
        messageElement.textContent = message;
        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

// Modal Management
export async function showModal(title: string, content: string) {
    elements.modalTitle.textContent = title;
    elements.modalBody.innerHTML = await marked.parse(content);
    elements.modalContainer.style.display = 'flex';
}

export function hideModal() {
    elements.modalContainer.style.display = 'none';
}

// Event Listeners
elements.modalCloseButton.addEventListener('click', hideModal);
elements.modalContainer.addEventListener('click', (e) => {
    if (e.target === elements.modalContainer) {
        hideModal();
    }
});

// Expose functions to window for HTML onclick handlers
(window as any).viewReport = async (competitorId: string) => {
    const competitor = stateManager.getState().competitors.find((c: { id: string }) => c.id === competitorId);
    if (competitor?.deep_research_markdown) {
        await showModal(`${competitor.name} Research Report`, competitor.deep_research_markdown);
    }
};

(window as any).triggerResearch = async (competitorId: string) => {
    try {
        stateManager.setLoading('research', true);
        await api.triggerDeepResearch(competitorId);
        // Start polling for status updates
        pollCompetitorStatus(competitorId);
    } catch (error) {
        stateManager.setError('research', error instanceof Error ? error.message : 'Failed to trigger research');
    } finally {
        stateManager.setLoading('research', false);
    }
};

(window as any).refreshInsights = async (companyId: string) => {
    try {
        stateManager.setLoading('insights', true);
        const insights = await api.refreshInsights(companyId);
        stateManager.setInsights(insights);
    } catch (error) {
        stateManager.setError('insights', error instanceof Error ? error.message : 'Failed to refresh insights');
    } finally {
        stateManager.setLoading('insights', false);
    }
};

(window as any).sendChatMessage = async (companyId: string) => {
    const input = document.getElementById('chat-input') as HTMLInputElement;
    const message = input.value.trim();
    if (!message) return;

    addChatMessage(message, true);
    input.value = '';

    try {
        stateManager.setLoading('chat', true);
        const response = await api.askChat(companyId, message);
        addChatMessage(response.answer, false);
    } catch (error) {
        addChatMessage('Sorry, I encountered an error while processing your message.', false);
    } finally {
        stateManager.setLoading('chat', false);
    }
};

// Helper function to poll competitor status
async function pollCompetitorStatus(competitorId: string) {
    const pollInterval = setInterval(async () => {
        try {
            const competitors = await api.getCompetitors(stateManager.getState().companyId!);
            const competitor = competitors.find((c: { id: string }) => c.id === competitorId);
            
            if (competitor?.deep_research_status === 'completed') {
                clearInterval(pollInterval);
                stateManager.setCompetitors(competitors);
            } else if (competitor?.deep_research_status === 'error') {
                clearInterval(pollInterval);
                stateManager.setError('research', 'Research failed');
            }
        } catch (error) {
            clearInterval(pollInterval);
            stateManager.setError('research', 'Failed to check research status');
        }
    }, 5000); // Poll every 5 seconds
} 