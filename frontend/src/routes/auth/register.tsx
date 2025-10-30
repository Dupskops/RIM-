import { createFileRoute } from '@tanstack/react-router';
import RegisterPage from '@/pages/RegisterPage';
import { requireGuest } from '@/lib/auth-guard';

export const Route = createFileRoute('/auth/register')({
  beforeLoad: requireGuest,
  component: RegisterPage,
});
