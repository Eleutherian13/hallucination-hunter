'use client';

import { motion } from 'framer-motion';
import { Bell, Search, User, ChevronDown } from 'lucide-react';

interface HeaderProps {
  title: string;
  description?: string;
}

export default function Header({ title, description }: HeaderProps) {
  return (
    <header className="sticky top-0 z-40 bg-dark-bg/80 backdrop-blur-xl border-b border-dark-border">
      <div className="flex items-center justify-between px-8 py-4">
        {/* Page Title */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <h1 className="text-2xl font-bold text-dark-text">{title}</h1>
          {description && (
            <p className="text-sm text-dark-muted mt-0.5">{description}</p>
          )}
        </motion.div>

        {/* Right Actions */}
        <div className="flex items-center gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-muted" />
            <input
              type="text"
              placeholder="Search..."
              className="w-64 pl-10 pr-4 py-2 rounded-xl bg-dark-card border border-dark-border text-sm text-dark-text placeholder:text-dark-muted focus:outline-none focus:border-primary-500 transition-colors"
            />
          </div>

          {/* Notifications */}
          <button className="relative p-2 rounded-xl hover:bg-dark-card transition-colors">
            <Bell className="w-5 h-5 text-dark-muted" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-primary-500 rounded-full" />
          </button>

          {/* Profile */}
          <button className="flex items-center gap-2 p-2 rounded-xl hover:bg-dark-card transition-colors">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center">
              <User className="w-4 h-4 text-white" />
            </div>
            <ChevronDown className="w-4 h-4 text-dark-muted" />
          </button>
        </div>
      </div>
    </header>
  );
}
