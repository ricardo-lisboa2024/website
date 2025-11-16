// ===== VARIÁVEIS GLOBAIS =====
let activities = [];
let currentFilter = 'all';

// ===== INICIALIZAÇÃO =====
document.addEventListener('DOMContentLoaded', function() {
    loadActivities();
    setupEventListeners();
    updateStats();
});

// ===== CONFIGURAÇÃO DE EVENTOS =====
function setupEventListeners() {
    // Slider de percentual
    const percentageSlider = document.getElementById('percentage');
    const percentageValue = document.getElementById('percentageValue');
    
    if (percentageSlider) {
        percentageSlider.addEventListener('input', function() {
            percentageValue.textContent = this.value + '%';
        });
    }
}

// ===== MENU E FORMULÁRIO =====
function toggleSubmenu() {
    const submenu = document.getElementById('submenu');
    submenu.classList.toggle('show');
}

function showActivityForm(type) {
    const form = document.getElementById('activityForm');
    const formTitle = document.getElementById('formTitle');
    const activityType = document.getElementById('activityType');
    const submenu = document.getElementById('submenu');
    
    // Configurar título baseado no tipo
    const typeNames = {
        'projeto': 'Projeto',
        'livro': 'Livro', 
        'curso': 'Curso'
    };
    
    formTitle.textContent = `Adicionar ${typeNames[type]}`;
    activityType.value = type;
    
    // Mostrar formulário e esconder submenu
    form.classList.add('show');
    submenu.classList.remove('show');
    
    // Focar no primeiro campo
    document.getElementById('title').focus();
}

function hideActivityForm() {
    const form = document.getElementById('activityForm');
    form.classList.remove('show');
    document.getElementById('addActivityForm').reset();
    document.getElementById('percentageValue').textContent = '0%';
}

// ===== GERENCIAMENTO DE ATIVIDADES =====
function addActivity(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const activity = {
        id: Date.now(), // ID temporário
        type: formData.get('type'),
        title: formData.get('title'),
        description: formData.get('description'),
        completion_date: formData.get('completion_date'),
        priority: formData.get('priority'),
        percentage: parseInt(formData.get('percentage')),
        completed: false,
        created_at: new Date().toISOString()
    };
    
    // Validar data de conclusão
    if (new Date(activity.completion_date) < new Date()) {
        alert('A data de conclusão não pode ser no passado!');
        return;
    }
    
    activities.push(activity);
    saveActivities();
    renderActivities();
    hideActivityForm();
    
    // Mostrar feedback
    showNotification('Atividade adicionada com sucesso!', 'success');
}

function completeActivity(activityId) {
    const activity = activities.find(a => a.id === activityId);
    if (activity) {
        activity.completed = true;
        activity.percentage = 100;
        saveActivities();
        renderActivities();
        showNotification('Atividade marcada como concluída!', 'success');
    }
}

function deleteActivity(activityId) {
    showConfirmModal(
        'Excluir Atividade',
        'Tem certeza que deseja excluir esta atividade? Esta ação não pode ser desfeita.',
        () => {
            activities = activities.filter(a => a.id !== activityId);
            saveActivities();
            renderActivities();
            showNotification('Atividade excluída com sucesso!', 'success');
        }
    );
}

function updateActivityPercentage(activityId, newPercentage) {
    const activity = activities.find(a => a.id === activityId);
    if (activity) {
        activity.percentage = newPercentage;
        if (newPercentage === 100) {
            activity.completed = true;
        }
        saveActivities();
        renderActivities();
    }
}

// ===== RENDERIZAÇÃO =====
function renderActivities() {
    const pendingContainer = document.getElementById('pendingActivities');
    const completedContainer = document.getElementById('completedActivities');
    
    // Limpar containers
    pendingContainer.innerHTML = '';
    completedContainer.innerHTML = '';
    
    // Filtrar e ordenar atividades
    const filteredActivities = filterActivitiesByType(activities);
    const pendingActivities = filteredActivities.filter(a => !a.completed);
    const completedActivities = filteredActivities.filter(a => a.completed);
    
    // Ordenar pendentes por prioridade
    const priorityOrder = {
        'urgente': 5,
        'alta': 4, 
        'media': 3,
        'baixa': 2,
        'nao-prioritario': 1
    };
    
    pendingActivities.sort((a, b) => {
        return priorityOrder[b.priority] - priorityOrder[a.priority] ||
               new Date(a.completion_date) - new Date(b.completion_date);
    });
    
    // Ordenar concluídas por data de conclusão (mais recente primeiro)
    completedActivities.sort((a, b) => new Date(b.completion_date) - new Date(a.completion_date));
    
    // Renderizar atividades pendentes
    if (pendingActivities.length === 0) {
        pendingContainer.innerHTML = '<p class="no-activities">Nenhuma atividade pendente</p>';
    } else {
        pendingActivities.forEach(activity => {
            pendingContainer.appendChild(createActivityCard(activity));
        });
    }
    
    // Renderizar atividades concluídas
    if (completedActivities.length === 0) {
        completedContainer.innerHTML = '<p class="no-activities">Nenhuma atividade concluída</p>';
    } else {
        completedActivities.forEach(activity => {
            completedContainer.appendChild(createActivityCard(activity));
        });
    }
    
    updateStats();
}

function createActivityCard(activity) {
    const card = document.createElement('div');
    card.className = `activity-card prioridade-${activity.priority} ${activity.completed ? 'completed' : ''}`;
    
    const priorityIcons = {
        'urgente': '🔴',
        'alta': '🟠',
        'media': '🟡',
        'baixa': '🟢',
        'nao-prioritario': '⚫'
    };
    
    const typeIcons = {
        'projeto': 'fas fa-project-diagram',
        'livro': 'fas fa-book',
        'curso': 'fas fa-graduation-cap'
    };
    
    card.innerHTML = `
        <div class="activity-header">
            <div class="activity-info">
                <div class="activity-title">
                    ${priorityIcons[activity.priority]} ${activity.title}
                </div>
                <span class="activity-type ${activity.type}">
                    <i class="${typeIcons[activity.type]}"></i>
                    ${activity.type.charAt(0).toUpperCase() + activity.type.slice(1)}
                </span>
                ${activity.description ? `
                    <div class="activity-description">${activity.description}</div>
                ` : ''}
            </div>
        </div>
        
        <div class="activity-meta">
            <span><i class="fas fa-calendar-alt"></i> Concluir até: ${formatDate(activity.completion_date)}</span>
            <span class="priority-badge">${getPriorityText(activity.priority)}</span>
        </div>
        
        <div class="progress-container">
            <div class="progress-label">
                <span>Progresso</span>
                <span>${activity.percentage}%</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${activity.percentage}%"></div>
            </div>
        </div>
        
        <div class="activity-actions">
            ${!activity.completed ? `
                <button class="btn-complete" onclick="completeActivity(${activity.id})">
                    <i class="fas fa-check"></i> Concluir
                </button>
            ` : ''}
            <button class="btn-delete" onclick="deleteActivity(${activity.id})">
                <i class="fas fa-trash"></i> Deletar
            </button>
        </div>
    `;
    
    return card;
}

// ===== FILTROS =====
function filterActivities(filter) {
    currentFilter = filter;
    
    // Atualizar botões ativos
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    renderActivities();
}

function filterActivitiesByType(activitiesList) {
    if (currentFilter === 'all') {
        return activitiesList;
    }
    return activitiesList.filter(activity => activity.type === currentFilter);
}

// ===== ESTATÍSTICAS =====
function updateStats() {
    const activeCount = activities.filter(a => !a.completed).length;
    const completedCount = activities.filter(a => a.completed).length;
    const urgentCount = activities.filter(a => !a.completed && a.priority === 'urgente').length;
    
    document.getElementById('activeCount').textContent = activeCount;
    document.getElementById('completedCount').textContent = completedCount;
    document.getElementById('urgentCount').textContent = urgentCount;
}

// ===== PERSISTÊNCIA (LocalStorage) =====
function saveActivities() {
    localStorage.setItem('personalSchedulerActivities', JSON.stringify(activities));
}

function loadActivities() {
    const saved = localStorage.getItem('personalSchedulerActivities');
    if (saved) {
        activities = JSON.parse(saved);
    }
    renderActivities();
}

// ===== MODAL =====
function showConfirmModal(title, message, confirmCallback) {
    const modal = document.getElementById('confirmModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalMessage = document.getElementById('modalMessage');
    const confirmBtn = document.getElementById('confirmBtn');
    
    modalTitle.textContent = title;
    modalMessage.textContent = message;
    
    confirmBtn.onclick = function() {
        confirmCallback();
        closeModal();
    };
    
    modal.classList.add('show');
}

function closeModal() {
    const modal = document.getElementById('confirmModal');
    modal.classList.remove('show');
}

// ===== UTILITÁRIOS =====
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR');
}

function getPriorityText(priority) {
    const priorityTexts = {
        'urgente': 'Urgente',
        'alta': 'Alta',
        'media': 'Média',
        'baixa': 'Baixa',
        'nao-prioritario': 'Não Prioritário'
    };
    return priorityTexts[priority];
}

function showNotification(message, type) {
    // Criar notificação simples
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#28a745' : '#dc3545'};
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        z-index: 3000;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// ===== FECHAR MENU AO CLICAR FORA =====
document.addEventListener('click', function(event) {
    const submenu = document.getElementById('submenu');
    const menuBtn = document.querySelector('.menu-btn');
    
    if (!menuBtn.contains(event.target) && !submenu.contains(event.target)) {
        submenu.classList.remove('show');
    }
});

// Fechar modal ao clicar fora
document.getElementById('confirmModal').addEventListener('click', function(event) {
    if (event.target === this) {
        closeModal();
    }
});