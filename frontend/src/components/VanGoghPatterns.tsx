import React from 'react';

interface VanGoghPatternsProps {
  className?: string;
  intensity?: 'light' | 'medium' | 'heavy';
}

const VanGoghPatterns: React.FC<VanGoghPatternsProps> = ({
  className = '',
  intensity = 'medium'
}) => {
  const opacityClass = {
    light: 'opacity-20',
    medium: 'opacity-30',
    heavy: 'opacity-50'
  }[intensity];

  return (
    <div className={`absolute inset-0 pointer-events-none ${className}`}>
      {/* Импрессионистические мазки */}
      <div className="absolute top-10 left-10 w-32 h-4 bg-van-gogh-vermilion transform rotate-12 animate-brush-stroke opacity-40"></div>
      <div className="absolute top-20 right-20 w-24 h-3 bg-van-gogh-cadmium-yellow transform -rotate-6 animate-brush-stroke opacity-30" style={{ animationDelay: '1s' }}></div>
      <div className="absolute bottom-32 left-1/4 w-40 h-5 bg-van-gogh-ultramarine transform rotate-45 animate-brush-stroke opacity-25" style={{ animationDelay: '2s' }}></div>
      <div className="absolute top-1/3 right-10 w-28 h-4 bg-van-gogh-chrome-green transform -rotate-12 animate-brush-stroke opacity-35" style={{ animationDelay: '0.5s' }}></div>

      {/* Вихревые паттерны */}
      <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
        <div className="w-64 h-64 border-4 border-van-gogh-ultramarine rounded-full animate-swirl opacity-10"></div>
        <div className="absolute inset-8 border-2 border-van-gogh-vermilion rounded-full animate-swirl opacity-15" style={{ animationDirection: 'reverse', animationDuration: '6s' }}></div>
        <div className="absolute inset-16 border border-van-gogh-cadmium-yellow rounded-full animate-swirl opacity-20" style={{ animationDuration: '8s' }}></div>
      </div>

      {/* Органические формы */}
      <div className="absolute top-16 right-1/4 w-20 h-20 bg-van-gogh-chrome-green organic-shape opacity-20"></div>
      <div className="absolute bottom-20 left-16 w-16 h-16 bg-van-gogh-vermilion organic-shape opacity-25" style={{ animationDelay: '3s' }}></div>
      <div className="absolute top-3/4 right-16 w-24 h-24 bg-van-gogh-ultramarine organic-shape opacity-15" style={{ animationDelay: '1.5s' }}></div>

      {/* Фоновый паттерн */}
      <div className={`absolute inset-0 van-gogh-pattern ${opacityClass}`}></div>
    </div>
  );
};

export default VanGoghPatterns;
