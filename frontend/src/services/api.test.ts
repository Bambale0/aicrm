import { shouldExpireSession } from './api';

describe('admin session invalidation', () => {
  it('expires an existing session on protected API 401', () => {
    expect(
      shouldExpireSession(401, '/messengers', 'existing-token'),
    ).toBe(true);
  });

  it('does not expire the current session for a failed login attempt', () => {
    expect(
      shouldExpireSession(401, '/auth/login/json', 'existing-token'),
    ).toBe(false);
  });

  it('does not emit expiry when there is no stored session', () => {
    expect(
      shouldExpireSession(401, '/messengers', null),
    ).toBe(false);
  });

  it('does not expire a session for non-authentication failures', () => {
    expect(
      shouldExpireSession(502, '/messengers', 'existing-token'),
    ).toBe(false);
  });
});
