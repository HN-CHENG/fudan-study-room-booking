// 等待文档加载完成
document.addEventListener('DOMContentLoaded', function() {
    // 启用所有工具提示
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // 启用所有弹出框
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // 自动关闭警告消息
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert:not(.alert-warning):not(.alert-danger)');
        alerts.forEach(function(alert) {
            bootstrap.Alert.getInstance(alert)?.close();
        });
    }, 5000);
    
    // 设置当前导航项为活动状态
    setActiveNavItem();
    
    // 初始化日期选择器
    initDatePickers();
});

// 设置当前导航项为活动状态
function setActiveNavItem() {
    var currentPath = window.location.pathname;
    var navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    navLinks.forEach(function(link) {
        var href = link.getAttribute('href');
        if (href && currentPath.startsWith(href) && href !== '/') {
            link.classList.add('active');
        } else if (currentPath === '/' && href === '/') {
            link.classList.add('active');
        }
    });
}

// 初始化日期选择器
function initDatePickers() {
    var datePickers = document.querySelectorAll('input[type="date"]');
    datePickers.forEach(function(picker) {
        // 如果没有设置最小日期，默认为今天
        if (!picker.getAttribute('min')) {
            picker.setAttribute('min', new Date().toISOString().split('T')[0]);
        }
        
        // 如果没有设置值，默认为今天
        if (!picker.value) {
            picker.value = new Date().toISOString().split('T')[0];
        }
    });
}

// 确认对话框
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// 格式化日期时间
function formatDateTime(dateTimeStr) {
    var date = new Date(dateTimeStr);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// 格式化时间
function formatTime(dateTimeStr) {
    var date = new Date(dateTimeStr);
    return date.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

// 计算两个日期时间之间的分钟差
function getMinutesDiff(start, end) {
    var startDate = new Date(start);
    var endDate = new Date(end);
    return Math.floor((endDate - startDate) / (1000 * 60));
} 