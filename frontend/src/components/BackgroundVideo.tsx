import React, { useEffect } from 'react';

interface BackgroundStarsProps {
  paused?: boolean;
}

const BackgroundStars: React.FC<BackgroundStarsProps> = ({ paused = false }) => {
  useEffect(() => {
    let animationFrame: number;
    let lastScale = window.devicePixelRatio;

    const createStars = () => {
      const container = document.getElementById('stars-container');
      if (!container) return;

      // Clear existing stars
      container.innerHTML = '';

      const width = window.innerWidth;
      const height = window.innerHeight;
      const starsCount = Math.floor(width * height / 800); // Optimized count

      // Use DocumentFragment for better performance
      const fragment = document.createDocumentFragment();

      for (let i = 0; i < starsCount; i++) {
        const star = document.createElement('div');

        // Optimized random generation
        const rand = Math.random();
        star.className = rand > 0.85 ? 'star large' : rand > 0.6 ? 'star medium' : 'star small';

        // Position with better distribution
        star.style.left = `${Math.random() * width}px`;
        star.style.top = `${Math.random() * height * 0.8}px`;

        // Optimized animation delays
        const twinkleDelay = (Math.random() * 3) | 0; // Integer for better perf
        const driftDelay = (Math.random() * 20) | 0;
        star.style.animationDelay = `${twinkleDelay}s, ${driftDelay}s`;

        fragment.appendChild(star);
      }

      container.appendChild(fragment);
    };

    // Throttled resize handler
    let resizeTimeout: NodeJS.Timeout;
    const handleResize = () => {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(createStars, 100);
    };

    const handleZoom = () => createStars();

    // Optimized zoom detection
    const checkZoom = () => {
      if (window.devicePixelRatio !== lastScale) {
        lastScale = window.devicePixelRatio;
        createStars();
      }
      animationFrame = requestAnimationFrame(checkZoom);
    };

    createStars();
    window.addEventListener('resize', handleResize, { passive: true });

    if (window.visualViewport) {
      window.visualViewport.addEventListener('resize', handleZoom, { passive: true });
    }

    checkZoom();

    return () => {
      window.removeEventListener('resize', handleResize);
      if (window.visualViewport) {
        window.visualViewport.removeEventListener('resize', handleZoom);
      }
      cancelAnimationFrame(animationFrame);
      clearTimeout(resizeTimeout);
    };
  }, []);

  return (
    <div className="fixed inset-0 z-0 overflow-hidden">
      {/* Image background with overlay */}
      <div
        className="absolute inset-0 z-0"
        style={{
          background: "url('/fon.jpg') center no-repeat",
          backgroundSize: "cover",
          filter: "brightness(0.4) contrast(1.2) saturate(1.3)"
        }}
      >
        <div className="swirl-effect"></div>
      </div>

      {/* Star background effect - positioned above the image */}
      <div id="stars-container" className="absolute inset-0 z-10"></div>
    </div>
  );
};

export default BackgroundStars;
