import { apiRequest } from './api';

export function saveRubric(payload) {
  return apiRequest('/rubrics', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function uploadRubricJson(file, linkedExam = '') {
  const formData = new FormData();
  formData.append('file', file);
  if (linkedExam) formData.append('linked_exam', linkedExam);

  return apiRequest('/rubrics/upload-json', {
    method: 'POST',
    body: formData,
  });
}

export function getRubrics() {
  return apiRequest('/rubrics');
}
