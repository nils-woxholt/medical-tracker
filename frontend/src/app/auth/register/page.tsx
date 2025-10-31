import { redirect } from 'next/navigation';

export default function AuthRegisterAlias() {
  // Alias page for older E2E specs expecting /auth/register
  redirect('/access?mode=register');
}