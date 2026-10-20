(() => {
    const carouselRoots = document.querySelectorAll('[data-carousel]');

    carouselRoots.forEach((root) => {
        const track = root.querySelector('[data-carousel-track]');
        if (!track) return;

        const slides = Array.from(track.children);
        const dots = Array.from(root.querySelectorAll('[data-carousel-dot]'));
        const isHero = root.hasAttribute('data-autoplay');
        let activeIndex = 0;
        let timer;

        const showSlide = (index) => {
            activeIndex = (index + slides.length) % slides.length;
            track.style.transform = `translateX(-${activeIndex * 100}%)`;
            slides.forEach((slide, slideIndex) => {
                const isActive = slideIndex === activeIndex;
                slide.classList.toggle('is-active', isActive);
                slide.setAttribute('aria-hidden', isActive ? 'false' : 'true');
                slide.inert = !isActive;
            });
            dots.forEach((dot, dotIndex) => {
                if (dotIndex === activeIndex) {
                    dot.setAttribute('aria-current', 'true');
                } else {
                    dot.removeAttribute('aria-current');
                }
            });
        };

        const moveTrack = (direction) => {
            if (isHero) {
                showSlide(activeIndex + direction);
                return;
            }
            track.scrollBy({
                left: direction * Math.max(track.clientWidth * 0.8, 240),
                behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth',
            });
        };

        root.querySelectorAll('[data-carousel-prev]').forEach((button) => {
            button.addEventListener('click', () => moveTrack(-1));
        });
        root.querySelectorAll('[data-carousel-next]').forEach((button) => {
            button.addEventListener('click', () => moveTrack(1));
        });
        dots.forEach((dot) => {
            dot.addEventListener('click', () => showSlide(Number(dot.dataset.carouselDot)));
        });

        if (isHero && slides.length > 1) {
            showSlide(0);
            const delay = Number(root.dataset.autoplay) || 6500;
            const start = () => {
                if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
                window.clearInterval(timer);
                timer = window.setInterval(() => showSlide(activeIndex + 1), delay);
            };
            const pause = () => window.clearInterval(timer);
            root.addEventListener('mouseenter', pause);
            root.addEventListener('mouseleave', start);
            root.addEventListener('focusin', pause);
            root.addEventListener('focusout', start);
            document.addEventListener('visibilitychange', () => {
                if (document.hidden) pause();
                else start();
            });
            start();
        }
    });

    document.querySelectorAll('.nav-item').forEach((menu) => {
        const summary = menu.querySelector('summary[data-category-url]');
        summary?.addEventListener('click', (event) => {
            event.preventDefault();
            window.location.assign(summary.dataset.categoryUrl);
        });

        menu.addEventListener('toggle', () => {
            if (!menu.open) return;
            document.querySelectorAll('.nav-item[open]').forEach((otherMenu) => {
                if (otherMenu !== menu) otherMenu.open = false;
            });
        });
    });

    const zoomDialog = document.querySelector('[data-product-zoom-dialog]');
    const zoomImage = zoomDialog?.querySelector('[data-zoom-image]');
    const zoomViewport = zoomDialog?.querySelector('[data-zoom-viewport]');
    const zoomLevel = zoomDialog?.querySelector('[data-zoom-level]');
    const zoomTitle = zoomDialog?.querySelector('[data-zoom-title]');

    if (zoomDialog && zoomImage && zoomViewport && zoomLevel && zoomTitle) {
        let zoom = 1;
        const setZoom = (value) => {
            zoom = Math.min(2.5, Math.max(0.5, value));
            zoomImage.style.width = `${zoom * 100}%`;
            zoomLevel.value = `${Math.round(zoom * 100)}%`;
            zoomLevel.textContent = zoomLevel.value;
        };

        document.querySelectorAll('[data-image-zoom]').forEach((button) => {
            button.addEventListener('click', () => {
                const imageSrc = button.dataset.zoomSrc;
                if (!imageSrc) return;
                zoomImage.src = imageSrc;
                zoomImage.alt = button.dataset.zoomAlt || 'Product image';
                zoomTitle.textContent = zoomImage.alt;
                zoomViewport.scrollTo(0, 0);
                setZoom(1);
                if (!zoomDialog.open) zoomDialog.showModal();
            });
        });

        zoomDialog.querySelector('[data-zoom-in]')?.addEventListener('click', () => {
            setZoom(zoom + 0.25);
        });
        zoomDialog.querySelector('[data-zoom-out]')?.addEventListener('click', () => {
            setZoom(zoom - 0.25);
        });
        zoomDialog.querySelector('[data-zoom-reset]')?.addEventListener('click', () => {
            zoomViewport.scrollTo(0, 0);
            setZoom(1);
        });
        zoomDialog.addEventListener('click', (event) => {
            if (event.target === zoomDialog) zoomDialog.close();
        });
    }
})();
