'use client';

import React, { useEffect, useRef } from 'react';

interface Shape {
  type: 'orb' | 'ring' | 'diamond' | 'pill' | 'star';
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  angle: number;
  rotationSpeed: number;
  colorStart: string;
  colorEnd: string;
  pulsePhase: number;
  pulseSpeed: number;
}

interface SparkleParticle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  alpha: number;
  color: string;
  rotation: number;
  vRot: number;
}

export const InteractiveAmbientBackground: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    // Mouse coordinates with smooth easing
    const mouse = {
      x: width / 2,
      y: height / 2,
      targetX: width / 2,
      targetY: height / 2,
      active: false,
    };

    let sparkles: SparkleParticle[] = [];
    const sparkleColors = [
      '#c084fc',
      '#818cf8',
      '#38bdf8',
      '#f472b6',
      '#34d399',
      '#fbbf24',
    ];

    const prefersReducedMotion =
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
      if (prefersReducedMotion) {
        drawStaticBackground();
      }
    };

    const drawStaticBackground = () => {
      ctx.clearRect(0, 0, width, height);
      const baseGrad = ctx.createLinearGradient(0, 0, width, height);
      baseGrad.addColorStop(0, '#f9f6ff');
      baseGrad.addColorStop(0.5, '#f4effe');
      baseGrad.addColorStop(1, '#f8f4ff');
      ctx.fillStyle = baseGrad;
      ctx.fillRect(0, 0, width, height);
    };

    if (prefersReducedMotion) {
      drawStaticBackground();
      window.addEventListener('resize', handleResize, { passive: true });
      return () => {
        window.removeEventListener('resize', handleResize);
      };
    }

    const handlePointerMove = (e: MouseEvent | TouchEvent) => {
      mouse.active = true;
      if ('touches' in e && e.touches.length > 0) {
        mouse.targetX = e.touches[0].clientX;
        mouse.targetY = e.touches[0].clientY;
      } else if ('clientX' in e) {
        mouse.targetX = (e as MouseEvent).clientX;
        mouse.targetY = (e as MouseEvent).clientY;
      }
    };

    const handlePointerDown = (e: MouseEvent | TouchEvent) => {
      const clientX = 'touches' in e && e.touches.length > 0 ? e.touches[0].clientX : (e as MouseEvent).clientX;
      const clientY = 'touches' in e && e.touches.length > 0 ? e.touches[0].clientY : (e as MouseEvent).clientY;

      // Spawn burst of 10-14 cute star sparkles
      const count = 12;
      for (let i = 0; i < count; i++) {
        const speed = 2 + Math.random() * 4;
        const angle = (Math.PI * 2 * i) / count + (Math.random() - 0.5) * 0.4;
        sparkles.push({
          x: clientX,
          y: clientY,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed,
          size: 6 + Math.random() * 8,
          alpha: 1,
          color: sparkleColors[Math.floor(Math.random() * sparkleColors.length)],
          rotation: Math.random() * Math.PI,
          vRot: (Math.random() - 0.5) * 0.1,
        });
      }
    };

    const handlePointerLeave = () => {
      mouse.active = false;
    };

    window.addEventListener('resize', handleResize, { passive: true });
    window.addEventListener('mousemove', handlePointerMove, { passive: true });
    window.addEventListener('touchmove', handlePointerMove, { passive: true });
    window.addEventListener('pointerdown', handlePointerDown, { passive: true });
    window.addEventListener('mouseleave', handlePointerLeave, { passive: true });

    // Generate luminescent interactive shapes
    const shapes: Shape[] = [
      {
        type: 'orb',
        x: width * 0.2,
        y: height * 0.25,
        vx: 0.3,
        vy: 0.2,
        radius: 190,
        angle: 0,
        rotationSpeed: 0.002,
        colorStart: 'rgba(192, 132, 252, 0.45)', // Luminous lilac
        colorEnd: 'rgba(129, 140, 248, 0.15)', // Luminous indigo
        pulsePhase: 0,
        pulseSpeed: 0.015,
      },
      {
        type: 'orb',
        x: width * 0.8,
        y: height * 0.3,
        vx: -0.25,
        vy: 0.35,
        radius: 220,
        angle: 0,
        rotationSpeed: -0.0015,
        colorStart: 'rgba(167, 139, 250, 0.40)', // Violet
        colorEnd: 'rgba(56, 189, 248, 0.20)', // Cyan
        pulsePhase: 2,
        pulseSpeed: 0.02,
      },
      {
        type: 'orb',
        x: width * 0.5,
        y: height * 0.8,
        vx: 0.2,
        vy: -0.25,
        radius: 200,
        angle: 0,
        rotationSpeed: 0.001,
        colorStart: 'rgba(236, 72, 153, 0.30)', // Rose violet
        colorEnd: 'rgba(192, 132, 252, 0.15)', // Light purple
        pulsePhase: 4,
        pulseSpeed: 0.018,
      },
      {
        type: 'ring',
        x: width * 0.15,
        y: height * 0.7,
        vx: 0.2,
        vy: 0.15,
        radius: 80,
        angle: 0,
        rotationSpeed: 0.008,
        colorStart: 'rgba(168, 85, 247, 0.5)',
        colorEnd: 'rgba(99, 102, 241, 0.3)',
        pulsePhase: 1,
        pulseSpeed: 0.025,
      },
      {
        type: 'diamond',
        x: width * 0.85,
        y: height * 0.75,
        vx: -0.15,
        vy: -0.2,
        radius: 65,
        angle: 0.5,
        rotationSpeed: 0.006,
        colorStart: 'rgba(192, 132, 252, 0.55)',
        colorEnd: 'rgba(56, 189, 248, 0.35)',
        pulsePhase: 3,
        pulseSpeed: 0.02,
      },
      {
        type: 'star',
        x: width * 0.35,
        y: height * 0.15,
        vx: 0.1,
        vy: 0.1,
        radius: 35,
        angle: 0,
        rotationSpeed: 0.01,
        colorStart: 'rgba(167, 139, 250, 0.6)',
        colorEnd: 'rgba(244, 114, 182, 0.4)',
        pulsePhase: 5,
        pulseSpeed: 0.03,
      },
      {
        type: 'pill',
        x: width * 0.7,
        y: height * 0.15,
        vx: -0.2,
        vy: 0.15,
        radius: 70,
        angle: 0.8,
        rotationSpeed: -0.005,
        colorStart: 'rgba(129, 140, 248, 0.45)',
        colorEnd: 'rgba(192, 132, 252, 0.25)',
        pulsePhase: 2.5,
        pulseSpeed: 0.02,
      },
    ];

    const render = () => {
      // Smooth mouse interpolation (lerp)
      mouse.x += (mouse.targetX - mouse.x) * 0.06;
      mouse.y += (mouse.targetY - mouse.y) * 0.06;

      ctx.clearRect(0, 0, width, height);

      // Base luminescent gradient
      const baseGrad = ctx.createLinearGradient(0, 0, width, height);
      baseGrad.addColorStop(0, '#f9f6ff');
      baseGrad.addColorStop(0.5, '#f4effe');
      baseGrad.addColorStop(1, '#f8f4ff');
      ctx.fillStyle = baseGrad;
      ctx.fillRect(0, 0, width, height);

      // Interactive cursor spotlight luminescence
      if (mouse.active) {
        const cursorGlow = ctx.createRadialGradient(
          mouse.x,
          mouse.y,
          0,
          mouse.x,
          mouse.y,
          360
        );
        cursorGlow.addColorStop(0, 'rgba(192, 132, 252, 0.32)');
        cursorGlow.addColorStop(0.5, 'rgba(147, 51, 234, 0.12)');
        cursorGlow.addColorStop(1, 'rgba(255, 255, 255, 0)');
        ctx.fillStyle = cursorGlow;
        ctx.beginPath();
        ctx.arc(mouse.x, mouse.y, 360, 0, Math.PI * 2);
        ctx.fill();
      }

      // Render each luminescent shape
      shapes.forEach((s) => {
        // Floating drift
        s.pulsePhase += s.pulseSpeed;
        const pulse = 1 + Math.sin(s.pulsePhase) * 0.08;
        const currentRadius = s.radius * pulse;

        s.angle += s.rotationSpeed;
        s.x += s.vx;
        s.y += s.vy;

        // Bounce gently off bounds
        if (s.x < s.radius || s.x > width - s.radius) s.vx *= -1;
        if (s.y < s.radius || s.y > height - s.radius) s.vy *= -1;

        // Interactive mouse deflection
        const dx = s.x - mouse.x;
        const dy = s.y - mouse.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const maxDist = 260;

        if (dist < maxDist && dist > 0) {
          const force = (1 - dist / maxDist) * 1.8;
          s.x += (dx / dist) * force;
          s.y += (dy / dist) * force;
        }

        ctx.save();
        ctx.translate(s.x, s.y);
        ctx.rotate(s.angle);

        if (s.type === 'orb') {
          // Luminescent blurry gradient orb
          const grad = ctx.createRadialGradient(0, 0, 0, 0, 0, currentRadius);
          grad.addColorStop(0, s.colorStart);
          grad.addColorStop(0.7, s.colorEnd);
          grad.addColorStop(1, 'rgba(255, 255, 255, 0)');

          ctx.fillStyle = grad;
          ctx.beginPath();
          ctx.arc(0, 0, currentRadius, 0, Math.PI * 2);
          ctx.fill();
        } else if (s.type === 'ring') {
          // Floating luminous ring
          const ringGrad = ctx.createLinearGradient(
            -currentRadius,
            -currentRadius,
            currentRadius,
            currentRadius
          );
          ringGrad.addColorStop(0, s.colorStart);
          ringGrad.addColorStop(1, s.colorEnd);

          ctx.strokeStyle = ringGrad;
          ctx.lineWidth = 14;
          ctx.shadowColor = 'rgba(168, 85, 247, 0.4)';
          ctx.shadowBlur = 24;
          ctx.beginPath();
          ctx.arc(0, 0, currentRadius, 0, Math.PI * 2);
          ctx.stroke();

          // Inner delicate line
          ctx.lineWidth = 2;
          ctx.beginPath();
          ctx.arc(0, 0, currentRadius * 0.7, 0, Math.PI * 2);
          ctx.stroke();
        } else if (s.type === 'diamond') {
          // Floating luminescent rounded diamond
          const diaGrad = ctx.createLinearGradient(
            0,
            -currentRadius,
            0,
            currentRadius
          );
          diaGrad.addColorStop(0, s.colorStart);
          diaGrad.addColorStop(1, s.colorEnd);

          ctx.fillStyle = diaGrad;
          ctx.strokeStyle = 'rgba(255, 255, 255, 0.6)';
          ctx.lineWidth = 2;
          ctx.shadowColor = 'rgba(192, 132, 252, 0.35)';
          ctx.shadowBlur = 20;

          ctx.beginPath();
          ctx.moveTo(0, -currentRadius);
          ctx.lineTo(currentRadius * 0.75, 0);
          ctx.lineTo(0, currentRadius);
          ctx.lineTo(-currentRadius * 0.75, 0);
          ctx.closePath();
          ctx.fill();
          ctx.stroke();
        } else if (s.type === 'star') {
          // 4-point glowing starburst
          ctx.fillStyle = s.colorStart;
          ctx.shadowColor = s.colorStart;
          ctx.shadowBlur = 20;

          ctx.beginPath();
          const r = currentRadius;
          const inner = r * 0.35;
          for (let i = 0; i < 8; i++) {
            const rad = (i * Math.PI) / 4;
            const distRadius = i % 2 === 0 ? r : inner;
            const px = Math.cos(rad) * distRadius;
            const py = Math.sin(rad) * distRadius;
            if (i === 0) ctx.moveTo(px, py);
            else ctx.lineTo(px, py);
          }
          ctx.closePath();
          ctx.fill();
        } else if (s.type === 'pill') {
          // Luminescent rounded pill / capsule
          const pillGrad = ctx.createLinearGradient(
            -currentRadius,
            0,
            currentRadius,
            0
          );
          pillGrad.addColorStop(0, s.colorStart);
          pillGrad.addColorStop(1, s.colorEnd);

          ctx.fillStyle = pillGrad;
          ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
          ctx.lineWidth = 2;
          ctx.shadowColor = 'rgba(129, 140, 248, 0.35)';
          ctx.shadowBlur = 22;

          const w = currentRadius * 1.4;
          const h = currentRadius * 0.6;
          const r = h / 2;

          ctx.beginPath();
          ctx.moveTo(-w / 2 + r, -h / 2);
          ctx.lineTo(w / 2 - r, -h / 2);
          ctx.arc(w / 2 - r, 0, r, -Math.PI / 2, Math.PI / 2);
          ctx.lineTo(-w / 2 + r, h / 2);
          ctx.arc(-w / 2 + r, 0, r, Math.PI / 2, -Math.PI / 2);
          ctx.closePath();
          ctx.fill();
          ctx.stroke();
        }

        ctx.restore();
      });

      // Render & update click sparkle particles
      sparkles = sparkles.filter((sp) => sp.alpha > 0.02);
      sparkles.forEach((sp) => {
        sp.x += sp.vx;
        sp.y += sp.vy;
        sp.vx *= 0.94;
        sp.vy *= 0.94;
        sp.alpha *= 0.92;
        sp.rotation += sp.vRot;

        ctx.save();
        ctx.translate(sp.x, sp.y);
        ctx.rotate(sp.rotation);
        ctx.globalAlpha = sp.alpha;
        ctx.fillStyle = sp.color;
        ctx.shadowColor = sp.color;
        ctx.shadowBlur = 10;

        // Draw 4-point sparkle star
        const r = sp.size;
        const inner = r * 0.25;
        ctx.beginPath();
        for (let i = 0; i < 8; i++) {
          const rad = (i * Math.PI) / 4;
          const distRadius = i % 2 === 0 ? r : inner;
          const px = Math.cos(rad) * distRadius;
          const py = Math.sin(rad) * distRadius;
          if (i === 0) ctx.moveTo(px, py);
          else ctx.lineTo(px, py);
        }
        ctx.closePath();
        ctx.fill();
        ctx.restore();
      });

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handlePointerMove);
      window.removeEventListener('touchmove', handlePointerMove);
      window.removeEventListener('pointerdown', handlePointerDown);
      window.removeEventListener('mouseleave', handlePointerLeave);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      style={{
        position: 'fixed',
        inset: 0,
        width: '100vw',
        height: '100vh',
        pointerEvents: 'none',
        zIndex: 0,
      }}
    />
  );
};
