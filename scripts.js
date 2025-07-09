document.addEventListener('DOMContentLoaded', () => {
    // Slide-in animations
    const elements = document.querySelectorAll('.animate-slide-in');
    elements.forEach((el, index) => {
        setTimeout(() => {
            el.style.opacity = '1';
            el.style.transform = 'translateX(0)';
        }, index * 100);
    });

    // Typewriter effect for summaries
    const summaries = document.querySelectorAll('.typewriter');
    summaries.forEach(summary => {
        const text = summary.textContent;
        summary.textContent = '';
        let i = 0;
        function type() {
            if (i < text.length) {
                summary.textContent += text.charAt(i);
                i++;
                setTimeout(type, 20);
            }
        }
        type();
    });

    // Dynamic ticker update
    const tickerWrapper = document.getElementById('ticker-wrapper');
    const allTickerItems = Array.from(document.querySelectorAll('.ticker-item'));
    const updateTicker = () => {
        const shuffled = allTickerItems.sort(() => 0.5 - Math.random());
        const selected = shuffled.slice(0, 5);
        tickerWrapper.innerHTML = '<span class="ticker-text">BREAKING NEWS: </span>' + 
            selected.map(item => `<span class="ticker-item" data-topic="${item.dataset.topic}">${item.textContent}</span>`).join('');
    };
    updateTicker();
    setInterval(updateTicker, 10000);

    // Pause ticker on hover
    tickerWrapper.addEventListener('mouseenter', () => {
        tickerWrapper.style.animationPlayState = 'paused';
    });
    tickerWrapper.addEventListener('mouseleave', () => {
        tickerWrapper.style.animationPlayState = 'running';
    });

    // Theme toggle
    const themeToggle = document.getElementById('theme-toggle');
    const body = document.body;
    const themeIcon = themeToggle.querySelector('i');
    const currentTheme = localStorage.getItem('theme') || 'dark';
    body.setAttribute('data-theme', currentTheme);
    themeIcon.className = currentTheme === 'dark' ? 'fas fa-moon' : 'fas fa-sun';

    themeToggle.addEventListener('click', () => {
        const newTheme = body.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        body.setAttribute('data-theme', newTheme);
        themeIcon.className = newTheme === 'dark' ? 'fas fa-moon' : 'fas fa-sun';
        localStorage.setItem('theme', newTheme);
    });

    // Nav bar scroll effect
    const navbar = document.getElementById('navbar');
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });
});