"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, File, X, FileText, FileCheck } from "lucide-react";

interface FileUploadProps {
  onFilesSelected: (files: File[]) => void;
  acceptedTypes?: string[];
  multiple?: boolean;
  label: string;
  description: string;
  maxSize?: number;
}

export function FileUpload({
  onFilesSelected,
  acceptedTypes = [".txt", ".pdf", ".docx"],
  multiple = true,
  label,
  description,
  maxSize = 10 * 1024 * 1024, // 10MB
}: FileUploadProps) {
  const [files, setFiles] = useState<File[]>([]);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const newFiles = multiple ? [...files, ...acceptedFiles] : acceptedFiles;
      setFiles(newFiles);
      onFilesSelected(newFiles);
    },
    [files, multiple, onFilesSelected],
  );

  const removeFile = (index: number) => {
    const newFiles = files.filter((_, i) => i !== index);
    setFiles(newFiles);
    onFilesSelected(newFiles);
  };

  const { getRootProps, getInputProps, isDragActive, isDragReject } =
    useDropzone({
      onDrop,
      accept: {
        "text/plain": [".txt"],
        "application/pdf": [".pdf"],
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
          [".docx"],
      },
      multiple,
      maxSize,
    });

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-dark-text">{label}</h3>
          <p className="text-sm text-dark-muted">{description}</p>
        </div>
        {files.length > 0 && (
          <span className="badge-verified">
            <FileCheck className="w-4 h-4" />
            {files.length} file{files.length !== 1 ? "s" : ""} selected
          </span>
        )}
      </div>

      <motion.div
        {...getRootProps()}
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.99 }}
        className={`
          relative border-2 border-dashed rounded-2xl p-8 transition-all duration-200 cursor-pointer
          ${isDragActive && !isDragReject ? "border-primary-500 bg-primary-500/10" : ""}
          ${isDragReject ? "border-hallucination bg-hallucination/10" : ""}
          ${!isDragActive ? "border-dark-border hover:border-primary-500/50 hover:bg-dark-card/50" : ""}
        `}
      >
        <input {...getInputProps()} />

        <div className="flex flex-col items-center text-center">
          <motion.div
            animate={{ y: isDragActive ? -5 : 0 }}
            className={`
              w-16 h-16 rounded-2xl flex items-center justify-center mb-4
              ${isDragActive ? "bg-primary-500/20" : "bg-dark-card"}
            `}
          >
            <Upload
              className={`w-8 h-8 ${isDragActive ? "text-primary-400" : "text-dark-muted"}`}
            />
          </motion.div>

          <p className="text-dark-text font-medium mb-1">
            {isDragActive ? "Drop files here" : "Drag & drop files here"}
          </p>
          <p className="text-sm text-dark-muted">
            or <span className="text-primary-400">browse</span> to upload
          </p>
          <p className="text-xs text-dark-muted mt-2">
            Supported: {acceptedTypes.join(", ")} (Max {formatFileSize(maxSize)}
            )
          </p>
        </div>
      </motion.div>

      {/* File List */}
      <AnimatePresence>
        {files.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-2"
          >
            {files.map((file, index) => (
              <motion.div
                key={`${file.name}-${index}`}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="flex items-center justify-between p-3 rounded-xl bg-dark-card border border-dark-border"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-primary-500/20 flex items-center justify-center">
                    <FileText className="w-5 h-5 text-primary-400" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-dark-text">
                      {file.name}
                    </p>
                    <p className="text-xs text-dark-muted">
                      {formatFileSize(file.size)}
                    </p>
                  </div>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile(index);
                  }}
                  className="p-2 rounded-lg hover:bg-dark-bg transition-colors"
                >
                  <X className="w-4 h-4 text-dark-muted hover:text-hallucination" />
                </button>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

interface TextInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  label: string;
  description: string;
  rows?: number;
}

export function TextInput({
  value,
  onChange,
  placeholder,
  label,
  description,
  rows = 8,
}: TextInputProps) {
  const wordCount = value.trim() ? value.trim().split(/\s+/).length : 0;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-dark-text">{label}</h3>
          <p className="text-sm text-dark-muted">{description}</p>
        </div>
        {wordCount > 0 && (
          <span className="text-sm text-dark-muted">{wordCount} words</span>
        )}
      </div>

      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={rows}
        className="input-field resize-none font-mono text-sm leading-relaxed"
      />
    </div>
  );
}
