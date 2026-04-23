import { motion, useMotionValue, useSpring } from "framer-motion";
import { useEffect } from "react";

export function MeshBackground() {
  const mx = useMotionValue(0);
  const my = useMotionValue(0);
  const sx = useSpring(mx, { stiffness: 60, damping: 20, mass: 0.5 });
  const sy = useSpring(my, { stiffness: 60, damping: 20, mass: 0.5 });

  useEffect(() => {
    const reduced = window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;
    const finePointer = window.matchMedia?.("(pointer: fine)")?.matches;
    if (reduced || !finePointer) return;

    let raf = 0;
    let lx = 0;
    let ly = 0;

    const tick = () => {
      raf = 0;
      mx.set(lx);
      my.set(ly);
    };

    const onMove = (e: PointerEvent) => {
      lx = (e.clientX / window.innerWidth - 0.5) * 28;
      ly = (e.clientY / window.innerHeight - 0.5) * 18;
      if (!raf) raf = window.requestAnimationFrame(tick);
    };

    window.addEventListener("pointermove", onMove, { passive: true });
    return () => {
      window.removeEventListener("pointermove", onMove);
      if (raf) window.cancelAnimationFrame(raf);
    };
  }, [mx, my]);

  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      <div className="absolute inset-0 bg-[size:48px_48px] bg-grid-fade opacity-[0.10] dark:opacity-[0.18]" />
      <motion.div
        className="absolute -left-[20%] -top-[30%] h-[70vmin] w-[70vmin] rounded-full bg-black/[0.08] blur-[110px] dark:bg-white/[0.06] will-change-transform"
        style={{ x: sx, y: sy }}
        animate={{ opacity: [0.5, 0.85, 0.5], scale: [1, 1.05, 1] }}
        transition={{ duration: 14, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute -right-[15%] top-[5%] h-[55vmin] w-[55vmin] rounded-full bg-black/[0.06] blur-[110px] dark:bg-white/[0.05] will-change-transform"
        style={{ x: sx, y: sy }}
        animate={{ opacity: [0.35, 0.7, 0.35], x: [0, 12, 0] }}
        transition={{ duration: 18, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute bottom-[-20%] left-[25%] h-[50vmin] w-[50vmin] rounded-full bg-black/[0.05] blur-[110px] dark:bg-white/[0.04] will-change-transform"
        style={{ x: sx, y: sy }}
        animate={{ opacity: [0.25, 0.55, 0.25] }}
        transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
      />
    </div>
  );
}
