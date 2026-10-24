import { makeRequest, resolveSignal } from './core.mjs';

export function routeOffline(visitorText, screen) {
  const request = makeRequest(visitorText, screen);
  return request.status === 'NO_DATA' ? request : resolveSignal(request);
}

export { makeRequest, moderateLocally, routeOnline } from './core.mjs';
