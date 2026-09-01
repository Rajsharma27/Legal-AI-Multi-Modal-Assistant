const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function queryRAG(question, docType = null) {
  const res = await fetch(`${BASE_URL}/api/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, doc_type: docType || null }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Query failed');
  }
  return res.json();
}

export function streamQueryRAG(question, docType = null, onChunk, onComplete, onError) {
  const params = new URLSearchParams({ question });
  if (docType) params.append('doc_type', docType);

  const eventSource = new EventSource(`${BASE_URL}/api/query/stream?${params.toString()}`);

  eventSource.onmessage = (event) => {
    if (event.data === '[DONE]') {
      eventSource.close();
      onComplete?.();
    } else {
      onChunk?.(event.data);
    }
  };

  eventSource.onerror = (err) => {
    eventSource.close();
    onError?.(err);
  };

  return () => eventSource.close();
}

export async function uploadDocument(file, onProgress) {
  const form = new FormData();
  form.append('file', file);
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${BASE_URL}/api/ingest`);
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) onProgress?.(Math.round((e.loaded / e.total) * 100));
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText));
      } else {
        reject(new Error('Upload failed'));
      }
    };
    xhr.onerror = () => reject(new Error('Network error'));
    xhr.send(form);
  });
}

export async function fetchDocuments() {
  const res = await fetch(`${BASE_URL}/api/documents`);
  if (!res.ok) throw new Error('Fetch documents failed');
  return res.json();
}

export async function deleteDocument(docId) {
  const res = await fetch(`${BASE_URL}/api/documents/${docId}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Delete document failed');
  return res.json();
}

export async function fetchHealth() {
  const res = await fetch(`${BASE_URL}/api/health`);
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}
