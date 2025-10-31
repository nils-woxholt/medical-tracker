import { redirect } from 'next/navigation';

export default function AuthLoginAlias() {
  // Alias page for older E2E specs expecting /auth/login
  redirect('/access?mode=login');
}