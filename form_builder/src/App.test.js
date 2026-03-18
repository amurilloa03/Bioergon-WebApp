import { render, screen } from '@testing-library/react';
import App from './App';

test('renders form builder app', () => {
  // Simular que estamos en la ruta /form-builder
  delete window.location;
  window.location = { pathname: '/form-builder', search: '', href: '' };

  render(<App />);
  const heading = screen.getByText(/Constructor de Formularios/i);
  expect(heading).toBeInTheDocument();
});
