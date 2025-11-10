'use client';

import { useState, useEffect, useRef } from 'react';
import { cn } from '@/lib/utils';
import { useNetworkStatus } from '@/hooks/useNetworkStatus';

interface LazyImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
  src: string;
  alt: string;
  lowQualitySrc?: string;
  aspectRatio?: string;
  priority?: boolean;
}

export function LazyImage({
  src,
  alt,
  lowQualitySrc,
  aspectRatio = '16/9',
  priority = false,
  className,
  ...props
}: LazyImageProps) {
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);
  const [currentSrc, setCurrentSrc] = useState(lowQualitySrc || src);
  const imgRef = useRef<HTMLImageElement>(null);
  const { isSlowConnection, saveData } = useNetworkStatus();

  useEffect(() => {
    if (priority || !imgRef.current) {
      setCurrentSrc(src);
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            // Load low quality first if available and on slow connection
            if (lowQualitySrc && (isSlowConnection || saveData)) {
              setCurrentSrc(lowQualitySrc);
              // Then upgrade to full quality after a delay
              setTimeout(() => {
                setCurrentSrc(src);
              }, 1000);
            } else {
              setCurrentSrc(src);
            }
            observer.disconnect();
          }
        });
      },
      {
        rootMargin: '50px',
      }
    );

    observer.observe(imgRef.current);

    return () => {
      observer.disconnect();
    };
  }, [src, lowQualitySrc, priority, isSlowConnection, saveData]);

  return (
    <div
      className={cn('relative overflow-hidden bg-muted', className)}
      style={{ aspectRatio }}
    >
      {!loaded && !error && (
        <div className="absolute inset-0 skeleton" />
      )}
      <img
        ref={imgRef}
        src={currentSrc}
        alt={alt}
        onLoad={() => setLoaded(true)}
        onError={() => setError(true)}
        className={cn(
          'w-full h-full object-cover transition-opacity duration-300',
          loaded ? 'opacity-100' : 'opacity-0',
          error && 'hidden'
        )}
        loading={priority ? 'eager' : 'lazy'}
        decoding="async"
        {...props}
      />
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-muted text-muted-foreground">
          <span className="text-sm">Failed to load image</span>
        </div>
      )}
    </div>
  );
}
