"use client";

import Link from "next/link";
import { useRouter } from "next/router";
import { motion } from "framer-motion";
import {
  Search,
  Home,
  FileText,
  GitBranch,
  BarChart3,
  Settings,
  HelpCircle,
  Zap,
} from "lucide-react";

const navigation = [
  { name: "Home", href: "/", icon: Home },
  { name: "Verify", href: "/verify", icon: Search },
  { name: "Results", href: "/results", icon: FileText },
  { name: "Pipeline", href: "/pipeline", icon: GitBranch },
  { name: "Benchmarks", href: "/benchmarks", icon: BarChart3 },
];

const secondaryNav = [
  { name: "Settings", href: "/settings", icon: Settings },
  { name: "Documentation", href: "/docs", icon: HelpCircle },
];

export default function Sidebar() {
  const router = useRouter();

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-dark-card/50 backdrop-blur-xl border-r border-dark-border flex flex-col z-50">
      {/* Logo */}
      <div className="p-6 border-b border-dark-border">
        <Link href="/" className="flex items-center gap-3 group">
          <motion.div
            whileHover={{ rotate: 360 }}
            transition={{ duration: 0.5 }}
            className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center shadow-glow-sm"
          >
            <Zap className="w-5 h-5 text-white" />
          </motion.div>
          <div>
            <h1 className="font-bold text-lg gradient-text">Hallucination</h1>
            <p className="text-xs text-dark-muted -mt-1">Hunter v2.0</p>
          </div>
        </Link>
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        <p className="text-xs uppercase tracking-wider text-dark-muted mb-3 px-3">
          Main Menu
        </p>
        {navigation.map((item) => {
          const isActive = router.pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={isActive ? "nav-link-active" : "nav-link"}
            >
              <item.icon className="w-5 h-5" />
              {item.name}
              {isActive && (
                <motion.div
                  layoutId="activeNav"
                  className="ml-auto w-1.5 h-1.5 rounded-full bg-primary-500"
                />
              )}
            </Link>
          );
        })}

        <div className="pt-6">
          <p className="text-xs uppercase tracking-wider text-dark-muted mb-3 px-3">
            Support
          </p>
          {secondaryNav.map((item) => {
            const isActive = router.pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={isActive ? "nav-link-active" : "nav-link"}
              >
                <item.icon className="w-5 h-5" />
                {item.name}
              </Link>
            );
          })}
        </div>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-dark-border">
        <div className="glass-card p-4 text-center">
          <p className="text-sm font-medium text-dark-text mb-1">
            E-Summit '26
          </p>
          <p className="text-xs text-dark-muted">DataForge Track 1</p>
        </div>
      </div>
    </aside>
  );
}
