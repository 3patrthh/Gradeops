import { apiRequest } from './api';

export function getExams() {
  return apiRequest('/exams');
}

export function uploadExam({ examName, course, semester, gradingModel, files }) {
  const formData = new FormData();
  formData.append('exam_name', examName);
  formData.append('course', course);
  formData.append('semester', semester || 'Fall 2024');
  formData.append('grading_model', gradingModel || 'qwen-vl');

  files.forEach((file) => {
    if (file.rawFile) formData.append('files', file.rawFile);
  });

  return apiRequest('/exams/upload', {
    method: 'POST',
    body: formData,
  });
}
