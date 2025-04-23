import { render, screen } from '@testing-library/react';
import App from './FrontPage';

/* 
    Just for debugging and testing the frontend
*/
test('renders learn react link', () => {
  render(<App />);
  const linkElement = screen.getByText(/learn react/i);
  expect(linkElement).toBeInTheDocument();
});
