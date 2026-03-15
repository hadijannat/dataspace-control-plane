import type { InputHTMLAttributes } from 'react';

interface TextInputProps extends InputHTMLAttributes<HTMLInputElement> { error?: boolean; }

export function TextInput({ error, className = '', ...props }: TextInputProps) {
  return (
    <input
      className={`block w-full rounded-md border text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
        error ? 'border-red-300 focus:ring-red-500' : 'border-gray-300'
      } ${className}`}
      {...props}
    />
  );
}
