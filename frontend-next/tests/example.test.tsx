import { test, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import Header from '@/components/Header';

test('renders Connect Etsy button', () => {
  render(<Header />);

  const connectButton = screen.getByRole('button', { name: /connect etsy/i });
  expect(connectButton).toBeDefined();
});