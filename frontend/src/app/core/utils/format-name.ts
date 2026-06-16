export function emailToDisplayName(email: string): string {
  const name = email.split('@')[0] || '';
  return name
    .split('.')
    .map(p => p.replace(/\d+$/, ''))
    .filter(p => p.length > 0)
    .map(p => p.charAt(0).toUpperCase() + p.slice(1))
    .join(' ');
}
