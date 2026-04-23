import { motion } from "framer-motion";
import clsx from "clsx";
import { Sparkles } from "lucide-react";
import type { ArchetypeItem } from "@/types";

type Props = {
  items: ArchetypeItem[];
  onPick: (item: ArchetypeItem) => void;
  disabled?: boolean;
};

export function ArchetypeChips({ items, onPick, disabled }: Props) {
  if (!items.length) return null;

  return (
    <section className="mb-8">
      <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.14em] text-ink-500 dark:text-ink-400">
        <Sparkles className="h-3.5 w-3.5 text-accent" aria-hidden />
        Quick fill from sample roles
      </div>
      <div className="no-scrollbar flex gap-2 overflow-x-auto pb-1">
        {items.map((item, i) => (
          <motion.button
            key={item.id}
            type="button"
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.04, duration: 0.35 }}
            whileHover={{ y: -1 }}
            whileTap={{ scale: 0.98 }}
            disabled={disabled}
            onClick={() => onPick(item)}
            className={clsx(
              "shrink-0 rounded-full border border-black/10 bg-black/[0.03] px-4 py-2 text-left text-sm font-medium text-ink-800 shadow-sm backdrop-blur-md transition-colors",
              "hover:border-accent/40 hover:bg-accent/10 hover:text-ink-950",
              "dark:border-white/10 dark:bg-white/[0.04] dark:text-ink-100 dark:hover:text-white",
              "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent",
              disabled && "pointer-events-none opacity-40",
            )}
          >
            {item.title}
          </motion.button>
        ))}
      </div>
    </section>
  );
}
