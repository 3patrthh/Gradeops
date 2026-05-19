import { apiRequest } from './api';

export function getReviewQueue() {
  return apiRequest('/reviews/queue');
}

export function approveReview(paperId) {
  return apiRequest(`/reviews/${paperId}/approve`, { method: 'POST' });
}

export function overrideReview(paperId, payload) {
  return apiRequest(`/reviews/${paperId}/override`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function flagReview(paperId, payload) {
  return apiRequest(`/reviews/${paperId}/flag`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
