const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function queryRAG(question, docType = null) {
  const res = await fetch(`${BASE_URL}/api/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, doc_type: docType || null }),
  });
  if (!res.ok) throw new Error('Query failed');
  return res.json();
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
    xhr.onload = () =>
      xhr.status === 200
        ? resolve(JSON.parse(xhr.responseText))
        : reject(new Error('Upload failed'));
    xhr.onerror = () => reject(new Error('Network error'));
    xhr.send(form);
  });
}

export async function fetchDocuments() {
  const res = await fetch(`${BASE_URL}/api/documents`);
  if (!res.ok) throw new Error('Fetch failed');
  return res.json();
}
