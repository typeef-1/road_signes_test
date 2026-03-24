// Основной JavaScript файл

document.addEventListener('DOMContentLoaded', function() {

    // Плавная прокрутка для якорей
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Анимация появления элементов при скролле
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fadeInUp');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Наблюдаем за карточками знаков
    document.querySelectorAll('.sign-card, .feature-card').forEach(el => {
        observer.observe(el);
    });

    // Фильтрация знаков по категориям
    const filterButtons = document.querySelectorAll('[data-filter]');
    const signCards = document.querySelectorAll('.sign-card');

    filterButtons.forEach(button => {
        button.addEventListener('click', () => {
            const filter = button.dataset.filter;

            // Обновляем активное состояние кнопок
            filterButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');

            // Фильтруем карточки
            signCards.forEach(card => {
                if (filter === 'all' || card.dataset.category === filter) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    });

    // Счетчик статистики (анимация чисел)
    function animateValue(element, start, end, duration) {
        const range = end - start;
        const increment = range / (duration / 16);
        let current = start;

        const timer = setInterval(() => {
            current += increment;
            if (current >= end) {
                element.textContent = end + '+';
                clearInterval(timer);
            } else {
                element.textContent = Math.floor(current) + '+';
            }
        }, 16);
    }

    // Запускаем анимацию статистики при появлении секции
    const statsSection = document.getElementById('stats');
    if (statsSection) {
        const statsObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const statValues = document.querySelectorAll('.stat-value');
                    statValues.forEach(stat => {
                        const value = parseInt(stat.textContent);
                        animateValue(stat, 0, value, 2000);
                    });
                    statsObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });

        statsObserver.observe(statsSection);
    }

    // Валидация формы
    const testForm = document.querySelector('form[action*="start_test"]');
    if (testForm) {
        testForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const nameInput = this.querySelector('input[type="text"]');
            const emailInput = this.querySelector('input[type="email"]');

            if (!nameInput.value.trim()) {
                showNotification('Пожалуйста, введите ваше имя', 'error');
                return;
            }

            if (!isValidEmail(emailInput.value)) {
                showNotification('Пожалуйста, введите корректный email', 'error');
                return;
            }

            // Если все ок, отправляем форму
            showNotification('Тест начинается! Проверьте email', 'success');
            setTimeout(() => {
                this.submit();
            }, 2000);
        });
    }

    // Вспомогательные функции
    function isValidEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    function showNotification(message, type) {
        // Создаем уведомление
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg text-white ${
            type === 'error' ? 'bg-red-500' : 'bg-green-500'
        } z-50 animate-fadeInUp`;
        notification.textContent = message;

        document.body.appendChild(notification);

        // Удаляем через 3 секунды
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
});