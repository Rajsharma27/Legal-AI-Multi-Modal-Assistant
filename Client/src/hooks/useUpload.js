import { useState, useCallback } from 'react';
import { uploadDocument } from '../services/api';

export function useUpload() {
  const [files, setFiles] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);

  const addFiles = useCallback((newFiles) => {
    const items = newFiles.map((f) => ({
      file: f,
      name: f.name,
      progress: 0,
      status: 'queue', // 'queue' | 'uploading' | 'done' | 'error'
    }));
    setFiles((prev) => [...prev, ...items]);
  }, []);

  const removeFile = useCallback((index) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const clearFiles = useCallback(() => {
    setFiles([]);
  }, []);

  const processAll = useCallback(async () => {
    setIsProcessing(true);
    for (let i = 0; i < files.length; i++) {
      if (files[i].status !== 'queue') continue;

      setFiles((prev) =>
        prev.map((f, j) => (j === i ? { ...f, status: 'uploading' } : f))
      );

      try {
        await uploadDocument(files[i].file, (pct) => {
          setFiles((prev) =>
            prev.map((f, j) => (j === i ? { ...f, progress: pct } : f))
          );
        });
        setFiles((prev) =>
          prev.map((f, j) => (j === i ? { ...f, progress: 100, status: 'done' } : f))
        );
      } catch (err) {
        setFiles((prev) =>
          prev.map((f, j) => (j === i ? { ...f, status: 'error' } : f))
        );
      }
    }
    setIsProcessing(false);
  }, [files]);

  return {
    files,
    isProcessing,
    addFiles,
    removeFile,
    clearFiles,
    processAll,
  };
}

export default useUpload;
