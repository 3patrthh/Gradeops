import { apiRequest } from './api';

export function login({ email, password, role }) {
  return apiRequest('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password, role }),
  });
}
