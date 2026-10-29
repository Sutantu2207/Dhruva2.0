'use client';

import React, { useEffect, useState } from 'react';

interface Message {
  text: string;
  emoji: string;
}

const MESSAGES: Message[] = [
  { text: "Studying hard today? You've got this!", emoji: '✨' },
  { text: 'Welcome back to the learning cosmos!', emoji: '🚀' },
  { text: 'Knowledge is your superpower!', emoji: '📚' },
  { text: 'Ready for liftoff to excellence?', emoji: '🌟' },
  { text: 'Curiosity leads to discovery!', emoji: '🛸' },
  { text: 'Great mentors inspire the universe!', emoji: '🎓' },
  { text: 'Take a deep breath and keep exploring!', emoji: '🌌' },
];

type PeekCorner = 'bottom-right' | 'bottom-left' | 'top-right';

export const CosmicCompanion: React.FC = () => {
  const [isPeeking, setIsPeeking] = useState(false);
  const [isInteracting, setIsInteracting] = useState(false);
  const [corner, setCorner] = useState<PeekCorner>('bottom-right');
  const [currentMessage, setCurrentMessage] = useState<Message>(MESSAGES[0]);
  const [sparkles, setSparkles] = useState<Array<{ id: number; x: number; y: number }>>([]);
  const hideTimerRef = React.useRef<NodeJS.Timeout | null>(null);
  const clickTimerRef = React.useRef<NodeJS.Timeout | null>(null);

  const triggerPeek = React.useCallback(() => {
    const corners: PeekCorner[] = ['bottom-right', 'bottom-left', 'top-right'];
    const randomCorner = corners[Math.floor(Math.random() * corners.length)];
    const randomMsg = MESSAGES[Math.floor(Math.random() * MESSAGES.length)];

    setCorner(randomCorner);
    setCurrentMessage(randomMsg);
    setIsPeeking(true);

    if (hideTimerRef.current) clearTimeout(hideTimerRef.current);
    // Auto-hide after 8.5 seconds if not clicked
    hideTimerRef.current = setTimeout(() => {
      setIsPeeking(false);
    }, 8500);
  }, []);

  // Peeking scheduler
  useEffect(() => {
    // Initial peek after 4 seconds
    const initialTimer = setTimeout(() => {
      triggerPeek();
    }, 4000);

    // Recurring peeking intervals
    const interval = setInterval(() => {
      if (!isPeeking) {
        triggerPeek();
      }
    }, 18000);

    return () => {
      clearTimeout(initialTimer);
      clearInterval(interval);
      if (hideTimerRef.current) clearTimeout(hideTimerRef.current);
      if (clickTimerRef.current) clearTimeout(clickTimerRef.current);
    };
  }, [isPeeking, triggerPeek]);

  const handleAstronautClick = (e: React.MouseEvent) => {
    setIsInteracting(true);
    setCurrentMessage({ text: 'High five, explorer!', emoji: '🖐️' });

    // Spawn sparkles
    const rect = e.currentTarget.getBoundingClientRect();
    const newSparkles = Array.from({ length: 6 }).map((_, i) => ({
      id: Date.now() + i,
      x: rect.left + rect.width / 2 + (Math.random() - 0.5) * 60,
      y: rect.top + rect.height / 2 + (Math.random() - 0.5) * 60,
    }));
    setSparkles((prev) => [...prev, ...newSparkles]);

    if (clickTimerRef.current) clearTimeout(clickTimerRef.current);
    clickTimerRef.current = setTimeout(() => {
      setSparkles([]);
      setIsInteracting(false);
    }, 1200);
  };

  const getPositionStyles = (): React.CSSProperties => {
    switch (corner) {
      case 'bottom-right':
        return {
          bottom: isPeeking ? '20px' : '-160px',
          right: '28px',
        };
      case 'bottom-left':
        return {
          bottom: isPeeking ? '20px' : '-160px',
          left: '28px',
        };
      case 'top-right':
        return {
          top: isPeeking ? '24px' : '-160px',
          right: '28px',
        };
    }
  };

  return (
    <>
      {/* Floating Sparkle Particles on Click */}
      {sparkles.map((sp) => (
        <span
          key={sp.id}
          style={{
            position: 'fixed',
            left: sp.x,
            top: sp.y,
            pointerEvents: 'none',
            fontSize: '18px',
            zIndex: 9999,
            animation: 'popAndFade 1s cubic-bezier(0.16, 1, 0.3, 1) forwards',
          }}
        >
          ✨
        </span>
      ))}

      {/* Astronaut Container */}
      <div
        aria-label="Dhruva Cosmic Explorer"
        style={{
          position: 'fixed',
          zIndex: 100,
          display: 'flex',
          flexDirection: corner.startsWith('bottom') ? 'column' : 'column-reverse',
          alignItems: corner.includes('right') ? 'flex-end' : 'flex-start',
          gap: '8px',
          transition: 'all 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)',
          ...getPositionStyles(),
        }}
      >
        {/* Cute Speech Bubble */}
        <div
          style={{
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(16px)',
            WebkitBackdropFilter: 'blur(16px)',
            border: '1.5px solid rgba(192, 132, 252, 0.4)',
            borderRadius: '16px',
            padding: '8px 14px',
            boxShadow: '0 8px 24px rgba(139, 92, 246, 0.15)',
            fontSize: '12px',
            fontWeight: 600,
            color: '#1e1135',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            maxWidth: '220px',
            transform: isPeeking ? 'scale(1)' : 'scale(0.7)',
            opacity: isPeeking ? 1 : 0,
            transition: 'all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)',
            pointerEvents: 'auto',
            cursor: 'pointer',
          }}
          onClick={() => setIsPeeking(false)}
        >
          <span style={{ fontSize: '15px' }}>{currentMessage.emoji}</span>
          <span>{currentMessage.text}</span>
        </div>

        {/* Astronaut Avatar Character */}
        <div
          role="button"
          tabIndex={0}
          title="Click to interact with the cosmic explorer!"
          onClick={handleAstronautClick}
          onKeyDown={(e) => e.key === 'Enter' && handleAstronautClick(e as unknown as React.MouseEvent)}
          style={{
            cursor: 'pointer',
            pointerEvents: 'auto',
            width: '90px',
            height: '100px',
            position: 'relative',
            filter: 'drop-shadow(0 10px 20px rgba(139, 92, 246, 0.25))',
            transform: isInteracting
              ? 'rotate(360deg) scale(1.15)'
              : 'scale(1)',
            transition: isInteracting
              ? 'transform 0.8s cubic-bezier(0.34, 1.56, 0.64, 1)'
              : 'transform 0.25s ease',
            outline: 'none',
          }}
        >
          <svg
            viewBox="0 0 100 110"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            style={{ width: '100%', height: '100%', overflow: 'visible' }}
          >
            {/* Life Support Backpack */}
            <rect
              x="22"
              y="38"
              width="56"
              height="45"
              rx="12"
              fill="#e2d7f4"
              stroke="#c084fc"
              strokeWidth="2"
            />
            {/* Antenna with Blinking Beacon */}
            <line
              x1="50"
              y1="16"
              x2="50"
              y2="4"
              stroke="#a855f7"
              strokeWidth="2.5"
              strokeLinecap="round"
            />
            <circle cx="50" cy="4" r="4" fill="#38bdf8">
              <animate
                attributeName="opacity"
                values="1;0.3;1"
                dur="1.2s"
                repeatCount="indefinite"
              />
            </circle>

            {/* Chubby Suit Body */}
            <ellipse
              cx="50"
              cy="62"
              rx="24"
              ry="26"
              fill="#ffffff"
              stroke="#d8b4fe"
              strokeWidth="2.5"
            />

            {/* Suit Chest Control Patch */}
            <rect
              x="42"
              y="54"
              width="16"
              height="12"
              rx="4"
              fill="#f5f0fd"
              stroke="#c084fc"
              strokeWidth="1.5"
            />
            <circle cx="46" cy="60" r="2" fill="#059669" />
            <circle cx="54" cy="60" r="2" fill="#38bdf8" />

            {/* Big Round Helmet */}
            <circle
              cx="50"
              cy="34"
              r="22"
              fill="#ffffff"
              stroke="#c084fc"
              strokeWidth="3"
            />

            {/* Cute Helmet Visor with Glowing Reflection */}
            <ellipse
              cx="50"
              cy="34"
              rx="16"
              ry="13"
              fill="url(#visorGrad)"
            />
            {/* Visor Glint Reflection */}
            <ellipse
              cx="45"
              cy="30"
              rx="6"
              ry="3"
              transform="rotate(-25 45 30)"
              fill="#ffffff"
              opacity="0.85"
            />
            <circle cx="56" cy="37" r="1.5" fill="#ffffff" opacity="0.7" />

            {/* Waving Right Hand */}
            <g style={{ transformOrigin: '70px 52px', animation: 'wavingHand 1.6s ease-in-out infinite' }}>
              <path
                d="M 68 52 Q 80 44 82 32 Q 86 32 86 38 Q 84 50 72 58 Z"
                fill="#ffffff"
                stroke="#c084fc"
                strokeWidth="2.5"
                strokeLinejoin="round"
              />
              {/* Cute little glove patch */}
              <circle cx="82" cy="34" r="3.5" fill="#a855f7" />
            </g>

            {/* Left Arm Resting */}
            <path
              d="M 30 52 Q 20 58 22 68 Q 26 68 30 62 Z"
              fill="#ffffff"
              stroke="#c084fc"
              strokeWidth="2.5"
              strokeLinejoin="round"
            />

            {/* Little Cute Boots */}
            <rect x="36" y="82" width="11" height="9" rx="4" fill="#a855f7" />
            <rect x="53" y="82" width="11" height="9" rx="4" fill="#a855f7" />

            {/* Definitions */}
            <defs>
              <linearGradient
                id="visorGrad"
                x1="34"
                y1="21"
                x2="66"
                y2="47"
                gradientUnits="userSpaceOnUse"
              >
                <stop offset="0%" stopColor="#38bdf8" />
                <stop offset="50%" stopColor="#818cf8" />
                <stop offset="100%" stopColor="#c084fc" />
              </linearGradient>
            </defs>
          </svg>
        </div>
      </div>

      {/* Global Embedded Styles for Hand Waving and Pop Particle */}
      <style jsx global>{`
        @keyframes wavingHand {
          0%, 100% {
            transform: rotate(0deg);
          }
          50% {
            transform: rotate(-24deg);
          }
        }
        @keyframes popAndFade {
          0% {
            transform: scale(0.4) translateY(0);
            opacity: 1;
          }
          100% {
            transform: scale(1.4) translateY(-40px);
            opacity: 0;
          }
        }
      `}</style>
    </>
  );
};
