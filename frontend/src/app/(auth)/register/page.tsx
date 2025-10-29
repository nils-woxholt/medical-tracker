// Registration page (T035)
import React, { useEffect, useRef } from 'react';
import RegisterForm from '../../../components/auth/RegisterForm';

export default function RegisterPage() {
  const headingRef = useRef<HTMLHeadingElement | null>(null);
  useEffect(() => {
    headingRef.current?.focus();
  }, []);
  return (
    <div className="max-w-md mx-auto p-4">
      <h1 ref={headingRef} tabIndex={-1} className="text-xl font-semibold mb-4">Create Account</h1>
      <RegisterForm />
    </div>
  );
}
