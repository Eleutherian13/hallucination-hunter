"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Layout } from "@/components/layout";
import {
  Settings as SettingsIcon,
  Sliders,
  Palette,
  Bell,
  Shield,
  Database,
  Zap,
  Save,
  RefreshCw,
  Check,
} from "lucide-react";

const defaultSettings = {
  confidenceThreshold: 0.7,
  enableCorrections: true,
  enableSemanticMatching: true,
  showUnverifiable: true,
  maxClaimsPerDocument: 50,
  theme: "dark",
  showConfidencePercent: true,
  enableClickToScroll: true,
  highlightSource: true,
  enableNotifications: false,
  autoSaveResults: true,
};

export default function SettingsPage() {
  const [settings, setSettings] = useState(defaultSettings);

  const [saved, setSaved] = useState(false);

  // Load settings from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem("verification_settings");
    if (stored) {
      try {
        setSettings(JSON.parse(stored));
      } catch (error) {
        console.error("Failed to load settings:", error);
      }
    }
  }, []);

  const handleSave = () => {
    // Save to localStorage
    localStorage.setItem("verification_settings", JSON.stringify(settings));
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleReset = () => {
    setSettings(defaultSettings);
    localStorage.setItem(
      "verification_settings",
      JSON.stringify(defaultSettings),
    );
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const updateSetting = (key: string, value: any) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <Layout
      title="Settings"
      description="Configure your verification preferences"
      pageTitle="Settings"
    >
      <div className="max-w-4xl">
        {/* Save Banner */}
        {saved && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="mb-6 p-4 rounded-xl bg-verified/20 border border-verified/30 flex items-center gap-3"
          >
            <Check className="w-5 h-5 text-verified" />
            <span className="text-verified">Settings saved successfully!</span>
          </motion.div>
        )}

        <div className="space-y-6">
          {/* Verification Settings */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card overflow-hidden"
          >
            <div className="p-4 border-b border-dark-border flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-primary-500/20 flex items-center justify-center">
                <Sliders className="w-5 h-5 text-primary-400" />
              </div>
              <div>
                <h2 className="font-semibold text-dark-text">
                  Verification Settings
                </h2>
                <p className="text-sm text-dark-muted">
                  Configure how claims are verified
                </p>
              </div>
            </div>
            <div className="p-6 space-y-6">
              {/* Confidence Threshold */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="font-medium text-dark-text">
                    Confidence Threshold
                  </label>
                  <span className="text-sm text-primary-400">
                    {(settings.confidenceThreshold * 100).toFixed(0)}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={settings.confidenceThreshold * 100}
                  onChange={(e) =>
                    updateSetting(
                      "confidenceThreshold",
                      parseInt(e.target.value) / 100,
                    )
                  }
                  className="w-full h-2 bg-dark-border rounded-full appearance-none cursor-pointer slider"
                />
                <p className="text-xs text-dark-muted mt-1">
                  Minimum confidence score to consider a claim as verified
                </p>
              </div>

              {/* Max Claims */}
              <div>
                <label className="block font-medium text-dark-text mb-2">
                  Max Claims per Document
                </label>
                <input
                  type="number"
                  value={settings.maxClaimsPerDocument}
                  onChange={(e) =>
                    updateSetting(
                      "maxClaimsPerDocument",
                      parseInt(e.target.value),
                    )
                  }
                  className="input-field w-32"
                />
                <p className="text-xs text-dark-muted mt-1">
                  Limit the number of claims extracted from each document
                </p>
              </div>

              {/* Toggle Options */}
              <div className="space-y-4">
                <ToggleOption
                  label="Auto-generate Corrections"
                  description="Automatically suggest corrections for hallucinated content"
                  enabled={settings.enableCorrections}
                  onChange={(v) => updateSetting("enableCorrections", v)}
                />
                <ToggleOption
                  label="Semantic Similarity Matching"
                  description="Use embedding-based matching for better evidence retrieval"
                  enabled={settings.enableSemanticMatching}
                  onChange={(v) => updateSetting("enableSemanticMatching", v)}
                />
                <ToggleOption
                  label="Show Unverifiable Claims"
                  description="Display claims that cannot be verified against sources"
                  enabled={settings.showUnverifiable}
                  onChange={(v) => updateSetting("showUnverifiable", v)}
                />
              </div>
            </div>
          </motion.div>

          {/* Display Settings */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="glass-card overflow-hidden"
          >
            <div className="p-4 border-b border-dark-border flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-purple-500/20 flex items-center justify-center">
                <Palette className="w-5 h-5 text-purple-400" />
              </div>
              <div>
                <h2 className="font-semibold text-dark-text">
                  Display Settings
                </h2>
                <p className="text-sm text-dark-muted">
                  Customize the interface appearance
                </p>
              </div>
            </div>
            <div className="p-6 space-y-6">
              {/* Theme Selection */}
              <div>
                <label className="block font-medium text-dark-text mb-3">
                  Theme
                </label>
                <div className="flex gap-3">
                  {["dark", "light", "system"].map((theme) => (
                    <button
                      key={theme}
                      onClick={() => updateSetting("theme", theme)}
                      className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-all ${
                        settings.theme === theme
                          ? "bg-primary-500 text-white"
                          : "bg-dark-card border border-dark-border text-dark-muted hover:text-dark-text"
                      }`}
                    >
                      {theme}
                    </button>
                  ))}
                </div>
              </div>

              {/* Toggle Options */}
              <div className="space-y-4">
                <ToggleOption
                  label="Show Confidence Percentages"
                  description="Display numerical confidence values"
                  enabled={settings.showConfidencePercent}
                  onChange={(v) => updateSetting("showConfidencePercent", v)}
                />
                <ToggleOption
                  label="Click-to-Scroll Navigation"
                  description="Clicking a claim scrolls to its source evidence"
                  enabled={settings.enableClickToScroll}
                  onChange={(v) => updateSetting("enableClickToScroll", v)}
                />
                <ToggleOption
                  label="Highlight Source Paragraphs"
                  description="Visually highlight the relevant source content"
                  enabled={settings.highlightSource}
                  onChange={(v) => updateSetting("highlightSource", v)}
                />
              </div>
            </div>
          </motion.div>

          {/* System Settings */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="glass-card overflow-hidden"
          >
            <div className="p-4 border-b border-dark-border flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-orange-500/20 flex items-center justify-center">
                <Database className="w-5 h-5 text-orange-400" />
              </div>
              <div>
                <h2 className="font-semibold text-dark-text">
                  System Settings
                </h2>
                <p className="text-sm text-dark-muted">
                  Advanced configuration options
                </p>
              </div>
            </div>
            <div className="p-6 space-y-4">
              <ToggleOption
                label="Enable Notifications"
                description="Receive alerts when verification is complete"
                enabled={settings.enableNotifications}
                onChange={(v) => updateSetting("enableNotifications", v)}
              />
              <ToggleOption
                label="Auto-save Results"
                description="Automatically save verification results locally"
                enabled={settings.autoSaveResults}
                onChange={(v) => updateSetting("autoSaveResults", v)}
              />
            </div>
          </motion.div>

          {/* Action Buttons */}
          <div className="flex gap-4">
            <button onClick={handleSave} className="btn-primary">
              <Save className="w-4 h-4" />
              Save Settings
            </button>
            <button onClick={handleReset} className="btn-secondary">
              <RefreshCw className="w-4 h-4" />
              Reset to Defaults
            </button>
          </div>
        </div>
      </div>
    </Layout>
  );
}

function ToggleOption({
  label,
  description,
  enabled,
  onChange,
}: {
  label: string;
  description: string;
  enabled: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <p className="font-medium text-dark-text">{label}</p>
        <p className="text-sm text-dark-muted">{description}</p>
      </div>
      <button
        onClick={() => onChange(!enabled)}
        className={`relative w-12 h-6 rounded-full transition-colors ${
          enabled ? "bg-primary-500" : "bg-dark-border"
        }`}
      >
        <span
          className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${
            enabled ? "translate-x-7" : "translate-x-1"
          }`}
        />
      </button>
    </div>
  );
}
