gsap.registerPlugin(ScrollTrigger);

        // Animations init
        document.querySelectorAll('.reveal-up, .reveal-zoom').forEach((el) => {
            ScrollTrigger.create({
                trigger: el,
                start: "top 85%",
                onEnter: () => el.classList.add('active'),
                once: true
            });
        });

        // Flashlight Logic
        window.updateFlashlight = function (e, card) {
            const rect = card.getBoundingClientRect();
            card.style.setProperty('--mouse-x', (e.clientX - rect.left) + 'px');
            card.style.setProperty('--mouse-y', (e.clientY - rect.top) + 'px');
        };

        // Accordion Logic
        function toggleFaq(button) {
            const content = button.nextElementSibling;
            const icon = button.querySelector('.iconify-icon-arrow');
            
            if (content.style.maxHeight && content.style.maxHeight !== '0px') {
                content.style.maxHeight = '0px';
                icon.style.transform = 'rotate(0deg)';
                button.classList.remove('text-esther-olive');
            } else {
                content.style.maxHeight = content.scrollHeight + 'px';
                icon.style.transform = 'rotate(180deg)';
                button.classList.add('text-esther-olive');
            }
        }